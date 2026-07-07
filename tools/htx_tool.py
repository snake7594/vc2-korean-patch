#!/usr/bin/env python3
"""VC2 HTX (HTEX / MIG.00.1PSP) texture tool — decode to PNG / encode from PNG.

An HTX (CPK-decrypted) is a HTEX container of one or more HTSF packets, each a
PSP texture:

  [HTSF 0x40][MIG hdr 0x80][index data (swizzled)][0x50 meta][palette] [mips...]

  MIG entry table (16-byte entries {u32 type,a,b,c}) holds:
    type 0x30 = surface: fmt(u16 @+4: 4=T4/4bpp idx, 5=T8/8bpp idx),
                w(u16 @+8), h(u16 @+10)
  Index data starts at mig+0x80, PSP-swizzled (16-byte x 8-row blocks).
  Palette (ABGR8888) follows the index data after a 0x50-byte meta block; the
  meta's type-05 `a` field = 0x50 + palette_bytes, so pal_n = (a-0x50)//4.

Multi-texture files (atlases) hold several HTSF packets; each is decoded and
re-inserted independently.

API:
  iter_packets(dec)          -> [pk, ...]  (dict per sub-texture)
  decode_all(dec)            -> [(PIL.Image RGBA, pk), ...]
  decode(dec)                -> (image, pk) for the FIRST packet (convenience)
  encode_into(dec, pk, img)  -> new dec bytes with that packet's pixels replaced
                                (unchanged pixels keep their exact index -> lossless)
"""
import struct
from PIL import Image

MAGIC = b'MIG.00.1PSP'

def _byte_w(w, bpp):
    return (w * bpp) // 8

def iter_packets(dec):
    """Enumerate every HTSF/MIG sub-texture. Returns list of packet dicts."""
    # HTSF packet starts; MIG magic sits 0x40 after each HTSF start.
    starts = []
    i = 0
    while True:
        j = dec.find(b'HTSF', i)
        if j < 0: break
        starts.append(j); i = j + 4
    # packet end = next HTSF start, else EOFC / end of file
    pkts = []
    for k, s in enumerate(starts):
        end = starts[k + 1] if k + 1 < len(starts) else len(dec)
        mig = dec.find(MAGIC, s, end)
        if mig < 0: continue
        pk = _parse_packet(dec, mig, end)
        if pk: pkts.append(pk)
    if not pkts:                       # no HTSF wrapper — try a bare MIG
        mig = dec.find(MAGIC)
        if mig >= 0:
            pk = _parse_packet(dec, mig, len(dec))
            if pk: pkts.append(pk)
    return pkts

def _parse_packet(dec, mig, end):
    o = mig + 0x10
    desc = None
    while o + 16 <= min(mig + 0x80, end):
        t = struct.unpack_from('<I', dec, o)[0]
        if t == 0x30:
            fmt = struct.unpack_from('<H', dec, o + 4)[0]
            w   = struct.unpack_from('<H', dec, o + 8)[0]
            h   = struct.unpack_from('<H', dec, o + 10)[0]
            if desc is None and fmt in (4, 5):
                desc = dict(fmt=fmt, w=w, h=h)
        o += 16
    if desc is None: return None
    bpp = 4 if desc['fmt'] == 4 else 8
    data_off = mig + 0x80
    idx_size = _byte_w(desc['w'], bpp) * desc['h']
    meta_off = data_off + idx_size
    # palette count from the 0x50-byte meta block's type-05 `a` (= 0x50 + pal bytes)
    pal_n = 16 if bpp == 4 else 256
    if meta_off + 8 <= end:
        a = struct.unpack_from('<I', dec, meta_off + 4)[0]
        n = (a - 0x50) // 4
        if 1 <= n <= 256: pal_n = n
    pal_off = meta_off + 0x50
    return dict(mig=mig, htsf_end=end, data_off=data_off, idx_size=idx_size,
                pal_off=pal_off, pal_n=pal_n, w=desc['w'], h=desc['h'],
                bpp=bpp, fmt=desc['fmt'])

# ---- PSP swizzle (16-byte x 8-row blocks). Exact inverses; leftover copied linearly ----
def _unswizzle(buf, byte_w, h):
    if byte_w // 16 == 0: return bytes(buf)
    out = bytearray(buf); src = 0
    for by in range(h // 8):
        for bx in range(byte_w // 16):
            for y in range(8):
                dst = (by * 8 + y) * byte_w + bx * 16
                out[dst:dst + 16] = buf[src:src + 16]; src += 16
    return bytes(out)

def _swizzle(buf, byte_w, h):
    if byte_w // 16 == 0: return bytes(buf)
    out = bytearray(buf); dst = 0
    for by in range(h // 8):
        for bx in range(byte_w // 16):
            for y in range(8):
                src = (by * 8 + y) * byte_w + bx * 16
                out[dst:dst + 16] = buf[src:src + 16]; dst += 16
    return bytes(out)

def _abgr(c):
    return (c & 0xff, (c >> 8) & 0xff, (c >> 16) & 0xff, (c >> 24) & 0xff)

def _palette(dec, pk):
    out = []
    for i in range(pk['pal_n']):
        o = pk['pal_off'] + i * 4
        c = struct.unpack_from('<I', dec, o)[0] if o + 4 <= len(dec) else 0
        out.append(_abgr(c))
    return out

def _indices(dec, pk):
    w, h, bpp = pk['w'], pk['h'], pk['bpp']
    bw = _byte_w(w, bpp); nd = bw * h
    raw = dec[pk['data_off']:pk['data_off'] + nd]
    if len(raw) < nd: raw = raw + b'\x00' * (nd - len(raw))
    lin = _unswizzle(raw, bw, h)
    rows = []
    for y in range(h):
        r = lin[y * bw:(y + 1) * bw]
        if bpp == 8:
            rows.append([r[x] for x in range(w)])
        else:
            rows.append([(r[x >> 1] & 0xf) if (x & 1) == 0 else (r[x >> 1] >> 4) for x in range(w)])
    return rows

def decode_packet(dec, pk):
    pal = _palette(dec, pk); idx = _indices(dec, pk); pn = pk['pal_n']
    im = Image.new('RGBA', (pk['w'], pk['h'])); px = im.load()
    for y in range(pk['h']):
        row = idx[y]
        for x in range(pk['w']):
            px[x, y] = pal[row[x] % pn]
    return im

def decode_all(dec):
    return [(decode_packet(dec, pk), pk) for pk in iter_packets(dec)]

def decode(dec):
    pk = iter_packets(dec)
    if not pk: raise ValueError('no MIG texture')
    return decode_packet(dec, pk[0]), pk[0]

def encode_indices(dec, pk, idx_rows):
    """Replace packet pk's pixel data with raw palette indices (list/array [h][w]).
    For alpha-ramp glyph textures where the palette is runtime-supplied and RGBA
    round-tripping would be lossy. Values are masked to the bpp range."""
    w, h, bpp = pk['w'], pk['h'], pk['bpp']
    bw = _byte_w(w, bpp)
    lin = bytearray(bw * h)
    mask = 0xf if bpp == 4 else 0xff
    for y in range(h):
        row = idx_rows[y]
        for x in range(w):
            v = int(row[x]) & mask
            if bpp == 8:
                lin[y * bw + x] = v
            else:
                bi = y * bw + (x >> 1)
                if (x & 1) == 0: lin[bi] = (lin[bi] & 0xf0) | v
                else: lin[bi] = (lin[bi] & 0x0f) | (v << 4)
    swz = _swizzle(bytes(lin), bw, h)
    out = bytearray(dec)
    out[pk['data_off']:pk['data_off'] + len(swz)] = swz
    return bytes(out)

def encode_into(dec, pk, img):
    """Replace packet pk's pixels with img (same w,h). Unchanged pixels keep their
    exact original index (lossless); edited pixels quantize to nearest palette colour."""
    w, h, bpp, pn = pk['w'], pk['h'], pk['bpp'], pk['pal_n']
    if img.size != (w, h): img = img.resize((w, h))
    img = img.convert('RGBA')
    pal = _palette(dec, pk); oidx = _indices(dec, pk)
    def nearest(c):
        best = 0; bd = 1 << 30
        for i in range(pn):
            p = pal[i]
            d = (c[0]-p[0])**2 + (c[1]-p[1])**2 + (c[2]-p[2])**2 + (c[3]-p[3])**2
            if d < bd: bd = d; best = i
        return best
    px = img.load(); bw = _byte_w(w, bpp)
    lin = bytearray(bw * h); cache = {}
    for y in range(h):
        orow = oidx[y]
        for x in range(w):
            c = px[x, y]
            if pal[orow[x] % pn] == c:
                idx = orow[x]
            else:
                idx = cache.get(c)
                if idx is None: idx = cache[c] = nearest(c)
            if bpp == 8:
                lin[y * bw + x] = idx
            else:
                bi = y * bw + (x >> 1)
                if (x & 1) == 0: lin[bi] = (lin[bi] & 0xf0) | idx
                else: lin[bi] = (lin[bi] & 0x0f) | (idx << 4)
    swz = _swizzle(bytes(lin), bw, h)
    out = bytearray(dec)
    out[pk['data_off']:pk['data_off'] + len(swz)] = swz
    return bytes(out)
