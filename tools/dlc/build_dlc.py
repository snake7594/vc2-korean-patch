# -*- coding: utf-8 -*-
"""Build Korean-patched VC2 DLC.

For each DLxx_DATA.EDAT (plain CPK): locate each mission_XXX.mxe, roll-decrypt
its MXEC data region, replace the player-facing runs with Korean (same byte
length, 0x00 pad), roll-encrypt (flag preserved), write back IN PLACE. CPK TOC
and every other byte untouched -> output file has identical size & structure.

Korean is encoded with the SHIPPED main-patch font mapping (tl/mapping_v17.json)
so glyphs render against the already-patched ODIN_FONT_16.BF1 in the main ISO.

Output mirrors the input tree under out/NPJH50145/ as a drop-in replacement.
"""
import sys, os, json, struct, shutil
sys.path.insert(0, '..'); sys.path.insert(0, '.')
import dlc_lib as dl, mxe_tool as mx, wansung_encode as we
from dlc_ko import TR

SRC  = "D:/psp/Valkyria Chronicles 2 Japan [NPJH50145]/DLC/NPJH50145"
OUT  = "out/NPJH50145"
MAP  = json.load(open('../tl/mapping_v17.json', encoding='utf-8'))
RAWM = json.load(open('dlc_missions_raw.json', encoding='utf-8'))
BY_DLC = {RAWM[k]['dlc']: RAWM[k] for k in RAWM}

def patch_blob(blob, runs, ko_list, log):
    """Return new blob (same length) with Korean runs injected."""
    info = dl.find_mxen(blob)
    assert info, "no MXEN"
    plain = bytearray(dl.decode_body(blob, info))          # roll-decrypted copy
    start, end, flags = info['start'], info['end'], info['flags']
    for r, ko in zip(runs, ko_list):
        s, nb = r['start'], r['nbytes']
        orig = bytes(plain[s:s+nb])
        nl = 'crlf' if b'\x0d\x0a' in orig else 'lf'
        enc = we.encode_ko(ko, MAP, nl=nl)
        assert len(enc) <= nb, f"overflow {len(enc)}/{nb}"
        plain[s:s+nb] = enc + b'\x00' * (nb - len(enc))
        log.append((s, nb, len(enc), ko[:16]))
    # re-encrypt only the data region, flag preserved
    if flags & mx.ENC_FLAG:
        newbody = mx.roll_encrypt(bytes(plain), start, end)
    else:
        newbody = bytes(plain)
    # splice: outside [start,end) must be byte-identical to original blob
    out = bytearray(blob)
    out[start:end] = newbody[start:end]
    assert len(out) == len(blob)
    assert bytes(out[:start]) == blob[:start] and bytes(out[end:]) == blob[end:]
    return bytes(out)

def build():
    os.makedirs(OUT, exist_ok=True)
    # top-level PARAM.PBP copied as-is
    if os.path.exists(f"{SRC}/PARAM.PBP"):
        shutil.copyfile(f"{SRC}/PARAM.PBP", f"{OUT}/PARAM.PBP")
    total_runs = 0
    for dcode in sorted(TR):
        m = BY_DLC[dcode]
        din = os.path.join(SRC, dcode)
        dout = os.path.join(OUT, dcode); os.makedirs(dout, exist_ok=True)
        # copy the small marker DLxx.EDAT unchanged
        for fn in os.listdir(din):
            if fn.lower().endswith('.edat') and not fn.lower().endswith('_data.edat'):
                shutil.copyfile(os.path.join(din, fn), os.path.join(dout, fn))
        data = os.path.join(din, dcode + "_DATA.EDAT")
        raw, files = dl.cpk_files(data)
        raw = bytearray(raw)
        fi = [f for f in files if f['name'] == m['file']][0]
        off, size = fi['off'], fi['size']
        blob = bytes(raw[off:off+size])
        log = []
        newblob = patch_blob(blob, m['runs'], TR[dcode], log)
        assert len(newblob) == size
        raw[off:off+size] = newblob
        open(os.path.join(dout, dcode + "_DATA.EDAT"), 'wb').write(bytes(raw))
        total_runs += len(log)
        print(f"  {dcode}/{m['file']}: {len(log)} runs injected  (file {size}B unchanged)")
    print(f"\nDONE: {len(TR)} DLC, {total_runs} runs -> {OUT}/")

if __name__ == '__main__':
    build()
