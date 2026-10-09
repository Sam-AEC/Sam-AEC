# Site

A small static site that documents AEC Model Bridge and the profile's selected work. It has no framework and no runtime dependencies beyond Python 3 (standard library) for the build.

## Pages

| File | Content |
| --- | --- |
| `index.html` | Positioning and selected work |
| `projects.html` | Evidence-based project summaries: what, who, maturity, where to try |
| `bridge.html` | AEC Model Bridge: approval model, architecture, compatibility, mock-mode configuration |
| `tools.html` | Four example workflows with copyable prompts, then a searchable catalogue of every registered tool |
| `about.html` | Background and contact |

The site documents the MCP server. Static hosting cannot run the live Revit bridge, and the pages say so.

## Where the content comes from

Nothing is copied by hand and nothing is fetched in the browser. At build time:

| Fact | Source in `Sam-AEC/aec-model-bridge` |
| --- | --- |
| Version | `VERSION` |
| Tool names, inputs, descriptions, read-only hints, provider, mutating flag | The running server in mock mode, exported by `scripts/export_bridge_data.py` |
| Revit version table, integration status table | `README.md` (parsed) |
| Architecture and approval-flow images | `docs/images/*.png` (copied) |
| Commit shown in the footer | `git rev-parse HEAD` of the checkout |

Prose that is specific to the profile (positioning, workflow prompts, provider prerequisites) lives in `build.py`. Workflow tool names are checked against the exported list, and the build stops if one is missing.

## Build locally

```bash
git clone https://github.com/Sam-AEC/aec-model-bridge ../aec-model-bridge
pip install -e ../aec-model-bridge/packages/mcp-server-revit
python site/scripts/export_bridge_data.py --out site/.cache
python site/build.py --bridge ../aec-model-bridge --data site/.cache --out site/dist
python -m http.server -d site/dist 8000
```

Open `http://localhost:8000/`. All links are relative, so the same output also works under `/Sam-AEC/`.

## Refresh

`.github/workflows/pages.yml` runs on every push to `main` that touches `site/`, on manual dispatch (choose a bridge branch, tag or commit), and on a `repository_dispatch` of type `bridge-release`. To update the site after a bridge release, run the workflow from the Actions tab, or add a step to the bridge's release workflow that sends `bridge-release` to this repository. Nothing else needs editing: the version, tool list and commit all update from the checkout.

To pin the documented version, run the workflow with a tag such as `v1.3.3` as `bridge_ref`.

## Publishing

Pages is not configured by this change. When you want it live, set Settings, Pages, Source to GitHub Actions, then run the workflow. The URL will be `https://sam-aec.github.io/Sam-AEC/`. Until then the workflow still builds the site, which checks that it builds. Then link the site from the profile README.
