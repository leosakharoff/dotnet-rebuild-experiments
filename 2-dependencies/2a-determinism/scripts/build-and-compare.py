"""Determinism of a NuGet package build in a fixed environment, measured as
Benedetti et al. (2025) measure it: reprotest varies one thing between two
builds of the same source, and the two packages are compared. Both sides of
every comparison are our own builds; nothing is compared with nuget.org.

    python3 -I build-and-compare.py try-build   TABLE PACKAGE LAB           clone, restore once (online), build and pack
    python3 -I build-and-compare.py build-twice TABLE PACKAGE LAB MODE AXIS reprotest: two builds, AXIS varied
    python3 -I build-and-compare.py batch       TABLE LAB                   every package, every axis, both modes
    python3 -I build-and-compare.py results     LAB OUT.tsv                 one row per (package, mode, axis)
    python3 -I build-and-compare.py environment LAB                          environment.txt: host, SDK, tools

TABLE is population.tsv, written by population.py: one row per package-version
with its repository, commit, the project file to build (relative to the
clone) and a status; only rows with status "ok" are built, the others are
recorded with their status (no repository, no commit, no project, ...).
PACKAGE names a row by package id, or "id@version" when the table has two
versions.

LAB is a folder outside any repository: LAB/sdk holds the one SDK (see
tools/install-sdk.py), LAB/nuget the one package cache, LAB/src/<id> the
clone being built, LAB/out/<id> everything measured, LAB/tools what a build
may need besides the SDK (pwsh, for the Azure SDK's build gate).

The default mode is the ecosystem's default command, not the publisher's (Benedetti's "as is"):

    dotnet build PROJECT -c Release --no-restore && dotnet pack PROJECT -c Release --no-build -o out

In the configured mode both commands also get the three properties the
.NET ecosystem offers for deterministic output: ContinuousIntegrationBuild
(source paths mapped to /_/), Deterministic, and DeterministicTimestamp set
to the commit's time (fixed ZIP entry times). UseSharedCompilation=false in
both modes keeps the compiler out of a server process, which the `time`
variation otherwise hangs on.

Each run compares reprotest's control build with its varied build at three
levels: 1 the .nupkg byte for byte; 2 every archive entry by bytes,
except NuGet's packaging files (nuget.psmdcp, _rels/.rels, [Content_Types].xml);
3 the assemblies (.dll, .exe) under lib/, ref/ and runtimes/. The verdict per
level is same, differs or failed (a build produced no package).

Linux only, as reprotest is. Needs reprotest, disorderfs and faketime.
"""
import csv
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

AXES = ['build_path', 'environment', 'locales', 'exec_path', 'time', 'timezone', 'umask', 'fileordering']
MODES = ['default', 'configured']
NUGET_METADATA = ('package/services/metadata/core-properties/', '_rels/.rels', '[Content_Types].xml')
REPROTEST = shutil.which('reprotest') or os.path.expanduser('~/.local/bin/reprotest')


# The population table and the lab

def load(table):
    """One dict per row of population.tsv, with an id used for the lab's folders."""
    rows = list(csv.DictReader(open(table, encoding='utf-8'), delimiter='\t'))
    for row in rows:
        row['id'] = f'{row["package"].lower()}-{row["version"].lower()}'
    return rows


def find(rows, name):
    """The row named on the command line: a package id, or id@version."""
    package, _, version = name.partition('@')
    hits = [row for row in rows
            if row['package'].lower() == package.lower() and (not version or row['version'] == version)]
    if len(hits) != 1:
        sys.exit(f'{name}: {len(hits)} rows match; name the version as id@version')
    return hits[0]


class Lab:
    """Where everything lives for one package: the shared SDK, cache and tools,
    and its own clone and output."""

    def __init__(self, root, row):
        self.root = os.path.abspath(root)
        self.sdk = os.path.join(self.root, 'sdk')
        self.nuget = os.path.join(self.root, 'nuget')
        self.clihome = os.path.join(self.root, 'clihome')
        self.tools = os.path.join(self.root, 'tools')
        self.src = os.path.join(self.root, 'src', row['id'])
        self.out = os.path.join(self.root, 'out', row['id'])

    def read_state(self):
        path = os.path.join(self.out, 'state.json')
        if os.path.exists(path):
            return json.load(open(path))
        return {}

    def write_state(self, state):
        os.makedirs(self.out, exist_ok=True)
        json.dump(state, open(os.path.join(self.out, 'state.json'), 'w'), indent=1)

    def build_env(self):
        """Only the lab's SDK on PATH, the lab's cache, no telemetry. The trailing slash on
        NUGET_PACKAGES matters: Source Link's source-root check rejects a package root without one."""
        env = dict(os.environ)
        env['PATH'] = f'{self.sdk}:{self.tools}:{os.environ["PATH"]}'
        env['DOTNET_ROOT'] = self.sdk
        env['DOTNET_CLI_HOME'] = self.clihome
        env['NUGET_PACKAGES'] = self.nuget + '/'
        env['DOTNET_CLI_TELEMETRY_OPTOUT'] = '1'
        env['DOTNET_NOLOGO'] = '1'
        env['DOTNET_SKIP_FIRST_TIME_EXPERIENCE'] = '1'
        env['NuGetAudit'] = 'false'
        return env


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec='seconds')


def run_logged(log, cmd, env, cwd=None, check=False):
    """Run cmd with its output appended to the open log; return the exit code."""
    log.write(f'$ {" ".join(cmd)}\n')
    log.flush()
    code = subprocess.run(cmd, env=env, cwd=cwd, stdout=log, stderr=subprocess.STDOUT).returncode
    if check and code:
        raise RuntimeError(f'{" ".join(cmd)} exited {code}')
    return code


def first_error(text):
    """The first line of a build log that reports an error, for the results table."""
    for line in text.splitlines():
        if re.search(r'error [A-Z]*\d*\s*:|fatal:|Unhandled exception|command not found', line):
            return line.strip()[:300]
    return ''


# The build command

def pack_command(row, mode, commit_time):
    """Build, then pack what was built. `dotnet pack` alone trips over GeneratePackageOnBuild in
    multi-targeting projects (NU5026); the two-step form packs the same bytes."""
    props = '-p:UseSharedCompilation=false'
    if mode == 'configured':
        props += ' -p:ContinuousIntegrationBuild=true -p:Deterministic=true'
        props += f' -p:DeterministicTimestamp={commit_time}'
    project = row['project']
    return (f'dotnet build {project} -c Release --no-restore {props} && '
            f'dotnet pack {project} -c Release --no-build -o out {props}')


# Getting the source ready: clone, unpin the SDK, restore

def clone(row, lab, env, log):
    """A clone at the declared commit, sources as committed (no CRLF conversion), submodules in."""
    shutil.rmtree(lab.src, ignore_errors=True)
    git = ['git', '-C', lab.src]
    run_logged(log, ['git', 'clone', '-q', '--no-checkout', row['repo'], lab.src], env, check=True)
    have_commit = subprocess.run(git + ['cat-file', '-e', f'{row["commit"]}^{{commit}}'], capture_output=True)
    if have_commit.returncode:
        # the commit is on no branch or tag; GitHub still serves it when asked for by name
        run_logged(log, git + ['fetch', '-q', 'origin', row['commit']], env)
    run_logged(log, git + ['config', 'core.autocrlf', 'false'], env, check=True)
    checkout = git + ['-c', 'advice.detachedHead=false', 'checkout', '-q', row['commit']]
    run_logged(log, checkout, env, check=True)
    if os.path.exists(os.path.join(lab.src, '.gitmodules')):
        run_logged(log, git + ['submodule', 'update', '--init', '--recursive', '-q'], env, check=True)


def unpin_sdk(src):
    """The repository's global.json may pin an SDK the lab does not have. The pin is removed so the
    one fixed SDK builds every package; the msbuild-sdks entries (Arcade in tree) are kept. What was
    done is returned and recorded with the package. Called after every checkout, since
    `git checkout -- .` puts the file back."""
    path = os.path.join(src, 'global.json')
    if not os.path.exists(path):
        return 'none'
    try:
        content = json.load(open(path, encoding='utf-8-sig'))
    except ValueError:
        return 'kept (unreadable)'
    if 'sdk' not in content:
        return 'kept'
    pinned = content['sdk'].get('version', '?')
    del content['sdk']
    if content:
        json.dump(content, open(path, 'w'), indent=2)
    else:
        os.remove(path)
    return f'sdk-removed (pinned {pinned})'


def clean_and_restore(row, lab, env, log):
    """Leave the tree clean but restored: obj/ holds restore output only, so every build that
    follows compiles from scratch. Returns restore's exit code."""
    run_logged(log, ['git', '-C', lab.src, 'clean', '-xdfq'], env, check=True)
    run_logged(log, ['git', '-C', lab.src, 'checkout', '-q', '--', '.'], env)
    unpin_sdk(lab.src)
    restore = ['dotnet', 'restore', row['project'], '-p:UseSharedCompilation=false']
    code = run_logged(log, restore, env, lab.src)
    run_logged(log, ['dotnet', 'build-server', 'shutdown'], env, lab.src)
    return code


def clone_and_restore(row, lab):
    """Make sure the package's clone exists, at the commit, restored. Records the commit time and
    what was done to global.json. A clone that is already there is left alone."""
    state = lab.read_state()
    if 'recipe' not in state:
        state['recipe'] = {key: row[key] for key in ('package', 'version', 'repo', 'commit', 'project')}
        lab.write_state(state)
    if state.get('prepared') and os.path.isdir(os.path.join(lab.src, '.git')):
        return state
    for folder in (lab.nuget, lab.clihome, lab.tools, lab.out):
        os.makedirs(folder, exist_ok=True)
    env = lab.build_env()
    with open(os.path.join(lab.out, 'prepare.log'), 'a', encoding='utf-8') as log:
        log.write(f'start {now()}\n')
        try:
            clone(row, lab, env, log)
        except RuntimeError as error:
            # the source cannot be had: that is a result about the package, not a fault of the driver
            state.update(screen='clone failed', screen_error=str(error)[:300], global_json='', nupkgs=[])
            lab.write_state(state)
            return state
        commit_time = subprocess.run(['git', '-C', lab.src, 'log', '-1', '--format=%ct'],
                                     capture_output=True, text=True).stdout.strip()
        state['commit_time'] = commit_time
        state['global_json'] = unpin_sdk(lab.src)
        state['prepared'] = now()
        if 'screen' in state:
            # the clone was dropped after an earlier run and made again: restore it as try_build left it
            clean_and_restore(row, lab, env, log)
    lab.write_state(state)
    return state


# One plain build: does the project build at all under the fixed SDK?

def try_build(row, lab):
    state = clone_and_restore(row, lab)
    if 'screen' in state:
        return state
    env = lab.build_env()
    started = datetime.datetime.now()
    log_path = os.path.join(lab.out, 'screen.log')
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f'start {now()}\n')
        if clean_and_restore(row, lab, env, log):
            state['screen'] = 'restore failed'
        else:
            command = pack_command(row, 'default', state['commit_time'])
            code = run_logged(log, ['bash', '-c', command], env, lab.src)
            run_logged(log, ['dotnet', 'build-server', 'shutdown'], env, lab.src)
            state['nupkgs'] = packages_in(os.path.join(lab.src, 'out'), names_only=True)
            if code:
                state['screen'] = f'pack failed (exit {code})'
            elif not state['nupkgs']:
                state['screen'] = 'no package'
            else:
                state['screen'] = 'built'
        log.write(f'end {now()} {state["screen"]}\n')
        clean_and_restore(row, lab, env, log)   # back to clean-and-restored for the reprotest builds
    state['screen_seconds'] = round((datetime.datetime.now() - started).total_seconds())
    if state['screen'] == 'built':
        state['screen_error'] = ''
    else:
        state['screen_error'] = first_error(open(log_path, encoding='utf-8', errors='replace').read())
    lab.write_state(state)
    return state


# Two builds with one thing varied, then the comparison

def build_twice(row, lab, mode, axes):
    """reprotest builds the package twice, the second time with AXES varied, and stores both
    out/ folders. The verdict goes into the package's state under "<mode>:<axis>"."""
    state = try_build(row, lab)
    if state['screen'] != 'built':
        return state
    name = 'all' if axes == AXES else '+'.join(axes)
    key = f'{mode}:{name}'
    if key in state.get('runs', {}):
        return state
    state = clone_and_restore(row, lab)   # the clone may have been dropped after an earlier package
    env = lab.build_env()
    # reprotest runs the command in a shell of its own, so the build environment is set once more
    # inside the command; the build server is shut down after it so nothing crosses into the next build
    exports = (f'export PATH={lab.sdk}:{lab.tools}:$PATH DOTNET_ROOT={lab.sdk} DOTNET_CLI_HOME={lab.clihome} '
               f'NUGET_PACKAGES={lab.nuget}/ DOTNET_CLI_TELEMETRY_OPTOUT=1 DOTNET_NOLOGO=1 NuGetAudit=false')
    command = (f'{exports} && rm -rf out && {pack_command(row, mode, state["commit_time"])}; '
               f'rc=$?; dotnet build-server shutdown >/dev/null 2>&1; exit $rc')
    store = os.path.join(lab.out, f'{mode}-{name}-store')
    shutil.rmtree(store, ignore_errors=True)
    log_path = os.path.join(lab.out, f'{mode}-{name}.log')
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f'start {now()}\n$ {command}\n')
        log.flush()
        variations = '--vary=-all,' + ','.join('+' + axis for axis in axes)
        reprotest = [REPROTEST, '--no-diffoscope', '--store-dir', store, variations,
                     '-c', command, lab.src, 'out']
        code = subprocess.run(reprotest, stdout=log, stderr=subprocess.STDOUT, env=env).returncode
        log.write(f'end {now()} exit {code}\n')
    verdict = compare_builds(store, row['package'])
    verdict['reprotest_exit'] = code
    if code not in (0, 1):   # 0 is reproducible, 1 is not; anything else is reprotest or the build failing
        log_text = open(log_path, encoding='utf-8', errors='replace').read()
        verdict['note'] = first_error(log_text) or f'reprotest exit {code}'
    state.setdefault('runs', {})[key] = verdict
    lab.write_state(state)
    keep_packages_only(store)
    return state


def keep_packages_only(store):
    """The store holds two full out/ folders per run; only the packages are kept for later reading."""
    for root, _, files in os.walk(store):
        for name in files:
            if not name.endswith(('.nupkg', '.snupkg')):
                os.remove(os.path.join(root, name))


def packages_in(folder, package_id=None, names_only=False):
    """The .nupkg files under FOLDER. With PACKAGE_ID, the ones of that package, paired by id and
    not by file name: a build that puts the clock into the version names its two packages
    differently. When the project packs under another id than the table names, every package
    produced is taken instead and the verdict's note says so."""
    found = []
    for root, _, files in os.walk(folder) if os.path.isdir(folder) else []:
        for name in files:
            if name.endswith('.nupkg') and not name.endswith('.symbols.nupkg'):
                found.append(os.path.join(root, name))
    found.sort()
    if names_only:
        return [os.path.basename(path) for path in found]
    if package_id:
        pattern = re.compile(r'^' + re.escape(package_id) + r'\.\d.*\.nupkg$', re.IGNORECASE)
        of_this_package = [path for path in found if pattern.match(os.path.basename(path))]
        return of_this_package or found
    return found


def entry_hashes(nupkg):
    with zipfile.ZipFile(nupkg) as archive:
        return {entry.filename: hashlib.sha256(archive.read(entry)).hexdigest()
                for entry in archive.infolist()}


def is_nuget_metadata(name):
    return name.startswith(NUGET_METADATA[0]) or name in NUGET_METADATA[1:]


def is_assembly(name):
    return name.split('/')[0] in ('lib', 'ref', 'runtimes') and name.endswith(('.dll', '.exe'))


def compare_builds(store, package_id):
    """Levels 1 to 3 between reprotest's control build and its varied build."""
    control = packages_in(os.path.join(store, 'control'), package_id)
    varied = packages_in(os.path.join(store, 'experiment-1'), package_id)
    if not control or not varied:
        have = sum(1 for side in (control, varied) if side)
        return dict(b1='failed', b2='failed', b3='failed', first='',
                    note=f'a build under the variation produced no package ({have} of 2 builds have one)')
    a, b = control[0], varied[0]
    name_a, name_b = os.path.basename(a), os.path.basename(b)
    verdict = dict(b1='same', b2='same', b3='same', first='', note='')
    if not name_a.lower().startswith(package_id.lower() + '.'):
        verdict['note'] = f'the project packs {name_a}, not {package_id}: that package is compared'
    if name_a != name_b:
        verdict['b1'] = 'differs'
        verdict['first'] = f'file name differs: {name_a} vs {name_b}'
    if hashlib.sha256(open(a, 'rb').read()).digest() != hashlib.sha256(open(b, 'rb').read()).digest():
        verdict['b1'] = 'differs'
    hashes_a, hashes_b = entry_hashes(a), entry_hashes(b)
    if verdict['b1'] == 'differs' and not verdict['first']:
        # the whole file differs but every entry is the same: only the entry timestamps can differ
        verdict['first'] = 'entry timestamps only' if hashes_a == hashes_b else 'packaging files only'
    for entry in sorted(set(hashes_a) | set(hashes_b)):
        if hashes_a.get(entry) == hashes_b.get(entry) or is_nuget_metadata(entry):
            continue
        if verdict['b2'] == 'same':
            verdict['b2'] = 'differs'
            verdict['first'] = f'{name_a}:{entry}'
        if is_assembly(entry):
            verdict['b3'] = 'differs'
            verdict['first'] = f'{name_a}:{entry}'
    return verdict


# Everything, for every package

def describe(state, key):
    """One run's verdict as a short line for the log."""
    verdict = state.get('runs', {}).get(key)
    if not verdict:
        return state.get('screen', '?')
    line = f'b1={verdict["b1"]} b2={verdict["b2"]} b3={verdict["b3"]}'
    if verdict['first']:
        line += f' ({verdict["first"]})'
    if verdict.get('note'):
        line += f' [{verdict["note"]}]'
    return line


def batch(table, root):
    """Every package of the table in turn: build it once, then every axis as is and configured.
    A package with its result recorded is skipped, so a stopped batch continues where it was.
    The clone is dropped after each package; a package's failure does not stop the batch."""
    root = os.path.abspath(root)
    os.makedirs(root, exist_ok=True)
    runlog = open(os.path.join(root, 'run.log'), 'a', encoding='utf-8')
    for row in sorted(load(table), key=lambda row: row['id']):
        lab = Lab(root, row)
        started = now()
        try:
            if row['status'] != 'ok':
                line = record_not_built(row, lab)
            else:
                line = build_all_axes(row, lab)
                shutil.rmtree(lab.src, ignore_errors=True)
        except Exception as error:
            line = f'ERROR {error}'
        runlog.write(f'{started} .. {now()} {row["id"]}: {line}\n')
        runlog.flush()
        print(f'{row["id"]}: {line}', flush=True)


def record_not_built(row, lab):
    """population.py found no source or project for this row: recorded, not built."""
    state = lab.read_state()
    if 'screen' not in state:
        state.update(recipe={key: row[key] for key in ('package', 'version', 'repo', 'commit', 'project')},
                     screen='not built', screen_error=row['status'], global_json='', nupkgs=[])
        lab.write_state(state)
    return f'not built: {row["status"]}'


def build_all_axes(row, lab):
    state = try_build(row, lab)
    if state['screen'] != 'built':
        return state['screen']
    for mode in MODES:
        for axis in AXES:
            state = build_twice(row, lab, mode, [axis])
    parts = []
    for mode in MODES:
        parts.append(mode + ': ' + '; '.join(f'{axis} {describe(state, f"{mode}:{axis}")}' for axis in AXES))
    return ' || '.join(parts)


def write_results(root, out_tsv):
    """One row per (package, mode, axis) from every state file in the lab."""
    columns = ['package', 'version', 'repo', 'commit', 'project', 'global_json', 'screen', 'screen_error',
               'mode', 'axes', 'b1', 'b2', 'b3', 'first_difference', 'note']
    rows = []
    out_root = os.path.join(root, 'out')
    for package_id in sorted(os.listdir(out_root)):
        path = os.path.join(out_root, package_id, 'state.json')
        if not os.path.exists(path):
            continue
        state = json.load(open(path))
        recipe = state.get('recipe', {})
        base = [recipe.get('package', package_id), recipe.get('version', ''), recipe.get('repo', ''),
                recipe.get('commit', ''), recipe.get('project', ''), state.get('global_json', ''),
                state.get('screen', ''), state.get('screen_error', '')]
        runs = state.get('runs', {})
        if not runs:
            rows.append(base + [''] * 7)
        for key in sorted(runs):
            mode, axes = key.split(':', 1)
            verdict = runs[key]
            rows.append(base + [mode, axes, verdict['b1'], verdict['b2'], verdict['b3'],
                                verdict['first'], verdict.get('note', '')])
    with open(out_tsv, 'w', encoding='utf-8') as out:
        out.write('\t'.join(columns) + '\n')
        for row in rows:
            out.write('\t'.join(str(cell).replace('\t', ' ') for cell in row) + '\n')
    print(f'{len(rows)} rows -> {out_tsv}')


def record_environment(root):
    """environment.txt: the host, the SDK and the tools, as they were when the run was made."""
    sdk = os.path.join(root, 'sdk')

    def output_of(command):
        return subprocess.run(command, shell=True, capture_output=True, text=True).stdout.strip()

    pwsh = f"{root}/tools/pwsh -NoProfile -Command '$PSVersionTable.PSVersion.ToString()'"
    pwsh_version = output_of(pwsh + ' 2>/dev/null')
    lines = [
        f'recorded {now()}',
        f'host {output_of("uname -a")}',
        f'glibc {output_of("ldd --version | head -1")}',
        f'sdk {output_of(f"{sdk}/dotnet --version")} at {sdk}',
        f'nuget {output_of(f"{sdk}/dotnet nuget --version | tail -1")}',
        'sdk tarball ' + output_of(f'grep sha512 {root}/install-sdk.log'),
        f'reprotest {output_of("reprotest --version 2>&1 | head -1")} at {REPROTEST}',
        f'disorderfs {output_of("disorderfs --version 2>&1 | head -1")}',
        f'faketime {output_of("faketime -v 2>&1 | grep -i version")}',
        f'pwsh {pwsh_version} at {root}/tools',
        'locales ' + ','.join(output_of('locale -a').split()),
        f'axes {",".join(AXES)}',
        '',
        'packages',
        output_of('pacman -Q 2>/dev/null || dpkg -l 2>/dev/null'),
    ]
    open(os.path.join(root, 'environment.txt'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('\n'.join(lines[:12]))


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else ''
    args = sys.argv[2:]
    if command == 'batch':
        batch(args[0], args[1])
    elif command == 'results':
        write_results(os.path.abspath(args[0]), args[1])
    elif command == 'environment':
        record_environment(os.path.abspath(args[0]))
    elif command in ('try-build', 'build-twice'):
        row = find(load(args[0]), args[1])
        lab = Lab(args[2], row)
        if command == 'try-build':
            state = try_build(row, lab)
        else:
            mode, axis = args[3], args[4]
            state = build_twice(row, lab, mode, AXES if axis == 'all' else [axis])
        print(json.dumps({key: value for key, value in state.items() if key != 'recipe'}, indent=1))
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
