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
| S1 | `S1_discourse.yaml` | Draft 0.1.0, Claude Haiku 5.5 |
| S2 | `S2_theme_tagger.yaml` | Draft 0.2.0, Claude Haiku 5.5 |
| S3 | `S3_norm_extractor.yaml` | Draft 0.1.0, Claude Haiku 5.5 |
| S4 | `S4_entities.yaml` | Draft 0.1.0, Claude Haiku 5.5 |
| A1 | `A1_themes.yaml`, `A1_norms.yaml` | Draft 0.1.0, Claude Opus 5.5; gold set only |
| T1, T2, V2, C1, B1, X1, X2 | — | To be written |

Cards have no examples yet; they come from the gold set (P0-11). Run them with `python -m pipeline` (see `pipeline/README.md`).

`models.lock` pins API models by ID with their prices, and local model files by SHA-256 once the bake-off picks them.
