# Agent cards

Every specialist is defined by exactly one card. Every call to it is assembled, by code, from three layers in this order:

1. `_base.md` — shared rules for all LLM agents (pinned version).
2. `<ID>.yaml` — the role card: task, inputs, output schema, codebook slice, fixed examples, model, settings.
3. Call data — the window and triage candidates. The only part that changes per call.

## Rules

- **Stateless:** each call starts fresh; no history, no memory between calls.
- **Deterministic assembly:** the same card and input produce a byte-identical prompt. Its SHA-256 is stored on every output.
- **Everything pinned:** model file hash (`models.lock`), server build, sampling settings, codebook and example versions.
- **Cards change only through the learning cycle:** new version, regression test, changelog entry, tagged release. A chunk never switches card versions partway.

## Cards

| ID | File | Status |
| --- | --- | --- |
| S2 | `S2_theme_tagger.yaml` | Template draft |
| T1, T2, S1, S3, S4, V2, A1, C1, B1, X1, X2 | — | To be written in phase 2 |

`models.lock` lists the pinned model files and their SHA-256 hashes once the pilot picks them.
