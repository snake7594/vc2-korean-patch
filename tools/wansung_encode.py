#!/usr/bin/env python3
"""VC2 Korean wansung encoder + font builder for the FULL patch.

Mapping is built from the ACTUAL set of Hangul syllables used across all
translations (not the fixed 2350), guaranteeing every syllable renders.
Each syllable -> one SJIS kanji slot (MFNT#2), glyph overwritten with Hangul.

encode_ko(text, mapping, nl): Korean text -> decoded (pre-+1) payload bytes.
  * Hangul syllable          -> its 2-byte SJIS slot code
  * ASCII (<0x80)            -> 1 byte  (letters/digits/punct/space/@fc markup/%s)
  * full-width symbol 0x81xx -> its 2 SJIS bytes (unmodified symbol plane)
  * '\n'                     -> 0x0a (nl='lf') or 0x0d 0x0a (nl='crlf')
  * full-width space U+3000  -> 0x20 (half-width, saves a byte)
"""
import struct, json, sys
sys.path.insert(0, '.')
import vc2_font2b as v2
import vc2_hangul_patch as hp

def sjis_kanji_slots(font):
    """Ordered in-bounds SJIS kanji codes: L1 (0x88-0x9f) + L2 (0xe0-0xef) +
    extension (0xf0-0xfc) for headroom. ~2996 base, more with extension."""
    def vt(t): return 0x40 <= t <= 0x7e or 0x80 <= t <= 0xfc
    slots = []
    for lead in list(range(0x88, 0xa0)) + list(range(0xe0, 0xfd)):
        for t in range(0x40, 0xfd):
            if not vt(t):
                continue
            code = (lead << 8) | t
            if font.in_bounds(font.glyph_offset(code)):
                slots.append(code)
    return slots

def collect_syllables(translations):
    """translations: iterable of Korean strings. -> sorted unique Hangul syllables."""
    s = set()
    for t in translations:
        for ch in t:
            if 0xAC00 <= ord(ch) <= 0xD7A3:
                s.add(ch)
    return sorted(s)

def build_mapping(syllables, src_bf1):
    font = v2.VC2Font2B(src_bf1)
    slots = sjis_kanji_slots(font)
    if len(syllables) > len(slots):
        raise ValueError(f'{len(syllables)} syllables > {len(slots)} slots')
    return {syl: slots[i] for i, syl in enumerate(syllables)}

def build_font(src_bf1, out_bf1, mapping, fontpath=hp.SEOUL_B):
    font = v2.VC2Font2B(src_bf1)
    for syl, code in mapping.items():
        font.write_glyph(code, hp.raster2bpp(syl, fontpath=fontpath))
    font.save(out_bf1)
    return len(mapping)

class EncodeError(Exception):
    pass

# characters translators use that map to a safe encodable equivalent
_NORM = {'·': '・', 'ㆍ': '・', '・': '・', 'ㅡ': '-', '²': '2', '³': '3',
         '─': '―', '━': '―', '～': '~', '’': "'", '‘': "'", '“': '"', '”': '"'}
# unmodified full-width symbol rows (kanji start at 0x88); 0x82/0x83 (kana) excluded
_SAFE_LEADS = (0x81, 0x84, 0x85, 0x86, 0x87)

def _normalize(text):
    out = []
    for ch in text:
        o = ord(ch)
        if 0xFF01 <= o <= 0xFF5E:            # full-width ASCII -> half-width (1 byte, renders)
            out.append(chr(o - 0xFEE0))
        elif ch in _NORM:
            out.append(_NORM[ch])
        else:
            out.append(ch)
    return ''.join(out)

def encode_ko(text, mapping, nl='lf'):
    text = _normalize(text)
    out = bytearray()
    for ch in text:
        o = ord(ch)
        if ch == '\n':
            out += b'\x0d\x0a' if nl == 'crlf' else b'\x0a'
        elif ch == '　':                 # full-width space -> half
            out.append(0x20)
        elif ch in mapping:
            c = mapping[ch]; out += bytes([(c >> 8) & 0xff, c & 0xff])
        elif o < 0x80:
            out.append(o)
        else:
            try:
                b = ch.encode('shift_jis')
            except Exception:
                raise EncodeError(f'unencodable char {ch!r} U+{o:04X}')
            if len(b) == 2 and b[0] in _SAFE_LEADS:      # unmodified symbol plane
                out += b
            elif 0xAC00 <= o <= 0xD7A3:
                raise EncodeError(f'hangul not in mapping: {ch!r}')
            else:
                raise EncodeError(f'disallowed char {ch!r} U+{o:04X} (sjis {b.hex()})')
    return bytes(out)

def block(n):
    return (4 + n + 1 + 3) & ~3

def fits(encoded_len, orig_len):
    return block(encoded_len) <= block(orig_len)
