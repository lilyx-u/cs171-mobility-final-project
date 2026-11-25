#!/usr/bin/env python3
"""Generate the three design-draft sketches as SVG from the real data.

They are deliberately drawn in a wireframe style (grey paper, annotation
callouts, dashed interaction notes) so nobody mistakes them for finished
charts, but the positions come from static/counties.json, so the final D3
versions will look like these.

Outputs (also copied to static/drafts/ so the website can show them):
  process-book/drafts/density_gradient.svg
  process-book/drafts/age_slope.svg
  process-book/drafts/twin_counties.svg

Usage:  python3 process-book/drafts/make_drafts.py
"""
import json, math, os, random, shutil, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', '..')
rows = json.load(open(os.path.join(ROOT, 'static', 'counties.json')))
derived = json.load(open(os.path.join(ROOT, 'static', 'derived.json')))
rel = [d for d in rows if d['n'] and d['n'] >= 1000 and d['kfr25'] is not None and d['kfr75'] is not None]
random.seed(1710)

INK, INK2, INK3, RULE = '#1b2233', '#555b6b', '#8a8f9c', '#d9d9d4'
BLUE, RED, VIOLET, PAPER = '#2a78d6', '#d6422a', '#6250d6', '#fafaf8'
FONT = 'Helvetica, Arial, sans-serif'

W, H = 880, 520


def head(title, question):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'font-family="{FONT}">'
            f'<rect width="{W}" height="{H}" fill="{PAPER}"/>'
            # faint grid paper
            + ''.join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="#eeeeea" stroke-width="1"/>' for x in range(0, W, 40))
            + ''.join(f'<line x1="0" y1="{y}" x2="{W}" y2="{y}" stroke="#eeeeea" stroke-width="1"/>' for y in range(0, H, 40))
            + f'<text x="24" y="34" font-size="20" font-weight="bold" fill="{INK}">{title}</text>'
            f'<text x="24" y="54" font-size="13" fill="{INK2}" font-style="italic">{question}</text>'
            f'<rect x="{W-118}" y="16" width="94" height="22" rx="11" fill="{INK}"/>'
            f'<text x="{W-71}" y="31" font-size="11" fill="#fff" text-anchor="middle">DESIGN DRAFT</text>')


def note(x, y, lines, w=230, dashed=True):
    h = 16 * len(lines) + 14
    s = (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#fff" stroke="{VIOLET}" '
         f'stroke-width="1" {"stroke-dasharray=\"4 3\"" if dashed else ""}/>')
    for i, l in enumerate(lines):
        s += f'<text x="{x+8}" y="{y+18+16*i}" font-size="11" fill="{INK}">{l}</text>'
    return s


def pct(v):
    return f'{round(v*100)}th'


# ---------------------------------------------------------------- 1. density
def density_gradient():
    bins = derived['density_bins']
    L, R, T, B = 80, 600, 90, 430
    bw = (R - L) / len(bins)
    y = lambda v: B - (v - 0.30) / (0.65 - 0.30) * (B - T)
    s = head('The density gradient', 'Do rural or urban counties give low-income children the better start?')
    # axes
    for v in (0.3, 0.4, 0.5, 0.6):
        s += f'<line x1="{L}" y1="{y(v)}" x2="{R}" y2="{y(v)}" stroke="{RULE}"/>'
        s += f'<text x="{L-8}" y="{y(v)+4}" font-size="11" fill="{INK3}" text-anchor="end">{pct(v)}</text>'
    s += f'<text transform="translate(28,{(T+B)/2}) rotate(-90)" font-size="12" fill="{INK2}" text-anchor="middle">adult income rank, children of low-income parents</text>'
    # strips
    byb = {}
    for d in rel:
        if d['popdens'] and d['popdens'] > 0:
            byb.setdefault(min(4, int(math.log10(max(d['popdens'], 1)))), []).append(d['kfr25'])
    pts = []
    for i, b in enumerate(bins):
        cx = L + bw * (i + 0.5)
        sample = random.sample(byb[b['bin']], min(220, len(byb[b['bin']])))
        for v in sample:
            jx = cx + random.gauss(0, bw * 0.13)
            s += f'<circle cx="{jx:.1f}" cy="{y(v):.1f}" r="2" fill="{BLUE}" opacity="0.25"/>'
        pts.append((cx, y(b['kfr25'])))
        s += f'<text x="{cx}" y="{B+18}" font-size="11" fill="{INK2}" text-anchor="middle">{b["label"].replace(" per sq mi","")}</text>'
        s += f'<text x="{cx}" y="{B+32}" font-size="10" fill="{INK3}" text-anchor="middle">n = {b["n"]:,}</text>'
    s += f'<text x="{(L+R)/2}" y="{B+52}" font-size="12" fill="{INK2}" text-anchor="middle">people per square mile (log bands)</text>'
    # mean line
    s += '<polyline points="' + ' '.join(f'{x:.1f},{yy:.1f}' for x, yy in pts) + f'" fill="none" stroke="{INK}" stroke-width="2.5"/>'
    for (x, yy), b in zip(pts, bins):
        s += f'<circle cx="{x:.1f}" cy="{yy:.1f}" r="5" fill="#fff" stroke="{INK}" stroke-width="2"/>'
        s += f'<text x="{x+9}" y="{yy-8}" font-size="11" font-weight="bold" fill="{INK}">{pct(b["kfr25"])}</text>'
    # your county marker
    s += f'<circle cx="{pts[1][0]-18:.1f}" cy="{y(0.48):.1f}" r="7" fill="none" stroke="{VIOLET}" stroke-width="2"/>'
    s += f'<text x="{pts[1][0]-8:.1f}" y="{y(0.48)-10:.1f}" font-size="11" fill="{VIOLET}" font-weight="bold">your county</text>'
    s += note(630, 100, ['Insight (Atul): the most rural', 'counties give poor children the', 'best outcomes; the advantage', 'fades as density rises, then', 'flattens past 100/sq mi.'], 230, False)
    s += note(630, 200, ['Interaction: hover a band to', 'highlight its counties on the', 'main map. Toggle to high-income', 'children: the gradient almost', 'disappears (62% to 57%).'])
    s += note(630, 300, ['Marks: one jittered dot per', 'county (strip plot), band mean', 'as a bold line. Dots fade as', 'the band is hovered elsewhere.'])
    s += note(630, 390, ['Open question: show the 8', 'counties over 10,000/sq mi, or', 'fold them into the 1,000+ band?'])
    return s + '</svg>'


# ---------------------------------------------------------------- 2. age slope
def age_slope():
    a = derived['ages']
    L, R, T, B = 110, 440, 100, 430
    y = lambda v: B - (v - 0.30) / (0.70 - 0.30) * (B - T)
    s = head('Ages 24 to 29: the paths diverge', 'Does the gap between rich and poor children grow after they enter the workforce?')
    for v in (0.3, 0.4, 0.5, 0.6, 0.7):
        s += f'<line x1="{L}" y1="{y(v)}" x2="{R}" y2="{y(v)}" stroke="{RULE}"/>'
        s += f'<text x="{L-8}" y="{y(v)+4}" font-size="11" fill="{INK3}" text-anchor="end">{pct(v)}</text>'
    for x, lab in ((L, 'age 24'), (R, 'age 29')):
        s += f'<line x1="{x}" y1="{T}" x2="{x}" y2="{B}" stroke="{INK3}"/>'
        s += f'<text x="{x}" y="{B+20}" font-size="12" fill="{INK2}" text-anchor="middle" font-weight="bold">{lab}</text>'
    s += f'<text transform="translate(40,{(T+B)/2}) rotate(-90)" font-size="12" fill="{INK2}" text-anchor="middle">income rank in the national distribution</text>'
    # faint county slopes, p25 (real)
    for d in random.sample([d for d in rel if d['kfr24_25'] and d['kfr29_25']], 400):
        s += f'<line x1="{L}" y1="{y(d["kfr24_25"]):.1f}" x2="{R}" y2="{y(d["kfr29_25"]):.1f}" stroke="{RED}" stroke-width="1" opacity="0.07"/>'
    # national p25 (real) and p75 (placeholder until rebuild: drawn as sketch)
    s += f'<line x1="{L}" y1="{y(a["kfr24_25"])}" x2="{R}" y2="{y(a["kfr29_25"])}" stroke="{RED}" stroke-width="3"/>'
    s += f'<text x="{R+10}" y="{y(a["kfr29_25"])+4}" font-size="12" fill="{RED}" font-weight="bold">low-income: {pct(a["kfr24_25"])} to {pct(a["kfr29_25"])}</text>'
    p75_24, p75_29 = 0.52, 0.61   # placeholder shape; real columns arrive with next data rebuild
    s += f'<line x1="{L}" y1="{y(p75_24)}" x2="{R}" y2="{y(p75_29)}" stroke="{BLUE}" stroke-width="3" stroke-dasharray="7 5"/>'
    s += f'<text x="{R+10}" y="{y(p75_29)+4}" font-size="12" fill="{BLUE}" font-weight="bold">high-income (sketched)</text>'
    # your county
    s += f'<line x1="{L}" y1="{y(0.44)}" x2="{R}" y2="{y(0.40)}" stroke="{VIOLET}" stroke-width="2.5"/>'
    s += f'<text x="{(L+R)/2}" y="{y(0.42)-8}" font-size="11" fill="{VIOLET}" font-weight="bold" text-anchor="middle">your county, low-income parents</text>'
    # scrubber
    s += f'<rect x="{L}" y="{B+42}" width="{R-L}" height="4" rx="2" fill="{RULE}"/>'
    s += f'<circle cx="{L+(R-L)*0.6}" cy="{B+44}" r="8" fill="#fff" stroke="{INK}" stroke-width="2"/>'
    s += f'<text x="{L+(R-L)*0.6}" y="{B+70}" font-size="11" fill="{INK2}" text-anchor="middle">scrub the cohort from 24 to 29</text>'
    s += note(650, 100, ['Insight (Atul): between 24 and', '29, children of low-income', 'parents FALL in the distribution', f'({pct(a["kfr24_25"])} to {pct(a["kfr29_25"])}) while children of', 'high-income parents rise.'], 210, False)
    s += note(650, 200, ['Why: early-twenties ranks are', 'compressed (everyone earns little);', 'by 29 college graduates pull away.', 'The gap by parent income widens', 'with age.'], 210)
    s += note(650, 300, ['Interaction: pick a county to draw', 'its own slopes on top. Faint red', 'lines = every county (p25).', 'Blue p75 line is sketched: the', 'p75 age columns are added to', 'build_counties.py for the rebuild.'], 210)
    return s + '</svg>'


# ---------------------------------------------------------------- 3. twins
def twin_counties():
    t = derived['twins'][0]
    flat, steep = t['flat'], t['steep']
    by = {d['fips']: d for d in rows}
    f, g = by[flat['fips']], by[steep['fips']]
    s = head('Twin counties: same floor, different ceiling', 'Can two places give poor children the same outcome but rich children very different ones?')
    L, R, T, B = 120, 520, 100, 420
    x = lambda p: L + (p - 25) / 50 * (R - L)
    y = lambda v: B - (v - 0.30) / (0.70 - 0.30) * (B - T)
    for v in (0.3, 0.4, 0.5, 0.6, 0.7):
        s += f'<line x1="{L}" y1="{y(v)}" x2="{R}" y2="{y(v)}" stroke="{RULE}"/>'
        s += f'<text x="{L-8}" y="{y(v)+4}" font-size="11" fill="{INK3}" text-anchor="end">{pct(v)}</text>'
    for p in (25, 50, 75):
        s += f'<text x="{x(p)}" y="{B+20}" font-size="12" fill="{INK2}" text-anchor="middle">p{p}</text>'
    s += f'<text x="{(L+R)/2}" y="{B+40}" font-size="12" fill="{INK2}" text-anchor="middle">parents\' income percentile</text>'
    s += f'<text transform="translate(50,{(T+B)/2}) rotate(-90)" font-size="12" fill="{INK2}" text-anchor="middle">child\'s adult income rank</text>'
    # shaded difference
    poly = f'{x(25)},{y(f["kfr25"])} {x(50)},{y(f["kfr50"])} {x(75)},{y(f["kfr75"])} {x(75)},{y(g["kfr75"])} {x(50)},{y(g["kfr50"])} {x(25)},{y(g["kfr25"])}'
    s += f'<polygon points="{poly}" fill="{VIOLET}" opacity="0.12"/>'
    for d, col, lab in ((f, RED, flat['name']), (g, BLUE, steep['name'])):
        pts = ' '.join(f'{x(p)},{y(d[k])}' for p, k in ((25, 'kfr25'), (50, 'kfr50'), (75, 'kfr75')))
        s += f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="3"/>'
        for p, k in ((25, 'kfr25'), (50, 'kfr50'), (75, 'kfr75')):
            s += f'<circle cx="{x(p)}" cy="{y(d[k])}" r="5" fill="{col}" stroke="#fff" stroke-width="1.5"/>'
        s += f'<text x="{x(75)+10}" y="{y(d["kfr75"])+4}" font-size="12" fill="{col}" font-weight="bold">{lab}: {pct(d["kfr75"])}</text>'
    s += f'<text x="{x(25)-10}" y="{y(f["kfr25"])-12}" font-size="11" fill="{INK}" text-anchor="end" font-weight="bold">both {pct(f["kfr25"])}</text>'
    s += f'<text x="{x(62)}" y="{y((f["kfr75"]+g["kfr75"])/2)+4}" font-size="11" fill="{VIOLET}" font-weight="bold">{round((g["kfr75"]-f["kfr75"])*100)}-point</text>'
    s += f'<text x="{x(62)}" y="{y((f["kfr75"]+g["kfr75"])/2)+18}" font-size="11" fill="{VIOLET}" font-weight="bold">difference</text>'
    # search box mock
    s += f'<rect x="{L}" y="{B+56}" width="{R-L}" height="30" rx="5" fill="#fff" stroke="{INK}" stroke-width="1.5"/>'
    s += f'<text x="{L+10}" y="{B+76}" font-size="12" fill="{INK3}">pick a county... its twin is found automatically</text>'
    s += note(640, 100, ['Insight: a single county average', 'hides this. Both counties give', f'poor children the {pct(f["kfr25"])}; rich', f'children reach {pct(f["kfr75"])} in one and', f'{pct(g["kfr75"])} in the other.'], 220, False)
    s += note(640, 200, ['Twin rule (derive_stats.py):', 'large counties, p25 outcome', 'within 0.5 pts, gap differs by', '8+ pts. Top 12 pairs are', 'precomputed in derived.json.'], 220)
    s += note(640, 300, ['Interaction: choose any county;', 'the app finds its nearest twin.', 'Both curves drawn, difference', 'shaded. Hover a point for the', 'exact value. A small map inset', 'shows where the two are.'], 220)
    s += note(640, 410, ['Why it matters: mobility should', 'be reported by parent income,', 'not as one county number.'], 220)
    return s + '</svg>'


out = {'density_gradient.svg': density_gradient(), 'age_slope.svg': age_slope(), 'twin_counties.svg': twin_counties()}
dst = os.path.join(ROOT, 'static', 'drafts')
os.makedirs(dst, exist_ok=True)
for name, svg in out.items():
    p = os.path.join(HERE, name)
    open(p, 'w', encoding='utf-8').write(svg)
    shutil.copy(p, os.path.join(dst, name))
    print('wrote', name, f'{len(svg)/1024:.0f} KB')
