"""Derive, build and compare the release recipe for each package; write a log and result table.

Usage: python3 -I run-batch.py POPULATION_TSV LAB

POPULATION_TSV has one row per package and version (columns package,
version, file: the DLL that ships in Phoenix). LAB is a folder outside any
repository. Every package is keyed by name and version together (folders
<Package>-<version>), so two versions of one package stay apart. The steps:

 0. the .NET 10 SDK that runs dllreport.cs, alone in LAB/report-sdk
    (../tools/install-sdk.py, when the folder has none);
 1. derive every package (derive.py) into LAB/derive/<key>/; a package with
    a facts.txt from an earlier run is kept, a failed derivation is redone;
 2. choose where each recipe builds: a Windows recipe on a windows-2022
    machine, a Linux recipe here, or on GitHub's ubuntu-24.04 runner when the
    build folder the PDB records (/home/runner/work/...) cannot be made here;
 3. build the local ones here, one after the other (rebuild.py), into
    LAB/build/<key>/; the others are listed in LAB/runner.txt with their
    recipe, to be built by rebuild.py on that machine (nupkg-rebuild.yml
    is how the stored run did it), and their out/ folder put under
    LAB/runner/<key>/;
 4. for every build whose output is there: the match against nuget.org
    (level.py on dllreport.cs reports of nuget.org's DLL and ours), the report
    lines that differ, and A against A2;
 5. write LAB/results.tsv, and LAB/compare.txt with each package
    comparison under a line "=== <key> (<its file in LAB>)"; then the same
    rows and comparisons into results/release-build.tsv and
    results/compare.txt beside the README, where they replace those of the
    same packages and leave the others (source column: run-batch.py and
    the date).

Reruns in the same LAB reuse derivations and existing build outputs.
Once runner outputs arrive, a rerun classifies them too.

results.tsv keeps the questions apart: publisher_match (the level.py
level against nuget.org: 1 identical, 2 identical without signatures, 3 same
code, 4 other code), a_eq_a2 (our own repeat) and variation (always "not
tested"; part 2a's question). The other columns: package, version, category
(derived, derived with defaults, or skipped with the rule), os, runner, sdk,
sdk_alternatives (the SDKs rule 3 did not read because a lower one matched:
an uncertainty, not a match), environment (the runner image or this
machine's kernel, from the build log), build, differs (the report lines that
differ, from level.py), note.

Combines run-batch.py and derive-batch.py (Speciale2026 at f127442). Omits
recipe commits and pushes, GitHub dispatch and polling, git mirrors, the
disk guard and copying into the data folder.
"""
import datetime, os, re, shutil, subprocess, sys, tomllib, zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, '..', '..', 'tools')
RESULTS = os.path.join(HERE, '..', 'results')
REPORT_SDK = '10.0.403'      # the .NET 10 SDK for the file-based dllreport.cs
REPORT_DOTNET = 'dotnet'     # set by report_sdk() to LAB/report-sdk/dotnet
COLUMNS = ['package', 'version', 'category', 'os', 'runner', 'sdk', 'sdk_alternatives', 'environment',
           'build', 'publisher_match', 'a_eq_a2', 'variation', 'differs', 'note']


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


def key(pkg, ver):
    return f'{pkg}-{ver}'


class Log:
    def __init__(self, path):
        self.f = open(path, 'a', encoding='utf-8')

    def __call__(self, msg):
        line = f'{now()} {msg}'
        print(line, flush=True)
        self.f.write(line + '\n'); self.f.flush()


def sh(args, log, cwd=None, timeout=None):
    log('$ ' + ' '.join(args))
    r = subprocess.run(args, capture_output=True, text=True, cwd=cwd, timeout=timeout)
    if r.returncode:
        log(f'  exit {r.returncode}: {(r.stderr or r.stdout).strip()[-600:]}')
    return r


def report_sdk(lab, log):
    """Install LAB/report-sdk if dotnet is missing; expose it to derive.py and derive-repo.py via DLLREPORT_DOTNET."""
    global REPORT_DOTNET
    sdk = os.path.join(lab, 'report-sdk')
    if not os.path.exists(os.path.join(sdk, 'dotnet')):
        shutil.rmtree(sdk, ignore_errors=True)
        if sh([sys.executable, '-I', os.path.join(TOOLS, 'install-sdk.py'), REPORT_SDK, sdk], log, timeout=1800).returncode:
            sys.exit(f'could not install SDK {REPORT_SDK} into {sdk}')
    REPORT_DOTNET = os.environ['DLLREPORT_DOTNET'] = os.path.join(sdk, 'dotnet')


def merge_results(results, sections, log):
    """Merge lab rows and comparisons into results/. Replace matching packages and keep the others."""
    tsv, listing = os.path.join(RESULTS, 'release-build.tsv'), os.path.join(RESULTS, 'compare.txt')
    rows = {}
    if os.path.exists(tsv):
        for line in open(tsv, encoding='utf-8').read().splitlines()[1:]:
            rows[key(*line.split('\t')[:2])] = line
    source = f'run-batch.py {datetime.date.today().isoformat()}'
    for k, r in results.items():
        rows[k] = '\t'.join(str(r[c]) for c in COLUMNS) + '\t' + source
    with open(tsv, 'w', encoding='utf-8') as f:
        f.write('\t'.join(COLUMNS + ['source']) + '\n' + ''.join(line + '\n' for line in rows.values()))
    kept, cur = {}, None
    if os.path.exists(listing):
        for line in open(listing, encoding='utf-8').read().splitlines(keepends=True):
            m = re.match(r'=== (\S+) \(', line)
            if m:
                cur = m.group(1); kept[cur] = ''
            if cur:
                kept[cur] += line
    for k in results:
        if k in sections:
            kept[k] = sections[k]
        else:
            kept.pop(k, None)
    open(listing, 'w', encoding='utf-8').write(''.join(kept.values()))
    log(f'results/: {len(results)} of {len(rows)} rows replaced in {tsv}, {len(sections)} comparisons in {listing}')


def report(dll, out, log):
    r = subprocess.run([REPORT_DOTNET, 'run', os.path.join(TOOLS, 'dllreport.cs'), '--', dll], capture_output=True, text=True)
    open(out, 'w', encoding='utf-8').write(r.stdout + r.stderr)
    if r.returncode:
        log(f'  dllreport failed on {dll}: exit {r.returncode}')
    return r.returncode == 0


def can_make(path):
    """Check whether PATH can be created: its nearest existing ancestor must be writable."""
    if not path or not path.startswith('/'):
        return True
    p = path
    while not os.path.exists(p):
        p = os.path.dirname(p)
    return os.access(p, os.W_OK)


def level_of(outdir, recipe, log):
    """Grade A's shipped DLL against nuget.org's from their reports; return differing lines too.
    Return '' when a package is missing."""
    ships = recipe['ships']
    lid, lver = recipe['package'].lower(), recipe['version'].lower()
    ref = os.path.join(outdir, 'nuget-org', f'{lid}.{lver}.nupkg')
    packed = sorted(f for f in os.listdir(os.path.join(outdir, 'A')) if f.lower().endswith('.nupkg')) if os.path.isdir(os.path.join(outdir, 'A')) else []
    a = next((os.path.join(outdir, 'A', f) for f in packed if f.lower() == f'{lid}.{lver}.nupkg'), None)
    other = ''
    if not a and len(packed) == 1:   # Also compare the DLL when a version tool gives the package another version.
        a = os.path.join(outdir, 'A', packed[0]); other = f'packed as {packed[0]}, not {lid}.{lver}.nupkg; '
    if not (a and os.path.exists(ref)):
        return '', '', 'no package to compare' + (f' (packed: {", ".join(packed)})' if packed else '')
    lv = os.path.join(outdir, 'level'); os.makedirs(lv, exist_ok=True)
    for src, name in ((ref, 'nugetorg'), (a, 'A')):
        try:
            data = zipfile.ZipFile(src).read(ships)
        except KeyError:
            return '', '', f'{ships} not in {os.path.basename(src)}'
        open(os.path.join(lv, f'{name}.dll'), 'wb').write(data)
        if not report(os.path.join(lv, f'{name}.dll'), os.path.join(lv, f'report-{name}.txt'), log):
            return '', '', 'report failed'
    r = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'level.py'), os.path.join(lv, 'report-nugetorg.txt'), os.path.join(lv, 'report-A.txt')],
                       capture_output=True, text=True)
    m = re.match(r'level (\d); differing lines: (.*)', r.stdout.strip())
    if not m:
        return '', '', other + r.stdout.strip()
    return m.group(1), m.group(2), other.rstrip('; ')


def sdk_alternatives(facts_path):
    """Read the SDKs left unexamined by rule 3 from the derivation's facts."""
    for line in open(facts_path, encoding='utf-8'):
        if line.startswith('sdk:'):
            m = re.search(r'not read: ([^)]*)\)', line)
            return '' if not m or m.group(1) == 'none' else m.group(1)
    return ''


def environment(outdir):
    """Read the runner image or kernel logged by rebuild.py for build A."""
    p = os.path.join(outdir, 'A', 'build.log')
    if not os.path.exists(p):
        return ''
    found = []
    for line in open(p, encoding='utf-8', errors='replace'):
        if line.startswith('runner ImageOS=') or line.startswith('runner ImageVersion=') or line.startswith('kernel '):
            found.append(line.strip().replace('runner ', ''))
        if line.startswith('--- build'):
            break
    return ', '.join(found)


def derive(pkg, ver, population, lab, dest):
    """Run derive.py for one package; read its category, OS and SDK from facts.txt and recipe.toml."""
    if not os.path.exists(os.path.join(dest, 'facts.txt')):
        shutil.rmtree(dest, ignore_errors=True)
        r = subprocess.run([sys.executable, '-I', os.path.join(HERE, 'derive.py'), pkg, ver, population, lab, dest],
                           capture_output=True, text=True)
        if not os.path.exists(os.path.join(dest, 'facts.txt')):
            err = (r.stderr.strip().splitlines() or [f'exit {r.returncode}'])[-1]
            os.makedirs(dest, exist_ok=True)
            open(os.path.join(dest, 'error.txt'), 'w', encoding='utf-8').write(r.stdout + r.stderr)
            return f'skipped (derive.py failed: {err[:160]})', '', ''
    cat = [l for l in open(os.path.join(dest, 'facts.txt'), encoding='utf-8') if l.startswith('category:')][-1].strip()[len('category: '):]
    rec = os.path.join(dest, 'recipe.toml')
    if os.path.exists(rec):
        t = tomllib.load(open(rec, 'rb'))
        return cat, t['os'], t['sdk']
    return cat, '', ''


def main():
    population, lab = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
    os.makedirs(lab, exist_ok=True)
    log = Log(os.path.join(lab, 'run.log'))
    pairs = [l.rstrip('\n').split('\t')[:2] for l in open(population, encoding='utf-8')][1:]
    log(f'release build: {len(pairs)} packages from {population}, lab {lab}')
    report_sdk(lab, log)

    # 1. derive
    results = {}
    for pkg, ver in pairs:
        k = key(pkg, ver)
        cat, os_, sdk = derive(pkg, ver, population, lab, os.path.join(lab, 'derive', k))
        log(f'{k}: {cat}')
        results[k] = dict(package=pkg, version=ver, category=cat, os=os_, runner='', sdk=sdk, sdk_alternatives='', environment='',
                          build='', publisher_match='', a_eq_a2='', variation='not tested', differs='', note='')
        facts = os.path.join(lab, 'derive', k, 'facts.txt')
        if os.path.exists(facts):
            results[k]['sdk_alternatives'] = sdk_alternatives(facts)
    derived = {k: r for k, r in results.items() if r['category'].startswith('derived')}
    log(f'derived {len(derived)} of {len(results)}; skipped: ' + ', '.join(k for k in results if k not in derived))

    # 2. where each recipe builds
    for k, r in derived.items():
        recipe = tomllib.load(open(os.path.join(lab, 'derive', k, 'recipe.toml'), 'rb'))
        r['runner'] = 'windows-2022' if r['os'] == 'windows' else ('local' if can_make(recipe.get('clone_dir')) else 'ubuntu-24.04')
    with open(os.path.join(lab, 'runner.txt'), 'w', encoding='utf-8') as f:
        f.write('# build each with: python -I rebuild.py RECIPE WORKDIR on the runner named, then put WORKDIR/out under LAB/runner/<key>/\n')
        for k, r in derived.items():
            if r['runner'] != 'local':
                f.write(f'{k}\t{r["runner"]}\t{os.path.join(lab, "derive", k, "recipe.toml")}\n')

    # 3. the local builds
    for k, r in derived.items():
        if r['runner'] != 'local':
            continue
        work = os.path.join(lab, 'build', k)
        if os.path.exists(os.path.join(work, 'out', 'summary.txt')):
            r['build'] = 'ran (earlier run, output reused)'
            log(f'{k}: reusing the build output in {work}')
            continue
        shutil.rmtree(work, ignore_errors=True)
        recipe_path = os.path.join(lab, 'derive', k, 'recipe.toml')
        res = sh([sys.executable, '-I', os.path.join(HERE, 'rebuild.py'), recipe_path, work], log, timeout=7200)
        r['build'] = 'ran' if res.returncode == 0 else f'rebuild.py exit {res.returncode}'
        log(f'{k}: ' + res.stdout.strip().replace('\n', ' | ')[-400:])
        for d in ('A', 'sdk'):   # After saving the output, remove the clone, cache and SDK; keep out/.
            shutil.rmtree(os.path.join(work, d), ignore_errors=True)
        recipe = tomllib.load(open(recipe_path, 'rb'))
        if recipe.get('clone_dir'):
            shutil.rmtree(recipe['clone_dir'], ignore_errors=True)

    # 4. levels, differing lines and A = A2; 5. the table
    listing = open(os.path.join(lab, 'compare.txt'), 'w', encoding='utf-8')
    sections = {}
    for k, r in derived.items():
        recipe = tomllib.load(open(os.path.join(lab, 'derive', k, 'recipe.toml'), 'rb'))
        if r['runner'] == 'local':
            outdir = os.path.join(lab, 'build', k, 'out')
        else:
            found = os.path.join(lab, 'runner', k)
            outdir = next((root for root, _, fs in os.walk(found) if 'summary.txt' in fs), None) if os.path.isdir(found) else None
            r['build'] = 'ran' if outdir else 'awaiting runner'
        if not outdir or not os.path.isdir(outdir):
            r['note'] = r['note'] or ('no output folder' if r['build'] != 'awaiting runner' else '')
            continue
        summary = open(os.path.join(outdir, 'summary.txt'), encoding='utf-8').read() if os.path.exists(os.path.join(outdir, 'summary.txt')) else ''
        m = re.search(r'builds A exit (\d+), A2 exit (\d+)', summary)
        if m and m.group(1) != '0':
            r['build'] = f'did not build (exit {m.group(1)})'
        a2 = re.search(r'\.dll A vs A2: (\w+)', summary)
        r['a_eq_a2'] = {'identical': 'yes', 'differs': 'no'}.get(a2.group(1), '') if a2 else 'not compared'
        r['environment'] = environment(outdir)
        r['publisher_match'], r['differs'], note = level_of(outdir, recipe, log)
        r['note'] = note
        if r['publisher_match'] and os.path.exists(os.path.join(outdir, 'compare-nupkg.txt')):
            listed = os.path.join(outdir, 'compare-nupkg.txt')
            sections[k] = f'=== {k} ({os.path.relpath(listed, lab)})\n' + open(listed, encoding='utf-8').read()
            listing.write(sections[k])
        log(f'{k}: build {r["build"]}, level {r["publisher_match"] or "-"}, A=A2 {r["a_eq_a2"] or "-"}; {note}')
    listing.close()
    with open(os.path.join(lab, 'results.tsv'), 'w', encoding='utf-8') as f:
        f.write('\t'.join(COLUMNS) + '\n')
        for r in results.values():
            f.write('\t'.join(str(r[c]) for c in COLUMNS) + '\n')
    log(f'done: {os.path.join(lab, "results.tsv")}')
    merge_results(results, sections, log)


if __name__ == '__main__':
    main()
