"""Draw the thesis's simplified variation figure for part 2a: which variations make the two builds differ.

    .venv/bin/python -I 2-dependencies/figures/variations.py [THESIS_IMAGES]

Reads 2a-determinism/results/runs.tsv and writes figures/variations.pdf and .png here;
with THESIS_IMAGES also rq2-variations.pdf there.

Two panels, the package file and the assemblies (package entries give the same counts as assemblies in
every run), three rows: build path, clock, and the other six variations, whose counts are the same for
all six. Bars count the packages of the 127 that built whose two builds differ, in each condition.
Orange as in the outcome figure: orange means the builds differ (darker = configured).
"""
import csv, os, sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIGURES = os.path.join(HERE, 'figures')
OTHERS = ('environment', 'locales', 'exec_path', 'timezone', 'umask', 'fileordering')
ROWS = (('build_path', 'Build path'), ('time', 'Clock'), ('others', 'Each of the other six'))
MODES = (('default', 'Default', '#f6c08f'), ('configured', 'Configured', '#d9661f'))
PANELS = (('b1', 'Package file'), ('b3', 'Assemblies'))

plt.rcParams.update({
    'font.family': 'sans-serif', 'font.sans-serif': ['Helvetica', 'Arial', 'DejaVu Sans'], 'font.size': 9,
    'axes.linewidth': 0.6, 'axes.edgecolor': '#555555', 'xtick.major.width': 0.6, 'xtick.major.size': 3,
    'ytick.major.size': 0, 'legend.frameon': False, 'pdf.fonttype': 42, 'savefig.dpi': 300,
})


def main(thesis):
    with open(os.path.join(HERE, '2a-determinism/results/runs.tsv'), newline='') as f:
        runs = [r for r in csv.DictReader(f, delimiter='\t') if r['mode'] in ('default', 'configured')]
    total = len({r['package'] + ' ' + r['version'] for r in runs})

    def count(level, axis, mode):
        if axis != 'others':
            return sum(r['axes'] == axis and r['mode'] == mode and r[level] == 'differs' for r in runs)
        counts = {sum(r['axes'] == a and r['mode'] == mode and r[level] == 'differs' for r in runs) for a in OTHERS}
        assert len(counts) == 1, (level, mode, counts)  # the six really do agree
        return counts.pop()

    fig, axes = plt.subplots(1, 2, figsize=(6.2, 2.3), sharey=True, gridspec_kw={'wspace': 0.12})
    for ax, (level, title) in zip(axes, PANELS):
        for y, (axis, _) in enumerate(reversed(ROWS)):
            for i, (mode, label, colour) in enumerate(MODES):
                n = count(level, axis, mode)
                bar = y + (0.19 if i == 0 else -0.19)
                ax.barh(bar, n, height=0.36, color=colour, label=label if y == 0 and ax is axes[0] else None)
                ax.text(n + 2, bar, str(n), va='center', ha='left', fontsize=8, color='#1a1a1a')
        ax.set_xlim(0, total + 14)
        ax.set_xticks([0, 25, 50, 75, 100, total])
        ax.set_title(title, fontsize=9, fontweight='bold', loc='left')
        ax.grid(axis='x', color='#e6e6e6', linewidth=0.5)
        ax.set_axisbelow(True)
        for side in ('top', 'right', 'left'):
            ax.spines[side].set_visible(False)
    axes[0].set_yticks(range(len(ROWS)), [label for _, label in reversed(ROWS)])
    fig.supxlabel(f'Packages whose two builds differ (of the {total} that built)', fontsize=9, y=-0.06)
    axes[0].legend(loc='upper left', bbox_to_anchor=(0, -0.24), ncol=2, handlelength=1, handleheight=1)
    os.makedirs(FIGURES, exist_ok=True)
    fig.savefig(os.path.join(FIGURES, 'variations.pdf'), bbox_inches='tight')
    fig.savefig(os.path.join(FIGURES, 'variations.png'), bbox_inches='tight')
    if thesis:
        fig.savefig(os.path.join(thesis, 'rq2-variations.pdf'), bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else None)
