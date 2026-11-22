# Developer guide

You build the pipeline from the plan. The plan is approved section by section before code is written, so check that an issue exists and is marked `approved` before starting anything substantial.

## Ground rules

1. **Text is split by deterministic code, never by an agent.** Agents only analyse.
2. **Agents are stateless.** Every call is assembled from the agent card and the call data, nothing else.
3. **No counts from LLMs.** Distributions, shares and rankings are computed in code.
4. **Every output names its versions:** card version, prompt hash, model hash, codebook version.
5. **Every job is resumable and idempotent.** A job key is the hash of input text plus card version. Done jobs are skipped.

## Repository layout

| Path | Contents |
| --- | --- |
| `agents/` | Shared base prompt, one card per specialist, `models.lock` |
| `codebook/` | Themes, topics, facets (the label registry) |
| `schemas/` | JSON Schemas for every agent's output |
| `pipeline/` | Code *(not started)*: adapters, runner, ledger, verifier, rollups |
| `chunks/` | Chunk claims for runners |
| `config/` | Example configuration; real config is gitignored |
| `docs/` | Architecture, team, guides |
| `.github/` | Issue forms, PR template, CI |

## Stack (planned)

Python 3.11, Pydantic and Instructor for typed calls, llama.cpp `llama-server` for local models, DuckDB and Parquet for records, SQLite for the ledger, DSPy for prompt optimization, wtpsplit for sentence splitting, GLiNER2 and SetFit for triage, Argilla for review. Choices are confirmed in the pilot.

## Workflow

1. Pick an `approved` issue, or open one describing the change.
2. Branch from `main`: `feat/<short-name>` or `fix/<short-name>`.
3. Keep PRs small: one component or one card change.
4. Fill in the PR template. CI must pass.
5. Changes to `agents/` or `codebook/` need a regression report attached (frozen test set; no label's F1 down more than 0.02).
6. The maintainer reviews and merges.

## Never commit

Corpus text, model files, outputs, API keys, `config/*.yaml` other than examples. `.gitignore` covers the usual paths; check before pushing.
