# output/ — distilled skills awaiting promotion

One subfolder per distillation run: `output/<date-target>/<skill-name>/`.
Produced by `DISTILL-PROMPT.md` runs (one run per session distills every
HANDOFF.md §5 candidate). Contents are gated per ADD-SESSION.md step 4,
then PROMOTED — copied by the operator into the excavator bundle's
`skills/` with a `SKILLS.md` row there (step 5). This folder is the
distiller's entire write boundary: nothing is written outside it and
`sessions/` stays read-only.
