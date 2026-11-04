"""Write the page: one self-contained HTML file with the graph, the layout, the texts and the font.

    python3 -I scripts/page.py results scripts/template.html scripts/fonts.css dependency-graph.html [--fragment]

Reads graph.json, layout.json, descriptions.json and reasons.json from the results folder. The template holds the
page's CSS and JavaScript; /*DATA*/null and /*FONTS*/ mark where the data and the @font-face rules go. The output
is a complete HTML document that opens in a browser without a network. With --fragment, the <!doctype>, <head>
and <body> are left out (the form a claude.ai page takes).
"""
import json, os, sys

args = [a for a in sys.argv[1:] if not a.startswith('--')]
FRAGMENT = '--fragment' in sys.argv
RESULTS, TEMPLATE, FONTS, OUT = args

load = lambda name: json.load(open(os.path.join(RESULTS, name)))
g, lay, desc, reasons = (load(n) for n in ('graph.json', 'layout.json', 'descriptions.json', 'reasons.json'))
KEEP = ('id', 'name', 'version', 'kind', 'repo', 'via', 's2a', 's2b')  # only the fields the page reads
pos = {n['id']: n for n in lay['nodes']}
nodes = []
for n in g['nodes']:
    d = {k: n[k] for k in KEEP if n.get(k) not in (None, '')}
    p = pos[n['id']]
    d.update(x=p['x'], y=p['y'], r=p['r'], step=p['step'], sector=p['sector'])
    d.update(desc.get(n['id'], {}))
    d.update(reasons.get(n['id'], {}))
    nodes.append(d)
data = {'nodes': nodes, 'edges': g['edges'], 'sectors': lay['sectors'], 'rings': lay['rings'], 'bracket': lay['bracket']}

page = open(TEMPLATE).read()
page = page.replace('/*DATA*/null', json.dumps(data, separators=(',', ':'), ensure_ascii=False))
page = page.replace('/*FONTS*/', open(FONTS).read())
if not FRAGMENT:
    head, body = page.split('</style>', 1)
    head = head.replace('<meta name="claude:viewport-fit-sides" content="cover">\n', '')
    page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            f'{head}\nbody {{ margin: 0; }}\n[hidden] {{ display: none !important; }}\n</style>\n</head>\n<body>\n'
            f'{body.lstrip()}\n</body>\n</html>\n')
open(OUT, 'w', encoding='utf-8').write(page)
print(OUT, len(page.encode()) // 1024, 'KiB')
