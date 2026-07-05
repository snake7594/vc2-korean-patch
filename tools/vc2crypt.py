#!/usr/bin/env python3
"""
VC2 (Valkyria Chronicles 2, NPJH50145) per-file resource crypto — SOLVED.

A CPK file contains one or more independently-encrypted RESOURCES.
Each resource: the first 16 bytes are a key; then a continuous keystream XOR:
    key[i%4] = (key[i%4]*3 + 1) mod 2**32 ; out[i] = data[i] ^ key[i%4]
(over 32-bit little-endian words; a sub-16-byte tail is XORed by key[0]&0xff).
The main data resource almost always begins at file offset 0x800 (a 2KB
header/directory precedes it). Resources are found by trying each offset and
checking whether the first decrypted word is a known packet magic.

The transform is a pure XOR keystream => symmetric: the same routine decrypts
and re-encrypts. Editing a resource's body and re-encrypting with the SAME key
(the resource's original first 16 bytes) reproduces valid ciphertext. This is
what makes translation injection possible without formalizing anything further.
"""
import struct

M = 0x100000000
MAGICS = {b'MTPA',b'MXEC',b'EOFC',b'ENRS',b'POF0',b'CCRS',b'OCRP',b'HMOT',
          b'MXTF',b'BPRS',b'CCOL',b'MSCR',b'IZCA',b'MTPT',b'DBTP',b'TARC',
          b'MFNT',b'SFNT',b'ABDA',b'ABRS',b'HTEX',b'KFMH',b'VBHD',b'KFMO',
          b'KSHP',b'HSPT',b'VBCT'}

def _xor_stream(key4, words):
    """Symmetric keystream XOR over a list of 32-bit words."""
    key = list(key4); out = []
    for i, w in enumerate(words):
        key[i % 4] = (key[i % 4] * 3 + 1) % M
        out.append(w ^ key[i % 4])
    return out

def decrypt_resource(raw, S):
    """Decrypt the resource whose 16-byte key sits at raw[S:S+16].
    Returns the decrypted body (WITHOUT the 16 key bytes)."""
    size = len(raw) - S
    key = struct.unpack('<4I', raw[S:S+16])
    n = (size - 16) // 4
    cw = struct.unpack('<%dI' % n, raw[S+16:S+16+n*4])
    dw = _xor_stream(key, cw)
    body = struct.pack('<%dI' % n, *dw)
    tail = raw[S+16+n*4:]                       # <16 leftover bytes
    if tail:
        k0 = key[0] & 0xff
        body += bytes(b ^ k0 for b in tail)
    return body

def encrypt_resource(key16, body):
    """Re-encrypt an edited body with the ORIGINAL 16-byte key (bytes)."""
    key = struct.unpack('<4I', key16)
    n = len(body) // 4
    dw = struct.unpack('<%dI' % n, body[:n*4])
    cw = _xor_stream(key, dw)
    out = struct.pack('<%dI' % n, *cw)
    tail = body[n*4:]
    if tail:
        k0 = key[0] & 0xff
        out += bytes(b ^ k0 for b in tail)
    return key16 + out                          # ciphertext resource = key || enc-body

def find_resources(raw):
    """Return list of (offset, magic) for every resource start in the file."""
    res = []
    for S in range(0, len(raw) - 64, 4):
        key = struct.unpack('<4I', raw[S:S+16])
        cw = struct.unpack('<2I', raw[S+16:S+24])
        dw = _xor_stream(key, cw)
        m = struct.pack('<I', dw[0])
        if m in MAGICS:
            res.append((S, m.decode('latin1')))
    return res

# ---- MTPA text helpers (text bytes are stored +1 in file) ----
def mtpa_strings(body):
    """Given a decrypted MTPA packet body (starts with 'MTPA'), return the
    list of decoded Shift-JIS dialogue strings from the text segment."""
    assert body[:4] == b'MTPA', body[:4]
    u5, pcount, dsize, dcount = struct.unpack('<IIII', body[0x20:0x30])
    off = 0x30 + dsize*4                        # skip unknown6[dsize]
    off += pcount*4                             # pointer segment
    off += dcount*dsize*4                       # data segment
    text_seg = off
    raw_text = body[text_seg:]
    # text bytes are +1 -> subtract 1, then split on NUL, decode sjis
    dec = bytes(((b-1) & 0xff) for b in raw_text)
    out = []
    for part in dec.split(b'\x00'):
        if not part:
            continue
        try:
            s = part.decode('shift_jis')
        except Exception:
            continue
        if any(0x3000 < ord(c) < 0xF000 for c in s):
            out.append(s)
    return out

if __name__ == '__main__':
    import sys, cpk as cpkmod
    CPK = sys.argv[1] if len(sys.argv) > 1 else 'extracted/ODIN.CPK'
    toc, cont, files = cpkmod.main(CPK)
    data = open(CPK, 'rb')
    for f in files:
        if not f['name'].upper().endswith('.MTP'):
            continue
        data.seek(f['off']); raw = data.read(f['csize'])
        res = find_resources(raw)
        mtpa = [S for S, m in res if m == 'MTPA']
        if not mtpa:
            continue
        body = decrypt_resource(raw, mtpa[0])
        try:
            ss = mtpa_strings(body)
        except Exception as e:
            print(f'{f["name"]}: parse error {e}'); continue
        print(f'{f["name"]:22} @0x{mtpa[0]:x}: {len(ss)} strings')
