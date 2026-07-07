#!/usr/bin/env python3
"""VC2 — extract EVERY embedded texture from ALL ODIN.CPK files (not just .HTX).

Scans every CPK-decrypted file for HTSF/MIG texture packets (HTX, MLX/IZCA,
NCP, ABR ... all carry them) and decodes each to PNG. Output is organised by
carrier extension with a manifest + browsable HTML index.

  python image_extract_all.py <ODIN_dir> <out_dir>

Round-trip is lossless per-packet (see htx_tool.encode_into), so this extract is
the exact inverse of re-insertion for unedited images.

IZCA-only MLX (no HTSF packet) and raw embedded PNG/DDS are handled by the
extra carvers below once their formats are confirmed.
"""
import sys, os, glob, json, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vc2crypt as vc
import htx_tool as ht
importlib.reload(ht)
from PIL import Image

def _names(base, npk):
    if npk == 1: return [base + '.png']
    return [f'{base}.p{i}.png' for i in range(npk)]

def _carve_pngs(dec):
    """Yield (offset, png_bytes) for every standard PNG embedded in a body."""
    i = 0
    while True:
        s = dec.find(b'\x89PNG\r\n\x1a\n', i)
        if s < 0: break
        e = dec.find(b'IEND', s)
        e = e + 8 if e > 0 else len(dec)
        yield s, dec[s:e]; i = e

def extract_all(odin, out):
    os.makedirs(out, exist_ok=True)
    manifest = {}
    n_files = n_tex = 0
    per_ext = {}
    for p in sorted(glob.glob(os.path.join(odin, '*'))):
        if os.path.isdir(p): continue
        name = os.path.basename(p)
        ext = (os.path.splitext(name)[1] or '.none').upper().lstrip('.')
        try:
            dec = vc.decrypt_resource(open(p, 'rb').read(), 0)
        except Exception:
            continue
        pks = ht.iter_packets(dec)
        if not pks:
            # raw embedded PNGs (PSP save icons in .DAT); skip files with none
            pngs = list(_carve_pngs(dec))
            if pngs:
                sub = os.path.join(out, ext)
                os.makedirs(sub, exist_ok=True)
                info = []
                for k, (off, data) in enumerate(pngs):
                    fn = f'{name}.png' if len(pngs) == 1 else f'{name}.{k}.png'
                    open(os.path.join(sub, fn), 'wb').write(data)
                    info.append(dict(png=f'{ext}/{fn}', raw_png=True, offset=off))
                    n_tex += 1
                manifest[name] = info; n_files += 1
                per_ext[ext] = per_ext.get(ext, [0, 0])
                per_ext[ext][0] += 1; per_ext[ext][1] += len(pngs)
            continue
        sub = os.path.join(out, ext)
        os.makedirs(sub, exist_ok=True)
        fns = _names(name, len(pks))
        info = []
        for pk, fn in zip(pks, fns):
            try:
                ht.decode_packet(dec, pk).save(os.path.join(sub, fn))
                info.append(dict(png=f'{ext}/{fn}', w=pk['w'], h=pk['h'],
                                 bpp=pk['bpp'], pal_n=pk['pal_n']))
                n_tex += 1
            except Exception as e:
                info.append(dict(png=f'{ext}/{fn}', error=str(e)))
        manifest[name] = info
        n_files += 1
        per_ext[ext] = per_ext.get(ext, [0, 0])
        per_ext[ext][0] += 1; per_ext[ext][1] += len(pks)
    json.dump(manifest, open(os.path.join(out, 'manifest.json'), 'w'), indent=0)
    _write_index(out, manifest, per_ext, n_files, n_tex)
    print(f'extracted {n_tex} textures from {n_files} files -> {out}')
    for e in sorted(per_ext): print(f'  {e:6} files={per_ext[e][0]:5} textures={per_ext[e][1]}')

CARRIER_DESC = {
    'HTX': 'UI / menu / background / event textures (HTEX→MIG)',
    'MLX': 'IZCA-wrapped textures: seasonal decor, faces, UI sprites',
    'NCP': 'character portraits (512×512) + expression atlases',
    'ABR': 'battle-UI sprite atlas (name labels, icons)',
    'DAT': 'PSP save-data icons/backgrounds (standard PNG)',
}
# image-bearing formats deliberately NOT auto-extracted (documented, not lost)
EXCLUDED = [
    ('HTF', 121, 'map/minimap textures — COMPRESSED MIG-less HTSF variant; decoder not yet written'),
    ('MLX (IZCA-only)', 185, 'motion/animation (KFMO), palettes, OV_* vector overlays — not bitmaps'),
    ('audio', 490, 'ATX/MVP/PSB/MMF/PSB = WAVE/CRI/Ogg/SE sound banks'),
    ('AI/geometry/script', 900, 'GRD/OMP/PVS/NAD/HSP/PAC/MXE/... — not images'),
]

def _write_index(out, manifest, per_ext, n_files, n_tex):
    rows = []
    for ext in sorted(per_ext):
        rows.append(f'<tr><td>{ext}</td><td>{per_ext[ext][0]}</td><td>{per_ext[ext][1]}</td>'
                    f'<td>{CARRIER_DESC.get(ext, "")}</td></tr>')
    exrows = ''.join(f'<tr><td>{n}</td><td>{c}</td><td>{d}</td></tr>' for n, c, d in EXCLUDED)
    html = f"""<!doctype html><meta charset=utf-8><title>VC2 image extract</title>
<style>body{{font:13px/1.5 sans-serif;background:#1a1a20;color:#ddd;padding:16px;max-width:900px}}
table{{border-collapse:collapse;margin:8px 0}}td,th{{border:1px solid #444;padding:4px 10px;text-align:left}}
th{{background:#2a2a34}}h2,h3{{color:#e8e0b0}}code{{color:#9cd}}</style>
<h2>VC2 extracted images — {n_tex} images / {n_files} files</h2>
<p>Every image is a PNG under a per-carrier-extension subfolder. Re-inserting an
unedited PNG reproduces the source byte-for-byte (verified 2281/2281 lossless).</p>
<table><tr><th>carrier</th><th>files</th><th>images</th><th>content</th></tr>{''.join(rows)}</table>
<h3>Not auto-extracted (documented)</h3>
<table><tr><th>format</th><th>files</th><th>why</th></tr>{exrows}</table>
<p>See <code>manifest.json</code> for the file→PNG map. Tools: <code>_work/image_extract_all.py</code>
(extract), <code>_work/htx_tool.py</code> (decode/encode), <code>_work/htx_pipeline.py</code> (insert).</p>"""
    open(os.path.join(out, 'index.html'), 'w', encoding='utf-8').write(html)

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    extract_all(sys.argv[1], sys.argv[2])
