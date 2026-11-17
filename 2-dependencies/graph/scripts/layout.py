"""Place the nodes of the dependency graph: ring = steps from WS.PEMS's projects, sector = source repository.

    python3 -I scripts/layout.py results/graph.json results/layout.json

No simulation: every package sits on its ring inside its own sector, so the same input gives the same positions.
Sectors with fewer than MIN_SECTOR packages are combined as "Other repositories". Inside a sector and ring, the
nodes are ordered by the mean angle of their neighbours (two sweeps), which keeps edges short. Where a ring has
no room for a sector's nodes in one row, they alternate between rows on both sides of the ring.
The output also holds each sector's label position: two columns beside the circle, with leader lines.
"""
import collections, json, math, re, sys

GRAPH, OUT = sys.argv[1:3]
RING = [0, 170, 295, 400, 475]          # ring 4 holds steps 4 to 7
NODE_R, OWN_R = 4.2, 8
SPACING, ROW_GAP = 11.0, 11.0           # between node centres along a row, and between rows
GAP, TOP = 0.022, 0.2                   # between sectors; an empty wedge at 12 o'clock for the ring labels
MIN_SECTOR = 4
OTHER = '(other)'
MS = {'dotnet', 'azure', 'azuread', 'microsoft', 'nuget'}
# Short names: organisation/repository for Microsoft's organisations, the repository name for a third party,
# organisation/* where a third-party organisation has several repositories here.
LABELS = {
    'dotnet/dotnet': 'dotnet/dotnet', 'dotnet/runtime': 'dotnet/runtime', 'dotnet/aspnetcore': 'dotnet/aspnetcore',
    'dotnet/roslyn': 'dotnet/roslyn', 'dotnet/scaffolding': 'dotnet/Scaffolding', 'humanizr': 'Humanizer',
    'fwlink': 'SkiaSharp (fwlink)', 'serilog': 'serilog/*', '(no repository)': 'No repository',
    'azuread/azure-activedirectory-identitymodel-extensions-for-dotnet': 'IdentityModel', 'azuread/microsoft-identity-web': 'microsoft-identity-web',
    'azure/azure-sdk-for-net': 'azure-sdk-for-net', 'nuget/nuget.client': 'NuGet.Client', 'domaindrivendev': 'Swashbuckle',
    'dotnet': 'github.com/dotnet', 'hangfireio': 'HangfireIO/*', 'wieslawsoltes': 'Svg.Skia', 'ericsink': 'SQLitePCL.raw',
    'quartznet': 'Quartz.NET', 'ststeiger': 'PdfSharpCore', OTHER: 'Other repositories',
}
CENTRE = {'WebAPI': (-34, -10), 'BackgroundJobExecutor': (30, -32), 'DbMigrator': (22, 34),
          'ApplicationCore': (-26, 40), 'Infrastructure': (0, 4)}

g = json.load(open(GRAPH))
nodes = {n['id']: n for n in g['nodes']}
own = {i for i, n in nodes.items() if n['kind'] != 'package'}
out, inn = collections.defaultdict(set), collections.defaultdict(set)
for e in g['edges']:
    out[e['source']].add(e['target'])
    inn[e['target']].add(e['source'])

# Steps from WS.PEMS's projects
step = {i: 0 for i in own}
queue = collections.deque(sorted(own))
while queue:
    a = queue.popleft()
    for b in sorted(out[a]):
        if b not in step:
            step[b] = step[a] + 1
            queue.append(b)
for i in nodes:
    step.setdefault(i, 1)  # dotnet-ef: a release tool without edges
ring = {i: min(s, len(RING) - 1) for i, s in step.items()}


def repo_key(n):
    u = (n.get('repo') or '').lower().rstrip('/')
    u = re.sub(r'\.git$', '', u)
    if not u:
        return '(no repository)'
    if 'go.microsoft.com/fwlink' in u:
        return 'fwlink'  # SkiaSharp and HarfBuzzSharp name a go.microsoft.com fwlink as their repository
    u = re.sub(r'^(https?|git)://(www\.)?github\.com/', '', u)
    org, _, rest = u.partition('/')
    repo = rest.split('/')[0]
    if not repo:
        return org
    return f'{org}/{repo}' if org in MS else org


repo = {i: repo_key(n) for i, n in nodes.items() if i not in own}
size = collections.Counter(repo.values())
sector = {i: (k if size[k] >= MIN_SECTOR else OTHER) for i, k in repo.items()}
members = collections.defaultdict(list)
for i, k in sector.items():
    members[k].append(i)

# Sector order: start with the largest; then add the sector with the most edges to those placed last. Other goes last.
links = collections.defaultdict(collections.Counter)
for e in g['edges']:
    a, b = sector.get(e['source']), sector.get(e['target'])
    if a and b and a != b:
        links[a][b] += 1
        links[b][a] += 1
remaining = set(members) - {OTHER}
order = []
cur = max(sorted(remaining), key=lambda k: len(members[k]))
while cur:
    order.append(cur)
    remaining.discard(cur)
    score = lambda k: sum(links[o][k] / (j + 1) for j, o in enumerate(reversed(order)))
    cur = max(sorted(remaining), key=lambda k: (score(k), len(members[k]))) if remaining else None
order.append(OTHER)

span_total = 2 * math.pi - TOP - GAP * (len(order) - 1)
total = sum(len(members[k]) for k in order)
a0 = -math.pi / 2 + TOP / 2
sectors = []
for k in order:
    w = len(members[k]) / total * span_total
    sectors.append({'key': k, 'label': LABELS.get(k, k), 'count': len(members[k]), 'start': a0, 'end': a0 + w, 'mid': a0 + w / 2})
    a0 += w + GAP
sec = {s['key']: s for s in sectors}

# Place: per sector and ring, order by neighbour angle, spread over the sector's span, rows if needed.
angle = {}
pos = {}
for i, (x, y) in CENTRE.items():
    pos[i] = (x, y)


def delta(a, mid):
    return (a - mid + math.pi) % (2 * math.pi) - math.pi


def place(group_order):
    for (k, r), ids in group_order.items():
        s = sec[k]
        R = RING[r]
        n = len(ids)
        cap = max(1, int((s['end'] - s['start']) * R / SPACING))
        rows = math.ceil(n / cap)
        for j, i in enumerate(ids):
            t = s['start'] + (s['end'] - s['start']) * (j + 0.5) / n
            rr = R + ((j % rows) - (rows - 1) / 2) * ROW_GAP
            angle[i] = t
            pos[i] = (math.cos(t) * rr, math.sin(t) * rr)


groups = collections.defaultdict(list)
for i in sector:
    groups[(sector[i], ring[i])].append(i)
for v in groups.values():
    v.sort()
place(groups)


def bary(i, neighbours, mid):
    ds = [delta(angle[j], mid) for j in neighbours if j in angle]
    return sum(ds) / len(ds) if ds else 0.0


for sweep in range(2):
    for r in range(2, len(RING)):           # outward: by the angles of the dependents
        for (k, rr), ids in groups.items():
            if rr == r:
                ids.sort(key=lambda i: (bary(i, inn[i], sec[k]['mid']), i))
        place(groups)
    for r in range(1, len(RING) - 1)[::-1]:  # inward: by the angles of the dependencies
        for (k, rr), ids in groups.items():
            if rr == r:
                ids.sort(key=lambda i: (bary(i, out[i], sec[k]['mid']), i))
        place(groups)

# Labels: two columns beside the circle; each label as close as possible to its sector's height, at least LINE apart.
R_OUT = RING[-1]
BRACKET = R_OUT + 22
COLUMN = R_OUT + 72
LINE = 36
for side in (1, -1):
    ss = [s for s in sectors if (math.cos(s['mid']) >= 0) == (side == 1)]
    ss.sort(key=lambda s: math.sin(s['mid']))
    ys = [math.sin(s['mid']) * (BRACKET + 14) for s in ss]
    for _ in range(200):                      # push apart, then pull back inside the limits
        for j in range(1, len(ys)):
            if ys[j] - ys[j - 1] < LINE:
                m = (ys[j] + ys[j - 1]) / 2
                ys[j - 1], ys[j] = m - LINE / 2, m + LINE / 2
        lim = R_OUT + 40
        shift = max(0, ys[-1] - lim) if ys else 0
        ys = [y - shift for y in ys]
        shift = min(0, ys[0] + lim) if ys else 0
        ys = [y - shift for y in ys]
    for s, y in zip(ss, ys):
        s['anchor'] = [round(math.cos(s['mid']) * BRACKET, 1), round(math.sin(s['mid']) * BRACKET, 1)]
        s['elbow'] = [round(math.cos(s['mid']) * (BRACKET + 14), 1), round(math.sin(s['mid']) * (BRACKET + 14), 1)]
        s['text'] = [side * COLUMN, round(y, 1)]
        s['side'] = side

result = {
    'nodes': [{'id': i, 'x': round(pos[i][0], 1), 'y': round(pos[i][1], 1), 'r': OWN_R if i in own else NODE_R,
               'step': step[i], 'sector': 'WS.PEMS' if i in own else sector[i], 'repo': repo.get(i, 'WS.PEMS')} for i in nodes],
    'sectors': [{**s, 'start': round(s['start'], 4), 'end': round(s['end'], 4), 'mid': round(s['mid'], 4)} for s in sectors],
    'rings': RING, 'bracket': BRACKET,
}
json.dump(result, open(OUT, 'w'))
outside = sum(1 for i in sector if not (sec[sector[i]]['start'] - 1e-9 <= angle[i] <= sec[sector[i]]['end'] + 1e-9))
print(len(sectors), 'sectors;', sec[OTHER]['count'], 'packages in Other repositories;', outside, 'nodes outside their sector')
