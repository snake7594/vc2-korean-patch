# -*- coding: utf-8 -*-
"""DLC text encoder + render-width calc that (unlike wansung_encode) keeps
FULL-WIDTH uppercase letters as 2-byte SJIS so they render at the proper 32-unit
full-width advance — NOT the garbage HFPR widths that half-width ASCII B-Z hit
(F=62, B=50, C=234, D=199, E=138, G=145, X=106 in the shipped BF1)."""
import struct, os

# HFPR half-width advance table from the shipped patched BF1 (codes 0x20-0x7f)
_BF1 = None
def _hfpr():
    global _BF1
    if _BF1 is None:
        for p in ('../patched/ODIN_FONT_16.dec.BF1',
                  'C:/Users/Jay/Pictures/ai/Valkyria Chronicles 2/_work/patched/ODIN_FONT_16.dec.BF1'):
            if os.path.exists(p):
                b = open(p, 'rb').read(); _BF1 = {0x20 + i: b[0x39ee0 + i] for i in range(96)}; break
    return _BF1
FW = 32  # full-width advance (de4)

def _is_fw_letter(ch):
    return 0xFF21 <= ord(ch) <= 0xFF3A or 0xFF41 <= ord(ch) <= 0xFF5A

def width(s):
    """Rendered advance width in font units (de6=16 unitsPerEm; full em = 32)."""
    hf = _hfpr(); w = 0
    for ch in s:
        if ch == '\n':
            continue
        o = ord(ch)
        if 0xAC00 <= o <= 0xD7A3:                 # hangul (full-width kanji slot)
            w += FW
        elif _is_fw_letter(ch):                   # full-width Ａ-Ｚ
            w += FW
        elif o < 0x80:                            # half-width ascii
            w += hf.get(o, FW)
        else:                                     # any other full-width (kanji/kana/symbol)
            w += FW
    return w

_NORM = {'·': '・', 'ㆍ': '・', '─': '―', '━': '―', '～': '~',
         '’': "'", '‘': "'", '“': '"', '”': '"'}
_SAFE_LEADS = (0x81, 0x82, 0x84, 0x85, 0x86, 0x87)  # +0x82 (full-width alnum row)

def encode(text, mapping, nl='lf'):
    """Korean/label text -> decoded (pre-+1) payload bytes.
    Hangul -> 2-byte kanji slot; full-width letter/symbol -> 2-byte SJIS;
    ascii -> 1 byte; full-width space -> half; newline -> 0x0a/0x0d0a."""
    out = bytearray()
    for ch in text:
        o = ord(ch)
        if ch == '\n':
            out += b'\x0d\x0a' if nl == 'crlf' else b'\x0a'
        elif ch == '　':
            out.append(0x20)
        elif ch in mapping:                        # hangul
            c = mapping[ch]; out += bytes([(c >> 8) & 0xff, c & 0xff])
        elif _is_fw_letter(ch):                    # KEEP full-width letter -> SJIS 2B
            out += ch.encode('shift_jis')
        elif ch in _NORM:
            n = _NORM[ch]
            out += n.encode('shift_jis') if ord(n) >= 0x80 else bytes([ord(n)])
        elif o < 0x80:
            out.append(o)
        else:
            b = ch.encode('shift_jis')
            if len(b) == 2 and b[0] in _SAFE_LEADS:
                out += b
            elif 0xAC00 <= o <= 0xD7A3:
                raise ValueError(f'hangul not in mapping: {ch!r}')
            else:
                raise ValueError(f'disallowed char {ch!r} U+{o:04X}')
    return bytes(out)

BOX_BRIEFING = 384   # 작전 briefing box width in units (== widest single-line JP)
