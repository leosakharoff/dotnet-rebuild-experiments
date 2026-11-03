"""Draw the two result figures of part 2a from results/, in the style of Benedetti et al. (2025).

    python3 -I scripts/figures.py [THESIS_IMAGES]

Reads `results/categories.tsv` and `results/runs.tsv` and writes to `figures/`:
  categories.pdf, .png  the Figure 3 category of the 127 measured packages at each comparison level
                        (Benedetti's Fig. 3: one 100 % bar per row, blues from light to dark)
  variations.pdf, .png  per variation, the share of the 127 whose two builds differ in content, default and
                        configured (Benedetti's Fig. 4). The whole-file level is left out: every default
                        pair differs or fails there, because NuGet stamps each ZIP entry with the build time, and
                        with DeterministicTimestamp it equals content. The DLL level equals content.
With THESIS_IMAGES, the PDFs are also written there as 2a-categories.pdf and 2a-variations.pdf.

Needs matplotlib. The 97 packages that did not build have no category and are left out of both figures.
"""
import csv, os, sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(HERE, 'results')
FIGURES = os.path.join(HERE, 'figures')

# Benedetti's Fig. 3 shades for as is, with infrastructure configuration and non reproducible.
# Their third shade, patched package manager, has no counterpart here: no patched tool was tested.
CATEGORY_COLOURS = {'as is': '#bdd7ee', 'with configuration': '#5b9bd5', 'unreproducible': '#0b2a55'}
CATEGORY_LABELS = {'as is': 'Reproducible as is', 'with configuration': 'Reproducible with configuration',
                   'unreproducible': 'Unreproducible'}
LEVELS = (('cat_whole_file', 'Whole file'), ('cat_content', 'Content'), ('cat_dll', 'DLLs'))

# The README's order: build_path, time, then the six that behave alike. Kernel is not varied here.
AXES = (('build_path', 'Build path'), ('time', 'Time'), ('environment', 'Environment'), ('locales', 'Locales'),
        ('exec_path', 'Exec path'), ('timezone', 'Timezone'), ('umask', 'Umask'), ('fileordering', 'Fileordering'))
MODE_COLOURS = {'default': '#bdd7ee', 'configured': '#0b2a55'}
MODE_LABELS = {'default': 'Default build', 'configured': 'Configured build'}

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


def style(ax, xlabel):
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
    ax.set_xlabel(xlabel)
    ax.grid(axis='x', color='#dddddd', linewidth=0.5)
    ax.set_axisbelow(True)
    for side in ('top', 'right'):
        ax.spines[side].set_visible(False)


def save(fig, name, thesis):
    fig.savefig(os.path.join(FIGURES, f'{name}.pdf'), bbox_inches='tight')
    fig.savefig(os.path.join(FIGURES, f'{name}.png'), bbox_inches='tight')
    if thesis:
        fig.savefig(os.path.join(thesis, f'2a-{name}.pdf'), bbox_inches='tight')
    plt.close(fig)


def categories(thesis):
    rows = [r for r in read_tsv('categories.tsv') if r['cat_whole_file']]
    fig, ax = plt.subplots(figsize=(6.0, 1.7))
    labels = []
    for y, (column, label) in enumerate(reversed(LEVELS)):
        left = 0
        for cat, colour in CATEGORY_COLOURS.items():
            n = sum(r[column] == cat for r in rows)
            share = n / len(rows)
            ax.barh(y, share, left=left, height=0.6, color=colour, label=CATEGORY_LABELS[cat] if y == 0 else None)
            count_label(ax, left + share / 2, y, n, colour)
            left += share
        labels.append(label)
    ax.set_yticks(range(len(labels)), labels)
    ax.set_ylabel('Comparison level')
    style(ax, f'% Packages (n = {len(rows)})')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.38), ncol=3, handlelength=1, handleheight=1)
    save(fig, 'categories', thesis)


def variations(thesis):
    runs = [r for r in read_tsv('runs.tsv') if r['mode'] in MODE_COLOURS and r['axes'] in dict(AXES)]
    packages = {r['package'] + ' ' + r['version'] for r in runs}
    fig, ax = plt.subplots(figsize=(6.0, 2.6))
    for y, (axis, _) in enumerate(reversed(AXES)):
        for i, mode in enumerate(MODE_COLOURS):
            n = sum(r['axes'] == axis and r['mode'] == mode and r['b2'] == 'differs' for r in runs)
            share = n / len(packages)
            bar = y + (0.18 if i == 0 else -0.18)
            ax.barh(bar, share, height=0.34, color=MODE_COLOURS[mode], label=MODE_LABELS[mode] if y == 0 else None)
            if share > 0.15:
                count_label(ax, share - 0.015, bar, n, MODE_COLOURS[mode], ha='right')
            else:
                count_label(ax, share + 0.015, bar, n, '#ffffff', ha='left')
    ax.set_yticks(range(len(AXES)), [label for _, label in reversed(AXES)])
    ax.set_ylabel('Variations')
    style(ax, f'% Packages whose content differs (n = {len(packages)})')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.22), ncol=2, handlelength=1, handleheight=1)
    save(fig, 'variations', thesis)

if __name__ == '__main__':
    thesis = sys.argv[1] if len(sys.argv) > 1 else None
    categories(thesis)
    variations(thesis)
