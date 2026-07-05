#!/usr/bin/env python3
"""
vc2_font2b.py - Valkyria Chronicles 2 (PSP) 2-byte / full-width glyph tool.

Reads and writes the FULL-WIDTH (kanji/full-width) glyph plane MFNT#2 inside the
decrypted BF1 font container (e.g. BF1_full.JPdec).

Glyph plane spec (reverse-engineered, verified by rendering):
  * Container: SFNT @0x00, resource dir @0x2c -> [MFNT#1, MFNT#2, MFNT#3, MFGT, HFPR]
  * MFNT#2 (full-width plane) header @0x1880, payload @0x18a0 .. 0x38ca0
      +0x10 = 0x00100010  (glyph W=0x10, H=0x10 -> 16x16 px)
      +0x14 = 0x7820      (plane-2 sub-offset)
      +0x18 = 0x1e420     (plane-3 sub-offset)
      +0x1c = 4           (bpp code: 4 -> 2 bits/pixel)
  * Glyph bitmap: 16x16 px, 2 bits/pixel, MSB-first, 4 bytes/row, 64 (0x40) bytes/glyph.
      pixel(x,y) value(0..3) = (byte[y*4 + (x*2)//8] >> (6 - (x*2)%8)) & 3
      2bpp -> 4 gray levels (0=transparent .. 3=solid). Game maps 0/1/2/3 to palette.
  * Full-width advance: de4=0x10 (16), de6=0x10 (16) -> advance = 16*fontsize/16 = 1.0*fontsize
      (a full em cell; half-width ASCII advances HFPR-width/16 * fontsize).

Code -> glyph offset (exact port of EBOOT FUN_003c38f4):
  Three arithmetic sub-planes tile the payload contiguously:
    Plane1  0x8140..0x839f  (JIS symbols + kana)   base d9c+dc8
    Plane2  0x8890..0x8fff  (JIS L1 kanji, 亜=0x889f) base d9c+dcc
    Plane3  0x9040..0x987f  (JIS L2 kanji)          base d9c+dd0
  Codes outside these fall through to the small MFGT remap table (64 special entries).
"""
import struct

def _u16(d,o): return struct.unpack_from("<H", d, o)[0]
def _u32(d,o): return struct.unpack_from("<I", d, o)[0]

GLYPH_BYTES = 0x40   # 16x16 @ 2bpp
GLYPH_W = 16
GLYPH_H = 16

class VC2Font2B:
    def __init__(self, path):
        self.path = path
        self.data = bytearray(open(path, "rb").read())
        d = self.data
        assert d[0:4] == b"SFNT", "not an SFNT container"
        # resource directory
        cnt = _u32(d, 0x20); tbloff = _u32(d, 0x24)
        offs = [_u32(d, tbloff + i*4) for i in range(cnt)]
        self.res = offs                      # [MFNT1, MFNT2, MFNT3, MFGT, HFPR]
        self.mfnt2 = offs[1]                  # 0x1880
        m = self.mfnt2
        assert d[m:m+4] == b"MFNT"
        self.payload = m + 0x20               # 0x18a0
        self.payload_end = offs[2]            # 0x38ca0 (start of MFNT#3)
        # fields (mirrors FUN_003c279c + FUN_003c31ac)
        self.d9c = m + 0x10                   # glyph-plane base ptr (points at hdr+0x10)
        self.dc8 = 0x10
        self.dcc = _u32(d, m + 0x14) - 0x10   # 0x7810
        self.dd0 = _u32(d, m + 0x18) - 0x10   # 0x1e410
        self.de4 = _u16(d, m + 0x12)          # 0x10 (full-width advance numerator)
        self.de6 = _u16(d, m + 0x10)          # 0x10 (advance denominator)
        self.ddc = _u32(d, m + 0x1c)          # 4 (bpp code)
        self.bppdiv = {2:8, 4:4, 8:2, 0x10:2}.get(self.ddc, 2)
        self.glyphbytes = (self.de4 * self.de6) // self.bppdiv   # 0x40
        # MFGT remap table (code -> offset), 8-byte entries
        self.mfgt = offs[3]
        self._mfgt = {}
        gpay = self.mfgt + _u32(d, self.mfgt + 8)   # hdr size 0x10
        gcnt = _u32(d, self.mfgt + 4) // 8
        for i in range(gcnt):
            raw = _u32(d, gpay + i*8)
            off = _u32(d, gpay + i*8 + 4)
            # code stored byte-swapped: raw low byte = high SJIS byte
            code = ((raw & 0xff) << 8) | ((raw >> 8) & 0xff)
            self._mfgt.setdefault(code, self.d9c + off)  # first wins

    # ---- code -> absolute file offset of the 16x16 glyph bitmap ----
    def glyph_offset(self, code):
        gb = self.glyphbytes
        if 0x8140 <= code <= 0x839f:
            return self.d9c + self.dc8 + (code-0x8140)*gb + ((code-0x8140)>>8)*gb*(-0x40)
        if 0x8890 <= code <= 0x8fff:
            return self.d9c + self.dcc + ((code-0x8800)&0xff)*gb + ((code-0x8800)>>8)*gb*0xc0 + gb*(-0x90)
        if 0x9040 <= code <= 0x987f:
            return self.d9c + self.dd0 + ((code-0x9000)&0xff)*gb + ((code-0x9000)>>8)*gb*0xc0 + gb*(-0x40)
        return self._mfgt.get(code)          # MFGT remap path (or None)

    def in_bounds(self, off):
        return off is not None and self.payload <= off and off + self.glyphbytes <= self.payload_end

    # ---- read glyph as 16x16 list of ints (0..3) ----
    def read_glyph(self, code):
        off = self.glyph_offset(code)
        if not self.in_bounds(off):
            raise ValueError(f"code {code:#06x} has no in-bounds glyph (off={off})")
        d = self.data
        g = [[0]*GLYPH_W for _ in range(GLYPH_H)]
        for y in range(GLYPH_H):
            for x in range(GLYPH_W):
                b = d[off + y*4 + (x*2)//8]
                g[y][x] = (b >> (6 - (x*2)%8)) & 3
        return g

    # ---- write glyph from 16x16 list of ints (0..3) ----
    def write_glyph(self, code, pix):
        off = self.glyph_offset(code)
        if not self.in_bounds(off):
            raise ValueError(f"code {code:#06x} has no in-bounds glyph slot (off={off})")
        d = self.data
        for y in range(GLYPH_H):
            for x in range(0, GLYPH_W, 4):     # 4 px per byte
                b = 0
                for k in range(4):
                    v = pix[y][x+k] & 3
                    b |= v << (6 - k*2)         # MSB-first pairs
                d[off + y*4 + x//4] = b

    def write_glyph_1bpp(self, code, bitmap16x16):
        """Convenience: write a 1bpp bitmap (0/1) as solid level-3 ink."""
        pix = [[3 if bitmap16x16[y][x] else 0 for x in range(16)] for y in range(16)]
        self.write_glyph(code, pix)

    def ascii_art(self, code, chars=" .:#"):
        g = self.read_glyph(code)
        return "\n".join("".join(chars[v] for v in row) for row in g)

    def save(self, path=None):
        open(path or self.path, "wb").write(self.data)


if __name__ == "__main__":
    import sys
    f = VC2Font2B(r"C:\Users\Jay\Pictures\ai\Valkyria Chronicles 2\_work\BF1_full.JPdec")
    print(f"payload 0x{f.payload:x}..0x{f.payload_end:x}  glyphbytes=0x{f.glyphbytes:x}")
    print(f"full-width advance: de4/de6 = {f.de4}/{f.de6} = {f.de4/f.de6:.2f} * fontsize")
    for c in (0x889f, 0x88a0, 0x88a1):     # 亜 唖 娃
        print(f"\nSJIS {c:#06x} @ 0x{f.glyph_offset(c):x}")
        print(f.ascii_art(c))
