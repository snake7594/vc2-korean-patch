#!/usr/bin/env python3
"""Apply the Valkyria Chronicles 2 Korean patch to your own NPJH50145 ISO.

Usage:  python apply_patch.py "path/to/original.iso" [output.iso]

Requires:  pip install pyxdelta
The patch only works on the exact original ISO (hash is verified below).
No game data is contained in the patch; you must supply your own legal copy.
"""
import sys, os, hashlib

PATCH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VC2_KoreanPatch_v29.xdelta')
SRC_SHA1 = '809a6a106aaf39d3a5aa18b5d7b0f7b70b6e1d65'
SRC_SIZE = 1120927744
OUT_SHA1 = '92da5ca0593bd2bf3191bb7ce6f8a4be5efdfbbd'

def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else 'VC2_Korean_v29.iso'
    if not os.path.exists(src):
        print(f'[!] Original ISO not found: {src}'); sys.exit(1)
    if not os.path.exists(PATCH):
        print(f'[!] Patch file not found next to this script: {PATCH}')
        print('    Download VC2_KoreanPatch_v29.xdelta from the Releases page and'
              ' put it in the same folder as this script.'); sys.exit(1)
    try:
        import pyxdelta
    except ImportError:
        print('[!] pyxdelta not installed.  Run:  pip install pyxdelta'); sys.exit(1)

    print('[*] Checking your ISO...')
    sz = os.path.getsize(src)
    if sz != SRC_SIZE:
        print(f'[!] Size mismatch: got {sz}, expected {SRC_SIZE}.')
        print('    You need the Japanese NPJH50145 v1.01 dump (see README).'); sys.exit(1)
    h = sha1(src)
    if h != SRC_SHA1:
        print(f'[!] SHA1 mismatch:\n      got      {h}\n      expected {SRC_SHA1}')
        print('    Wrong/edited ISO. Use a clean NPJH50145 v1.01 dump.'); sys.exit(1)
    print('    OK — source ISO verified.')

    print('[*] Applying patch...')
    if not pyxdelta.decode(src, PATCH, out):
        print('[!] Patch failed.'); sys.exit(1)

    print('[*] Verifying result...')
    ho = sha1(out)
    if ho == OUT_SHA1:
        print(f'[✓] Done!  Korean-patched ISO written to: {out}')
        print('    Run it in PPSSPP (recommended) or on CFW PSP.')
    else:
        print(f'[!] Output hash unexpected ({ho}). The patch may not have applied cleanly.')
        sys.exit(1)

if __name__ == '__main__':
    main()
