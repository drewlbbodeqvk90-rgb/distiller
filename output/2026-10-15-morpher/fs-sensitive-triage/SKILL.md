---
name: fs-sensitive-triage
description: Sensitive-content discovery by PATH/FILENAME heuristics only — a pruned,
  budgeted walk of the user profile that lexicon-scores directory and file names,
  adds extension and media-density scoring, and ranks the folders where people
  actually keep material they would not want exfiltrated (private media, wallet
  backups, KYC scans, chat exports). Found a 4 × 209 MB personal-video cluster that
  every shell-folder audit missed because Pictures/Videos were empty. Use when you
  need a cheap, silent, name-only first pass for sensitive files on a Windows host —
  run it BEFORE the credential inventory passes.
purpose: Name-only sensitive-file discovery (lexicon + extension + media-density scoring); silent first pass
version: 1.0.0
requires: python3+stdlib (os, time, re) | read-only | operator consent for scope
---

# FS path/filename triage for sensitive content

## When to use

- The finding class is "files the user would not want exfiltrated" — private
  media, personal documents, phone backups, secret material — which standard
  credential inventories (C01–C28-style passes) never look for.
- You need discovery WITHOUT content reads: name-only scoring is cheap, silent,
  and high-precision for this class.
- Early in an engagement: runtime is trivial (4–15 s per pass) — belongs in the
  WIDE SWEEP FIRST phase, before targeted credential work.

## Workflow (proven end-to-end on session 2026-10-15-morpher)

1. **Configure `scripts/fs-triage.py`** (byte-identical session copy): set
   `OUT` (report dir, created if missing) and `ROOTS` (session: user profile +
   `C:\Users\Public`). Wall-clock budget `BUDGET_S = 150` (actual: 15 s v1 /
   4 s v2).
2. **Run v2 (calibrated)**: `python -X utf8 fs-triage.py v2`
   (no argument = v1 behavior). The walk prunes by directory NAME
   (`PRUNE` set — v2 extends it with toolchains/app-internals), stats every
   file, and buckets media/doc/archive extensions.
3. **Read the two outputs** in `OUT`:
   - `dir-hits-v2.txt` — directories ranked by name-keyword score + media-density
     bonus (`files=… media=N(…MB) docs=… arch=… [keywords]`), top 250.
   - `file-hits-v2.txt` — globally ranked files (score ≥4), top 3000, with size,
     mtime, and matched keywords/ext as the reason string.
4. **Confirm the top cluster with a targeted media listing** (name/size/mtime
   only) before reporting — proven flow: the top hit cluster was 4 × ~209 MB
   `0926*.mp4` dated 2026-09-27, 3 in `AppData\Local\CapCut\Videos` + 1 copy in
   Downloads root, while shell Pictures/ AND Videos/ were EMPTY — a standard
   media-folder audit would have reported none.
5. **Report as severity-ranked findings** with the reason string intact (which
   keywords/ext matched); tag AppData hits separately from user-space roots
   (calibration rule 5). Negative space is informative too (proven: no Dropbox,
   OneDrive client present but 0 personal files).

## Calibration rules (v1 → v2, all proven — see references/)

1. Prune by NAME first (toolchains, package managers, app internals): `private`
   in a Qt cache is noise, `private` in `Dropbox\` is gold.
2. Noise-extension blacklist (`.rst .html .h .py .js .dll .exe …` docs/code of
   installed software) — else CMake/Python doc files flood the ranking
   (`FIND_XXX.rst` matched 'xxx').
3. Tag the agent's own prior audit output as self-referential noise AND as an
   integrity check (proven: the previous session's `windows-creds-extractor`
   results dir scored top in v1).
4. Media-density bonus beats keyword score for the video-class finding.
5. Score dirs RELATIVE to user-space roots; report AppData hits separately.
6. Runtime is trivial — schedule the pass in the wide-first sweep.

## Gotchas (proven)

- **v1 is noisy by design**: 95 k files / 724 hits in 15 s vs v2 31 k files /
  363 hits in 4 s — always run v2 for reporting; keep v1 only for baseline
  comparison.
- **Results are indicators, not proof**: a `private` dir may be empty; an
  innocuous dir may hold the secret. Confirm top clusters with a name/size/mtime
  listing before severity assignment.
- **Names only**: no file content is opened (optional EXIF/EXT-header spot-checks
  on flagged media are a follow-up, NOT part of this pass by default).
- **Ethics/scope**: operator consent for the walked scope; keep the report
  name/metadata-level.
- **Budget guard**: the walk hard-stops at `BUDGET_S`; on huge profiles the
  last roots may be unterminated — re-run with tighter `PRUNE` if needed.
- Proven follow-up leads (open, not in this skill): EXIF camera correlation,
  EXIF-stripping detection, duplicate detection across devices, cloud-sync
  config review (which folders ARE synced where).

## Environment (tested)

| component | version / value |
|---|---|
| Windows | 11 build 26200 (NT 10.0.26200), medium integrity (NOT elevated) |
| Python | portable CPython 3.13 (portablepy) — stdlib only |
| Walk volume | ~31–95 k files, 4–15 s wall clock, no AV friction (Defender only) |
| Output | 2 ranked text reports per run (`dir-hits[-v2].txt`, `file-hits[-v2].txt`) |

## Provenance

- Source session: `sessions/2026-10-15-morpher` (DESKTOP-0563647\morpher,
  operator-owned declared-test machine), excavation 2026-10-11.
- Evidence: `scripts/fs-triage.py` (byte-identical copy in `scripts/`);
  proposals.md §3 (full technique record + calibration doctrine); findings
  FS-01/FS-02/FS-03 in `findings.jsonl`; HANDOFF.md §3.3 + §5.4;
  `loot\fs-triage\` (path pointer; loot kept operator-side).
- A hardened copy of this script also lives in the excavator bundle's
  `helpers\agentpack` (walk+rank verified live in the 2026-10-14/15 pass per
  state.json CLOSE) — bundle-side, not part of this drop.

## Changelog

- 1.0.0 — 2026-10-16 — initial release, proven end-to-end on session
  2026-10-15-morpher (v1+v2 runs; personal-media cluster found).
