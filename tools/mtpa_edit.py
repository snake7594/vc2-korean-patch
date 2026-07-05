#!/usr/bin/env python3
"""Edit a decrypted VC2 MTPA dialogue file.

Text segment layout (verified against MTPA_EV10002.MTP):
  - text_seg starts right after the data-record segment (= p_dataseg + dcount*dsize*4).
  - each data record's text_pos is a byte offset into text_seg pointing at an ENTRY.
  - ENTRY = [u32 length][payload (length bytes)][0x00 terminator + padding], where the
    whole entry is padded so that align_up(4 + length + 1, 4). length excludes the
    terminator/padding. Multiple records may share an entry (same text_pos).
  - EVERYTHING in the text segment (length header, payload, terminator, padding) is
    stored with each byte +1; the game subtracts 1 at load. So NUL bytes are 0x01.

We work in the DECODED (-1) domain and re-encode (+1) the whole pool at the end.
"""
import struct

def parse(body):
    assert body[:4] == b'MTPA', body[:4]
    psz, hsz = struct.unpack('<II', body[4:12])
    u5, pcount, dsize, dcount = struct.unpack('<IIII', body[0x20:0x30])
    p_ptrseg = 0x30 + dsize*4
    p_dataseg = p_ptrseg + pcount*4
    p_textseg = p_dataseg + dcount*dsize*4        # length headers begin here
    return dict(psz=psz, hsz=hsz, pcount=pcount, dsize=dsize, dcount=dcount,
                p_dataseg=p_dataseg, p_textseg=p_textseg, tpf=(2 if dsize == 4 else 1))

def records(body):
    m = parse(body)
    return m, [struct.unpack('<%dI' % m['dsize'],
               body[m['p_dataseg']+k*m['dsize']*4: m['p_dataseg']+(k+1)*m['dsize']*4])
               for k in range(m['dcount'])]

def _decoded_pool(body, text_seg):
    return bytes(((b-1) & 0xff) for b in body[text_seg:])          # -1 domain

def _entry_payload(pool, tp):
    length = struct.unpack('<I', pool[tp:tp+4])[0]
    return pool[tp+4: tp+4+length]

def get_texts(body):
    m, recs = records(body)
    pool = _decoded_pool(body, m['p_textseg'])
    return [_entry_payload(pool, r[m['tpf']]).decode('shift_jis', 'replace') for r in recs]

def get_payloads(body):
    """Raw decoded payload bytes per record (no length header/terminator)."""
    m, recs = records(body)
    pool = _decoded_pool(body, m['p_textseg'])
    return [_entry_payload(pool, r[m['tpf']]) for r in recs]

def _entry_bytes(payload):
    """Build one decoded entry: u32 len + payload + terminator/pad to 4-byte align."""
    total = 4 + len(payload) + 1
    total = (total + 3) & ~3
    e = bytearray(struct.pack('<I', len(payload)))
    e += payload
    e += b'\x00' * (total - len(e))
    return bytes(e)

def rebuild_inplace(body, replacements):
    """Overwrite each replaced record's entry IN-PLACE within its original allocated
    block (only works when the new payload fits). Keeps text_pos, all other records,
    trailing packets (ENRS/EOFC) and packet_size byte-identical — the safest edit.
    replacements: {record_index: real_payload_bytes} (decoded, pre-+1)."""
    m, recs = records(body)
    ts = m['p_textseg']; tpf = m['tpf']
    pool = _decoded_pool(body, ts)
    out = bytearray(body)
    for k, payload in replacements.items():
        payload = bytes(payload)
        tp = recs[k][tpf]
        L = struct.unpack('<I', pool[tp:tp+4])[0]
        orig_block = (4 + L + 1 + 3) & ~3
        new_block = (4 + len(payload) + 1 + 3) & ~3
        if new_block > orig_block:
            raise ValueError(f'record {k}: payload {len(payload)}B needs {new_block}B '
                             f'but slot is only {orig_block}B')
        ent = bytearray(struct.pack('<I', len(payload))) + payload
        ent += b'\x00' * (orig_block - len(ent))          # NUL term+pad (decoded domain)
        out[ts+tp:ts+tp+orig_block] = bytes(((b+1) & 0xff) for b in ent)  # +1 encode in place
    return bytes(out)

def rebuild_contiguous(body, replacements):
    """Rebuild the ENTIRE text pool contiguously (in record order), so all content —
    including edited records — stays inside one contiguous region that the game's
    load-time -1 decode covers. text_pos recomputed; packet_size fixed.
    replacements: {record_index: real_payload_bytes} (decoded, pre-+1)."""
    m, recs = records(body)
    tpf = m['tpf']; text_seg = m['p_textseg']
    pool = _decoded_pool(body, text_seg)
    # decoded payload per record (dedup identical to mirror original sharing)
    new_pool = bytearray(); slot = {}; new_tp = {}
    for k, r in enumerate(recs):
        p = bytes(replacements[k]) if k in replacements else _entry_payload(pool, r[tpf])
        if p in slot:
            new_tp[k] = slot[p]
        else:
            slot[p] = len(new_pool); new_tp[k] = len(new_pool)
            new_pool += _entry_bytes(p)
    out = bytearray(body[:text_seg])
    for k, r in enumerate(recs):
        r = list(r); r[tpf] = new_tp[k]
        struct.pack_into('<%dI' % m['dsize'], out, m['p_dataseg']+k*m['dsize']*4, *r)
    out += bytes(((b+1) & 0xff) for b in new_pool)           # re-encode +1
    newpsz = len(out) - 0x20
    if newpsz % 16:
        pad = 16 - (newpsz % 16); out += bytes([1]) * pad; newpsz += pad
    struct.pack_into('<I', out, 4, newpsz)
    return bytes(out)

def rebuild(body, replacements):
    """Minimal-append rebuild: keep the original text segment byte-for-byte and only
    APPEND new entries for changed records (redirecting their text_pos). Unchanged
    dialogue is left completely untouched.
    replacements: {record_index: real_payload_bytes} (decoded, pre-+1, no terminator).
    """
    m, recs = records(body)
    tpf = m['tpf']; text_seg = m['p_textseg']
    out = bytearray(body)                                         # start from the original
    # strip trailing 16-byte-alignment padding of the packet so appends are contiguous
    psz = struct.unpack('<I', out[4:8])[0]
    seg = out[text_seg:0x20 + psz]                                # current text pool (+1 domain)
    out = out[:text_seg] + seg
    append = bytearray()
    new_tp = {}
    dedup = {}
    for k in sorted(replacements):
        payload = bytes(replacements[k])
        if payload in dedup:
            new_tp[k] = dedup[payload]
        else:
            entry = _entry_bytes(payload)                         # decoded entry
            new_tp[k] = len(seg) + len(append)
            dedup[payload] = new_tp[k]
            append += bytes(((b+1) & 0xff) for b in entry)       # +1 encode
    out = bytearray(out) + append
    for k in replacements:
        off = m['p_dataseg'] + k*m['dsize']*4 + tpf*4
        struct.pack_into('<I', out, off, new_tp[k])
    newpsz = len(out) - 0x20
    if newpsz % 16:
        pad = 16 - (newpsz % 16)
        out += bytes([1]) * pad
        newpsz += pad
    struct.pack_into('<I', out, 4, newpsz)
    return bytes(out)
