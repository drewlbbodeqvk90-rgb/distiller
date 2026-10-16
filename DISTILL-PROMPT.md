# DISTILL-PROMPT — first message for a distillation run

Fill the placeholders (`<date-target>`, `<excavator-root>`), then feed to an
agent as its first message. ONE run per session — the agent reads the
session's HANDOFF.md and distills every skill candidate listed in its §5
(typically one run yields one or several skills).

--- BEGIN PROMPT ---
You are a skill-distillation agent. Convert the completed post-exploitation
session `<date-target>` under the distiller's `sessions/` into versioned,
self-contained skill folders, ready for the excavator bundle.

SESSION ENTRY: read `<date-target>/HANDOFF.md` FIRST — it is the
excavator's fixed interface (§1 identity, §2 results, §3 proven techniques
with evidence pointers, §4 dead-ends, §5 skill candidates, §6 scripts
verdicts, §7 artifact index, §8 open leads). Its §5 SKILL CANDIDATES are
the binding extraction plan: distill every candidate listed there, in
order. If the session has no HANDOFF.md, fall back to the raw record and
the DISTILLATION.md §1 checklist.

For each candidate, follow DISTILLATION.md §2–§4:
1. Inventory the session artifacts the candidate points to.
2. Extract the PROVEN end-to-end workflow as numbered steps. Every factual
   claim must be proven in-session or tagged `[UNVERIFIED]`.
3. Carve scripts into the skill's `scripts/` — byte-identical to the
   session-tested code, one purpose per file, payloads ≤6000 chars.
4. Write `references/`: deep-format facts (binary/container formats, crypto
   recipes, field maps) + `references/toolchain-versions.md` (tool matrix +
   sha256 of every script).
5. Write `SKILL.md` from the §3 template: frontmatter (name, description
   ending with "Use when ...", version), When to use, Workflow, Gotchas
   (proven), Environment (tested), Provenance, Changelog.
6. Apply §4 quality gates and report any item you could not satisfy.

OUTPUT: one finished skill folder per §5 candidate at
`<excavator-root>/skills/<skill-name>/`, each with a row appended to
`<excavator-root>/SKILLS.md` (name, version, source session =
`<date-target>`). Resolve `<excavator-root>` from the excavator bundle's
actual deployment location. Version per `<excavator-root>/VERSIONING.md`:
1.0.0 when proven end-to-end, 0.x while draft/partial. Finish with a final
tally: skills created, candidates skipped and why.

RULES: never copy secret values into a skill (paths/masks only, ≤4–6 chars
+ length); do not modify the session folder; every claim traceable to raw
evidence.
--- END PROMPT ---

## Changelog

- 1.2.0 — 2026-10-15 — session-driven flow: ONE run per session distills
every HANDOFF.md §5 candidate (placeholders reduced to `<date-target>` +
`<excavator-root>`); dead-ends and scripts-verdict ingestion explicit;
final-tally reporting added.
- 1.1.0 — 2026-10-15 — INPUT reads `HANDOFF.md` first when present
(fixed excavator-side interface; §5 skill candidates binding); OUTPUT
paths de-Linuxed to `<excavator-root>` placeholders.
- 1.0.0 — 2026-10-09 — initial release; flow per DISTILLATION.md §0.