"""Draw the match figure of part 2b from results/, in the style of Solarin et al. (2026), Fig. 4.

    python3 -I scripts/figures.py [THESIS_IMAGES]

Reads `results/categories.tsv` and writes `figures/match.pdf` and `.png`: one 100 % bar
per group of packages, the release build above (third-party, Microsoft, all 198) and the publisher's build
below (windows-2022, Linux VMR, all 96). The matches take Solarin's level colours: identical as L1, identical
without signatures as L2, same code as L3, other code as NV, and the two not-built outcomes as L0, in two greys:
no package (darker) and no recipe (lighter).
With THESIS_IMAGES, the PDF is also written there as 2b-match.pdf.

Needs matplotlib. The publisher's build uses the Roslyn rule (column publisher_build), as the README's table.
"""
import csv, os, sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, 'results')
FIGURES = os.path.join(HERE, 'figures')

MATCHES = (
    (('identical',), 'Identical', '#1f3f7a'),
    (('identical without signatures',), 'Identical without signatures', '#3f7fbf'),
    (('same code',), 'Same code', '#9ec5e6'),
    (('other code',), 'Other code', '#f4a261'),
    (('no package',), 'No package', '#bdbdbd'),
    (('no recipe',), 'No recipe', '#e6e6e6'),
)

plt.rcParams.update({
    'font.family': 'DejaVu Sans', 'font.size': 8, 'axes.linewidth': 0.6, 'axes.edgecolor': '#555555',
    'xtick.major.width': 0.6, 'ytick.major.width': 0.6, 'xtick.major.size': 3, 'ytick.major.size': 0,
    'legend.frameon': False, 'pdf.fonttype': 42, 'savefig.dpi': 300,
})


def read_tsv(name):
    with open(os.path.join(RESULTS, name), newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def count_label(ax, x, y, n, colour, ha='center'):
    """Write the count n at x on bar y: white on the dark shades, near-black on the light ones."""
    if n == 0:
        return
    dark = sum(int(colour[i:i + 2], 16) for i in (1, 3, 5)) < 3 * 128
    ax.text(x, y, str(n), ha=ha, va='center', fontsize=7, color='white' if dark else '#1a1a1a')


def groups(rows):
    """Return (build, label, matches) per bar, top to bottom."""
    publisher = [r for r in rows if r['publisher_build']]
    return [
        ('Release build', 'Third-party', [r['release_build'] for r in rows if r['owner'] == 'third-party']),
        ('Release build', 'Microsoft', [r['release_build'] for r in rows if r['owner'] == 'Microsoft']),
        ('Release build', 'All', [r['release_build'] for r in rows]),
        ("Publisher's build", 'windows-2022', [r['publisher_build'] for r in publisher if r['publisher_build_host'] == 'windows']),
        ("Publisher's build", 'Linux (VMR)', [r['publisher_build'] for r in publisher if r['publisher_build_host'] == 'linux']),
        ("Publisher's build", 'All', [r['publisher_build'] for r in publisher]),
    ]


def match(thesis):
    bars = groups(read_tsv('categories.tsv'))
    fig, ax = plt.subplots(figsize=(6.0, 2.4))
    ys = [len(bars) - i - (0.6 if i >= 3 else 0) for i in range(len(bars))]
    for y, (_, label, values) in zip(ys, bars):
        left = 0
        for names, legend, colour in MATCHES:
            n = sum(v in names for v in values)
            share = n / len(values)
            ax.barh(y, share, left=left, height=0.7, color=colour, label=legend if y == ys[0] else None)
            count_label(ax, left + share / 2, y, n, colour)
            left += share
    ax.set_yticks(ys, [f'{label} (n = {len(values)})' for _, label, values in bars])
    for build, middle in (('Release build', ys[1]), ("Publisher's build", ys[4])):
        ax.annotate(build, xy=(0, middle), xycoords=('axes fraction', 'data'), xytext=(-118, 0),
                    textcoords='offset points', rotation=90, ha='center', va='center')
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_xlabel('% Packages')
    ax.grid(axis='x', color='#dddddd', linewidth=0.5)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)
    ax.legend(loc='upper center', bbox_to_anchor=(0.45, -0.22), ncol=6, handlelength=1, handleheight=1,
              columnspacing=0.9)
    fig.savefig(os.path.join(FIGURES, 'match.pdf'), bbox_inches='tight')
    fig.savefig(os.path.join(FIGURES, 'match.png'), bbox_inches='tight')
    if thesis:
        fig.savefig(os.path.join(thesis, '2b-match.pdf'), bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    match(sys.argv[1] if len(sys.argv) > 1 else None)
