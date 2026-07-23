#!/usr/bin/env python3
"""Apply the Valkyria Chronicles 2 Korean patch to your own NPJH50145 ISO.

Usage:  python apply_patch.py "path/to/original.iso" [output.iso]

Requires:  pip install pyxdelta
Put ONE of the patch files next to this script (download from the Releases page):
  - VC2_KoreanPatch_v33_hw.xdelta   real PSP (CFW)  -> Korean-subtitled movies (Sony encoder)
  - VC2_KoreanPatch_v33_emu.xdelta  PPSSPP emulator -> Korean-subtitled movies (x264)
The script auto-detects which one is present, verifies the source hash, applies
it, and verifies the result. No game data is contained in the patch.

The main-ISO patch is byte-identical to v32 (only the DLC is new in v33), so if
you already applied v32 to your ISO you do NOT need to re-apply it -- just install
the DLC zip. See the Releases page / README for DLC install instructions.
"""
import sys, os, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC_SHA1 = '809a6a106aaf39d3a5aa18b5d7b0f7b70b6e1d65'
SRC_SIZE = 1120927744
# patch filename -> (result SHA1, default output name, label)
PATCHES = {
    'VC2_KoreanPatch_v33_hw.xdelta':
        ('a7bb9739c748fc1bd2b8773d8e00332fd4fc98ea', 'VC2_Korean_v33_hw.iso',
         'real PSP (movies Korean-subtitled, Sony PSMF encoder)'),
    'VC2_KoreanPatch_v33_emu.xdelta':
        ('59f1ec0a61912223115258a2efb09821f74bc14e', 'VC2_Korean_v33_emu.iso',
         'PPSSPP (movies Korean-subtitled, x264)'),
    # v32 names still accepted (identical bytes) so old downloads keep working
    'VC2_KoreanPatch_v32_hw.xdelta':
        ('a7bb9739c748fc1bd2b8773d8e00332fd4fc98ea', 'VC2_Korean_v32_hw.iso',
         'real PSP (movies Korean-subtitled, Sony PSMF encoder)'),
    'VC2_KoreanPatch_v32_emu.xdelta':
        ('59f1ec0a61912223115258a2efb09821f74bc14e', 'VC2_Korean_v32_emu.iso',
         'PPSSPP (movies Korean-subtitled, x264)'),
}


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
    found = [(p, HERE + os.sep + p) for p in PATCHES if os.path.exists(HERE + os.sep + p)]
    if not found:
        print('[!] No patch file found next to this script.')
        print('    Download VC2_KoreanPatch_v33_hw.xdelta (real PSP) or '
              'VC2_KoreanPatch_v33_emu.xdelta (PPSSPP)')
        print('    from the Releases page and put it in this folder.'); sys.exit(1)
    pname, ppath = found[0]
    out_sha1, defout, label = PATCHES[pname]
    out = sys.argv[2] if len(sys.argv) > 2 else defout
    print(f'[*] Using {pname}  ->  {label}')

    if not os.path.exists(src):
        print(f'[!] Original ISO not found: {src}'); sys.exit(1)
    try:
        import pyxdelta
    except ImportError:
        print('[!] pyxdelta not installed.  Run:  pip install pyxdelta'); sys.exit(1)

    print('[*] Checking your ISO...')
    if os.path.getsize(src) != SRC_SIZE:
        print(f'[!] Size mismatch. You need the Japanese NPJH50145 v1.01 dump.'); sys.exit(1)
    if sha1(src) != SRC_SHA1:
        print(f'[!] SHA1 mismatch. Use a clean NPJH50145 v1.01 dump.'); sys.exit(1)
    print('    OK — source ISO verified.')

    print('[*] Applying patch...')
    if not pyxdelta.decode(src, ppath, out):
        print('[!] Patch failed.'); sys.exit(1)

    print('[*] Verifying result...')
    if sha1(out) == out_sha1:
        print(f'[✓] Done!  Korean-patched ISO written to: {out}')
        print('    Run it in PPSSPP or on a CFW PSP.')
    else:
        print('[!] Output hash unexpected. The patch may not have applied cleanly.')
        sys.exit(1)


if __name__ == '__main__':
    main()
