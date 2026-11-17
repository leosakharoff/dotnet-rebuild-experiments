"""Summarise stored release-build and publisher-build results, separately and per package.

    python3 -I summary.py [RESULTS] [PUBLISHER_RESULTS] [POPULATION_TSV]

RESULTS (default ../results/) holds:
  release-build.tsv    run-batch.py's results.tsv, one row per package
  compare.txt          compare.py's listing of nuget.org's package against ours, one section
                       "=== <Package>-<version>" per compared package
PUBLISHER_RESULTS (default ../publisher-build/results/) holds:
  publisher-build.tsv  the publisher's build, one row per package: host (windows-2022 or linux),
                       publisher_match, and match_without_roslyn_rule (the level with the
                       release-branding properties for Roslyn too)
POPULATION_TSV (default ../population.tsv) gives the owner.

Writes RESULTS/summary.md and RESULTS/categories.tsv (one row per package).

Matches, of the DLL that ships in WS.PEMS against nuget.org's (level.py):
  identical                     the same bytes
  identical without signatures  equal once the Authenticode block, the strong-name signature
                                and the PE checksum are removed
  same code                     IL, metadata streams and resources equal; the build identity
                                (MVID, PE timestamp, PDB id and checksum) differs
  other code                    anything else
Groups: reproduced (the first two), built but differs (the last two), no package to compare (no package,
or no recipe).

Per package category, from the release build alone:
  from the release            the release build reproduces it
  built, but differs          built and compared, same code or other code
  no package                  the release build produced no package to compare
  no recipe                   the derivation stopped at a rule
The publisher's build does not change a category. It is a diagnostic, run only for Arcade
repositories; section 3 counts, per category, the packages it reproduces.
"""
import collections, csv, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
MATCH = {'1': 'identical', '2': 'identical without signatures', '3': 'same code', '4': 'other code'}
PACKAGING = ('.psmdcp', '_rels/.rels', '[Content_Types].xml', '.signature.p7s')
GROUPS = [('reproduced', ['identical', 'identical without signatures']),
          ('built, but differs', ['same code', 'other code']),
          ('no package to compare', ['no package', 'no recipe'])]
CATEGORIES = ['from the release', 'built, but differs', 'no package', 'no recipe']
REPRODUCED = ('identical', 'identical without signatures')


def rows(path):
    return list(csv.DictReader(open(path, encoding='utf-8'), delimiter='\t'))


def outcome(x):
    """Return the match, or the reason it is missing."""
    if x['publisher_match']:
        return MATCH[x['publisher_match']]
    if x.get('category', '').startswith('skipped'):
        return 'no recipe'
    return 'no package'


def skip_cause(category):
    for pattern, cause in (('ran on .NET Framework', 'the compiler ran on .NET Framework, which no dotnet SDK bundles'),
                           ('no public SDK', 'the compiler is in no public SDK'),
                           ('not reachable', 'the commit is not reachable at the repository'),
                           ('project:', 'no single project with the assembly name'),
                           ('pdb:', 'no PDB with a compiler record'),
                           ('derive.py failed', 'the derivation failed')):
        if pattern in category:
            return cause
    return category[:80]


def nopackage_cause(x):
    if x['build'].startswith('did not build'):
        return 'the build failed'
    if x['note'] == 'no output folder':
        return 'the runner job left no output'
    return 'the build ran, but packed no package of that name and version'


def listings(path):
    """Split compare.txt into sections keyed by <Package>-<version>."""
    found, name = {}, None
    for line in open(path, encoding='utf-8'):
        if line.startswith('=== '):
            name = line[4:].split(' (')[0]; found[name] = []
        elif name:
            found[name].append(line)
    return found


def scope(lines):
    """Apply 2a's levels to a compare.py listing: package file, package entries, assemblies.
    Column 0 is nuget.org; column 1 is ours."""
    whole = content = dlls = True
    signed = False
    for line in lines:
        m = re.match(r'^(same|DIFFERS|only in some)\s+(.+?)( \((packaging|SHIPS)\))?: (.+)$', line.rstrip())
        if not m:
            continue
        name, hashes = m.group(2), m.group(5).split()
        same = hashes[0] == hashes[1]
        signed |= name == '.signature.p7s' and hashes[0] != '-'
        whole &= same
        if name.endswith(PACKAGING):
            continue
        content &= same
        if re.match(r'^(lib|ref|runtimes)/', name) and name.endswith(('.dll', '.exe')):
            dlls &= same
    return whole, content, dlls, signed


def group_table(title, counts, total):
    lines = [f'### {title}', '', '| group | match or outcome | packages |', '|---|---|---|']
    for group, members in GROUPS:
        n = sum(counts.get(m, 0) for m in members)
        if not n:
            continue
        first = True
        for m in members:
            if counts.get(m):
                lines.append(f'| {f"{group} ({n})" if first else ""} | {m} | {counts[m]} |')
                first = False
    lines += [f'| | total | {total} |', '']
    return lines


def main():
    results = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, '..', 'results')
    publisher_results = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(HERE, '..', 'publisher-build', 'results')
    population = os.path.abspath(sys.argv[3]) if len(sys.argv) > 3 else os.path.join(HERE, '..', 'population.tsv')
    owner = {(r['package'], r['version']): r['owner'] for r in csv.DictReader(open(population, encoding='utf-8'), delimiter='\t')}

    release = {(x['package'], x['version']): x for x in rows(os.path.join(results, 'release-build.tsv'))}
    publisher, without_rule = {}, {}
    for x in rows(os.path.join(publisher_results, 'publisher-build.tsv')):
        k, host = (x['package'], x['version']), 'windows' if x['host'] == 'windows-2022' else 'linux'
        publisher[k] = (host, x)
        without_rule[k] = (host, {**x, 'publisher_match': x['match_without_roslyn_rule']})

    lines = [f'# Rebuild against nuget.org, summary ({len(release)} packages)', '']

    # 1. the release build
    lines += ['## 1. The release build', '']
    out = {k: outcome(x) for k, x in release.items()}
    lines += group_table(f'All {len(release)}', collections.Counter(out.values()), len(release))
    for who in ('third-party', 'Microsoft'):
        ks = [k for k in release if owner.get(k) == who]
        lines += group_table(f'{who.capitalize() if who == "third-party" else who} ({len(ks)})', collections.Counter(out[k] for k in ks), len(ks))

    lines += ['### No package to compare, by cause', '', '| outcome | cause | packages |', '|---|---|---|']
    causes = collections.Counter(('no recipe', skip_cause(x['category'])) for k, x in release.items() if out[k] == 'no recipe')
    causes.update(('no package', nopackage_cause(x)) for k, x in release.items() if out[k] == 'no package')
    for (o, cause), n in sorted(causes.items(), key=lambda kv: (kv[0][0], -kv[1])):
        lines.append(f'| {o} | {cause} | {n} |')
    lines.append('')

    compared = [k for k in release if release[k]['publisher_match']]
    levels = collections.Counter()
    listed = listings(os.path.join(results, 'compare.txt'))
    for k in compared:
        if f'{k[0]}-{k[1]}' in listed:
            whole, content, dlls, signed = scope(listed[f'{k[0]}-{k[1]}'])
            levels['listed'] += 1; levels['whole'] += whole; levels['content'] += content; levels['dlls'] += dlls; levels['signed'] += signed
    lines += ['### Against part 2a\'s levels', '',
              f'Of the {len(compared)} packages compared, {levels["listed"]} have a package listing. Level 1 (package file): '
              f'{levels["whole"]}; nuget.org\'s package carries its repository signature (`.signature.p7s`) in '
              f'{levels["signed"]} of them, which no rebuild can produce. Level 2 (package entries without NuGet\'s packaging files '
              f'and that signature): {levels["content"]}. Level 3 (assemblies: every DLL under lib/, ref/, runtimes/): {levels["dlls"]}. '
              f'The DLL that ships in Phoenix, identical: {sum(out[k] == "identical" for k in compared)}.', '']

    a2 = collections.Counter(release[k]['a_eq_a2'] for k in compared)
    lines += ['### A against A2 (our own repeat)', '',
              f'Of the {len(compared)} compared: equal {a2.get("yes", 0)}, differ {a2.get("no", 0)}, not compared {len(compared) - a2.get("yes", 0) - a2.get("no", 0)}. '
              'Differ: ' + (', '.join(f'{p} {v}' for p, v in compared if release[(p, v)]['a_eq_a2'] == 'no') or 'none') + '.', '']

    lines += ['### Per package, by match', '']
    for g in ('identical', 'identical without signatures', 'same code', 'other code'):
        ks = [k for k in release if out[k] == g]
        lines.append(f'- {g} ({len(ks)}): ' + ', '.join(f'{p} {v}' for p, v in ks))
    lines.append('')

    # 2. the publisher's build
    lines += ["## 2. The publisher's build (Arcade repositories)", '']
    pub = {k: outcome(x) for k, (_, x) in publisher.items()}
    lines += group_table(f'All {len(pub)}, Roslyn without the release-branding properties', collections.Counter(pub.values()), len(pub))
    for host in ('windows', 'linux'):
        ks = [k for k in publisher if publisher[k][0] == host]
        lines += group_table(f'On {"windows-2022" if host == "windows" else "Linux (the VMR builds)"} ({len(ks)})',
                             collections.Counter(pub[k] for k in ks), len(ks))
    plain = {k: outcome(x) for k, (_, x) in without_rule.items()}
    lines += group_table(f'All {len(plain)}, every repository with the release-branding properties (Roslyn too)',
                         collections.Counter(plain.values()), len(plain))
    missing = [k for k in publisher if k not in release]
    if missing:
        lines += ['Not in the release build: ' + ', '.join(f'{p} {v}' for p, v in missing), '']

    # 3. per package: the release build's category; the publisher's build only as a diagnostic beside it
    def category(k):
        if out[k] in REPRODUCED:
            return 'from the release'
        return 'built, but differs' if out[k] in ('same code', 'other code') else out[k]
    cats = {k: category(k) for k in release}
    ran = collections.Counter(cats[k] for k in pub)
    rep = collections.Counter(cats[k] for k in pub if pub[k] in REPRODUCED)
    rep_plain = collections.Counter(cats[k] for k in plain if plain[k] in REPRODUCED)
    lines += ['## 3. Per package', '',
              "The category comes from the release build alone. The publisher's build, run for the Arcade packages, is a diagnostic beside it.", '',
              "| category | packages | publisher's build ran | reproduces | without the Roslyn rule |", '|---|---|---|---|---|']
    c = collections.Counter(cats.values())
    for name in CATEGORIES:
        lines.append(f'| {name} | {c.get(name, 0)} | {ran.get(name, 0)} | {rep.get(name, 0)} | {rep_plain.get(name, 0)} |')
    lines += [f'| total | {len(release)} | {sum(ran.values())} | {sum(rep.values())} | {sum(rep_plain.values())} |', '',
              f'Built, but differs, by match: same code {sum(out[k] == "same code" for k in release)}, other code {sum(out[k] == "other code" for k in release)}.', '']

    os.makedirs(results, exist_ok=True)
    open(os.path.join(results, 'summary.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    columns = ['package', 'version', 'owner', 'release_build', 'a_eq_a2', 'publisher_build_host', 'publisher_build',
               'publisher_build_without_roslyn_rule', 'category']
    with open(os.path.join(results, 'categories.tsv'), 'w', encoding='utf-8') as f:
        f.write('\t'.join(columns) + '\n')
        for k, x in release.items():
            cells = [k[0], k[1], owner.get(k, ''), out[k], x['a_eq_a2'],
                     publisher[k][0] if k in publisher else '', pub.get(k, ''), plain.get(k, ''), cats[k]]
            f.write('\t'.join(cells) + '\n')
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
