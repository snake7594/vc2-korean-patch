#!/usr/bin/env python3
"""Automated PPSSPP boot test: launch ISO, wait, count decrypted game magics in
emulated RAM (many = booted past loading; near-zero = crashed/halted), kill emu.

usage: boottest.py <iso_path> [wait_seconds]
prints: MAGIC_COUNT=<n>
"""
import sys, os, time, subprocess, ctypes, ctypes.wintypes as w

PPSSPP = r'C:\Users\Jay\Pictures\ai\Valkyria Chronicles 2\_work\tools\ppsspp\PPSSPPWindows64.exe'

def scan(pid):
    PROCESS_QUERY_INFORMATION=0x0400; PROCESS_VM_READ=0x0010
    k=ctypes.windll.kernel32
    class MBI(ctypes.Structure):
        _fields_=[("BaseAddress",ctypes.c_void_p),("AllocationBase",ctypes.c_void_p),
          ("AllocationProtect",w.DWORD),("RegionSize",ctypes.c_size_t),
          ("State",w.DWORD),("Protect",w.DWORD),("Type",w.DWORD)]
    h=k.OpenProcess(PROCESS_QUERY_INFORMATION|PROCESS_VM_READ, False, pid)
    if not h: return -1
    MEM_COMMIT=0x1000
    magics=[b'OCRP',b'EOFC',b'IZCA',b'MTPA',b'MXEC',b'CCRS',b'ENRS']
    addr=0; total=0
    mbi=MBI()
    while addr < 0x7fffffffffff:
        r=k.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi))
        if not r: break
        base=mbi.BaseAddress or 0; size=mbi.RegionSize
        if mbi.State==MEM_COMMIT and (mbi.Protect & 0xff) not in (0x01,) and size>=0x1000000:
            buf=(ctypes.c_char*min(size,0x4000000))()
            got=ctypes.c_size_t(0)
            if k.ReadProcessMemory(h, ctypes.c_void_p(base), buf, len(buf), ctypes.byref(got)):
                data=buf.raw[:got.value]
                total+=sum(data.count(m) for m in magics)
        addr=base+size
        if addr==0: break
    k.CloseHandle(h)
    return total

def main():
    iso=sys.argv[1]
    wait=int(sys.argv[2]) if len(sys.argv)>2 else 30
    subprocess.run(['taskkill','/F','/IM','PPSSPPWindows64.exe'], capture_output=True)
    time.sleep(1)
    p=subprocess.Popen([PPSSPP, iso], cwd=os.path.dirname(PPSSPP))
    time.sleep(wait)
    n=scan(p.pid)
    subprocess.run(['taskkill','/F','/IM','PPSSPPWindows64.exe'], capture_output=True)
    print(f'MAGIC_COUNT={n}')

if __name__=='__main__':
    main()
