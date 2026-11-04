"""Write the @font-face rules for the page: DejaVu Sans regular and bold, the font of the thesis figures.

    python3 -I scripts/fonts.py scripts/fonts.css

Takes the two TrueType files that matplotlib ships (mpl-data/fonts/ttf), keeps Basic Latin, Latin-1 and the few
signs the page uses (– — ’ “ ” … ≥ ×), and embeds them as WOFF data: URIs, about 65 KiB together.
Needs matplotlib and fontTools (pyftsubset). DejaVu Sans is under the Bitstream Vera licence, which allows this.
"""
import base64, os, subprocess, sys, tempfile

import matplotlib

OUT = sys.argv[1]
TTF = os.path.join(os.path.dirname(matplotlib.__file__), 'mpl-data', 'fonts', 'ttf')
UNICODES = 'U+0020-007E,U+00A0-00FF,U+2013,U+2014,U+2019,U+201C,U+201D,U+2026,U+2265,U+00D7'
rules = []
with tempfile.TemporaryDirectory() as tmp:
    for name, weight in (('DejaVuSans', 400), ('DejaVuSans-Bold', 700)):
        woff = os.path.join(tmp, name + '.woff')
        subprocess.run(['pyftsubset', os.path.join(TTF, name + '.ttf'), f'--unicodes={UNICODES}', '--flavor=woff',
                        '--layout-features=kern,liga', f'--output-file={woff}'], check=True, capture_output=True)
        data = base64.b64encode(open(woff, 'rb').read()).decode()
        rules.append(f"@font-face {{ font-family: 'DejaVu Sans'; font-weight: {weight}; font-style: normal; "
                     f"font-display: swap; src: url(data:font/woff;base64,{data}) format('woff'); }}")
open(OUT, 'w').write('\n'.join(rules) + '\n')
print(OUT, os.path.getsize(OUT) // 1024, 'KiB')
