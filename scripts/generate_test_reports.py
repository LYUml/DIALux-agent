"""Regenerate redistributable synthetic PDF fixtures (requires reportlab)."""
import hashlib
import json
from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'tests/fixtures/reports'


def generate():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    # Use the Windows font's document embedding permission. Only embedded PDF
    # subsets are distributed, never the system font file itself.
    font = Path('C:/Windows/Fonts/arial.ttf')
    pdfmetrics.registerFont(TTFont('FixtureText', str(font)))
    cases = {
        'three-rooms': (39, [(15, 'A', 24, 0, '-', 0), (20, 'B', 24, 693, .57, 9.75), (28, 'C', 24, 0, '-', 0)]),
        'two-lit-rooms': (42, [(15, 'A', 24, 531, .57, 6.5), (23, 'B', 24, 693, .59, 9.75), (31, 'C', 24, 0, '-', 0)]),
        'full-document': (28, [(14, 'Office', 24, 104, .21, 1.08)]),
        'summary-v1': (2, [(1, 'Office', 24, 104, .20, 1.08)]),
        'summary-v2': (2, [(1, 'Office', 24, 104, .22, 1.08)]),
        'concave-area': (24, [(14, 'Concave area', 20, 493, .55, 6.5)]),
    }
    manifest = {}
    for name, (count, rooms) in cases.items():
        path = OUTPUT/f'{name}.pdf'
        canvas = Canvas(str(path), pagesize=(595, 842), invariant=1, pageCompression=1)
        canvas.setTitle('Synthetic parser fixture - '+name)
        canvas.setAuthor('DIALux-agent contributors')
        summaries = {}
        for page, room, area, illuminance, uniformity, power in rooms:
            header = f'Synthetic Building · Synthetic Storey · {room} (Light scene 1)\nSummary\n'
            summaries[page] = header+f'Ground area {area:.2f} m² Clearance height 3.000 m\nHeight Working plane 0.800 m'
            summaries[page+1] = header+f'Results\nWorking plane Ēperpendicular {illuminance} lx ≥ 500 lx WP1\nUo (g1) {uniformity} ≥ 0.60 WP1\nSpace Lighting power density {power} W/m² –'
        for page in range(1, count+1):
            text = canvas.beginText(36, 800)
            text.setFont('FixtureText', 10)
            text.setLeading(18)
            text.textLine('SYNTHETIC TEST DATA - NOT A DIALUX SIMULATION')
            text.textLine('')
            for line in summaries.get(page, 'Synthetic filler page').splitlines():
                text.textLine(line)
            canvas.drawText(text)
            canvas.setFont('FixtureText', 9)
            canvas.drawString(36, 30, f'Fixture {name} | Page {page} of {count}')
            canvas.showPage()
        canvas.save()
        manifest[name] = {'file': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'pages': count}
    (OUTPUT/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    generate()
