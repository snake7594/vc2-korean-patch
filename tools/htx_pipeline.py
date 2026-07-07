#!/usr/bin/env python3
"""VC2 image (HTX) extract / re-insert pipeline.

Extracts EVERY texture (every HTSF sub-texture) in an ODIN.CPK extract to editable
PNG, and re-inserts edited PNGs into same-size CPK-encrypted HTX files. Re-inserting
an UNEDITED PNG is byte-identical to the original (indices are preserved), so
untouched images can never be corrupted.

  python htx_pipeline.py extract <ODIN_dir> <png_out_dir>
  python htx_pipeline.py insert  <ODIN_dir> <png_edited_dir> <htx_out_dir>

Naming: single-texture files -> <name>.HTX.png ; multi-texture files ->
<name>.HTX.p0.png, .p1.png, ...  (insert matches the same names back).
"""
import sys, os, glob, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vc2crypt as vc
import htx_tool as ht
from PIL import Image

def _png_names(name, npk):
    if npk == 1: return [name + '.png']
    return [f'{name}.p{i}.png' for i in range(npk)]

def extract(odin, out):
    os.makedirs(out, exist_ok=True)
    man = {}; ok = fail = tex = 0
    for p in sorted(glob.glob(os.path.join(odin, '*.HTX'))):
        name = os.path.basename(p)
        try:
            dec = vc.decrypt_resource(open(p, 'rb').read(), 0)
            pks = ht.iter_packets(dec)
            fns = _png_names(name, len(pks))
            info = []
            for pk, fn in zip(pks, fns):
                ht.decode_packet(dec, pk).save(os.path.join(out, fn))
                info.append(dict(png=fn, w=pk['w'], h=pk['h'], bpp=pk['bpp'], pal_n=pk['pal_n']))
                tex += 1
            man[name] = info; ok += 1
        except Exception as e:
            man[name] = dict(error=str(e)); fail += 1
    json.dump(man, open(os.path.join(out, 'manifest.json'), 'w'), indent=1)
    print(f'extract: {ok} files ({tex} textures) ok, {fail} fail -> {out}')

def insert(odin, png_dir, out):
    os.makedirs(out, exist_ok=True)
    changed = same = 0
    for p in sorted(glob.glob(os.path.join(odin, '*.HTX'))):
        name = os.path.basename(p)
        raw = open(p, 'rb').read()
        dec = vc.decrypt_resource(raw, 0)
        pks = ht.iter_packets(dec)
        fns = _png_names(name, len(pks))
        cur = dec; edited = False
        for pk, fn in zip(pks, fns):
            fp = os.path.join(png_dir, fn)
            if not os.path.exists(fp): continue
            cur = ht.encode_into(cur, pk, Image.open(fp).convert('RGBA'))
            edited = True
        if not edited or cur == dec:
            same += 1; continue
        open(os.path.join(out, name), 'wb').write(vc.encrypt_resource(raw[:16], cur))
        changed += 1; print(f'  edited: {name}')
    print(f'insert: {changed} changed, {same} unchanged -> {out}')

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(__doc__); sys.exit(1)
    if sys.argv[1] == 'extract': extract(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'insert': insert(sys.argv[2], sys.argv[3], sys.argv[4])
    else: print(__doc__); sys.exit(1)
