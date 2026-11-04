"""Short texts for the page: what a package is (its own .nuspec) and why Phoenix has it (dependencies.yml).

    python3 -I scripts/describe.py fetch results/graph.json NUSPEC_DIR
    python3 -I scripts/describe.py results/graph.json NUSPEC_DIR results/descriptions.json [DEPENDENCIES_YML]

fetch: downloads the .nuspec of every package from nuget.org's flat container,
https://api.nuget.org/v3-flatcontainer/<id>/<version>/<id>.nuspec (lower case), into NUSPEC_DIR.
Then: what = the first sentence of the <summary>, else of the <description>, at most about 160 characters;
why = the sentence in Phoenix's dependencies.yml (WS.Phoenix 79cb67a7) for a package a project names. The
page shows "why" on ring 1 only, because dependencies.yml names packages without a version. Without the yml,
there is no "why". The "why" sentences are Weel-Sandvig's text.
"""
import html, json, os, re, sys, urllib.request


def nuspec_path(folder, n):
    return os.path.join(folder, f"{n['name'].lower()}.{n['version'].lower()}.nuspec")


def fetch(graph, folder):
    os.makedirs(folder, exist_ok=True)
    for n in json.load(open(graph))['nodes']:
        if n['kind'] != 'package' or os.path.exists(nuspec_path(folder, n)):
            continue
        i, v = n['name'].lower(), n['version'].lower()
        with urllib.request.urlopen(f'https://api.nuget.org/v3-flatcontainer/{i}/{v}/{i}.nuspec', timeout=60) as r:
            open(nuspec_path(folder, n), 'wb').write(r.read())
    print(len(os.listdir(folder)), 'files in', folder)


def tag(t, x):
    m = re.search(rf'<{t}>(.*?)</{t}>', x, re.S)
    return re.sub(r'\s+', ' ', html.unescape(m.group(1))).strip() if m else ''


def first_sentence(t):
    t = re.split(r'\s*(Commonly Used Types:|When using NuGet 3\.x|This package was built from the source code)', t)[0].strip()
    m = re.match(r'(.{30,}?[.!?])(\s|$)', t)  # the first sentence end after 30 characters; dots in names have no space after them
    s = m.group(1) if m else t
    if len(s) > 160:
        s = s[:157].rsplit(' ', 1)[0].rstrip(',;:') + '…'
    return s


def describe(graph, folder, out, deps=None):
    why = {}
    if deps:
        import yaml  # PyYAML, only for the optional dependencies.yml
        why = {k.lower(): (v or {}).get('why', '') for k, v in (yaml.safe_load(open(deps)).get('nuget') or {}).items()}
    result, missing = {}, []
    for n in json.load(open(graph))['nodes']:
        if n['kind'] != 'package':
            continue
        x = open(nuspec_path(folder, n), encoding='utf-8-sig', errors='replace').read()
        what = first_sentence(tag('summary', x) or tag('description', x))
        w = why.get(n['name'].lower(), '')
        if deps and n.get('direct') and not w:
            missing.append(n['id'])
        result[n['id']] = {k: v for k, v in (('what', what), ('why', w)) if v}
    json.dump(result, open(out, 'w'), ensure_ascii=False, indent=0)
    print(len(result), 'packages;', sum('why' in v for v in result.values()), 'with why;', 'direct without why:', missing)


if __name__ == '__main__':
    if sys.argv[1] == 'fetch':
        fetch(*sys.argv[2:4])
    else:
        describe(*sys.argv[1:])
