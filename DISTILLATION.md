# DISTILLATION.md — session summary → skill playbook

The repeatable procedure for turning a collected post-exploitation session
summary (AGENTS.md runbook, notes, audit reports, tested scripts) into a
versioned skill folder in this library. Written after distilling the three
collected sessions; follow it so every skill has the same shape and composes
into a skill set rather than a pile of documents.

## 0. The flow — adding a new session (copy → distill → index)

1. **Capture (during the session, ideally):** keep the runbook (`AGENTS.md`),
   notes, reports and tested scripts in the session workspace, written so they
   pass the §1 checklist below. If the session is already closed: **copy the
   raw summary** — the rawest form available (runbook + notes + reports +
   scripts), not a further-distilled version of it.
2. **Add the session folder** to `sessions/<date-target>/` — one folder per
   target/case, named after it (see `sessions/2026-10-09-uygar-uslu/`,
   `sessions/2026-10-09-pixel9/`). Keep unredacted secret material in side
   files (mode 600); it never goes into a skill.
3. **Run the distill agent** with `DISTILL-PROMPT.md` (or this playbook):
   apply §1 to `sessions/<date-target>/`, then distill per §2 into
   `output/<date-target>/<skill-name>/` — the distiller's staging area;
   never write into the excavator bundle. One session can yield zero, one or
   several skills (2026-10-09-pixel9 → 2, 2026-10-09-uygar-uslu → 1,
   2026-10-06-keeper-vault → 1 draft).
4. **Gate** the result through §4 (quality gates) — no unproven claims, tagged
   `[UNVERIFIED]` where needed, checksum manifest present.
5. **Index:** add the skill row to `excavator/SKILLS.md` (this is §2 step 8)
   and version per `excavator/VERSIONING.md`.

## 1. When a session is distillable

A session summary is ready when it contains:

- [ ] a **proven end-to-end workflow** (steps that actually worked, not plans)
- [ ] **gotchas / failed approaches** — the time-savers; record even dead ends
- [ ] **tested scripts or paste-ready code** (copy byte-identical)
- [ ] an **environment/toolchain matrix** (exact versions — versions are crypto
      boundaries)
- [ ] a **deliverables pattern** (what the session produced, so the skill
      states its expected output)
- [ ] **provenance** (workspace, date, evidence paths)

If claims exist that were never tested, either drop them or tag `[UNVERIFIED]`
in SKILL.md — never present them as proven.

## 2. Procedure

1. **Inventory raw artifacts**: runbook (AGENTS.md), narrative (notes*.md),
   reports (audit.me / CREDENTIALS.md), scripts, probe outputs, recovered
   crypto facts, key-list files.
2. **Extract the proven workflow** as numbered steps. Every factual statement
   about a tool/format must be backed by the tested version from the source
   session.
3. **Carve scripts** into `scripts/` — but only when re-derivation is
   expensive (non-obvious crypto/framing, finicky host steps, repeat-canned
   sweeps; decision rule in `excavator/VERSIONING.md` "Code vs text").
   Byte-identical copies of session-tested code, one purpose per file,
   payloads ≤6000 chars (CLI/editor constraint learned in the win-cred
   session). Otherwise a paste-ready recipe in `references/` suffices.
4. **Deep-format facts** → `references/*.md` (binary/container formats, crypto
   recipes, protobuf field maps, version matrices). Toolchain matrix + sha256
   of every script → `references/toolchain-versions.md`; update it on every
   release (versioning policy: `excavator/VERSIONING.md`).
5. **Write SKILL.md** from the template (§3 below).
6. **Record provenance**: originating workspace, date, evidence artifacts —
   every claim must be traceable back to raw session material.
7. **Version**: 1.0.0 when the workflow is proven end-to-end; 0.x while draft
   or partially proven. Bump MINOR for a new technique/script, PATCH for
   wording/matrix refresh (policy: `excavator/VERSIONING.md`).
8. **Promote** (operator): the finished folder stays in
   `output/<date-target>/`; copying it into the excavator bundle's
   `skills/` and adding its `SKILLS.md` row is the explicit operator
   promotion step (ADD-SESSION.md step 5).

## 3. SKILL.md template

```markdown
---
name: <kebab-case-name>
description: <one paragraph; end with "Use when ...">
version: X.Y.Z
requires: <runtime/deps — e.g. python3+stdlib | pycryptodomex (bundled)>
---

# <title>

## When to use
## Workflow (proven end-to-end on the source session)
## Gotchas (proven)
## Environment (tested)
## Provenance
## Changelog
- X.Y.Z — <date> — initial release, proven on <session>.
```

## 4. Quality gates (check before release)

- No unproven claims — or explicitly tagged `[UNVERIFIED]`.
- Every script listed in `references/toolchain-versions.md` with sha256.
- **Secrets never appear** in SKILL.md or references — masked values
  (≤4–6 leading chars + length) or paths only; unredacted material stays in
  session side files (mode 600), never in the skill.
- No orphan findings rule: every technique states its expected output and
  where it lands in the deliverable.

## 5. Shared rules every post-exploitation skill inherits

Cross-session synthesis of the collected sessions — the common backbone:

1. **Fingerprint the environment first.** App versions are crypto boundaries
   (Chromium 148 vs v20 app-bound; py7zr 1.1.3 header format; Keeper 18.6.4
   proto schema ≠ Commander 18.1).
2. **Recon → index → targeted passes → masked reads → severity-ranked report**
   (P0/P1/P2/P3), then a rotation/remediation section.
3. **Attack the key-chain, not the data**: store → KDF → wrapping key → cached
   payloads → data. Prefer authenticated oracles (GCM tag, ECIES); reject
   unauthenticated CBC "decryptions" as garbage-oracles.
4. **Time-box every probe**: 20–30 s per CLI command; background process +
   exit-code poll + log tail for long jobs; never stream live output.
5. **Mask secrets in reports**; unredacted values only in separate mode-600
   files with a cleanup checklist.
6. **Minimal footprint on live stores** — prefer copies to scratch; when
   you must modify something live, journal before/after state (note:
   hardlinks to root-owned files may fail; plain cp -a to a scratch dir).
7. **Negative findings are findings**: empty wallet, absent keystore, a
   boundary that held (e.g. Keeper dataKey stayed master-password-bound) —
   report them explicitly.
8. **Denoise before reporting**: adblock filter lists, Fernet blobs and random
   base64 in transcripts are classic false positives; verify provider format,
   length and context.

## 6. Building the skill set (next steps)

- **Router skill** `post-exploitation-triage`: an index skill that, given a
  target (OS × installed-app inventory), routes to the applicable library
  skills in P0 order and states what to do when no skill exists yet (capture
  the session per §1 so it becomes distillable).
- **Pending distillations**: Keeper record-data decryption (blocked on
  master-password material — see the keeper skill's Open items);
  macOS Keychain / kwallet sessions; cloud-token sprawl sweep.
- **Per new session**: run §1 checklist during the session (write the runbook
  so it distills cleanly), then §2 after session close.

## Changelog

- 1.4.0 — 2026-10-16 — distillation output decoupled from the excavator
  bundle: §0 step 3 and §2 step 8 target `output/<date-target>/` (the
  distiller's staging area, tracked in git); promotion into `skills/` +
  a `SKILLS.md` row is the operator's explicit step (ADD-SESSION.md
  step 5).
- 1.3.0 — 2026-10-09 — content policy: text-first, code-when-expensive
  (decision rule in `excavator/VERSIONING.md` "Code vs text"); `requires:`
  frontmatter field added to the SKILL.md template.
- 1.2.0 — 2026-10-09 — excavator/distiller split: session drops live in
  `sessions/<date-target>/`, skill output goes to `excavator/skills/`,
  versioning policy extracted to `excavator/VERSIONING.md`.
- 1.1.0 — 2026-10-09 — §0 "adding a session" flow added (copy → distill →
  index).
- 1.0.0 — 2026-10-09 — initial playbook, distilled from the three collected
  sessions (win-cred-forensics, sms-backup-archive-crack,
  firefox-thunderbird-logins-decrypt, keeper-desktop-vault-decrypt draft).
