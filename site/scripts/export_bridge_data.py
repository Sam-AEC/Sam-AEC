#!/usr/bin/env python3
"""Export machine-readable data from a checkout of aec-model-bridge.

Run it with the bridge installed (``pip install -e packages/mcp-server-revit``):

    python site/scripts/export_bridge_data.py --out site/.cache

It starts the real server registry in mock mode (no Revit, no credentials) and writes:

  tools.json     every tool the default setup registers: name, provider, description,
                 JSON input schema, MCP annotations (readOnlyHint etc.) and the
                 is_mutating flag the approval gate checks
  examples.json  real output of the IFC tools run on a tiny IFC4 file generated
                 here with IfcOpenShell, so the site can show verified output.
"""
import argparse, asyncio, json, os, sys, tempfile
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="site/.cache")
args = ap.parse_args()
out = Path(args.out).resolve()
out.mkdir(parents=True, exist_ok=True)

work = Path(tempfile.mkdtemp(prefix="amb-export-"))
os.environ["MCP_REVIT_MODE"] = "mock"
os.environ["MCP_REVIT_WORKSPACE_DIR"] = str(work)
os.environ["MCP_REVIT_ALLOWED_DIRECTORIES"] = str(work)

from revit_mcp_server import mcp_server  # noqa: E402
import ifcopenshell, ifcopenshell.api  # noqa: E402


def make_ifc(path: Path) -> None:
    f = ifcopenshell.api.run("project.create_file")
    run = lambda usecase, **kw: ifcopenshell.api.run(usecase, f, **kw)
    project = run("root.create_entity", ifc_class="IfcProject", name="Demo")
    run("unit.assign_unit")
    site = run("root.create_entity", ifc_class="IfcSite", name="Site")
    building = run("root.create_entity", ifc_class="IfcBuilding", name="Block A")
    storey = run("root.create_entity", ifc_class="IfcBuildingStorey", name="Level 1")
    run("aggregate.assign_object", products=[site], relating_object=project)
    run("aggregate.assign_object", products=[building], relating_object=site)
    run("aggregate.assign_object", products=[storey], relating_object=building)
    wall = run("root.create_entity", ifc_class="IfcWall", name="Wall-01")
    run("spatial.assign_container", products=[wall], relating_structure=storey)
    pset = run("pset.add_pset", product=wall, name="Pset_WallCommon")
    run("pset.edit_pset", pset=pset, properties={"FireRating": "60"})
    f.write(str(path))


async def main() -> None:
    registry, approval, jobs, _modules, _ws = mcp_server.build_registry()
    mcp_server.registry, mcp_server.approval_provider, mcp_server.job_manager = registry, approval, jobs

    tools = []
    for t in await mcp_server.list_tools():
        a = t.annotations
        pt = registry.lookup_tool(t.name)
        tools.append({
            "provider": registry.lookup_tool_provider(t.name).get_identity(),
            "is_mutating": bool(pt.is_mutating),
            "destructive": bool(pt.destructive),
            "permissions": list(pt.permissions),
            "name": t.name,
            "description": t.description,
            "inputSchema": t.inputSchema,
            "annotations": a.model_dump() if a else {},
        })
    tools.sort(key=lambda x: x["name"])
    (out / "tools.json").write_text(json.dumps(tools, indent=1), encoding="utf-8")

    ifc = work / "demo.ifc"
    make_ifc(ifc)
    examples = {"_note": "Output of the real IFC provider on a small IFC4 file generated with IfcOpenShell. Machine-specific fields are removed."}

    async def call(name, arguments, keep=None):
        res = await registry.lookup_tool_provider(name).execute_tool(name, arguments)
        examples[name] = {"arguments": arguments, "result": keep(res) if keep else res}
        return res

    sample_args = {"ifc_path": "C:\\RevitProjects\\demo.ifc"}
    real = {"ifc_path": str(ifc)}
    r = await registry.lookup_tool_provider("ifc_get_metadata").execute_tool("ifc_get_metadata", real)
    examples["ifc_get_metadata"] = {"arguments": sample_args, "result": {k: r[k] for k in ("schema", "project_name", "units", "georeferencing")}}
    r = await registry.lookup_tool_provider("ifc_get_spatial_structure").execute_tool("ifc_get_spatial_structure", real)
    examples["ifc_get_spatial_structure"] = {"arguments": sample_args, "result": r}
    r = await registry.lookup_tool_provider("ifc_query_elements").execute_tool("ifc_query_elements", {**real, "ifc_class": "IfcWall"})
    examples["ifc_query_elements"] = {"arguments": {**sample_args, "ifc_class": "IfcWall"}, "result": r}
    (out / "examples.json").write_text(json.dumps(examples, indent=1), encoding="utf-8")
    print(f"wrote {len(tools)} tools and {len(examples)-1} examples to {out}")

asyncio.run(main())
