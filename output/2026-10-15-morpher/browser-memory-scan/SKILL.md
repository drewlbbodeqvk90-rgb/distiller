---
name: browser-memory-scan
description: Passive, read-only sweep of a live browser process's memory on Windows
  (OpenProcess PROCESS_VM_READ + VirtualQueryEx + ReadProcessMemory) that recovers
  DECRYPTED content the user has on screen — viewed email bodies, verification codes,
  DOM strings — with zero visible action. Proven on live Firefox 157 recovering Proton
  Mail body text and one-time codes from the JS heap. Use when you need the plaintext
  of viewed content from a running browser whose data-at-rest is encrypted, and a
  silent, no-disclosure, read-only technique is required.
purpose: Read-only live-process memory sweep recovering decrypted viewed content (emails, codes) from Firefox/Edge; silent
version: 1.0.0
requires: python3+stdlib (ctypes) | Windows (kernel32) | target: same-user browser process
---

# Browser memory scan ("MEMORY IS A CACHE")

## When to use

- A webmail/web-app session is live in a browser on the target and you need the
  plaintext of content the user has OPENED/viewed — the decrypted copy lives in the
  process heap even when every store on disk is encrypted end-to-end.
- Data-at-rest decryption is blocked (E2E-encrypted bodies, missing keyPassword,
  memory-only sessions) but the browser is running right now.
- You need zero visible action: the scan only holds PROCESS_VM_READ |
  PROCESS_QUERY_INFORMATION handles and never writes to the process.

Scope limit (proven): only OPENED/viewed messages have decrypted bodies in memory;
unopened bodies are NOT cached anywhere decryptable. Re-scan after each message the
user opens to accumulate coverage.

## Workflow (proven end-to-end on session 2026-10-15-morpher)

1. **Enumerate target processes with memory size.** On Windows 11 24H2+/26200 `wmic`
   is REMOVED — use PowerShell:
   `Get-CimInstance Win32_Process -Filter "Name='firefox.exe'" | Select ProcessId,WorkingSetSize`.
   Sort descending by WorkingSetSize; the tab holding the content is among the
   largest processes (session scanned the top 8).
2. **Configure `scripts/memscan.py`** (byte-identical session-tested copy):
   - `OUT` — output text path (edit per run).
   - `NEEDLES` — search terms, each encoded BOTH as UTF-8 and UTF-16LE (proven:
     JS-heap strings appear in both encodings; dual needles doubled coverage).
     Session needles: `Your verification code`, `Paybis`, `NanoGPT`.
   - Context windows: `CTX_BEFORE = 1500`, `CTX_AFTER = 9000` (proven values —
     enough to capture a full body around a subject/code needle).
3. **Run passively, passing PIDs on argv** (the script's built-in `wmic` fallback is
   dead on Win11 26200):
   `python -X utf8 memscan.py <pid1> <pid2> ...`
4. **What the script does** (all proven): walks committed regions only
   (`MEM_COMMIT`, protect in {0x02 READONLY, 0x04 READWRITE, 0x08 WRITECOPY,
   0x20 EXECUTE_READ, 0x40 EXECUTE_READWRITE}), skips regions ≥1 GB, reads in 4 MB
   chunks up to user-space 0x7fffffffffff, finds every needle occurrence, captures
   the context window, dedupes on a context signature (`ctx[380:420]`), and writes
   ≤400 contexts to `OUT` as UTF-8 text with `===== pid N needle=... =====`
   headers, NULs stripped. Console prints per-PID "scanned %.1f MB, hits N".
5. **Harvest**: read `OUT` for recovered bodies/codes. Session result: full
   decrypted body of the Paybis "Your verification code" mail incl. the code
   (644245) and the NanoGPT code (357852), from `firefox.exe` memory —
   evidence pointer `loot\C14\proton-hits.txt` (loot stays operator-side).
6. **Iterate**: repeat the scan each time the user opens a new message; each scan
   is a fresh snapshot of whatever is decrypted at that moment.

## Gotchas (proven)

- **Medium integrity is enough** for same-user processes: the session ran
  non-elevated (admin group deny-only) and OpenProcess with
  VM_READ|QUERY_INFORMATION succeeded on all firefox.exe PIDs.
- **`wmic` is gone on Win11 24H2+** — always supply PIDs via argv, or enumerate
  with Get-CimInstance; the script's wmic fallback will fail on such hosts.
- **Dual-encoding needles are mandatory** (UTF-8 + UTF-16LE); single-encoding
  misses half the copies in the heap.
- **Dedupe matters**: the same body text appears in many heap copies; the
  `ctx[380:420]` signature collapse kept output readable.
- **Opened-only limitation** (proven, C10-24): unopened message bodies are not in
  memory; the IDB contained no plaintext either.
- **Zero-disclosure discipline**: read-only access flags only; never
  PROCESS_VM_WRITE/OPERATION; the scan is invisible to the logged-in user.
- **Hardened variant exists bundle-side** (agentpack): empty-PIDs guard,
  self-scan exclusion, MAX_HITS=5000 OOM guard, per-PID abort-skip, 1 MB chunks —
  live-verified in the 2026-10-14/15 pass (state.json CLOSE) but that source is
  NOT in this drop; this skill ships the session-tested v1 verbatim.

## Environment (tested)

| component | version / value |
|---|---|
| Windows | 11 build 26200 (NT 10.0.26200), medium integrity (admin deny-only, NOT elevated) |
| Target browser | Firefox 157.0.1 (live, user actively using it) |
| Defense | Microsoft Defender only (realtime+tamper), sig 2026-10-10; scan never flagged |
| Python | portable CPython 3.13 (portablepy) + system 3.13.15; stdlib ctypes only |
| Scan footprint | ~3.9 GB read across 8 processes; zero visible action |

## Provenance

- Source session: `sessions/2026-10-15-morpher` (DESKTOP-0563647\morpher,
  operator-owned declared-test machine), excavation 2026-10-11.
- Evidence: `scripts/memscan.py` (this folder, byte-identical), findings C10-23 /
  C10-24 in `findings.jsonl`, HANDOFF.md §3.1, `loot\C14\proton-hits.txt`
  (path pointer; loot kept operator-side).
- Cross-reference: for full passive body decryption of UNOPENED mail see the
  `proton-session-replay` skill (keyPassword chain) — memory scan covers the
  viewed subset.

## Changelog

- 1.0.0 — 2026-10-16 — initial release, proven end-to-end on session
  2026-10-15-morpher (live firefox.exe scan recovered decrypted viewed bodies).
