"""The dependency graph of the 341 shipped packages, in two commands.

    python3 -I scripts/graph.py edges LOCKS_DIR results/edges.tsv
    python3 -I scripts/graph.py join results/edges.tsv EXPERIMENT_2_DIR results/graph.json

edges (step 1, needs Phoenix): reads the three programs' packages.lock.json from LOCKS_DIR (WebAPI.json,
BackgroundJobExecutor.json, DbMigrator.json, from Phoenix 79cb67a7) and writes one row per edge: source,
target and the programs whose lock file gives it. The sections net10.0 and net10.0/linux-x64 are read
together; a dependency resolves to the version locked in the same program; names are matched without regard
to case (FluentValidation names 'Microsoft.Extensions.Dependencyinjection.Abstractions'). A node is a package
version (name/version) or one of the five projects. The three runtime and host packs are joined to every
program, because the population does not record which program needs which pack.

join (step 2): reads edges.tsv and, under EXPERIMENT_2_DIR, population/results/packages.tsv and the two
categories.tsv, and writes graph.json: every package of the population with its facts and its 2a and 2b
category, and the edges. dotnet-ef has no edge: it is a tool whose SQL script ships.
"""
import collections, csv, json, os, sys

PROGRAMS = ['WebAPI', 'BackgroundJobExecutor', 'DbMigrator']
PROJECTS = {'applicationcore': 'ApplicationCore', 'infrastructure': 'Infrastructure'}
PACKS = ['Microsoft.AspNetCore.App.Runtime.linux-x64/10.0.12', 'Microsoft.NETCore.App.Host.linux-x64/10.0.12',
         'Microsoft.NETCore.App.Runtime.linux-x64/10.0.12']
TOOLS = ['dotnet-ef/10.0.12']


def edges(locks, out):
    found = collections.defaultdict(set)
    for prog in PROGRAMS:
        with open(os.path.join(locks, prog + '.json')) as f:
            lock = json.load(f)['dependencies']
        sec = {k: dict(v) for k, v in lock['net10.0'].items()}
        for k, v in lock['net10.0/linux-x64'].items():
            if k in sec:
                assert sec[k].get('resolved') == v.get('resolved'), k
                sec[k]['dependencies'] = {**sec[k].get('dependencies', {}), **v.get('dependencies', {})}
            else:
                sec[k] = v
        lower = {k.lower(): k for k in sec}

        def node(name):
            k = lower[name.lower()]
            return PROJECTS[k] if sec[k]['type'] == 'Project' else f"{k}/{sec[k]['resolved']}"

        for name, v in sec.items():
            if v['type'] == 'Direct':
                found[(prog, node(name))].add(prog)
            for dep in v.get('dependencies', {}):
                if dep.lower() in lower:
                    found[(node(name), node(dep))].add(prog)
        # The ProjectReferences: WebAPI and BackgroundJobExecutor name both libraries, DbMigrator only Infrastructure
        for p in (['Infrastructure'] if prog == 'DbMigrator' else ['ApplicationCore', 'Infrastructure']):
            found[(prog, p)].add(prog)
        for pack in PACKS:
            found[(prog, pack)].add(prog)
    with open(out, 'w', newline='') as f:
        w = csv.writer(f, delimiter='\t', lineterminator='\n')
        w.writerow(['source', 'target', 'programs'])
        for (a, b), ps in sorted(found.items()):
            w.writerow([a, b, ','.join(p for p in PROGRAMS if p in ps)])
    print(len(found), 'edges')


def tsv(*parts):
    with open(os.path.join(*parts), newline='') as f:
        return list(csv.DictReader(f, delimiter='\t'))


def join(edges_tsv, exp, out):
    key = lambda r: f"{r['package']}/{r['version']}"
    facts = {key(r): r for r in tsv(exp, 'population', 'results', 'packages.tsv')}
    cat2a = {key(r): r for r in tsv(exp, '2a-determinism', 'results', 'categories.tsv')}
    cat2b = {key(r): r for r in tsv(exp, '2b-rebuild', 'results', 'categories.tsv')}
    edge_rows = tsv(edges_tsv)

    nodes = {p: {'id': p, 'name': p, 'kind': 'program'} for p in PROGRAMS}
    nodes.update({p: {'id': p, 'name': p, 'kind': 'project'} for p in PROJECTS.values()})
    for i, r in facts.items():
        n = {'id': i, 'name': r['package'], 'version': r['version'], 'kind': 'package', 'owner': r['owner'],
             'cls': r['class'], 'direct': r['direct'] == 'yes', 'repo': r['repository'], 'commit': r['commit']}
        if i in PACKS:
            n['via'] = 'sdk'
        if i in TOOLS:
            n['via'] = 'tool'
        # 2a: the assembly level (as is, with configuration, unreproducible), else why the package stopped
        c = cat2a.get(i)
        n['s2a'] = ('not in 2a' if not c else c['cat_assemblies'] if c['screen'] == 'built' else 'did not build')
        # 2b: the category column, the release build and the publisher's build together
        n['s2b'] = cat2b[i]['category'] if i in cat2b else 'not in 2b'
        nodes[i] = n
    unknown = {x for e in edge_rows for x in (e['source'], e['target'])} - set(nodes)
    assert not unknown, f'edges to nodes outside the population: {sorted(unknown)[:5]}'
    assert len(facts) == 341, len(facts)

    graph = {'nodes': list(nodes.values()),
             'edges': [{'source': e['source'], 'target': e['target'], 'programs': e['programs'].split(',')} for e in edge_rows]}
    with open(out, 'w') as f:
        json.dump(graph, f, indent=1)
    print(len(nodes), 'nodes', len(edge_rows), 'edges')
    print('2a', dict(collections.Counter(n['s2a'] for n in nodes.values() if n['kind'] == 'package')))
    print('2b', dict(collections.Counter(n['s2b'] for n in nodes.values() if n['kind'] == 'package')))


if __name__ == '__main__':
    cmd, *rest = sys.argv[1:]
    {'edges': edges, 'join': join}[cmd](*rest)
