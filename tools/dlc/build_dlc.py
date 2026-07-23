# -*- coding: utf-8 -*-
"""Build Korean-patched VC2 DLC (v34): mission_XXX.mxe briefings/names AND the
content-list .MLX menu files (DL11 story mission, DL2B stickers).

Same-byte-length in-place injection: locate the MXEC packet containing the runs,
roll-decrypt its data region, replace runs (0x00 pad, space-trim to fit),
roll-encrypt (flag preserved), write back. File size / CPK TOC unchanged.
Korean encoded with the shipped main-patch font mapping (mapping_v17.json)."""
import sys, os, json, struct, shutil
sys.path.insert(0, '..'); sys.path.insert(0, '.')
import dlc_lib as dl, mxe_tool as mx, wansung_encode as we
from dlc_ko import TR as MISSION_TR
from dlc_mlx_ko import TR as MLX_TR

SRC = "D:/psp/Valkyria Chronicles 2 Japan [NPJH50145]/DLC/NPJH50145"
OUT = "out/NPJH50145"
MAP = json.load(open('../tl/mapping_v17.json', encoding='utf-8'))
MAPPED = set(MAP)
RAWM = json.load(open('dlc_missions_raw.json', encoding='utf-8'))
RAWX = json.load(open('dlc_mlx_raw.json', encoding='utf-8'))
BY_DLC = {RAWM[k]['dlc']: RAWM[k] for k in RAWM}

def _cost(ko, nl):
    return len(we.encode_ko(ko, MAP, nl=nl))

def _fit(ko, nb, nl):
    """encode_ko bytes <= nb; trim spaces right-to-left if needed."""
    if _cost(ko, nl) <= nb:
        return we.encode_ko(ko, MAP, nl=nl)
    idxs = [i for i, c in enumerate(ko) if c == ' ']
    for k in range(1, len(idxs) + 1):
        rm = set(idxs[-k:])
        t = ''.join(c for i, c in enumerate(ko) if not (c == ' ' and i in rm))
        if _cost(t, nl) <= nb:
            return we.encode_ko(t, MAP, nl=nl)
    raise AssertionError(f"cannot fit {ko!r} into {nb}B")

def _find_region(blob, first_off):
    """MXEC packet whose data region contains first_off -> (start,end,flags)."""
    i = 0
    while True:
        m = blob.find(b'MXEC', i)
        if m < 0:
            return None
        i = m + 4
        psz, hsz, flags = struct.unpack_from('<III', blob, m + 4)
        ds = struct.unpack_from('<I', blob, m + 0x14)[0]
        s = m + hsz; e = min(s + ds, len(blob))
        if s <= first_off < e:
            return s, e, flags

def patch_file(blob, runs, ko_list, log):
    s, e, flags = _find_region(blob, runs[0]['start'])
    plain = bytearray(mx.roll_decrypt(blob, s, e) if (flags & mx.ENC_FLAG) else blob)
    for r, ko in zip(runs, ko_list):
        st, nb = r['start'], r['nbytes']
        orig = bytes(plain[st:st + nb])
        nl = 'crlf' if b'\x0d\x0a' in orig else 'lf'
        enc = _fit(ko, nb, nl)
        plain[st:st + nb] = enc + b'\x00' * (nb - len(enc))
        log.append((st, nb, len(enc)))
    newbody = mx.roll_encrypt(bytes(plain), s, e) if (flags & mx.ENC_FLAG) else bytes(plain)
    out = bytearray(blob)
    out[s:e] = newbody[s:e]
    assert len(out) == len(blob) and bytes(out[:s]) == blob[:s] and bytes(out[e:]) == blob[e:]
    return bytes(out)

def build():
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(f"{SRC}/PARAM.PBP"):
        shutil.copyfile(f"{SRC}/PARAM.PBP", f"{OUT}/PARAM.PBP")
    # map DLC code -> list of (filename, runs, ko_list)
    jobs = {}
    for dcode, ko in MISSION_TR.items():
        m = BY_DLC[dcode]
        jobs.setdefault(dcode, []).append((m['file'], m['runs'], ko))
    for key, ko in MLX_TR.items():
        dcode, fname = key.split('/')
        jobs.setdefault(dcode, []).append((fname, RAWX[key]['runs'], ko))

    total = 0
    for dcode in sorted(os.listdir(SRC)):
        sp = os.path.join(SRC, dcode)
        if not os.path.isdir(sp):
            continue
        dout = os.path.join(OUT, dcode); os.makedirs(dout, exist_ok=True)
        # copy marker .EDAT (non _DATA) unchanged
        for fn in os.listdir(sp):
            if fn.lower().endswith('.edat') and not fn.lower().endswith('_data.edat'):
                shutil.copyfile(os.path.join(sp, fn), os.path.join(dout, fn))
        data = os.path.join(sp, dcode + "_DATA.EDAT")
        raw, files = dl.cpk_files(data)
        raw = bytearray(raw)
        for fname, runs, ko in jobs.get(dcode, []):
            fi = [f for f in files if f['name'] == fname][0]
            off, size = fi['off'], fi['size']
            blob = bytes(raw[off:off + size])
            log = []
            newblob = patch_file(blob, runs, ko, log)
            assert len(newblob) == size
            raw[off:off + size] = newblob
            total += len(log)
            print(f"  {dcode}/{fname}: {len(log)} runs")
        open(os.path.join(dout, dcode + "_DATA.EDAT"), 'wb').write(bytes(raw))
    print(f"\nDONE: {total} runs injected -> {OUT}/")

if __name__ == '__main__':
    build()
