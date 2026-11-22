# Wisdom Graph

Sentence-level, chapter-level and book-level metadata for about 1,900 public-domain religious and philosophical texts, built to show where traditions agree and where they differ. It starts with religious texts; philosophy follows. The corpus lives in Google Drive, so Drive access is needed to run anything.

**New here? Read [START-HERE.md](START-HERE.md).**

## Status

Phase 0 (setup). This repository currently holds the structure, onboarding guides, draft codebook and agent-card templates. Pipeline code starts after the plan's open decisions are answered. Progress: [CHECKLIST.md](CHECKLIST.md).

## Layout

| Path | Contents |
| --- | --- |
| `START-HERE.md` | Orientation for every new contributor |
| `CHECKLIST.md` | Project task list (generated from `project/checklist.csv`) |
| `docs/` | Architecture summary, team and workflows, one guide per role |
| `agents/` | Shared base prompt, agent cards, pinned model list |
| `codebook/` | Themes, topics and facets (the label registry) |
| `schemas/` | JSON Schemas for agent outputs |
| `pipeline/` | Code (not started) |
| `chunks/` | Chunk claims for compute runners |
| `config/` | Example configuration |
| `tools/` | Small helper scripts |

## Data

The corpus and outputs live in Google Drive (Wisdom Graph folder), not in this repository. See [docs/team.md](docs/team.md) for access.

## License

Code: Apache License 2.0 (see `LICENSE`). Output data: license to be decided (checklist item P0-07).
