#!/usr/bin/env python3
"""Generate the three profile hero images (SVG, no dependencies).

    python3 assets/src/make_hero.py

Output: assets/hero/hero-facade.svg, hero-graph.svg, hero-modules.svg
All three are drawn for a dark card, so they read the same on GitHub's light and
dark themes. Name, role and links live in README.md as real text.
"""
import math, os, html

OUT = os.path.join(os.path.dirname(__file__), "..", "hero")
W, H = 1200, 340
FONT = '-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif'
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'
TEAL, BLUE, INK, MUTE = "#2dd4bf", "#60a5fa", "#e8eefc", "#8fa3c7"


def shell(title, desc, body, extra_defs=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">{html.escape(title)}</title><desc id="d">{html.escape(desc)}</desc>
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#060a13"/><stop offset="1" stop-color="#0b1424"/></linearGradient>
<radialGradient id="gt" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#14b8a6" stop-opacity=".34"/><stop offset="1" stop-color="#14b8a6" stop-opacity="0"/></radialGradient>
<radialGradient id="gb" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#3b82f6" stop-opacity=".28"/><stop offset="1" stop-color="#3b82f6" stop-opacity="0"/></radialGradient>
<pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".9" fill="#7c93bd" fill-opacity=".2"/></pattern>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="5" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<clipPath id="card"><rect width="{W}" height="{H}" rx="20"/></clipPath>
{extra_defs}
</defs>
<style>text{{font-family:{FONT}}}.m{{font-family:{MONO}}}</style>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#dots)"/>
<ellipse cx="900" cy="120" rx="380" ry="230" fill="url(#gt)"/><ellipse cx="260" cy="330" rx="340" ry="190" fill="url(#gb)"/>
{body}
</g>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="20" fill="none" stroke="#fff" stroke-opacity=".1"/>
</svg>'''


def caption(label):
    return (f'<rect x="48" y="40" width="30" height="3" rx="1.5" fill="{TEAL}"/>'
            f'<text x="48" y="68" class="m" font-size="12" letter-spacing="2.4" fill="{MUTE}">{html.escape(label)}</text>')


# ---------------------------------------------------------------- facade
def facade():
    cols, rows = 24, 8
    x0, y0, cw, ch = 430, 52, 30, 30          # unit-panel pitch
    ax, ay = 15.5, 3.0                        # attractor position (grid units)
    out = [caption("BIM  ·  AEC AUTOMATION")]
    # mullions + transoms
    for c in range(cols + 1):
        out.append(f'<line x1="{x0+c*cw}" y1="{y0}" x2="{x0+c*cw}" y2="{y0+rows*ch}" stroke="#1f2c47" stroke-width="1"/>')
    for r in range(rows + 1):
        out.append(f'<line x1="{x0}" y1="{y0+r*ch}" x2="{x0+cols*cw}" y2="{y0+r*ch}" stroke="#1f2c47" stroke-width="1"/>')
    approved = {(13, 2), (14, 2), (15, 3), (16, 3), (14, 4), (15, 4), (16, 2)}
    proposed = {(17, 4), (18, 4), (17, 5), (18, 5)}
    for c in range(cols):
        for r in range(rows):
            d = math.hypot(c + .5 - ax, (r + .5 - ay) * 1.1)
            k = max(0.0, 1 - d / 11)                      # 0 far .. 1 at attractor
            pad = 3 + 8 * (1 - k)                          # aperture closes with distance
            x, y = x0 + c * cw + pad, y0 + r * ch + pad
            w, h = cw - 2 * pad, ch - 2 * pad
            if (c, r) in approved:
                out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" fill="{TEAL}" fill-opacity=".92"/>')
            elif (c, r) in proposed:
                out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" fill="{TEAL}" fill-opacity=".08" stroke="#5eead4" stroke-dasharray="3 2.5"/>')
            else:
                a = .10 + .55 * k
                out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" fill="#60a5fa" fill-opacity="{a:.2f}"/>')
    # grid bubbles (column lines) along top
    for c in range(0, cols + 1, 6):
        bx = x0 + c * cw
        out.append(f'<line x1="{bx}" y1="{y0-14}" x2="{bx}" y2="{y0}" stroke="{MUTE}" stroke-opacity=".6"/>'
                   f'<circle cx="{bx}" cy="{y0-24}" r="10" fill="none" stroke="{MUTE}" stroke-opacity=".7"/>'
                   f'<text x="{bx}" y="{y0-20}" text-anchor="middle" class="m" font-size="11" fill="{MUTE}">{chr(65+c//6)}</text>')
    # level markers
    for r in range(0, rows + 1, 2):
        ly = y0 + r * ch
        out.append(f'<path d="M{x0-26} {ly} h18 l-4 -4 m4 4 l-4 4" fill="none" stroke="{MUTE}" stroke-opacity=".6"/>'
                   f'<text x="{x0-32}" y="{ly+4}" text-anchor="end" class="m" font-size="10.5" fill="{MUTE}">L{(rows-r)//2+1}</text>')
    # legend
    ly = y0 + rows * ch + 34
    out.append(f'<g class="m" font-size="11.5" fill="{MUTE}" letter-spacing="1.2">'
               f'<rect x="{x0}" y="{ly-9}" width="14" height="10" rx="2" fill="#60a5fa" fill-opacity=".5"/><text x="{x0+22}" y="{ly}">PARAMETRIC PANEL</text>'
               f'<rect x="{x0+190}" y="{ly-9}" width="14" height="10" rx="2" fill="{TEAL}"/><text x="{x0+212}" y="{ly}">APPROVED</text>'
               f'<rect x="{x0+320}" y="{ly-9}" width="14" height="10" rx="2" fill="none" stroke="#5eead4" stroke-dasharray="3 2"/><text x="{x0+342}" y="{ly}">PROPOSED</text></g>')
    # left scrim text block (non-essential; README holds the real text)
    out.append(f'<g font-size="34" font-weight="800" fill="{INK}" letter-spacing="-.6"><text x="48" y="150">From model</text><text x="48" y="192">to façade.</text></g>')
    out.append(f'<text x="48" y="226" font-size="15" fill="{MUTE}">Parametric geometry, BIM data</text><text x="48" y="248" font-size="15" fill="{MUTE}">and software, in one workflow.</text>')
    return shell("Parametric façade elevation", "A unitised façade elevation. Panel apertures follow an attractor point, as in a parametric Grasshopper definition; teal panels are approved changes and dashed panels are proposed.", "".join(out))


# ---------------------------------------------------------------- node graph
def graph():
    out = [caption("BIM  ·  AEC AUTOMATION")]
    out.append(f'<g font-size="34" font-weight="800" fill="{INK}" letter-spacing="-.6"><text x="48" y="150">AI proposes.</text><text x="48" y="192">You approve.</text></g>')
    out.append(f'<text x="48" y="226" font-size="15" fill="{MUTE}">Revit changes only after sign-off.</text>')

    def node(x, y, w, title, rows, color, hl=False):
        h = 34 + 24 * len(rows) + 12
        s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#0d1628" stroke="{color if hl else "#2b3b57"}" stroke-width="{1.6 if hl else 1}"{" filter=\"url(#glow)\"" if hl else ""}/>'
        s += f'<path d="M{x} {y+10}a10 10 0 0 1 10-10h{w-20}a10 10 0 0 1 10 10v14H{x}z" fill="{color}" fill-opacity=".22"/>'
        s += f'<text x="{x+14}" y="{y+22}" class="m" font-size="12" font-weight="700" letter-spacing="1.2" fill="{color}">{html.escape(title)}</text>'
        for i, r in enumerate(rows):
            ry = y + 34 + 24 * i + 14
            s += f'<text x="{x+14}" y="{ry}" font-size="13" fill="#cbd5e8">{html.escape(r)}</text>'
        return s, h

    nodes = {}
    layout = [("ai", 400, 56, 150, "AI CLIENT", ["Claude, Codex…", "propose plan"], BLUE),
              ("ifc", 400, 200, 150, "IFC READER", ["no Revit needed"], "#a78bfa"),
              ("hub", 590, 128, 150, "MCP HUB", ["approval gate", "routes tools"], TEAL),
              ("panel", 780, 56, 160, "REVIEW", ["human approves", "in Revit panel"], "#f59e0b"),
              ("rvt", 980, 128, 160, "REVIT ADD-IN", ["one named", "transaction"], TEAL)]
    geo = {}
    for key, x, y, w, t, rows, col in layout:
        s_, h = node(x, y, w, t, rows, col, hl=(key == "panel"))
        out.append(s_); geo[key] = (x, y, w, h)

    def wire(a, b, color=TEAL, dash=False):
        ax, ay, aw, ah = geo[a]; bx, by, bw, bh = geo[b]
        x1, y1 = ax + aw, ay + ah / 2
        x2, y2 = bx, by + bh / 2
        mx = (x1 + x2) / 2
        d = f'M{x1} {y1} C{mx} {y1} {mx} {y2} {x2} {y2}'
        out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-opacity=".75" stroke-width="2"{" stroke-dasharray=\"5 5\"" if dash else ""}/>')
        out.append(f'<circle cx="{x1}" cy="{y1}" r="4" fill="#0b1424" stroke="{color}" stroke-width="1.6"/><circle cx="{x2}" cy="{y2}" r="4" fill="#0b1424" stroke="{color}" stroke-width="1.6"/>')
    wire("ai", "hub", BLUE)
    wire("ifc", "hub", "#a78bfa", dash=True)
    wire("hub", "panel", "#f59e0b")
    wire("panel", "rvt", TEAL)
    return shell("Approval flow as a node graph", "A node graph: an AI client proposes a plan to the MCP hub, a human reviews it in the Revit panel, and only then does the Revit add-in apply it in one named transaction. An IFC reader runs without Revit.", "".join(out))


# ---------------------------------------------------------------- modules
def modules():
    c30, s30 = math.cos(math.radians(30)), .5
    S, OX, OY = 40, 800, 232
    P = lambda x, y, z: (OX + (x - y) * c30 * S, OY + (x + y) * s30 * S - z * S)
    poly = lambda pts: " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)

    def cube(x, y, z, g=.05):
        x0, x1, y0, y1, z0, z1 = x + g, x + 1 - g, y + g, y + 1 - g, z + g, z + 1 - g
        return ([P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1)],
                [P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0), P(x0, y1, z0)],
                [P(x1, y0, z1), P(x1, y1, z1), P(x1, y1, z0), P(x1, y0, z0)])
    heights = {(0,0):3,(1,0):3,(2,0):2,(0,1):3,(1,1):2,(2,1):1,(0,2):2,(1,2):1,(2,2):1}
    approved = {(1,1,1),(2,0,1),(1,2,0)}
    cubes = sorted(((x, y, z) for (x, y), h in heights.items() for z in range(h)), key=lambda c: (c[0]+c[1], c[2]))
    defs = '''<linearGradient id="et" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#3a4a6b"/><stop offset="1" stop-color="#2a3752"/></linearGradient>
<linearGradient id="el" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e2a44"/><stop offset="1" stop-color="#121a2e"/></linearGradient>
<linearGradient id="er" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#16213a"/><stop offset="1" stop-color="#0c1324"/></linearGradient>
<linearGradient id="tt" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#99f6e4"/><stop offset="1" stop-color="#2dd4bf"/></linearGradient>
<linearGradient id="tl" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#14b8a6"/><stop offset="1" stop-color="#0f766e"/></linearGradient>
<linearGradient id="tr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d9488"/><stop offset="1" stop-color="#0a4f4b"/></linearGradient>'''
    out = [caption("BIM  ·  AEC AUTOMATION")]
    gp = [P(-.5,-.5,0), P(3.5,-.5,0), P(3.5,3.5,0), P(-.5,3.5,0)]
    out.append(f'<polygon points="{poly(gp)}" fill="#0f1a30" fill-opacity=".55" stroke="#7c93bd" stroke-opacity=".35"/>')
    for i in range(4):
        a, b = P(-.5, i, 0), P(3.5, i, 0); out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#7c93bd" stroke-opacity=".16"/>')
        a, b = P(i, -.5, 0), P(i, 3.5, 0); out.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#7c93bd" stroke-opacity=".16"/>')
    for (x, y, z) in cubes:
        t, l, r = cube(x, y, z)
        if (x, y, z) in approved:
            out.append(f'<polygon points="{poly(l)}" fill="url(#tl)"/><polygon points="{poly(r)}" fill="url(#tr)"/><polygon points="{poly(t)}" fill="url(#tt)"/>')
        else:
            out.append(f'<polygon points="{poly(l)}" fill="url(#el)" stroke="#9fb3d1" stroke-opacity=".16" stroke-width=".8"/><polygon points="{poly(r)}" fill="url(#er)" stroke="#9fb3d1" stroke-opacity=".12" stroke-width=".8"/><polygon points="{poly(t)}" fill="url(#et)" stroke="#cfe0ff" stroke-opacity=".28" stroke-width=".8"/>')
    for (x, y, z) in [(0,0,3.9),(1,0,3.9)]:
        t, l, r = cube(x, y, z)
        gx, gy = P(x+.5, y+.5, z); bx, by = P(x+.5, y+.5, 3.05)
        out.append(f'<line x1="{gx:.1f}" y1="{gy:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{TEAL}" stroke-opacity=".5" stroke-dasharray="2 4"/>')
        for pts, op in ((l,.07),(r,.04),(t,.16)):
            out.append(f'<polygon points="{poly(pts)}" fill="{TEAL}" fill-opacity="{op}" stroke="#5eead4" stroke-width="1.1" stroke-dasharray="4 3"/>')
    out.append(f'<g font-size="34" font-weight="800" fill="{INK}" letter-spacing="-.6"><text x="48" y="150">Repeatable</text><text x="48" y="192">construction.</text></g>')
    out.append(f'<text x="48" y="226" font-size="15" fill="{MUTE}">Modules in, reviewed changes out.</text>')
    labels = [(P(2,0,4.9),"PROPOSED",TEAL),(P(3,.5,2),"APPROVED",TEAL),(P(3,2.5,.5),"MODEL",MUTE)]
    for (px, py), t, col in labels:
        out.append(f'<polyline points="{px:.1f},{py:.1f} {px+36:.1f},{py:.1f} 1080,{py:.1f}" fill="none" stroke="{col}" stroke-opacity=".55"/><circle cx="{px:.1f}" cy="{py:.1f}" r="2.5" fill="{col}"/><text x="1088" y="{py+4:.1f}" class="m" font-size="10.5" letter-spacing="1.6" fill="{col}">{t}</text>')
    return shell("Isometric stack of building modules", "Existing modules in slate, approved modules in teal and proposed modules as dashed outlines.", "".join(out), defs)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, fn in (("hero-facade", facade), ("hero-graph", graph), ("hero-modules", modules)):
        path = os.path.join(OUT, name + ".svg")
        with open(path, "w", encoding="utf-8") as f:
            f.write(fn())
        print(path)
