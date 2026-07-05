#!/usr/bin/env python3
"""Structure-agnostic translation for the 5 NESTED MTPA files (EV30000/30100/30152/
EV50001/SLG_EV) whose text_pos does not uniformly point to [len][text].

Strategy: operate on the -1 text pool as a byte buffer. Find maximal runs of
full-width Japanese text (+ internal newlines). Replace each run with Korean encoded
to EXACTLY the same byte length (space-padded). Byte count is preserved, so every
length header / offset in the container stays valid -> cannot corrupt structure.
"""
import sys, struct
sys.path.insert(0, '_work')
import vc2crypt as vc, mtpa_edit as me, wansung_encode as we

def _valid_fw(b, i):
    """Is pool[i:i+2] a valid full-width SJIS char? return 2 if yes else 0."""
    if i + 1 >= len(b):
        return 0
    c, t = b[i], b[i+1]
    lead = (0x81 <= c <= 0x9f) or (0xe0 <= c <= 0xfc)
    trail = (0x40 <= t <= 0x7e) or (0x80 <= t <= 0xfc)
    return 2 if (lead and trail) else 0

def extract_runs(pool):
    """-> list of dict(start, nbytes, text, nchars). A run = maximal seq of full-width
    SJIS chars and internal newlines (0x0a, or 0x0d0a). Runs must contain >=1 fw char."""
    runs = []
    i = 0; n = len(pool)
    while i < n:
        adv = _valid_fw(pool, i)
        if adv:
            start = i; has_fw = True; i += adv
            # extend over fw chars and newlines
            while i < n:
                a = _valid_fw(pool, i)
                if a:
                    i += a
                elif pool[i] == 0x0a:
                    i += 1
                elif pool[i] == 0x0d and i+1 < n and pool[i+1] == 0x0a:
                    i += 2
                else:
                    break
            # trim trailing newlines out of the run (keep them structural-safe inside though)
            seg = pool[start:i]
            runs.append(dict(start=start, nbytes=len(seg), text=_readable(seg),
                             nchars=_count_fw(seg)))
        else:
            i += 1
    return runs

def _readable(seg):
    out = []; i = 0
    while i < len(seg):
        c = seg[i]
        if c == 0x0a: out.append('\n'); i += 1
        elif c == 0x0d and i+1 < len(seg) and seg[i+1] == 0x0a: out.append('\n'); i += 2
        elif _valid_fw(seg, i):
            try: out.append(bytes(seg[i:i+2]).decode('shift_jis'))
            except: out.append('?')
            i += 2
        else: out.append('?'); i += 1
    return ''.join(out)

def _count_fw(seg):
    i = 0; n = 0
    while i < len(seg):
        if _valid_fw(seg, i): n += 1; i += 2
        elif seg[i] == 0x0d and i+1 < len(seg) and seg[i+1] == 0x0a: i += 2
        else: i += 1
    return n

def encode_exact(ko, mapping, nbytes, nl='lf'):
    """Encode Korean to EXACTLY nbytes (space-pad). Raise if it overflows nbytes."""
    enc = we.encode_ko(ko, mapping, nl=nl)
    if len(enc) > nbytes:
        raise we.EncodeError(f'{len(enc)}B > {nbytes}B run')
    return enc + b'\x20' * (nbytes - len(enc))

def inject_runs(pool, runs, translations, mapping):
    """translations: {run_index: korean}. Replace each run in place, same nbytes.
    Returns (new_pool, n_applied, overflow_list)."""
    out = bytearray(pool)
    applied = 0; overflow = []
    for idx, ko in translations.items():
        r = runs[idx]
        nl = 'crlf' if b'\x0d\x0a' in pool[r['start']:r['start']+r['nbytes']] else 'lf'
        try:
            enc = encode_exact(ko, mapping, r['nbytes'], nl=nl)
        except we.EncodeError as e:
            overflow.append((idx, str(e))); continue
        out[r['start']:r['start']+r['nbytes']] = enc
        applied += 1
    return bytes(out), applied, overflow

def file_pool(base, FRESH='C:/vc2work/ODIN_fresh'):
    raw = open(f'{FRESH}/{base}.MTP', 'rb').read()
    body = vc.decrypt_resource(raw, 0)
    m = me.parse(body)
    pool = bytes(((b-1) & 0xff) for b in body[m['p_textseg']:])
    return raw, body, m, pool

def repack(base, new_pool, body, m, raw, out_dir='_work/patched', FRESH='C:/vc2work/ODIN_fresh'):
    """Rebuild body with new (+1 re-encoded) pool, re-encrypt."""
    enc_pool = bytes(((b+1) & 0xff) for b in new_pool)
    new_body = bytearray(body)
    new_body[m['p_textseg']:] = enc_pool           # same length -> everything else intact
    key = raw[:16]
    import os; os.makedirs(out_dir, exist_ok=True)
    open(f'{out_dir}/{base}.MTP', 'wb').write(vc.encrypt_resource(key, bytes(new_body)))
    return len(new_body) == len(body)
