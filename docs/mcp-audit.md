# AEC Model Bridge: MCP metadata audit

Audit of [Sam-AEC/aec-model-bridge](https://github.com/Sam-AEC/aec-model-bridge) at commit `29384e1` (v1.3.3, 9 Oct 2026). I changed nothing in that repository. Findings below are for you to apply or ignore.

## What was checked

| Source | Role | Result |
| --- | --- | --- |
| `README.md` | Human documentation, shown on GitHub and scraped by directories | Version, Revit range, tool count (219) and integration table agree with the code |
| `server.json` | Official MCP Registry metadata | Name, version 1.3.3, env vars and `mcpb` package present. See finding 1 |
| `packages/mcp-server-revit/manifest.json` | MCPB bundle metadata | Version 1.3.3, same description as `server.json` |
| `packages/mcp-server-revit/pyproject.toml` | Python package metadata | Version 1.3.3, GPL-3.0-or-later, Python 3.11+, `mcp>=1.10,<2` |
| `smithery.yaml` | Smithery build | Runs the root `Dockerfile` in mock mode only, as its comments say |
| `glama.json` | Glama maintainer claim | Names `Sam-AEC` as maintainer |
| GitHub release v1.3.3 | Distribution | `.mcpb`, four per-Revit-year zips, wheel and `SHA256SUMS.txt` attached |
| Live server (mock mode) | Machine-readable schemas | 219 tools registered; this is the source for the site's catalogue |

## Findings

1. **`server.json` hash differs from the release.** The committed `fileSha256` is `005c9524…` but the v1.3.3 `SHA256SUMS.txt` lists `bbb1ffff…` for `aec-model-bridge-1.3.3.mcpb`. `publish-mcp.yml` recomputes the hash from the downloaded asset and rewrites `server.json` on the runner, so the registry should receive the right value. The copy in `main` is stale, though, and `mcp-publisher publish` run by hand from a clone would publish the wrong hash. Fix: commit the synchronised file, or note in `marketplaces.md` that the CI step owns it.
2. **Registry listing is unverified.** The README shows an "MCP Registry: listed" badge, while `docs/marketplaces.md` says "Status: configured". I could not reach `registry.modelcontextprotocol.io` from this environment, so I did not confirm either. The profile README and site make no claim about registry listing. Check `https://registry.modelcontextprotocol.io/?q=io.github.Sam-AEC%2Faec-model-bridge` yourself; change the badge to "configured" if the entry is not live.
3. **The generated catalogue omits three tools.** `docs/tools-generated.md` has 228 rows. The live default server registers 219 tools. Twelve catalogue rows are Autodesk Data tools that appear only with APS credentials. Three registered tools (`snapshot_take`, `snapshot_query`, `snapshot_diff`, from `semantic_provider.py`) are missing because `generate_tool_docs.py` does not instantiate that provider. The catalogue is otherwise consistent: its `Mutating?` column matches the `is_mutating` flag the approval gate reads for every tool.
4. **Two metadata fields mean different things.** MCP `readOnlyHint` is false for approval tools such as `plan_actions` (they write plan state, not the model), while the catalogue lists them as `Mutating? No`. The site separates these as "changes the model" and "writes files or state". Consider saying so in `tools-generated.md`.
5. **Client configuration differs between documents.** The README quick start uses `uvx --from git+…`. `docs/marketplaces.md` uses `python -m revit_mcp_server.mcp_server` plus `MCP_REVIT_HOST_VERSION`, which `server.json` does not list. Both can be valid; say which is preferred.
6. **Tool counts are rounded consistently.** README says 219 (counted) and "more than 200"; `server.json` and `manifest.json` say "200+". No change needed.

## Distinguishing the four kinds of content

- **GitHub-sourced directory text** (Glama, PulseMCP and similar) comes from the repository description, topics and README. The description and 15 topics are set.
- **Official registry metadata** is `server.json`, published by the workflow on release.
- **Human documentation** is the README and `docs/`. The site on this repository links back to it and never copies prose.
- **Machine-readable schemas** are the tool definitions the running server returns. `site/scripts/export_bridge_data.py` exports them; the site builds from that output.

## Steps only you can take

These need your accounts, so none were attempted.

- Confirm the registry entry exists and, if it does not, run the publish workflow or `mcp-publisher publish` after fixing finding 1.
- Claim or verify maintainer pages on Glama, PulseMCP and others listed in `docs/marketplaces.md`.
- Submit the repository URL to directories that need a form (MCP.Directory, MCP.so and similar).
- Enable GitHub Pages for this repository (Settings, Pages, Source: GitHub Actions) when you want the site published.
