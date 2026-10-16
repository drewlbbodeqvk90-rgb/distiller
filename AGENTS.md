# AGENTS.md — distiller project: development & maintenance manual

**Audience:** an agent or human maintaining THIS project (the operator's
distillation workspace). NOT the distillation agent itself — session
distillation is driven by `DISTILL-PROMPT.md` + `DISTILLATION.md` via the
`ADD-SESSION.md` flow.

## What this folder is

Append-only workspace: raw excavation session records (`sessions/`) plus
distillation prompts/playbooks. May contain sensitive session material —
keep it local; never publish without a secret scan.

## Maintenance rules

1. `sessions/` is append-only: never edit or delete a session record;
   additions only. Unredacted secret side-files stay mode-600 here or at
   their original location (record with a `POINTER.md`).
2. Skills are produced INTO `excavator/skills/<name>/` + an
   `excavator/SKILLS.md` row (versioning per `excavator/VERSIONING.md`) —
   never store skill folders inside this project.
3. `DISTILLATION.md` / `DISTILL-PROMPT.md` / `ADD-SESSION.md`: bump the
   Changelog on every edit; keep the `--- BEGIN/END PROMPT ---` markers in
   DISTILL-PROMPT.md intact.
4. `references/` holds source material — do not modify (historical
   provenance); add new reference docs as siblings.
5. New-session intake: follow `ADD-SESSION.md` steps 1–5 (drop → §1
   checklist → DISTILL-PROMPT run → gates → SKILLS.md row).

## Verification

- Every session folder carries a README/POINTER with provenance and
  distillation status.
- No skill folders inside this project.
- Secret scan (provider key prefixes) across `sessions/` before any
  sharing or commit.
- `.gitignore` excludes `sessions/` wholesale — session records are
  plaintext-by-design and are never committed (mirrors the excavator's
  `session/` policy). Defensive per-file patterns remain for material
  copied outside `sessions/`. The secret scan remains the gate for
  anything that is not under `sessions/`.