"""Draw the RQ2 outcome figure for the thesis: one 100 % bar per group of packages.

    .venv/bin/python -I 2-dependencies/figures/outcomes.py [THESIS_IMAGES]

Reads 2a-determinism/results/categories.tsv, 2b-rebuild/results/categories.tsv and
population/results/packages.tsv, and writes figures/outcomes.pdf and .png here.
With THESIS_IMAGES, the PDF is also written there as rq2-outcomes.pdf.

Two panels with one meaning per colour in both:
  blues   the builds match (2a: darker = without configuration)
  orange  the builds differ
  greys   nothing to compare (did not build, no package, no recipe)
Part 2a is counted at assembly level. Part 2b's six outcomes are folded into three; the publisher's build is left to the text.
"""
import csv, os, sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES = os.path.join(HERE, 'figures')

DARK, MID, LIGHT, ORANGE, GREY, PALE = '#1f3f7a', '#3f7fbf', '#9ec5e6', '#e8863a', '#a6a6a6', '#dcdcdc'

OUTCOMES_2A = (
    ('as is', 'Identical as is', DARK),
    ('with configuration', 'Identical with configuration', MID),
    ('unreproducible', 'Not identical', ORANGE),
    ('did not build', 'Could not be built', GREY),
)
OUTCOMES_2B = (
    (('identical', 'identical without signatures'), 'Reproduced', DARK),
    (('same code', 'other code'), 'Differs', ORANGE),
    (('no package', 'no recipe'), 'Could not be rebuilt', GREY),
)

plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'], 'font.size': 9,
    'axes.linewidth': 0.6, 'axes.edgecolor': '#555555', 'xtick.major.width': 0.6, 'xtick.major.size': 3,
    'ytick.major.size': 0, 'legend.frameon': False, 'pdf.fonttype': 42, 'savefig.dpi': 300,
})


def read_tsv(path):
    with open(os.path.join(HERE, path), newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def key(r):
    return r['package'].lower(), r['version']


def bars_2a():
    owner = {key(r): r['owner'] for r in read_tsv('population/results/packages.tsv')}
    rows = read_tsv('2a-determinism/results/categories.tsv')
    value = lambda r: r['cat_assemblies'] if r['screen'] == 'built' else 'did not build'
    return [
        ('Third-party', [value(r) for r in rows if owner[key(r)] == 'third-party']),
        ('Microsoft', [value(r) for r in rows if owner[key(r)] == 'Microsoft']),
        ('All', [value(r) for r in rows]),
    ]


def bars_2b():
    rows = read_tsv('2b-rebuild/results/categories.tsv')
    return [
        ('Third-party', [r['release_build'] for r in rows if r['owner'] == 'third-party']),
        ('Microsoft', [r['release_build'] for r in rows if r['owner'] == 'Microsoft']),
        ('All', [r['release_build'] for r in rows]),
    ]


def count_label(ax, x, y, n, colour, share):
    if n == 0:
        return
    dark = sum(int(colour[i:i + 2], 16) for i in (1, 3, 5)) < 3 * 140
    size = 7 if share < 0.03 else 8  # a narrow segment still takes its one digit, a little smaller
    ax.text(x, y, str(n), ha='center', va='center', fontsize=size, color='white' if dark else '#1a1a1a')


def panel(ax, bars, outcomes, title):
    ys, labels = [], []
    y = 0
    for bar in bars:
        if bar is None:
            y -= 0.5
            continue
        name, values = bar
        left = 0
        for code, legend, colour in outcomes:
            n = sum(v in (code if isinstance(code, tuple) else (code,)) for v in values)
            share = n / len(values)
            ax.barh(y, share, left=left, height=0.68, color=colour, edgecolor='white', linewidth=1,
                    label=legend if not ys else None)
            count_label(ax, left + share / 2, y, n, colour, share)
            left += share
        ys.append(y)
        labels.append(f'{name} (n = {len(values)})')
        y -= 1
    ax.set_yticks(ys, labels)
    ax.set_xlim(0, 1)
    ax.set_xticks([])  # each bar is all of its packages; the counts are written on the segments
    for side in ('top', 'right', 'left', 'bottom'):
        ax.spines[side].set_visible(False)
    ax.set_title(title, loc='left', fontsize=9, fontweight='bold', pad=6)
    return ys


def main(thesis):
    fig, (top, bottom) = plt.subplots(2, 1, figsize=(6.2, 3.9), gridspec_kw={'height_ratios': [3, 3], 'hspace': 0.75})
    panel(top, bars_2a(), OUTCOMES_2A, 'Part 2a: determinism under variation (assemblies)')
    panel(bottom, bars_2b(), OUTCOMES_2B, 'Part 2b: rebuilding the published assembly')
    top.legend(loc='upper left', bbox_to_anchor=(0, -0.02), ncol=4, handlelength=1, handleheight=1, columnspacing=1.0)
    bottom.legend(loc='upper left', bbox_to_anchor=(0, -0.02), ncol=3, handlelength=1, handleheight=1, columnspacing=1.0)
    bottom.set_xlabel('')
    os.makedirs(FIGURES, exist_ok=True)
    fig.savefig(os.path.join(FIGURES, 'outcomes.pdf'), bbox_inches='tight')
    fig.savefig(os.path.join(FIGURES, 'outcomes.png'), bbox_inches='tight')
    if thesis:
        fig.savefig(os.path.join(thesis, 'rq2-outcomes.pdf'), bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
