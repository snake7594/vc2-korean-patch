#!/usr/bin/env python3
"""MXE (MXEN/MXEC) text tool for VC2 Korean patch.

File layout (after file-level decrypt_resource):
  MXEN packet hdr (0x20) -> MXEC packet @0x20: [magic][psz][hsz=0x20][flags]...
  flags bit 0x40000 = body is ROLLING-XOR encrypted: plain[i] = enc[i] ^ enc[i-1]
  (vc3_formats.txt L279-287). First byte stays as-is.

Strategy: decrypt rolling XOR -> same-length Korean run replacement (like
nested_runs) -> re-encrypt rolling XOR forward -> file-level re-encrypt.
Byte length and all offsets preserved; flags unchanged.
"""
import struct, sys
sys.path.insert(0, '_work')
import vc2crypt as vc

ENC_FLAG = 0x40000

def parse_packets(dec):
    """Yield (offset, magic, psz, hsz, flags) for top-level packets."""
    out = []
    i = 0
    while i + 0x10 <= len(dec):
        magic = dec[i:i+4]
        if not all(0x20 <= b < 0x7f for b in magic):
            break
        psz, hsz, flags = struct.unpack_from('<III', dec, i+4)
        out.append((i, magic.decode(), psz, hsz, flags))
        if magic == b'EOFC':
            break
        if magic in (b'MXEN',):        # container: descend
            i += hsz
        else:
            i += hsz + psz
            i = (i + 15) & ~15 if False else i
    return out

def roll_decrypt(buf, start, end):
    """plain[i] = enc[i] ^ enc[i-1] for i in (start, end); buf[start] unchanged."""
    out = bytearray(buf)
    for i in range(end-1, start, -1):
        out[i] = buf[i] ^ buf[i-1]
    return bytes(out)

def roll_encrypt(buf, start, end):
    """enc[i] = plain[i] ^ enc[i-1] forward; buf[start] unchanged."""
    out = bytearray(buf)
    for i in range(start+1, end):
        out[i] = buf[i] ^ out[i-1]
    return bytes(out)

def body_range(dec):
    """Return (start, end, flags_off) of the MXEC ROLL-ENCRYPTED DATA region, or None.
    The roll region is ONLY the data (size = datasize @ MXEC+0x14), NOT the trailing
    POF0/ENRS/CCRS relocation packets — those are appended AFTER and are read
    un-roll-decrypted by the game. (Earlier bug: using the whole packet size (psz)
    made re-encryption chain-propagate into POF0/ENRS -> corrupted relocation -> crash.)"""
    if dec[:4] != b'MXEN':
        return None
    if dec[0x20:0x24] != b'MXEC':
        return None
    psz, hsz, flags = struct.unpack_from('<III', dec, 0x24)
    datasize = struct.unpack_from('<I', dec, 0x20 + 0x14)[0]
    start = 0x20 + hsz
    end = min(start + datasize, 0x20 + hsz + psz, len(dec))
    return start, end, 0x2c, flags

def decrypt_file(raw):
    """raw (CPK-encrypted MXE) -> (dec_plainbody, meta). meta needed for re-encrypt."""
    dec = vc.decrypt_resource(raw, 0)
    br = body_range(dec)
    if br is None:
        return None, None
    start, end, foff, flags = br
    enc_body_orig = dec[start:end]
    if flags & ENC_FLAG:
        plain = roll_decrypt(dec, start, end)
    else:
        plain = dec
    return plain, dict(start=start, end=end, foff=foff, flags=flags,
                       key16=raw[:16], enc_body_orig=enc_body_orig)

def encrypt_file(plain, meta):
    """plain (modified, same length) -> CPK-encrypted bytes ready to ship."""
    start, end, flags = meta['start'], meta['end'], meta['flags']
    if flags & ENC_FLAG:
        # forward rolling encrypt; first byte identical to original cipher first byte
        out = roll_encrypt(plain, start, end)
    else:
        out = plain
    return vc.encrypt_resource(meta['key16'], bytes(out))

def encrypt_file_plainbody(plain, meta):
    """Ship the body PLAINTEXT with the MXEC 0x40000 encryption flag CLEARED
    (the configuration the Russian fan patch ships — the game then skips the
    rolling-XOR decrypt and any integrity check tied to it). File-level CPK
    encryption is still applied on top."""
    out = bytearray(plain)
    flags = struct.unpack_from('<I', out, 0x2c)[0]
    struct.pack_into('<I', out, 0x2c, flags & ~ENC_FLAG)
    return vc.encrypt_resource(meta['key16'], bytes(out))

# ---- text runs (same approach as nested_runs, over the whole plain body) ----
def _valid_fw(b, i):
    if i + 1 >= len(b):
        return 0
    c, t = b[i], b[i+1]
    lead = (0x81 <= c <= 0x9f) or (0xe0 <= c <= 0xfc)
    trail = (0x40 <= t <= 0x7e) or (0x80 <= t <= 0xfc)
    return 2 if (lead and trail) else 0

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
        else: out.append(chr(c) if 0x20 <= c < 0x7f else '?'); i += 1
    return ''.join(out)

def extract_runs(plain, start, end, min_chars=2):
    """Maximal runs of full-width SJIS + newlines + embedded ASCII inside the body.
    A run must contain >= min_chars JP full-width chars to be a translation target."""
    runs = []
    i = start
    while i < end:
        if _valid_fw(plain, i):
            rs = i; jp = 0; i += 2; jp += 1
            while i < end:
                a = _valid_fw(plain, i)
                if a:
                    i += 2; jp += 1
                elif plain[i] == 0x0a:
                    i += 1
                elif plain[i] == 0x0d and i+1 < end and plain[i+1] == 0x0a:
                    i += 2
                elif 0x20 <= plain[i] < 0x7f and (i+1 < end and (_valid_fw(plain, i+1) or (0x20 <= plain[i+1] < 0x7f and i+2 < end and _valid_fw(plain, i+2)))):
                    # short ASCII bridge (e.g. 'B案', 'ND-1') inside JP text
                    i += 1
                else:
                    break
            seg = plain[rs:i]
            # verify decodes as SJIS with kana/kanji
            try:
                t = seg.replace(b'\x0d\x0a', b'\n').replace(b'\x0a', b'\n').decode('shift_jis')
                has_jp = any('぀' <= ch <= 'ヿ' or '一' <= ch <= '鿿' or ch in '「」『』、。・…―ー' for ch in t)
            except Exception:
                has_jp = False; t = None
            if has_jp and jp >= min_chars:
                runs.append(dict(start=rs, nbytes=len(seg), text=_readable(seg), nchars=jp))
        else:
            i += 1
    return runs
