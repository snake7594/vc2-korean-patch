#!/usr/bin/env python3
"""Rebuild the VC2 Korean patch files from an editable translations.json.

Edit the "ko" values in translations.json (see this folder's README), then run:

    python rebuild.py  <ODIN_extract_dir>  <korean_font.ttf>  [out_dir]

- <ODIN_extract_dir> : folder of the game's ODIN.CPK files extracted with YACpkTool
                       (encrypted, as they come out of the CPK). YOU supply these from
                       YOUR OWN legal copy of the game. No game data ships with this repo.
- <korean_font.ttf>  : any Korean TrueType font (e.g. a free public font).
- [out_dir]          : where the patched files are written (default: ./patched_out).

Then copy out_dir/* over your ODIN extract, repack with YACpkTool, and inject with
UMD-replace (see ../docs/TECHNICAL.md §8). Every output file is the SAME SIZE as the
original, so you can also patch the CPK in place for a tiny xdelta.

Needs the modules in ../tools on the path, plus Pillow:  pip install pillow
"""
import sys, os, json, struct
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'tools'))
import vc2crypt as vc, mtpa_edit as me, wansung_encode as we, mxe_tool as mx
import vc2_font2b as v2, vc2_hangul_patch as hp

def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(1)
    ODIN = sys.argv[1]
    TTF  = sys.argv[2]
    OUT  = sys.argv[3] if len(sys.argv) > 3 else os.path.join(HERE, 'patched_out')
    os.makedirs(OUT, exist_ok=True)
    tr = json.load(open(os.path.join(HERE, 'translations.json'), encoding='utf-8'))

    # ---- 1) build font + mapping from EVERY Korean syllable actually used ----
    def all_ko():
        for f, recs in tr['records'].items():
            for e in recs.values(): yield e['ko']
        for f, runs in tr['runs'].items():
            for e in runs: yield e['ko']
    syls = we.collect_syllables(all_ko())
    base_font_dec = vc.decrypt_resource(open(os.path.join(ODIN, 'ODIN_FONT_16.BF1'), 'rb').read(), 0)
    tmp_dec = os.path.join(OUT, '_font_base.dec')
    open(tmp_dec, 'wb').write(base_font_dec)
    mapping = we.build_mapping(syls, tmp_dec)
    dec_out = os.path.join(OUT, '_font.dec')
    n = we.build_font(tmp_dec, dec_out, mapping, fontpath=TTF)
    fkey = open(os.path.join(ODIN, 'ODIN_FONT_16.BF1'), 'rb').read()[:16]
    open(os.path.join(OUT, 'ODIN_FONT_16.BF1'), 'wb').write(
        vc.encrypt_resource(fkey, open(dec_out, 'rb').read()))
    os.remove(tmp_dec); os.remove(dec_out)
    print(f'font: {n} syllables mapped')

    def enc_fit(ko, nbytes, nl):
        try: e = we.encode_ko(ko, mapping, nl=nl)
        except we.EncodeError: return None
        if len(e) <= nbytes: return e
        t = ko.rstrip()
        while t and len(we.encode_ko(t, mapping, nl=nl)) > nbytes: t = t[:-1].rstrip()
        return we.encode_ko(t, mapping, nl=nl) if t else None

    files = set(tr['records']) | set(tr['runs'])
    for name in sorted(files):
        raw = open(os.path.join(ODIN, name), 'rb').read()
        if name.endswith('.MXE'):
            plain, meta = mx.decrypt_file(raw)
            buf = bytearray(plain)
            for e in tr['runs'].get(name, []):
                if e['start'] >= meta['end']: continue      # never touch POF0/ENRS reloc region
                nl = 'crlf' if b'\x0d\x0a' in plain[e['start']:e['start']+e['nbytes']] else 'lf'
                enc = enc_fit(e['ko'], e['nbytes'], nl)
                if enc is None: continue
                buf[e['start']:e['start']+e['nbytes']] = enc + b'\x00'*(e['nbytes']-len(enc))
            open(os.path.join(OUT, name), 'wb').write(mx.encrypt_file(bytes(buf), meta))
        else:  # MTP
            body = vc.decrypt_resource(raw, 0)
            # a) clean records via rebuild_inplace
            recs = tr['records'].get(name, {})
            repl = {}
            if recs:
                pays = me.get_payloads(body)
                for rec, e in recs.items():
                    rec = int(rec)
                    nl = 'crlf' if b'\x0d\x0a' in pays[rec] else 'lf'
                    enc = enc_fit(e['ko'], len(pays[rec]), nl)
                    if enc is not None and we.fits(len(enc), len(pays[rec])): repl[rec] = enc
                body = bytearray(me.rebuild_inplace(bytes(body), repl))
            else:
                body = bytearray(body)
            # b) same-length runs (nested / cleanfix / sys)
            for e in tr['runs'].get(name, []):
                s, nb = e['start'], e['nbytes']
                seg = bytes(((body[s+i]-1) & 0xff) for i in range(nb))
                nl = 'crlf' if b'\x0d\x0a' in seg else 'lf'
                if e['src'] == 'sys':                        # {MS}=0x8765 gaiji preserved
                    out = bytearray()
                    for i, part in enumerate(e['ko'].split('{MS}')):
                        if i: out += bytes([0x87, 0x65])
                        out += we.encode_ko(part, mapping, nl=nl)
                    enc = bytes(out) if len(out) <= nb else None
                else:
                    enc = enc_fit(e['ko'], nb, nl)
                if enc is None: continue
                rep = enc + b'\x20'*(nb-len(enc))
                body[s:s+nb] = bytes(((b+1) & 0xff) for b in rep)
            open(os.path.join(OUT, name), 'wb').write(vc.encrypt_resource(raw[:16], bytes(body)))
    print(f'wrote {len(files)+1} patched files to {OUT}')
    print('Next: copy these over your ODIN extract, repack (YACpkTool), inject (UMD-replace).')

if __name__ == '__main__':
    main()
