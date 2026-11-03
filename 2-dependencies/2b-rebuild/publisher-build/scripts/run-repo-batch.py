"""Run the publisher's build for Arcade packages and record a log and result table.

Usage: python3 -I run-repo-batch.py LAB

LAB is the release build's lab (2b-rebuild/scripts/run-batch.py): the publisher's build reads the release
derivations in LAB/derive/ for each package's commit, project and file version. The steps:

 1. derive the recipes (derive-repo.py) from ../packages.txt into LAB/repo-recipes/<name>/;
 2. build the recipes for dotnet/dotnet's inner repositories here, one at a time
    (repo-build.py, in its own process group, killed after four hours), into
    LAB/repo-build/<name>/; a runtime recipe needs clang, cmake and ninja;
 3. list the others in LAB/repo-runner.txt: they build on windows-2022, the publisher's
    host (python -I repo-build.py RECIPE WORKDIR there, with the recipe's Node line first
    on PATH when it names one; nupkg-repository-build.yml is how the stored run did it),
    and their out/ folder goes under LAB/repo-runner/<name>/;
 4. classify every product whose output is there (run-batch.py's level_of, the same
    level.py as the release build) and write LAB/publisher-build.tsv in the shape of
    results/publisher-build.tsv.

A second run reuses the recipes and every build whose output exists.

Combines run-repo-batch.py and collect-runner.py (Speciale2026 at f127442). Omits
order files, the disk guard, data commits and pushes, GitHub artifact downloads and log excerpts.
"""
import importlib.util, os, shutil, signal, subprocess, sys, threading, tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('rb', os.path.join(HERE, '..', '..', 'scripts', 'run-batch.py'))
rb = importlib.util.module_from_spec(spec); spec.loader.exec_module(rb)
TIMEOUT = 4 * 3600
COLUMNS = ['host', 'recipe', 'repository', 'commit', 'inner', 'build_id', 'package', 'version', 'ships', 'publisher_match',
           'differs', 'a_eq_a2', 'variation', 'build', 'environment', 'note', 'match_without_roslyn_rule']


def run_build(args, log, timeout):
    """Run repo-build.py in its own process group. On timeout, kill the group, including MSBuild nodes."""
    log('$ ' + ' '.join(args))
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, start_new_session=True)
    timer = threading.Timer(timeout, lambda: os.killpg(p.pid, signal.SIGKILL))
    timer.start()
    out = p.communicate()[0]
    timer.cancel()
    return p.returncode, out


def main():
    lab = os.path.abspath(sys.argv[1])
    log = rb.Log(os.path.join(lab, 'run.log'))
    rb.report_sdk(lab, log)   # the release build's LAB/report-sdk, for derive-repo.py and level_of
    recipes = os.path.join(lab, 'repo-recipes')

    # 1. recipes
    if not os.path.isdir(recipes):
        rb.sh([sys.executable, '-I', os.path.join(HERE, 'derive-repo.py'), os.path.join(HERE, '..', 'packages.txt'),
               os.path.join(HERE, '..', '..', 'population.tsv'), os.path.join(lab, 'derive'), lab, recipes], log, timeout=14400)
    names = sorted(n for n in os.listdir(recipes) if os.path.exists(os.path.join(recipes, n, 'recipe.toml')))
    log(f"publisher's build: {len(names)} recipes; not covered: {open(os.path.join(recipes, 'not-covered.txt'), encoding='utf-8').read().strip() or 'none'}")

    # 2. the dotnet/dotnet recipes here; 3. the others on windows-2022
    with open(os.path.join(lab, 'repo-runner.txt'), 'w', encoding='utf-8') as f:
        f.write('# build each with: python -I repo-build.py RECIPE WORKDIR on windows-2022, then put WORKDIR/out under LAB/repo-runner/<name>/\n')
        for name in names:
            r = tomllib.load(open(os.path.join(recipes, name, 'recipe.toml'), 'rb'))
            if not r.get('inner'):
                f.write(f'{name}\twindows-2022\t{os.path.join(recipes, name, "recipe.toml")}\tnode {r.get("node", "-")}\n')
    for name in names:
        rpath = os.path.join(recipes, name, 'recipe.toml')
        r = tomllib.load(open(rpath, 'rb'))
        work = os.path.join(lab, 'repo-build', name)
        if not r.get('inner') or os.path.exists(os.path.join(work, 'out', 'summary.txt')):
            continue
        missing = [t for t in ('cmake', 'ninja', 'clang') if not shutil.which(t, path='/usr/bin')] if r['kind'] == 'runtime' else []
        if missing:
            log(f'{name}: not run, missing {", ".join(missing)}'); continue
        shutil.rmtree(work, ignore_errors=True)
        code, stdout = run_build([sys.executable, '-I', os.path.join(HERE, 'repo-build.py'), rpath, work], log, TIMEOUT)
        log(f'{name}: exit {code}; ' + (stdout or '').strip().replace('\n', ' | ')[-600:])
        for d in ('A',):   # Remove the clone, the repository's .dotnet and artifacts; keep out/.
            shutil.rmtree(os.path.join(work, d), ignore_errors=True)

    # 4. classify
    rows = []
    for name in names:
        r = tomllib.load(open(os.path.join(recipes, name, 'recipe.toml'), 'rb'))
        host = 'linux' if r.get('inner') else 'windows-2022'
        out = os.path.join(lab, 'repo-build', name, 'out') if r.get('inner') else os.path.join(lab, 'repo-runner', name)
        base = {'host': host, 'recipe': name, 'repository': r['repo'], 'commit': r['commit'], 'inner': r.get('inner', ''),
                'build_id': r['official_build_id'], 'a_eq_a2': 'not tested', 'variation': 'not tested'}
        first = open(os.path.join(out, 'summary.txt'), encoding='utf-8').readline() if os.path.exists(os.path.join(out, 'summary.txt')) else ''
        exit_code = first.split('build exit ')[1].split(',')[0] if 'build exit ' in first else ''
        build = 'ran' if exit_code == '0' else (f'did not build (exit {exit_code})' if exit_code else 'not built yet')
        env = rb.environment(os.path.join(out, next((p['package'] + '-' + p['version'] for p in r['products']), ''))) if os.path.isdir(out) else ''
        for p in r['products']:
            pd = os.path.join(out, f'{p["package"]}-{p["version"]}')
            row = {**base, 'package': p['package'], 'version': p['version'], 'ships': p['ships'], 'build': build, 'environment': env}
            if os.path.isdir(pd):
                row['publisher_match'], row['differs'], row['note'] = rb.level_of(pd, p, log)
            else:
                row['note'] = 'no output folder'
            row['match_without_roslyn_rule'] = row.get('publisher_match', '')
            rows.append(row)
            log(f'  {p["package"]} {p["version"]} on {host}: level {row.get("publisher_match") or "-"}; {row.get("note", "")}')
    with open(os.path.join(lab, 'publisher-build.tsv'), 'w', encoding='utf-8') as f:
        f.write('\t'.join(COLUMNS) + '\n')
        for row in rows:
            f.write('\t'.join(str(row.get(c, '')).replace('\t', ' ').replace('\n', ' ') for c in COLUMNS) + '\n')
    log(f'done: {len(rows)} rows in {os.path.join(lab, "publisher-build.tsv")}')


if __name__ == '__main__':
    main()
