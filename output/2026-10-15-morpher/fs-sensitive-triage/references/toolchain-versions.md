# toolchain-versions — fs-sensitive-triage 1.0.0

## Environment matrix (tested on the source session)

| component | version / value |
|---|---|
| OS | Windows 11 build 26200 (NT 10.0.26200), medium integrity (NOT elevated) |
| Python | portable CPython 3.13 (portablepy) — stdlib only (os, time, re, sys) |
| Walk volume | v1: ~95 k files / 15 s / 724 hits; v2: ~31 k files / 4 s / 363 hits |
| Budget | BUDGET_S = 150 s wall clock (hard stop) |
| Defense | Defender only (realtime+tamper, sig 2026-10-10) — walk not flagged |

Runtime scales with file count, not size — the 150 s budget held with big
margin on both v1 and v2 runs; on exotic profiles re-check via the console
walk-stats line.

## Script manifest (sha256, bytes = size)

| script | sha256 | bytes | session-tested context |
|---|---|---|---|
| scripts/fs-triage.py | 459d997b330c99df716975dbfee8a857e2ba2be5011c50023892a4500fd6c1d3 | 6356 | v1 + v2 (`v2` argv) runs on the source host; produced dir-hits/file-hits reports and the CapCut media-cluster finding (FS-01/02) |

Copy is byte-identical to `sessions/2026-10-15-morpher/scripts/fs-triage.py`
(sha256 verified at distillation time, 2026-10-16). `py_compile` clean.

Script notes:

- Edit `OUT` (report dir) and `ROOTS` (walk roots) at the top before running;
  the session values point at the operator's original session workspace paths.
- `python -X utf8 fs-triage.py v2` for the calibrated pass; no argument runs
  v1 (kept for baseline comparison only).
- A hardened/verified copy of this script also lives in the excavator bundle's
  `helpers\agentpack` (walk+rank verified live per state.json CLOSE) —
  bundle-side, not part of this drop; the hash above is the session-tested
  original.

## Update policy

Re-hash and bump this manifest on every release: MINOR for a new
technique/script, PATCH for wording/matrix refresh (excavator VERSIONING
policy).
