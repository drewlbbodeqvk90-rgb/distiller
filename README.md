# distiller — session records → versioned skills

Operator-side project. The sibling `excavator/` bundle (independent folder)
runs the actual excavations; this project turns their raw session records
into versioned skill folders that are handed back to the excavator's
`skills/`.

## Layout

| Path | Purpose |
|---|---|
| `DISTILL-PROMPT.md` | paste-ready first message for a distillation run |
| `DISTILLATION.md` | detailed playbook (§1 checklist, §2 procedure, §3 template, §4 gates) |
| `ADD-SESSION.md` | human-facing session → skill flow |
| `sessions/` | raw session drops, one folder per session (append-only) |
| `references/` | source material (`rules-from-another-project.md` — provenance of the C01–C28 inventory embedded in the excavator's START-PROMPT) |

## Intake — sessions/

- One folder per completed session: `sessions/<YYYY-MM-DD-target>/` with the
  agent's session package (`AGENTS.md` runbook, `scripts/`, `state.json` /
  findings). See `sessions/_template/` for the expected shape.
- Unredacted secret side-files NEVER enter a skill — keep them mode-600 in
  the session folder or at their original location with a `POINTER.md`.

## Process

1. Verify the drop against the `DISTILLATION.md` §1 distillability
   checklist.
2. Run `DISTILL-PROMPT.md` as the agent's first message (or follow
   `ADD-SESSION.md` manually).
3. The produced skill folder lands in `excavator/skills/<skill-name>/` + a
   row in `excavator/SKILLS.md` (versioning per `excavator/VERSIONING.md`).

## Changelog

- 1.0.0 — 2026-10-09 — split from the former CASE-SKILLS collection into an
independent distiller project (sessions + distillation prompts); the 4
distilled skills moved verbatim to the sibling excavator/ bundle.
