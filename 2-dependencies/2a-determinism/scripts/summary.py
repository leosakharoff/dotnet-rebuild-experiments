"""Summarise the lab's state files by population, axis, package category and unresolved differences.

    python3 -I summary.py LAB [OUTDIR]

Write `summary.md` to OUTDIR (default LAB) with:
  1. population: built / did not build, with the first error of each
  2. per axis, default build: how many packages differ at each level
  3. per package, Benedetti's Figure 3 category at each level
     (as is / with configuration / unreproducible / not reached)
  4. the packages the configuration does not fix, with the first difference
  5. the packages whose assemblies are identical under every axis as is
and `categories.tsv` with one row per package and the category columns.

Category rules, per level L in {1 package file, 2 package entries, 3 assemblies}:
  as is               every default run is `same` at L ("as is" is Benedetti's term for the default build)
  with configuration  not as is; every default run that differed at L has a configured run that is `same` at L
  unreproducible      some configured run differs or fails at L
  not reached         a default or configured run is missing (the run did not get to the package)
"""
import collections, json, os, re, sys

AXES = ['build_path', 'environment', 'locales', 'exec_path', 'time', 'timezone', 'umask', 'fileordering']
LEVELS = (('b1', '1 package file'), ('b2', '2 package entries'), ('b3', '3 assemblies'))
CATEGORIES = ['as is', 'with configuration', 'unreproducible', 'not reached']


def category(runs, level):
    default = {axis: runs.get(f'default:{axis}') for axis in AXES}
    if any(run is None for run in default.values()):
        return 'not reached'
    if all(run[level] == 'same' for run in default.values()):
        return 'as is'
    for axis, run in default.items():
        if run[level] == 'same':
            continue
        configured = runs.get(f'configured:{axis}')
        if configured is None:
            return 'not reached'
        if configured[level] != 'same':
            return 'unreproducible'
    return 'with configuration'


def load_states(lab):
    states = []
    for pid in sorted(os.listdir(os.path.join(lab, 'out'))):
        path = os.path.join(lab, 'out', pid, 'state.json')
        if os.path.exists(path):
            state = json.load(open(path))
            state['id'] = pid
            states.append(state)
    return states


def name_of(state):
    return f'{state["recipe"]["package"]} {state["recipe"]["version"]}'


def error_key(state):
    """Return the error code (MSB4019, NETSDK1226, CS0234, ...), else the text after the last ': error :'."""
    text = state.get('screen_error') or state.get('screen') or ''
    found = re.search(r'error\s+([A-Z]+\d+)', text)
    if found:
        return found.group(1)
    if ': error :' in text:
        return text.split(': error :', 1)[1].strip()[:70]
    return text[:70]


def axis_row(name, runs):
    """Count differences at each level and failures for one table row."""
    differs = [sum(run[level] == 'differs' for run in runs) for level in ('b1', 'b2', 'b3')]
    failed = sum(run['b1'] == 'failed' for run in runs)
    return f'| {name} | {len(runs)} | {differs[0]} | {differs[1]} | {differs[2]} | {failed} |'


def main():
    lab = os.path.abspath(sys.argv[1])
    outdir = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else lab
    states = load_states(lab)
    built = [s for s in states if s.get('screen') == 'built']
    not_built = [s for s in states if s.get('screen') == 'not built']   # No source or project was found by population.py.
    failed = [s for s in states if s.get('screen') not in ('built', 'not built', None)]
    lines = [f'# Determinism experiment, summary ({len(states)} packages)', '']

    lines += ['## 1. Population', '', '| outcome | packages |', '|---|---|',
              f'| built under the fixed SDK | {len(built)} |',
              f'| did not build (first error logged) | {len(failed)} |']
    if not_built:
        lines.append(f'| no source or project (population.py) | {len(not_built)} |')
    lines += ['', 'Did not build, by first error:', '']
    causes = collections.Counter(error_key(s) for s in failed)
    for cause, n in causes.most_common():
        lines.append(f'- {n}: {cause}')
    lines += ['', 'Did not build, per package:', '']
    for s in failed:
        lines.append(f'- {name_of(s)}: {s.get("screen")}; {s.get("screen_error", "")[:140]}')
    lines.append('')

    lines += ['## 2. Per axis, default build: packages that differ', '',
              '| axis | runs | differs at 1 (package file) | differs at 2 (package entries) | differs at 3 (assemblies) | build failed |',
              '|---|---|---|---|---|---|']
    for axis in AXES:
        runs = [s['runs'][f'default:{axis}'] for s in built if f'default:{axis}' in s.get('runs', {})]
        lines.append(axis_row(axis, runs))
    runs = [s['runs']['default:all'] for s in built if 'default:all' in s.get('runs', {})]
    lines.append(axis_row('all eight at once', runs))
    lines.append('')

    lines += ['## 3. Per package category, by level', '']
    cats = {s['id']: {level: category(s.get('runs', {}), level) for level, _ in LEVELS} for s in built}
    lines += ['| level | ' + ' | '.join(CATEGORIES) + ' |', '|---|' + '---|' * len(CATEGORIES)]
    for level, name in LEVELS:
        count = collections.Counter(cats[i][level] for i in cats)
        lines.append(f'| {name} | ' + ' | '.join(str(count.get(c, 0)) for c in CATEGORIES) + ' |')
    lines.append('')

    lines += ['## 4. Not fixed by the configuration (level 3, assemblies)', '']
    for s in built:
        if cats[s['id']]['b3'] != 'unreproducible':
            continue
        bad = []
        for axis in AXES:
            run = s['runs'].get(f'configured:{axis}')
            if run and run['b3'] != 'same':
                text = f'{axis}: {run["b3"]}'
                if run.get('first'):
                    text += f' ({run["first"]})'
                if run.get('note'):
                    text += f' [{run["note"][:80]}]'
                bad.append(text)
        lines.append(f'- {name_of(s)}: ' + '; '.join(bad))
    lines.append('')

    lines += ['## 5. Identical assemblies under every axis with the default build (level 3 "as is")', '']
    for s in built:
        if cats[s['id']]['b3'] == 'as is':
            lines.append(f'- {name_of(s)}')
    lines.append('')

    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, 'summary.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    columns = ['package', 'version', 'repo', 'screen', 'global_json', 'cat_package_file', 'cat_package_entries', 'cat_assemblies',
               'axes_run', 'first_difference_all_axes']
    with open(os.path.join(outdir, 'categories.tsv'), 'w', encoding='utf-8') as f:
        f.write('\t'.join(columns) + '\n')
        for s in states:
            cat = cats.get(s['id'], {})
            runs = s.get('runs', {})
            axes_run = sum(1 for key in runs if key.startswith('default:') and key != 'default:all')
            cells = [s['recipe']['package'], s['recipe']['version'], s['recipe']['repo'],
                     s.get('screen', ''), s.get('global_json', ''),
                     cat.get('b1', ''), cat.get('b2', ''), cat.get('b3', ''),
                     str(axes_run), runs.get('default:all', {}).get('first', '')]
            f.write('\t'.join(cells) + '\n')
    print('\n'.join(lines[:60]))


if __name__ == '__main__':
    main()
