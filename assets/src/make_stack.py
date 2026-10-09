#!/usr/bin/env python3
"""Generate assets/stack.svg: the tech stack as a terminal listing.

    python3 assets/src/make_stack.py

Logos come from Simple Icons (CC0, https://simpleicons.org), saved in icons.json.
Tools without an official logo there (Revit, Dynamo, Grasshopper, IFC, Speckle,
APS) are listed as text rather than with an invented mark. Revit is shown with the
Autodesk mark. Edit SECTIONS to change the content.
"""
import html, json, os

HERE = os.path.dirname(__file__)
IC = json.load(open(os.path.join(HERE, "icons.json")))
COL = {"autodesk": "#e8eefc", "python": "#6aa5dc", "dotnet": "#9b7df5", "typescript": "#4a90e2", "git": "#F05133",
       "github": "#e8eefc", "docker": "#2496ED", "rhino": "#e05a5a", "actions": "#2088FF", "mcp": "#e8eefc"}

# (section, [(icon key or None, label)])
SECTIONS = [
    ("applications", [("autodesk", "Revit"), (None, "Dynamo"), ("rhino", "Rhino"), (None, "Grasshopper")]),
    ("languages", [("python", "Python"), ("dotnet", "C# / .NET"), ("typescript", "TypeScript")]),
    ("interoperability", [("mcp", "MCP"), (None, "IFC"), (None, "Speckle"), (None, "Revit API"), (None, "APS")]),
    ("delivery", [("git", "Git"), ("github", "GitHub"), ("actions", "GitHub Actions"), ("docker", "Docker")]),
]
W, H = 1200, 400


def icon(k, x, y, s):
    return f'<path transform="translate({x} {y}) scale({s/24:.4f})" d="{IC[k]["path"]}" fill="{COL[k]}"/>'


b = []
b.append('<rect x="40" y="30" width="1120" height="340" rx="14" fill="#0a111f" stroke="#243247"/>')
b.append('<path d="M40 44a14 14 0 0 1 14-14h1092a14 14 0 0 1 14 14v28H40z" fill="#0f1a30"/><line x1="40" y1="72" x2="1160" y2="72" stroke="#243247"/>')
for i, c in enumerate(["#ff5f57", "#febc2e", "#28c840"]):
    b.append(f'<circle cx="{68+i*22}" cy="51" r="6.5" fill="{c}"/>')
b.append('<text x="600" y="56" text-anchor="middle" class="m" font-size="13" fill="#6b7a99">sam-aec ~ stack.toml</text>')
y = 118
b.append(f'<text x="72" y="{y}" class="m" font-size="15" fill="#5b6b8c">$ </text><text x="90" y="{y}" class="m" font-size="15" fill="#e8eefc">cat stack.toml</text>')
y += 42
for n, (sec, items) in enumerate(SECTIONS):
    b.append(f'<text x="72" y="{y}" class="m" font-size="12" fill="#3d4b69">{n+1:02d}</text>')
    b.append(f'<text x="112" y="{y}" class="m" font-size="17" fill="#5eead4">[{sec}]</text>')
    x = 360
    for k, t in items:
        if k:
            b.append(icon(k, x, y - 17, 22)); tx = x + 32
        else:
            tx = x
        b.append(f'<text x="{tx}" y="{y}" class="m" font-size="17" fill="#e2e8f0">{html.escape(t)}</text>')
        x = tx + len(t) * 10.2 + 34
    y += 46
b.append(f'<text x="72" y="{y+4}" class="m" font-size="15" fill="#5b6b8c">$ </text><rect x="92" y="{y-10}" width="9" height="19" fill="#5eead4"/>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t">
<title id="t">Tech stack: applications, languages, interoperability and delivery tools</title>
<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#060a13"/><stop offset="1" stop-color="#0b1424"/></linearGradient>
<radialGradient id="g1" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#14b8a6" stop-opacity=".28"/><stop offset="1" stop-color="#14b8a6" stop-opacity="0"/></radialGradient>
<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".9" fill="#7c93bd" fill-opacity=".2"/></pattern>
<clipPath id="c"><rect width="{W}" height="{H}" rx="20"/></clipPath></defs>
<style>text{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif}}.m{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}</style>
<g clip-path="url(#c)"><rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#dots)"/><ellipse cx="960" cy="90" rx="340" ry="200" fill="url(#g1)"/>
{"".join(b)}</g><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="#fff" stroke-opacity=".08"/></svg>'''
out = os.path.join(HERE, "..", "stack.svg")
open(out, "w", encoding="utf-8").write(svg)
print(os.path.normpath(out))
