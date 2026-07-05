#!/usr/bin/env python3
"""VC2 Korean patch — Wansung(KS X 1001) 2350-syllable substitution method.

Standard SJIS-game Korean-patch technique:
  * The 2350 KS X 1001 (Wansung/EUC-KR) Hangul syllables are placed, in KS order,
    into the game's SJIS full-width KANJI glyph slots (in SJIS order), overwriting
    the kanji bitmaps in MFNT#2.
  * Dialogue text then contains the SJIS code of the kanji slot that holds each
    Hangul; the game renders that "kanji", but its glyph is now the Hangul => Korean
    shows on screen at full-width, while ASCII/symbols/half-width space stay intact.

Mapping is positional: hangul2350[i] <-> sjis_slots[i].
"""
import struct
from PIL import Image, ImageFont, ImageDraw
import vc2_font2b as v2

SEOUL_M = 'C:/Users/Jay/AppData/Local/Microsoft/Windows/Fonts/SeoulHangangM.ttf'
SEOUL_B = 'C:/Users/Jay/Pictures/ai/Valkyria Chronicles 2/SeoulHangangB.ttf'

def wansung_2350():
    out = []
    for hi in range(0xB0, 0xC9):
        for lo in range(0xA1, 0xFF):
            try:
                ch = bytes([hi, lo]).decode('euc-kr')
            except Exception:
                continue
            if len(ch) == 1 and 0xAC00 <= ord(ch) <= 0xD7A3:
                out.append(ch)
    return out                                   # 2350 syllables, KS order

def sjis_kanji_slots(font):
    def vt(t): return 0x40 <= t <= 0x7e or 0x80 <= t <= 0xfc
    slots = []
    for lead in list(range(0x88, 0xa0)) + list(range(0xe0, 0xf0)):
        for t in range(0x40, 0xfd):
            if not vt(t):
                continue
            code = (lead << 8) | t
            if font.in_bounds(font.glyph_offset(code)):
                slots.append(code)
    return slots

_SIZE_HI = 48    # high-res render size
_CROP = 48       # SQUARE crop side (px) -> uniform aspect-preserving scale, natural width

def raster2bpp(ch, fontpath=SEOUL_B):
    """16x16, 4-level (0..3). UNIFORM scale, aspect-PRESERVED (no horizontal stretch):
    render at one fixed size, crop a fixed SQUARE box (side _CROP) centered on the
    advance from the top, downscale to 16. Gives the font's natural (narrower) width."""
    f = ImageFont.truetype(fontpath, _SIZE_HI)
    adv = round(f.getlength('가'))
    canvas = Image.new('L', (70, 70), 0)
    ImageDraw.Draw(canvas).text((2, 2), ch, font=f, fill=255)
    x0 = max(0, 2 + (adv - _CROP)//2)
    g = canvas.crop((x0, 1, x0 + _CROP, 1 + _CROP)).resize((16, 16), Image.LANCZOS)
    out = [[0]*16 for _ in range(16)]
    for y in range(16):
        for x in range(16):
            val = g.getpixel((x, y))
            out[y][x] = 0 if val < 40 else (1 if val < 110 else (2 if val < 190 else 3))
    return out

def build(src_bf1, out_bf1, verbose=True):
    """Render all 2350 Hangul into kanji slots; return {syllable: sjis_code} map."""
    font = v2.VC2Font2B(src_bf1)
    hs = wansung_2350()
    slots = sjis_kanji_slots(font)
    assert len(slots) >= len(hs), f'{len(slots)} slots < {len(hs)} hangul'
    mapping = {}
    for i, ch in enumerate(hs):
        code = slots[i]
        font.write_glyph(code, raster2bpp(ch))
        mapping[ch] = code
        if verbose and i % 500 == 0:
            print(f'  ...{i}/{len(hs)}')
    font.save(out_bf1)
    return mapping

def encode(text, mapping):
    """Korean text -> decoded (pre-+1) byte payload. Hangul -> 2-byte SJIS kanji code;
    space -> 0x20 (half-width); '.'-> 0x2e; newline -> 0x0a; ASCII kept as-is."""
    out = bytearray()
    for ch in text:
        if ch == '\n':
            out.append(0x0a)
        elif ch in mapping:
            c = mapping[ch]; out += bytes([(c >> 8) & 0xff, c & 0xff])
        elif ord(ch) < 0x80:
            out.append(ord(ch))                  # ASCII/space/punct half-width
        else:
            raise KeyError(f'no mapping for {ch!r} (U+{ord(ch):04X})')
    return bytes(out)
