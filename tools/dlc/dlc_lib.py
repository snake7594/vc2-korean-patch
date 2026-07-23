#!/usr/bin/env python3
"""DLC MXE extract/inject library for VC2 (NPJH50145) Korean patch.

DLC CPK content differs from main-game ODIN.CPK: files are NOT file-level
key*3+1 encrypted. Each MXE file = plaintext framing; the MXEN/MXEC main
resource sits after a preamble (usually at 0x800). Only the MXEC DATA region
(size = datasize @ MXEC+0x14) is rolling-XOR encrypted (flag 0x40000).

Patch path: locate MXEN -> roll-decrypt data region -> same-length run
replacement -> roll-encrypt (flag preserved) -> write back in place. CPK TOC
untouched (sizes unchanged).
"""
import struct, os, sys, io, contextlib
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # _work
import cpk as _cpk, mxe_tool as mx

def cpk_files(path):
    """Return (raw_bytes, [ {name,off,size} ]) for a DLC _DATA.EDAT (plain CPK)."""
    with contextlib.redirect_stdout(io.StringIO()):
        _, _, files = _cpk.main(path)
    raw = open(path, 'rb').read()
    return raw, files

def find_mxen(blob):
    """Locate the MXEN resource whose MXEC packet fully fits in blob.
    Returns (mxen_off, mxec_hsz, flags, datasize, data_start, data_end) or None."""
    pos = 0
    while True:
        m = blob.find(b'MXEN', pos)
        if m < 0:
            return None
        if blob[m+0x20:m+0x24] == b'MXEC':
            psz, hsz, flags = struct.unpack_from('<III', blob, m+0x24)
            datasize = struct.unpack_from('<I', blob, m+0x20+0x14)[0]
            data_start = m + 0x20 + hsz
            data_end = data_start + datasize
            if data_end <= len(blob) and 0 < datasize:
                return dict(mxen=m, hsz=hsz, flags=flags, datasize=datasize,
                            start=data_start, end=data_end)
        pos = m + 4

def decode_body(blob, info):
    """Return roll-decrypted (plain) copy of blob (only [start,end) changed)."""
    if info['flags'] & mx.ENC_FLAG:
        return mx.roll_decrypt(blob, info['start'], info['end'])
    return bytes(blob)

def extract_runs(blob):
    info = find_mxen(blob)
    if not info:
        return None, []
    plain = decode_body(blob, info)
    runs = mx.extract_runs(plain, info['start'], info['end'])
    return info, runs
