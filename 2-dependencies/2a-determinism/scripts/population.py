"""Find source commits and project files for the determinism experiment
from a list of NuGet packages.

    python3 -I population.py shipped-packages.txt WORK population.tsv

shipped-packages.txt has one "Package Version" per line (# comments allowed). For each:

 1. the .nupkg is fetched from nuget.org (the public flat-container API) into WORK/nupkg/;
 2. its .nuspec is read for <repository url="..." commit="..."/>, the publisher's own
    statement of where the code came from; a package without url or commit stops here;
 3. the assembly the package ships is read from lib/: the .dll named like the package,
    else the one .dll there; a package with none (meta, analyzer, native) stops here;
 4. the repository is fetched at that commit, shallow, into WORK/src/ (once per
    repository and commit), and the .csproj whose assembly name is that .dll is looked
    for: its <AssemblyName> when set, else its file name. Of several, reference-assembly
    and shim projects (ref/, referencePackages/, shims/) are dropped, then the one named like
    the package wins; still none or several stops here, and the row says which were found.

Write one row per package to population.tsv: package, version, repo, commit, project, dll,
status. status is "ok" when the row can be built; otherwise it records where and why it stopped.
Read only public sources. Do not build anything.
"""
import hashlib, os, re, shutil, subprocess, sys, urllib.request, zipfile
import xml.etree.ElementTree as ET


def fetch_nupkg(pkg, ver, workdir):
    os.makedirs(os.path.join(workdir, 'nupkg'), exist_ok=True)
    path = os.path.join(workdir, 'nupkg', f'{pkg}.{ver}.nupkg')
    if not os.path.exists(path):
        name = f'{pkg.lower()}/{ver.lower()}'
        url = f'https://api.nuget.org/v3-flatcontainer/{name}/{pkg.lower()}.{ver.lower()}.nupkg'
        with urllib.request.urlopen(url, timeout=120) as r:
            data = r.read()
        open(path, 'wb').write(data)
    return path


def read_nuspec(nupkg):
    """Read (repository url, commit) from the package's .nuspec; use '' for missing values."""
    with zipfile.ZipFile(nupkg) as z:
        name = next(n for n in z.namelist() if n.endswith('.nuspec') and '/' not in n)
        root = ET.fromstring(z.read(name))
    for el in root.iter():
        if el.tag.split('}')[-1] == 'repository':
            return el.get('url', '').strip().removesuffix('.git'), el.get('commit', '').strip()
    return '', ''


def shipped_dll(nupkg, pkg):
    """Find the assembly under lib/, excluding satellite resources in culture folders."""
    with zipfile.ZipFile(nupkg) as z:
        dlls = sorted({os.path.basename(n) for n in z.namelist()
                       if n.startswith('lib/') and n.endswith('.dll') and n.count('/') == 2})
    named = [d for d in dlls if d.lower() == f'{pkg.lower()}.dll']
    if named:
        return named[0][:-4]
    return dlls[0][:-4] if len(dlls) == 1 else ''


def fetch_source(repo, commit, workdir):
    """Check out one commit shallowly; share it across packages from that repository and commit."""
    key = hashlib.sha256(f'{repo.lower()} {commit}'.encode()).hexdigest()[:16]
    src = os.path.join(workdir, 'src', key)
    if os.path.exists(os.path.join(src, '.population-ok')):
        return src
    shutil.rmtree(src, ignore_errors=True)   # An earlier failed fetch left an incomplete folder.
    os.makedirs(src)
    # Disable git-lfs: reading project files does not need the large files.
    git = ['git', '-c', 'filter.lfs.smudge=', '-c', 'filter.lfs.process=', '-c', 'filter.lfs.required=false']
    cmds = [git + ['init', '-q'], git + ['remote', 'add', 'origin', repo],
            git + ['fetch', '-q', '--depth=1', 'origin', commit],
            git + ['-c', 'advice.detachedHead=false', 'checkout', '-q', 'FETCH_HEAD']]
    for c in cmds:
        p = subprocess.run(c, cwd=src, capture_output=True, text=True)
        if p.returncode:
            said = (p.stderr or p.stdout).strip()
            raise RuntimeError(said.splitlines()[-1][:200] if said else f'{c[1]} failed')
    open(os.path.join(src, '.population-ok'), 'w').close()
    return src


def project_candidates(src, asm):
    """Find .csproj files under SRC with assembly name ASM: <AssemblyName> if set, else the file name."""
    hits = []
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d != '.git']
        for f in files:
            if not f.endswith('.csproj'):
                continue
            path = os.path.join(root, f)
            try:
                x = ET.parse(path).getroot()
            except ET.ParseError:
                continue
            names = [e.text.strip() for e in x.iter('AssemblyName') if e.text]
            name = names[-1] if names else f[:-7]
            if name == asm:
                hits.append(os.path.relpath(path, src))
    return sorted(hits)


def choose_project(hits, asm, pkg):
    """Choose one project, or return '' with a reason. For multiple candidates, exclude
    reference-assembly and shim projects (ref/, referencePackages/, shims/): these build
    ref/ assemblies or stubs, not the lib/ assembly. Then prefer the package's name."""
    if len(hits) == 1:
        return hits[0], ''
    if not hits:
        return '', f'no project (0 .csproj with assembly name {asm})'
    impl = [h for h in hits if not re.search(r'(^|/)ref/|(^|/)referencePackages/|(^|/)shims/', h)]
    if len(impl) > 1:
        named = [h for h in impl if os.path.basename(h).lower() == f'{pkg.lower()}.csproj']
        impl = named if len(named) == 1 else impl
    if len(impl) == 1:
        return impl[0], ''
    return '', f'no project ({len(hits)} .csproj with assembly name {asm}: {", ".join(hits)})'


def find_project(src, asm, pkg):
    return choose_project(project_candidates(src, asm), asm, pkg)


def main():
    listing, workdir, out = sys.argv[1:4]
    rows = []
    for line in open(listing, encoding='utf-8'):
        line = line.split('#')[0].strip()
        if not line:
            continue
        pkg, ver = line.split()
        row = dict(package=pkg, version=ver, repo='', commit='', project='', dll='', status='')
        try:
            nupkg = fetch_nupkg(pkg, ver, workdir)
            row['repo'], row['commit'] = read_nuspec(nupkg)
            if not row['repo']:
                row['status'] = 'no repository in the .nuspec'
            elif not row['commit']:
                row['status'] = 'no commit in the .nuspec'
            else:
                row['dll'] = shipped_dll(nupkg, pkg)
                if not row['dll']:
                    row['status'] = 'no managed assembly under lib/'
                else:
                    try:
                        src = fetch_source(row['repo'], row['commit'], workdir)
                    except RuntimeError as e:
                        row['status'] = f'source not fetched: {e}'
                    else:
                        row['project'], why = find_project(src, row['dll'], pkg)
                        row['status'] = why or 'ok'
        except Exception as e:   # Record a failed download or broken package and continue.
            row['status'] = f'{type(e).__name__}: {str(e)[:150]}'
        rows.append(row)
        print(f'{pkg} {ver}: {row["status"]}' + (f' {row["project"]}' if row['project'] else ''), flush=True)
    cols = ['package', 'version', 'repo', 'commit', 'project', 'dll', 'status']
    with open(out, 'w', encoding='utf-8') as f:
        f.write('\t'.join(cols) + '\n')
        for r in rows:
            f.write('\t'.join(r[c].replace('\t', ' ') for c in cols) + '\n')
    ok = sum(1 for r in rows if r['status'] == 'ok')
    print(f'{len(rows)} packages, {ok} with a project to build -> {out}')


if __name__ == '__main__':
    main()
