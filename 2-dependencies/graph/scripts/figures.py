"""Draw the dependency graph of Phoenix's shipped packages, coloured by the outcome of part 2a and part 2b.

    python3 -I scripts/figures.py results/graph.json results/layout.json figures/dependency-graph

Writes OUT_PREFIX.pdf and OUT_PREFIX.png: two panels, one above the other, with the positions from scripts/layout.py.
Every second sector has a grey band, and a bracket outside the circle marks where each sector starts and ends.
One colour scale serves both panels, so that a colour means the same kind of outcome in (a) and (b): dark blue,
reproduced with the default inputs; mid blue, reproduced with extra inputs (2a's configuration); orange, built and
compared, but different; grey, did not build or no package to compare; hollow, not attempted. 2b counts the release build alone;
the publisher's build is a diagnostic and has no colour.
The style follows the figures of parts 2a and 2b (DejaVu Sans, embedded TrueType, 300 dpi).
"""
import json, math, sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Arc, Circle, Wedge

GRAPH, LAYOUT, OUT = sys.argv[1:4]

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8, 'legend.frameon': False, 'pdf.fonttype': 42, 'savefig.dpi': 300,
})

SCALE = {'strong': '#1f3f7a', 'repro': '#3f7fbf', 'differs': '#f4a261', 'nobuild': '#bdbdbd'}
BAND = '#f1f1f1'
PARTS = (
    ('a', 'Part 2a: build determinism (assemblies)', 's2a', (
        ('as is', 'strong', 'Reproducible as is'),
        ('with configuration', 'repro', 'Reproducible with configuration'),
        ('unreproducible', 'differs', 'Unreproducible'),
        ('did not build', 'nobuild', 'Did not build'),
        ('not in 2a', 'notin', 'Not attempted'),
    )),
    ('b', 'Part 2b: rebuild against nuget.org', 's2b', (
        ('from the release', 'strong', 'Reproduced from the release'),
        ('built, but differs', 'differs', 'Built, but differs'),
        ('no package', 'nobuild', 'No package to compare'),
        ('no recipe', 'nobuild', None),
        ('not in 2b', 'notin', 'Not attempted'),
    )),
)

g = json.load(open(GRAPH))
lay = json.load(open(LAYOUT))
pos = {n['id']: n for n in lay['nodes']}
nodes = g['nodes']
xy = lambda i: (pos[i]['x'], -pos[i]['y'])  # the layout's y axis points down, as in SVG
segments = [(xy(e['source']), xy(e['target'])) for e in g['edges']]
rings, R, B = lay['rings'], lay['rings'][-1], lay['bracket']
deg = lambda a: -math.degrees(a)  # layout angle (y down) to matplotlib degrees (y up)

fig, axes = plt.subplots(2, 1, figsize=(6.3, 8.9))
fig.subplots_adjust(left=0.0, right=1.0, top=0.985, bottom=0.015, hspace=0.05)
for ax, (letter, title, field, classes) in zip(axes, PARTS):
    ax.set_aspect('equal')
    ax.axis('off')
    lim = R + 345
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-R - 150, R + 45)
    # Bands for every second sector, and a bracket for each sector
    for j, s in enumerate(lay['sectors']):
        t1, t2 = sorted((deg(s['start']), deg(s['end'])))
        if j % 2 == 0:
            ax.add_patch(Wedge((0, 0), R + 12, t1, t2, width=R + 12 - 125, fc=BAND, ec='none', zorder=0))
        ax.add_patch(Arc((0, 0), 2 * B, 2 * B, theta1=t1, theta2=t2, lw=0.6, color='#555555', zorder=1))
        for t in (s['start'], s['end']):
            ax.plot([math.cos(t) * (B - 5), math.cos(t) * (B + 5)], [-math.sin(t) * (B - 5), -math.sin(t) * (B + 5)], lw=0.6, color='#555555')
        (ax_, ay_), (ex, ey), (tx, ty) = s['anchor'], s['elbow'], s['text']
        ax.plot([ax_, ex, tx - s['side'] * 6], [-ay_, -ey, -ty], lw=0.4, color='#888888', zorder=1)
        ax.text(tx, -ty, f"{s['label']} ({s['count']})", fontsize=6, ha='left' if s['side'] > 0 else 'right', va='center', color='#222222')
    for i, r in enumerate(rings[1:], 1):
        ax.add_patch(Circle((0, 0), r, fill=False, lw=0.4, ec='#cfcfcf', zorder=1))
        ax.text(0, r - 4, f'{i}' if i < len(rings) - 1 else f'≥{i}', ha='center', va='top', fontsize=5.5, color='#666666')
    ax.add_collection(LineCollection(segments, lw=0.2, colors='#8c8c8c', alpha=0.22, zorder=2))
    status = {c[0]: c[1] for c in classes}
    groups = {}
    for n in nodes:
        k = 'own' if n['kind'] != 'package' else status[n[field]]
        groups.setdefault(k, []).append(n)
    own = groups.pop('own')
    ax.scatter([xy(n['id'])[0] for n in own], [xy(n['id'])[1] for n in own], s=12, marker='s', c='#1a1a1a', lw=0, zorder=5)
    for k, members in groups.items():
        xs, ys = zip(*(xy(n['id']) for n in members))
        if k == 'notin':
            ax.scatter(xs, ys, s=7, facecolors='white', edgecolors='#8f8f8f', linewidths=0.4, zorder=3)
        else:
            ax.scatter(xs, ys, s=8, c=SCALE[k], linewidths=0, zorder=4)
    ax.text(-lim + 20, R + 38, f'({letter}) {title}', fontsize=8, ha='left', va='top')
    counts = {}
    for n in nodes:
        if n['kind'] == 'package':
            counts[status[n[field]]] = counts.get(status[n[field]], 0) + 1
    handles = []
    for _, k, label in classes:
        if not label:
            continue
        if k == 'notin':
            h = Line2D([], [], ls='', marker='o', ms=3.6, mfc='white', mec='#8f8f8f', mew=0.6)
        else:
            h = Line2D([], [], ls='', marker='o', ms=3.6, mfc=SCALE[k], mec=SCALE[k])
        handles.append((h, f'{label} ({counts.get(k, 0)})'))
    ax.legend([h for h, _ in handles], [t for _, t in handles], loc='lower center', bbox_to_anchor=(0.5, 0.0),
              ncol=3, fontsize=6.5, handletextpad=0.3, borderaxespad=0, labelspacing=0.4, columnspacing=1.4)

fig.savefig(OUT + '.pdf', metadata={'CreationDate': None})  # no date in the PDF: the same input gives the same bytes
fig.savefig(OUT + '.png')
print('wrote', OUT + '.pdf', OUT + '.png')
