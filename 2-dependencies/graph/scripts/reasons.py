"""One short line per package and part: why the package has its 2a and its 2b category.

    python3 -I scripts/reasons.py results/graph.json EXPERIMENT_2_DIR results/reasons.json

2a: from 2a-determinism/results/categories.tsv and runs.tsv (assembly level, column b3), and the in_2a reason in
    population/results/packages.tsv. The error key is the one summary.py uses: the error code, else the message.
2b: from 2b-rebuild/results/categories.tsv (release_build, publisher_build, publisher_build_host), release-build.tsv
    (category: the rule that stopped a recipe; build; differs) and publisher-build.tsv (differs), and the class in
    packages.tsv for a package outside 2b.
"""
import csv, json, os, re, sys

GRAPH, EXP, OUT = sys.argv[1:4]


def tsv(*p):
    with open(os.path.join(EXP, *p), newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


key = lambda r: f"{r['package']}/{r['version']}"
pop = {key(r): r for r in tsv('population', 'results', 'packages.tsv')}
cat2a = {key(r): r for r in tsv('2a-determinism', 'results', 'categories.tsv')}
runs = {}
for r in tsv('2a-determinism', 'results', 'runs.tsv'):
    runs.setdefault(key(r), []).append(r)
cat2b = {key(r): r for r in tsv('2b-rebuild', 'results', 'categories.tsv')}
rel = {key(r): r for r in tsv('2b-rebuild', 'results', 'release-build.tsv')}
pub = {key(r): r for r in tsv('2b-rebuild', 'publisher-build', 'results', 'publisher-build.tsv')}

AXES = {'build_path': 'build path', 'exec_path': 'exec path', 'fileordering': 'file order', 'time': 'time',
        'environment': 'environment', 'locales': 'locales', 'timezone': 'timezone', 'umask': 'umask'}
CLASSES = {
    'N0': 'Ships no files (class N0).', 'N1': 'Native code only (class N1).',
    'C1a': 'No repository in the .nuspec (class C1a).', 'C1b': 'A repository, but no commit in the .nuspec (class C1b).',
    'C2a': 'No PDB, so no compiler record (class C2a).', 'C2b': 'PDB only referenced, not in the package, so no compiler record (class C2b).',
    'C2c': 'PDB in the package, but no compiler record (class C2c).',
}
GENERIC = {'file', 'sha256', 'size'}  # these differ whenever anything differs


def axes_that_differ(rs, mode):
    names = [r['axes'] for r in rs if r['mode'] == mode and r['b3'] == 'differs']
    named = [AXES.get(a, a) for a in names if a != 'all']
    return ', '.join(dict.fromkeys(named)) or ('all variations together' if 'all' in names else '')


def cap(s):
    return s[:1].upper() + s[1:]  # str.capitalize() would lower-case package names


def cut(s, n=70):
    s = re.sub(r'\s+', ' ', s).strip()
    return s if len(s) <= n else s[:n].rsplit(' ', 1)[0].rstrip(',;:.') + '…'


def error_key(text):
    """As summary.py: the error code, else the message after ': error :'; cut at a word."""
    found = re.search(r'error\s+([A-Z]+\d+)', text)
    if found:
        return found.group(1)
    if ': error :' in text:
        return cut(text.split(': error :', 1)[1])
    return cut(text)


def short_diff(text, n=4):
    parts = [p.strip() for p in text.split(',') if p.strip() and p.strip() not in GENERIC]
    return ', '.join(parts[:n]) + (' …' if len(parts) > n else '')


def first_difference(text):
    if ':' in text:
        pkg, entry = text.split(':', 1)
        return f'{pkg}: …/{entry.rsplit("/", 1)[-1]}' if '/' in entry else f'{pkg}: {entry}'
    return text


def reason_2a(i):
    c = cat2a.get(i)
    if not c:
        why = pop[i]['in_2a'].removeprefix('no: ')
        if why.count('(') > why.count(')'):
            why += ')'  # packages.tsv cuts this reason before its closing parenthesis
        return cap(why) + '.'
    if c['screen'] != 'built':
        err = next((r['screen_error'] for r in runs.get(i, []) if r['screen_error']), '')
        k = error_key(err)
        return f"{cap(c['screen'].replace(' (exit 1)', ''))}: {k}{'' if k.endswith('…') else '.'}" if err else cap(c['screen']) + '.'
    rs, level = runs.get(i, []), c['cat_assemblies']
    if level == 'as is':
        return 'Identical in every variation, also with the default build.'
    if level == 'with configuration':
        d = axes_that_differ(rs, 'default')
        return 'Identical with configuration.' + (f' The default build differs under {d}.' if d else '')
    d = axes_that_differ(rs, 'configured')
    fd = first_difference(c['first_difference_all_axes'])
    return f'Differs under {d or "a variation"}, also with configuration.' + (f' First difference: {fd}.' if fd else '')


def release_text(i, c):
    lvl, r = c['release_build'], rel.get(i, {})
    if lvl == 'no recipe':
        rule = re.sub(r'^skipped \(', '', r.get('category', '')).rstrip(')')
        rule = re.sub(r'\s*\(read \d+:.*$', '', rule)        # drop the list of SDKs read
        rule = re.sub(r'^(sdk|source|package|project|pdb|os|version): ', '', rule)
        return f'no recipe ({rule[:110]}{"…" if len(rule) > 110 else ""})' if rule else 'no recipe'
    if lvl == 'no package':
        b = r.get('build', '')
        return 'no package (did not build)' if b.startswith('did not build') else 'no package (built, but no package to compare)'
    if lvl in ('same code', 'other code'):
        d = short_diff(r.get('differs', ''))
        return f'{lvl} ({d})' if d else lvl
    return lvl


def reason_2b(i):
    c = cat2b.get(i)
    if not c:
        return CLASSES.get(pop[i]['class'], f"Class {pop[i]['class']}.")
    text = f'Release build: {release_text(i, c)}.'
    if c['publisher_build']:
        host = {'windows': 'windows-2022', 'linux': 'Linux'}.get(c['publisher_build_host'], c['publisher_build_host'])
        lvl = c['publisher_build']
        d = short_diff(pub.get(i, {}).get('differs', '')) if lvl in ('same code', 'other code') else ''
        text += f" Publisher's build on {host}: {lvl}{f' ({d})' if d else ''}."
    return text


g = json.load(open(GRAPH))
out = {}
for n in g['nodes']:
    if n['kind'] == 'package':
        out[n['id']] = {'r2a': reason_2a(n['id']), 'r2b': reason_2b(n['id'])}
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=0)
print(len(out), 'packages; longest 2a', max(len(v['r2a']) for v in out.values()), 'longest 2b', max(len(v['r2b']) for v in out.values()))
