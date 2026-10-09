#!/usr/bin/env python3
"""Build the static site from a checkout of aec-model-bridge. Standard library only.

    python site/build.py --bridge ../aec-model-bridge --data site/.cache --out site/dist

Inputs (all read at build time, nothing is fetched in the browser):
  <bridge>/VERSION, server.json, README.md (integration tables),
  docs/images/*.png                        -> project facts, provider status, images
  <data>/tools.json, examples.json         -> from scripts/export_bridge_data.py
Every internal link is relative, so the site works under /Sam-AEC/ and from any host.
"""
import argparse, html, json, re, shutil, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = "https://github.com/Sam-AEC/aec-model-bridge"
LINKEDIN = "https://www.linkedin.com/in/a-sam-mohammad-92790416b"
PROFILE = "https://github.com/Sam-AEC/Sam-AEC"
FACADEIQ = "https://facadedata.vercel.app/"
esc = html.escape


# ------------------------------------------------------------------ sources
def read_sources(bridge: Path, data: Path) -> dict:
    sha = subprocess.run(["git", "-C", str(bridge), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() or "unknown"
    readme = (bridge / "README.md").read_text(encoding="utf-8")
    tools = json.loads((data / "tools.json").read_text(encoding="utf-8"))

    provider = {t['name']: t['provider'] for t in tools}
    mutating = {t['name']: t['is_mutating'] for t in tools}

    def table(heading_re, ncols):
        m = re.search(heading_re + r".*?\n((?:\|.*\n)+)", readme, re.S)
        rows = []
        if m:
            for l in m.group(1).splitlines()[2:]:
                cells = [c.strip() for c in l.strip().strip("|").split("|")]
                if len(cells) >= ncols:
                    rows.append(cells)
        return rows

    return {
        "sha": sha,
        "version": (bridge / "VERSION").read_text().strip(),
        "server": json.loads((bridge / "server.json").read_text(encoding="utf-8")),
        "tools": tools,
        "examples": json.loads((data / "examples.json").read_text(encoding="utf-8")),
        "provider": provider, "mutating": mutating,
        "revit_versions": table(r"## Supported Revit versions", 3),
        "integrations": table(r"### Other integrations", 2),
        "bridge": bridge,
    }


# provider identity (get_identity() in the bridge source) -> display name, source file,
# status and what you need. Statuses are quoted from the project README's integration table
# where it has one; the rest are "registered by default" because the default listing includes them.
PP = "packages/mcp-server-revit/src/revit_mcp_server/providers/"
PROVIDERS = {
    "revit": ("Revit", PP + "revit.py", "Available", "A running licensed Revit 2024–2027 on Windows with the AEC Model Bridge add-in loaded and a project open."),
    "ifc": ("IFC", PP + "ifc.py", "Available", "Nothing but the server: it reads IFC files with IfcOpenShell, without Revit. Paths must be inside the allowed workspace."),
    "rhino": ("Rhino and Grasshopper", PP + "rhino.py", "Available", "Rhino with the Rhino add-in listening on localhost:3004."),
    "speckle": ("Speckle", PP + "cloud.py", "Available", "A Speckle client ID in your environment."),
    "navisworks": ("Navisworks", PP + "navisworks.py", "In progress", "The provider and its tools are registered, but the Navisworks add-in is not finished."),
    "approval": ("Approval", PP + "approval_provider.py", "Core", "None. These tools manage the human-approval plans that gate every model change."),
    "module": ("Modules", PP + "module_provider.py", "Registered by default", "Snapshots, parameter tools, QA/QC checks, recipes and reports built on module manifests. Many need a snapshot or a live Revit model."),
    "graph": ("Semantic graph", PP + "graph.py", "Registered by default", "Works on saved model snapshots."),
    "semantic": ("Snapshots", PP + "semantic_provider.py", "Registered by default", "Take, query and diff model snapshots. Taking one needs a live Revit model."),
    "exporter": ("SQLite exporter", PP + "exporter.py", "Registered by default", "Writes into the allowed workspace."),
    "mapper": ("AEC mapper", PP + "identity_mapper.py", "Registered by default", "None beyond the allowed workspace."),
    "jobs": ("Jobs", PP + "job_provider.py", "Registered by default", "None. Inspect and cancel background jobs."),
}
KIND_LABEL = {"read": "Read-only", "model": "Changes the model (approval required)", "state": "Writes files or state, not the model"}


def classify(name, s):
    t = next(x for x in s["tools"] if x["name"] == name) if isinstance(name, str) else name
    if t["annotations"].get("readOnlyHint"):
        return "read"
    return "model" if t["is_mutating"] else "state"


# ------------------------------------------------------------------ workflows
# Every tool named here is checked against the exported tool list at build time.
WORKFLOWS = [
    {"id": "warnings", "title": "Inspect model warnings", "tools": ["revit_get_warnings"],
     "prompt": "List the current warnings in the open Revit project. Group them by warning type, count each group, and tell me which three groups to fix first and why. Only read the model; do not change anything.",
     "expect": "The warning list for the active project, as the Revit tool returns it (for example overlapping or duplicate elements). Read-only, so no approval is needed.",
     "limits": "Needs a live Revit session with a project open. In mock mode the tool returns only a placeholder."},
    {"id": "parameters", "title": "Read parameters on elements", "tools": ["revit_list_elements", "revit_get_element_parameters", "revit_get_parameter_value"],
     "prompt": "In the open Revit project, list the elements in the Doors category. For the first five, read the Fire Rating parameter and show the element id, name and value in a table. Only read the model.",
     "expect": "Element ids from the category listing, then the named parameter per element. Use revit_get_element_parameters when you want every parameter on one element.",
     "limits": "Parameter names must match the project exactly. Reads are not approval-gated; writing a value later is."},
    {"id": "sheets", "title": "Prepare a sheet workflow", "tools": ["revit_list_sheets", "revit_list_levels", "plan_actions", "revit_renumber_sheets", "approve_plan", "execute_plan"],
     "prompt": "List the existing sheets and levels. Then draft a plan, without running it, that renumbers all sheets with the prefix \"A-\" starting at 101. Show me the plan so I can review it in the Revit panel.",
     "expect": "A draft plan that records the before-state of each change. Nothing in the model changes until you approve the plan; execute_plan then runs it in one named transaction.",
     "limits": "Renumbering touches every sheet, so review the plan. With MCP_REVIT_APPROVAL_MODE=auto the human check is off; do not use that on real projects."},
    {"id": "ifc", "title": "Query IFC properties without Revit", "tools": ["ifc_get_spatial_structure", "ifc_query_elements", "ifc_get_properties"],
     "prompt": "Open C:\\RevitProjects\\demo.ifc. Show the spatial structure, then find every IfcWall and read the properties of the first one. Only read the file.",
     "expect": "The spatial hierarchy with element counts per storey, a list of matching elements (id, GUID, class, name), then property sets for the chosen element. Real output from a small test file is shown below.",
     "limits": "The file must be inside MCP_REVIT_ALLOWED_DIRECTORIES. Large IFC files may take time to open. Read-only."},
]


# ------------------------------------------------------------------ html shell
NAV = [("index.html", "Home"), ("projects.html", "Projects"), ("bridge.html", "AEC Model Bridge"), ("tools.html", "Tools & workflows"), ("about.html", "About")]


def page(fname, title, desc, body, s):
    nav = "".join(f'<a href="{h}"{" aria-current=\"page\"" if h == fname else ""}>{esc(t)}</a>' for h, t in NAV)
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title><meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="img/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="static/style.css"></head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="top"><div class="wrap bar"><a class="brand" href="index.html">A. Sam Mohammad</a><nav aria-label="Main">{nav}</nav></div></header>
<main id="main" class="wrap">
{body}
</main>
<footer class="wrap foot"><p>Built from <a href="{REPO}/tree/{s["sha"]}">aec-model-bridge</a> v{esc(s["version"])} at commit <code>{s["sha"][:7]}</code>. This static site documents the MCP server; it does not run Revit or the live bridge. <a href="{PROFILE}">Profile source</a></p></footer>
<script src="static/site.js" defer></script>
</body></html>'''


def src_link(s, path, label=None):
    return f'<a href="{REPO}/blob/{s["sha"]}/{path}">{esc(label or path)}</a>'


def anchor(provider_name):
    return re.sub(r"[^a-z0-9 -]", "", provider_name.lower() + " provider").replace(" ", "-")


# ------------------------------------------------------------------ pages
def p_home(s):
    n = len(s["tools"])
    body = f'''
<section class="hero"><p class="eyebrow">BIM · AEC automation</p>
<h1>Engineering knowledge, turned into working software.</h1>
<p class="lead">I'm A. Sam Mohammad, a product engineer with more than 15 years in construction and façade engineering. I build tools that connect BIM models, geometry and software so construction work becomes repeatable.</p>
<p class="cta"><a class="btn primary" href="bridge.html">Explore AEC Model Bridge</a><a class="btn" href="{LINKEDIN}">Discuss a collaboration</a></p></section>

<section aria-labelledby="work"><h2 id="work">Selected work</h2>
<div class="grid2">
<article class="card"><h3><a href="bridge.html">AEC Model Bridge</a></h3>
<p>An open-source MCP server and Revit add-in that lets AI assistants such as Claude and Codex work inside a Revit model. The assistant proposes a plan, you approve it in Revit, and only then does the model change.</p>
<ul class="facts"><li>{n} tools in the default setup</li><li>Revit 2024–2027</li><li>v{esc(s["version"])}</li></ul>
<p><a href="bridge.html">How it works</a> · <a href="tools.html">Browse the tools</a> · <a href="{REPO}">Source on GitHub</a></p></article>
<article class="card"><h3><a href="projects.html#facadeiq">FacadeIQ <span class="tag">Beta</span></a></h3>
<p>A free web platform that automates several early-stage façade engineering calculations and environmental checks, so teams get a faster first technical overview before detailed engineering.</p>
<p><a href="{FACADEIQ}">Open FacadeIQ</a> · <a href="projects.html#facadeiq">Project notes</a></p></article>
</div></section>

<section aria-labelledby="flow"><h2 id="flow">Why the approval step matters</h2>
<p>AI assistants can read a model at any time. Any change to it needs a plan that a person reviews first.</p>
{picture("approval-flow", "Approval flow: the assistant proposes a plan, the hub shows it in the Revit panel, and only after you approve does the add-in run it in one named transaction.")}
<p><a href="bridge.html#approval">Read how approval works</a></p></section>
'''
    return page("index.html", "A. Sam Mohammad: BIM and AEC automation", "Product engineer building BIM and AEC automation: AEC Model Bridge, an MCP server for Revit, and FacadeIQ.", body, s)


def picture(name, alt):
    return (f'<figure><picture><source media="(prefers-color-scheme: dark)" srcset="img/{name}-dark.png">'
            f'<img src="img/{name}-light.png" alt="{esc(alt)}" loading="lazy" width="900"></picture>'
            f'<figcaption>Diagram from the project repository.</figcaption></figure>')


def p_projects(s):
    body = f'''
<h1>Projects</h1>
<p class="lead">Two projects, one idea: engineering work that is repeatable because it lives in software.</p>
<article class="card wide" id="aec-model-bridge"><h2>AEC Model Bridge</h2>
<dl class="meta"><dt>What it enables</dt><dd>AI assistants read and edit Revit models through MCP tools. Every model change goes through a plan a person approves first.</dd>
<dt>Who it helps</dt><dd>BIM managers, computational designers and engineers who want to automate documentation, parameter and QA work without giving an AI unchecked write access.</dd>
<dt>Maturity</dt><dd>Released (v{esc(s["version"])}), with CI on the main branch and installable add-in packages per Revit year. Navisworks and Power BI are in progress.</dd>
<dt>License</dt><dd>GPL-3.0-or-later with a Revit linking exception, or a commercial license. See {src_link(s, "LICENSING.md")}.</dd>
<dt>Try it</dt><dd>Start in mock mode without Revit (<a href="bridge.html#try">instructions</a>), or <a href="{REPO}/releases/latest">download a release</a>.</dd>
<dt>Inspect</dt><dd><a href="{REPO}">Source</a> · <a href="tools.html">Tool catalogue</a> · {src_link(s, "docs/security.md", "Security notes")}</dd></dl></article>
<article class="card wide" id="facadeiq"><h2>FacadeIQ <span class="tag">Beta</span></h2>
<dl class="meta"><dt>What it enables</dt><dd>Faster first-pass façade engineering calculations and environmental checks in the browser.</dd>
<dt>Who it helps</dt><dd>Façade engineers, architects and developers who need a technical overview before detailed engineering starts.</dd>
<dt>Maturity</dt><dd>Beta and free to use. Its feature list and limits are described on the live site, not copied here.</dd>
<dt>Try it</dt><dd><a href="{FACADEIQ}">facadedata.vercel.app</a></dd></dl></article>
'''
    return page("projects.html", "Projects: A. Sam Mohammad", "AEC Model Bridge and FacadeIQ: what they enable, who they help and how mature they are.", body, s)


def p_bridge(s):
    rows = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td><td>{esc(c)}</td></tr>" for a, b, c in [r[:3] for r in s["revit_versions"]])
    integ = "".join(f"<tr><td>{esc(a)}</td><td>{esc(b)}</td></tr>" for a, b in [r[:2] for r in s["integrations"]])
    cfg = json.dumps({"mcpServers": {"aec-model-bridge": {"command": "uvx", "args": ["--from", f"git+{REPO}#subdirectory=packages/mcp-server-revit", "aec-model-bridge"],
                      "env": {"MCP_REVIT_MODE": "mock", "MCP_REVIT_WORKSPACE_DIR": "C:\\RevitProjects", "MCP_REVIT_ALLOWED_DIRECTORIES": "C:\\RevitProjects"}}}}, indent=2)
    body = f'''
<h1>AEC Model Bridge</h1>
<p class="lead">A Python MCP server and native Revit add-in. An AI assistant connects to the server, and the server runs BIM tasks in the Revit model you have open. It also reads IFC files and has providers for Rhino and Grasshopper, Speckle and Navisworks.</p>
<p class="note"><strong>This site is documentation.</strong> The bridge runs on your Windows machine next to Revit. Static hosting cannot run it.</p>
<p><a class="btn primary" href="{REPO}/releases/latest">Latest release (v{esc(s["version"])})</a> <a class="btn" href="{REPO}">Source</a> <a class="btn" href="tools.html">Browse {len(s["tools"])} tools</a></p>

<h2 id="approval">How approval works</h2>
<ol class="steps"><li><strong>The assistant proposes.</strong> It calls <code>plan_actions</code> with the changes it wants. Nothing in the model changes, and the plan records the before-state.</li>
<li><strong>You review.</strong> The plan appears in the Revit side panel. You can approve or reject it (<code>approve_plan</code>, <code>reject_plan</code>).</li>
<li><strong>Revit changes.</strong> Only an approved plan can run. <code>execute_plan</code> applies it in one named transaction.</li>
<li><strong>You can roll back.</strong> <code>rollback_plan</code> reverses an executed plan using Revit Undo in the same session, or inverse parameter values. Irreversible operations such as file output ask for a second confirmation.</li></ol>
<p>The default mode is <code>MCP_REVIT_APPROVAL_MODE=required</code>. A model-changing call without an approved <code>plan_id</code> is blocked by the hub. <code>auto</code> turns the human check off for unattended pipelines. Use it only in a controlled environment. Source: {src_link(s, "docs/0008-approval-gate-lifecycle.md", "ADR 0008")}.</p>
{picture("approval-flow", "Approval flow diagram: assistant proposes a plan, the hub shows it in the Revit panel, execute_plan runs it only after approval, and a rejected plan leaves the model untouched.")}

<h2 id="architecture">Architecture</h2>
<p>One Python hub receives every MCP call and routes it to the provider that owns the tool. Providers for desktop apps talk to a small add-in inside that app over localhost.</p>
{picture("architecture", "Architecture: an MCP client calls the Python hub, which routes to the Revit, Rhino, Navisworks, IFC and Speckle providers.")}

<h2 id="compat">Compatibility</h2>
<div class="tw" tabindex="0" role="region" aria-label="Revit versions table"><table><caption>Revit versions (from the project README)</caption><thead><tr><th scope="col">Revit</th><th scope="col">Add-in target</th><th scope="col">Build tools</th></tr></thead><tbody>{rows}</tbody></table></div>
<p>Windows 10 or 11, Python 3.11 or later and a licensed Revit are required for live use. Mock mode needs no Revit.</p>
<div class="tw" tabindex="0" role="region" aria-label="Other integrations table"><table><caption>Other integrations (from the project README)</caption><thead><tr><th scope="col">Integration</th><th scope="col">Status</th></tr></thead><tbody>{integ}</tbody></table></div>
<p>Compatibility with a given MCP client depends on that client. The project documents Claude Desktop, Codex, Cursor and VS Code configuration; this site does not claim certification by any vendor.</p>

<h2 id="try">Try it</h2>
<p><strong>Without Revit (mock mode).</strong> The server starts, lists every tool with its schema and returns canned responses. Add this to <code>claude_desktop_config.json</code> (other clients use the same values):</p>
<div class="code"><button class="copy" type="button" data-copy>Copy</button><pre tabindex="0"><code>{esc(cfg)}</code></pre></div>
<p><strong>With Revit.</strong> Install the add-in for your Revit year, then use <code>"MCP_REVIT_MODE": "bridge"</code>. Steps and troubleshooting: {src_link(s, "docs/install.md", "docs/install.md")}.</p>
<p class="small">This is the shape documented in the project README with the mode set to mock. It needs <a href="https://docs.astral.sh/uv/">uv</a> for the <code>uvx</code> command and a network connection to fetch the package.</p>

<h2 id="docs">Source documentation</h2>
<ul><li>{src_link(s, "README.md", "Project README")}</li><li>{src_link(s, "docs/install.md", "Install guide")}</li><li>{src_link(s, "docs/security.md", "Security")}</li><li>{src_link(s, "docs/marketplaces.md", "Marketplaces and client configuration")}</li><li>{src_link(s, "docs/tools-generated.md", "Generated tool catalogue")}</li></ul>
'''
    return page("bridge.html", "AEC Model Bridge: Revit MCP server", "How AEC Model Bridge works: install, architecture, compatibility and the human approval model for AI changes to Revit.", body, s)


def schema_rows(schema):
    props, req = schema.get("properties", {}), set(schema.get("required", []))
    if not props:
        return "<p>No inputs.</p>"
    r = "".join(f'<tr><td><code>{esc(k)}</code></td><td>{esc(str(v.get("type", "any")))}</td><td>{"yes" if k in req else "no"}</td><td>{esc(v.get("description", ""))}</td></tr>' for k, v in props.items())
    return f'<div class="tw" tabindex="0" role="region" aria-label="Tool inputs"><table class="inputs"><thead><tr><th scope="col">Input</th><th scope="col">Type</th><th scope="col">Required</th><th scope="col">Description</th></tr></thead><tbody>{r}</tbody></table></div>'


def p_tools(s):
    names = {t["name"] for t in s["tools"]}
    for w in WORKFLOWS:
        missing = [t for t in w["tools"] if t not in names]
        if missing:
            sys.exit(f"workflow '{w['id']}' names tools that do not exist: {missing}")
    wf = ""
    for w in WORKFLOWS:
        links = ", ".join(f'<a href="#{t}"><code>{t}</code></a>' for t in w["tools"])
        ex = ""
        if w["id"] == "ifc":
            for t in ("ifc_get_spatial_structure", "ifc_query_elements"):
                e = s["examples"][t]
                ex += f'<p class="small">Verified output of <code>{t}</code> on a small generated IFC4 file:</p><pre class="out" tabindex="0"><code>{esc(json.dumps(e["result"], indent=2))}</code></pre>'
        wf += f'''<article class="card" id="wf-{w["id"]}"><h3>{esc(w["title"])}</h3>
<p><strong>Tools:</strong> {links}</p>
<div class="code"><button class="copy" type="button" data-copy>Copy prompt</button><pre class="wrap-pre" tabindex="0"><code>{esc(w["prompt"])}</code></pre></div>
<p><strong>Expect:</strong> {esc(w["expect"])}</p>{ex}<p class="small"><strong>Limits:</strong> {esc(w["limits"])}</p></article>'''

    by_provider = {}
    for t in s["tools"]:
        by_provider.setdefault(t["provider"], []).append(t)
        prov_opts = "".join(f'<option value="{esc(p)}">{esc(PROVIDERS.get(p, (p,))[0])} ({len(v)})</option>' for p, v in sorted(by_provider.items(), key=lambda kv: PROVIDERS.get(kv[0], (kv[0],))[0]))
    groups = ""
    for p, tools in sorted(by_provider.items(), key=lambda kv: PROVIDERS.get(kv[0], (kv[0],))[0]):
        pname, pfile, status, prereq = PROVIDERS.get(p, (p, "", "Registered by default", "See the project documentation."))
        items = ""
        for t in tools:
            k = classify(t, s)
            desc = t["description"] or ""
            first = re.split(r"(?<=[.!?])\s", desc.strip())[0] if desc else ""
            hay = f'{t["name"]} {desc} {p}'.lower()
            items += f'''<details class="tool" id="{esc(t["name"])}" data-provider="{esc(p)}" data-kind="{k}" data-text="{esc(hay)}">
<summary><code>{esc(t["name"])}</code><span class="pill {k}">{esc(KIND_LABEL[k])}</span><span class="sum">{esc(first)}</span></summary>
<div class="tool-body"><p>{esc(desc)}</p>{schema_rows(t["inputSchema"])}
<ul class="small"><li><strong>Behaviour:</strong> {esc(KIND_LABEL[k])}{"; reads run immediately" if k == "read" else ("; needs an approved plan_id while approval mode is required" if k == "model" else "")}.</li>
<li><strong>Integration status:</strong> {esc(status)} ({esc(pname)}).</li><li><strong>Prerequisites:</strong> {esc(prereq)}</li>
<li><strong>Source:</strong> provider code {src_link(s, pfile, pfile.rsplit("/", 1)[-1])}; project catalogue {src_link(s, "docs/tools-generated.md", "tools-generated.md")}.</li></ul></div></details>'''
        groups += f'<section class="prov" data-provider-group="{esc(p)}" id="p-{re.sub("[^a-z0-9]+", "-", p.lower())}"><h3>{esc(pname)} <span class="count">{len(tools)}</span></h3><p class="small"><strong>{esc(status)}.</strong> {esc(prereq)}</p>{items}</section>'

    n_read = sum(1 for t in s["tools"] if classify(t, s) == "read")
    n_model = sum(1 for t in s["tools"] if classify(t, s) == "model")
    n_state = len(s["tools"]) - n_read - n_model
    body = f'''
<h1>MCP tools &amp; workflows</h1>
<p class="lead">{len(s["tools"])} tools are registered in the default setup of v{esc(s["version"])}: {n_read} read-only, {n_model} that change the model after approval, and {n_state} that write files or plan state. The list below was exported from the real server in mock mode on this build.</p>
<p class="note"><strong>Not everything here is equally finished.</strong> Navisworks tools are registered while their add-in is unfinished. Autodesk Data tools need APS credentials and are not in the default listing. A tool existing here does not mean it was tested against live Revit.</p>

<h2 id="workflows">Example workflows</h2>
<p>Copy a prompt into your MCP client once the server is connected. Each one names the exact tools involved.</p>
<div class="grid2">{wf}</div>

<h2 id="catalogue">Tool catalogue</h2>
<form class="filters" role="search" aria-label="Filter tools" onsubmit="return false">
<div><label for="q">Search</label><input id="q" type="search" placeholder="e.g. sheet, warnings, ifc" autocomplete="off"></div>
<div><label for="f-provider">Provider</label><select id="f-provider"><option value="">All providers</option>{prov_opts}</select></div>
<div><label for="f-kind">Behaviour</label><select id="f-kind"><option value="">All</option><option value="read">Read-only</option><option value="model">Changes the model</option><option value="state">Writes files or state</option></select></div>
</form>
<p id="result-count" role="status" aria-live="polite" class="small">Showing all {len(s["tools"])} tools.</p>
<div id="catalogue-list">{groups}</div>
<p class="small">Inputs come from each tool's JSON schema. Behaviour: "read-only" is the tool's <code>readOnlyHint</code>; "changes the model" is a tool the catalogue marks as mutating, which the approval gate blocks without an approved plan. Provider status is quoted from the project README. Full catalogue: {src_link(s, "docs/tools-generated.md")}. Revit lengths are in feet.</p>
'''
    return page("tools.html", "MCP tools and workflows: AEC Model Bridge", "Searchable catalogue of AEC Model Bridge MCP tools with inputs, behaviour, status and copyable example prompts.", body, s)


def p_about(s):
    body = f'''
<h1>About</h1>
<p class="lead">I'm A. Sam Mohammad, a product engineer based in the Netherlands.</p>
<p>I have more than 15 years of experience across construction and façade engineering. My work sits between engineering, BIM and software development: I use Revit, Dynamo, Python, Rhino and Grasshopper to turn repetitive engineering work into structured, reusable workflows.</p>
<h2>Open to</h2>
<ul><li>Revit tooling and BIM workflow automation</li><li>Façade systems and parametric or industrialised construction</li><li>AEC product development</li><li>Practical applications of AI in engineering</li></ul>
<p>The quickest route is LinkedIn. A short note on the workflow you want to improve is a good start.</p>
<p><a class="btn primary" href="{LINKEDIN}">Message me on LinkedIn</a> <a class="btn" href="https://github.com/Sam-AEC">GitHub profile</a></p>
'''
    return page("about.html", "About: A. Sam Mohammad", "Background and how to get in touch about BIM automation, façade engineering technology and AEC product development.", body, s)


# ------------------------------------------------------------------ build
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bridge", required=True)
    ap.add_argument("--data", default=str(HERE / ".cache"))
    ap.add_argument("--out", default=str(HERE / "dist"))
    a = ap.parse_args()
    bridge, data, out = Path(a.bridge).resolve(), Path(a.data).resolve(), Path(a.out).resolve()
    s = read_sources(bridge, data)
    if out.exists():
        shutil.rmtree(out)
    (out / "img").mkdir(parents=True)
    shutil.copytree(HERE / "static", out / "static")
    shutil.copy(HERE / "static" / "favicon.svg", out / "img" / "favicon.svg")
    for n in ("approval-flow", "architecture"):
        for t in ("light", "dark"):
            shutil.copy(bridge / "docs" / "images" / f"{n}-{t}.png", out / "img" / f"{n}-{t}.png")
    for fn, fnc in (("index.html", p_home), ("projects.html", p_projects), ("bridge.html", p_bridge), ("tools.html", p_tools), ("about.html", p_about)):
        (out / fn).write_text(fnc(s), encoding="utf-8")
    (out / ".nojekyll").write_text("")
    (out / "404.html").write_text(page("404.html", "Page not found", "Page not found", '<h1>Page not found</h1><p><a href="index.html">Back to home</a></p>', s), encoding="utf-8")
    print(f"built {len(list(out.glob('*.html')))} pages, {len(s['tools'])} tools, bridge v{s['version']} @ {s['sha'][:7]} -> {out}")


if __name__ == "__main__":
    main()
