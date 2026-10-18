# toolchain-versions — browser-memory-scan 1.0.0

## Environment matrix (tested on the source session)

| component | version / value |
|---|---|
| OS | Windows 11 build 26200 (NT 10.0.26200), medium integrity (admin deny-only, NOT elevated) |
| Target app | Firefox 157.0.1 (live, user-active); technique is browser-agnostic |
| Python | portable CPython 3.13 (portablepy) + system 3.13.15 |
| Deps | stdlib only (ctypes, ctypes.wintypes, subprocess fallback) |
| Defense | Microsoft Defender only (realtime+tamper, sig 2026-10-10) — scan not flagged |

Versions are crypto/boundary-relevant: the Win32 memory API surface used here
(VirtualQueryEx protect-value set, user-space ceiling 0x7fffffffffff) is
x64-Windows specific; re-verify on other builds.

## Script manifest (sha256, bytes = size)

| script | sha256 | bytes | session-tested context |
|---|---|---|---|
| scripts/memscan.py | 0d1fd2b4dafae92a4b97403a547c0bba3efe16d0716d5b88710d6b87b966ed8d | 4635 | live firefox.exe scan 2026-10-11, recovered decrypted viewed mail bodies (C10-23) |

Copies are byte-identical to `sessions/2026-10-15-morpher/scripts/` (verified
by matching sha256 at distillation time, 2026-10-16). `py_compile` clean.

## Bundle-side variant note

A hardened memscan (empty-PIDs guard, self-scan exclusion, MAX_HITS=5000,
per-PID abort-skip, 1 MB chunks) was live-verified in the excavator bundle's
`helpers\agentpack` during the 2026-10-14/15 pass (state.json CLOSE) — that
source is NOT part of this drop; the hash above is the session-tested v1.

## Update policy

Re-hash and bump this manifest on every release: MINOR for a new
technique/script, PATCH for wording/matrix refresh (excavator VERSIONING
policy).
