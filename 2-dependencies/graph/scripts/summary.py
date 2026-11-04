"""Print the counts that the README states: results/summary.md.

    python3 -I scripts/summary.py results/graph.json results/layout.json results/summary.md

Transitive dependencies are computed inside each program and then combined, so that no path joins two
programs' lock files. Dependencies of class N0 ship no files and are left out of the dependency counts.
"""
import collections, json, sys

GRAPH, LAYOUT, OUT = sys.argv[1:4]
PROGRAMS = ['WebAPI', 'BackgroundJobExecutor', 'DbMigrator']
OK = {'s2a': {'as is', 'with configuration'}, 's2b': {'from the release'}}
DIFFERS = {'s2a': {'unreproducible'}, 's2b': {'built, but differs'}}
OUTSIDE = {'s2a': 'not in 2a', 's2b': 'not in 2b'}

g, lay = json.load(open(GRAPH)), json.load(open(LAYOUT))
N = {n['id']: n for n in g['nodes']}
pkgs = [n for n in g['nodes'] if n['kind'] == 'package']
ring = {n['id']: n['step'] for n in lay['nodes']}
sector = {n['id']: n['sector'] for n in lay['nodes']}
out_by = {p: collections.defaultdict(set) for p in PROGRAMS}
out_all, inn = collections.defaultdict(set), collections.defaultdict(set)
for e in g['edges']:
    out_all[e['source']].add(e['target'])
    inn[e['target']].add(e['source'])
    for p in e['programs']:
        out_by[p][e['source']].add(e['target'])


def reach(i, adj):
    seen, stack = set(), [i]
    while stack:
        for b in adj[stack.pop()]:
            if b not in seen:
                seen.add(b)
                stack.append(b)
    return seen


def down(i):
    return set().union(*(reach(i, out_by[p]) for p in PROGRAMS))


lines = ['# Dependency graph: the counts in the README', '']
add = lines.append

# The graph
pack_edges = sum(1 for e in g['edges'] if N[e['target']].get('via') == 'sdk')
add('## The graph')
add('')
add(f'- {len(pkgs)} package versions and {len(N) - len(pkgs)} Phoenix projects; {len(g["edges"])} edges, the union over the three programs; '
    f'{pack_edges} of them join the runtime and host packs to the programs; '
    f'{sum(1 for n in pkgs if n.get("via") == "tool" and not inn[n["id"]] and not out_all[n["id"]])} package without edges (dotnet-ef)')
rc = collections.Counter(min(ring[n['id']], 4) for n in pkgs)
r1 = [n for n in pkgs if ring[n['id']] == 1]
add(f'- ring 1: {rc[1]} ({sum(1 for n in r1 if not n.get("via"))} named by a project, '
    f'{sum(1 for n in r1 if n.get("via") == "sdk")} packs, {sum(1 for n in r1 if n.get("via") == "tool")} tool); '
    f'ring 2: {rc[2]}; ring 3: {rc[3]}; 4 or more: {rc[4]}')
sec_count = collections.Counter(sector[n['id']] for n in pkgs)
add(f'- {len(lay["sectors"])} sectors; Other repositories: {sec_count["(other)"]}; no repository: {sec_count["(no repository)"]}')
two = sum(1 for i in N if any(c > 1 for c in collections.Counter(
    N[t]['name'].lower() for t in out_all[i] if N[t]['kind'] == 'package').values()))
add(f'- {two} nodes have edges to two versions of one package (the programs lock some packages at different versions)')
direct_rows = [n for n in pkgs if n.get('direct')]
add(f'- packages.tsv marks {len(direct_rows)} rows direct, for {len({n["name"] for n in direct_rows})} names; '
    f'by version, {sum(1 for n in r1 if not n.get("via"))} are named by a project')
add('')

# Status counts
add('## Status counts')
add('')
for f, part in (('s2a', '2a'), ('s2b', '2b')):
    c = collections.Counter(n[f] for n in pkgs)
    add(f'- {part}: ' + ', '.join(f'{k} {v}' for k, v in c.most_common()))
add('')

# Reproduced packages and their dependencies
add('## Reproduced packages and their dependencies')
add('')
add('| part | reproduced | no dependency with files | all dependencies reproduced | a dependency differs | a dependency did not build or has no package to compare | only dependencies not attempted |')
add('|---|---|---|---|---|---|---|')
for f, part in (('s2a', '2a'), ('s2b', '2b')):
    rep = [n for n in pkgs if n[f] in OK[f]]
    cells = collections.Counter()
    for n in rep:
        deps = [N[i] for i in down(n['id']) if N[i]['kind'] == 'package' and N[i]['cls'] != 'N0']
        if not deps:
            cells['none'] += 1
        elif all(d[f] in OK[f] for d in deps):
            cells['all'] += 1
        elif any(d[f] in DIFFERS[f] for d in deps):
            cells['differs'] += 1
        elif any(d[f] not in OK[f] and d[f] != OUTSIDE[f] for d in deps):
            cells['notbuilt'] += 1
        else:
            cells['outside'] += 1
    add(f'| {part} | {len(rep)} | {cells["none"]} | {cells["all"]} | {cells["differs"]} | {cells["notbuilt"]} | {cells["outside"]} |')
add('')

# In-degree
add('## Highest in-degree')
add('')
top = sorted(pkgs, key=lambda n: (-len(inn[n['id']]), n['id']))[:10]
for n in top:
    add(f'- {n["id"]}: {len(inn[n["id"]])} dependents; 2a {n["s2a"]}; 2b {n["s2b"]}')
hz = 'Humanizer.Core/2.14.1'
add(f'- {sum(1 for i in inn[hz] if N[i]["name"].startswith("Humanizer.Core."))} of the {len(inn[hz])} dependents of {hz} are its culture packages')
me = {p: len({e['target'] for e in g['edges'] if p in e['programs'] and N[e['target']]['name'].startswith('Microsoft.Extensions.')}) for p in PROGRAMS}
add('- Microsoft.Extensions package versions in each program\'s edges: ' + ', '.join(f'{p} {c}' for p, c in me.items()))
add('')

# Reached through one direct dependency only
add('## Reached through one direct dependency only')
add('')
roots = [i for i, n in N.items() if n['kind'] != 'package']
everything = set().union(*(reach(r, out_all) for r in roots))
best = None
for n in r1:
    seen, stack = set(), list(roots)
    while stack:
        for b in out_all[stack.pop()]:
            if b != n['id'] and b not in seen:
                seen.add(b)
                stack.append(b)
    only = [N[i] for i in everything - seen - {n['id']} if N[i]['kind'] == 'package']
    if not best or len(only) > len(best[1]):
        best = (n, only)
n, only = best
sat = [x for x in only if x['name'].startswith('Humanizer.Core.')]
files = [x for x in only if x not in sat and x['cls'] != 'N0']
add(f'- {n["id"]}: {len(only)} package versions reached only through it; {len(sat)} Humanizer culture packages, '
    f'{len(only) - len(sat) - len(files)} with no files (N0), {len(files)} that ship assemblies, '
    f'{sum(1 for x in files if x["s2b"] == "not in 2b")} of these not attempted in 2b')
add('')

open(OUT, 'w').write('\n'.join(lines))
print('\n'.join(lines))
