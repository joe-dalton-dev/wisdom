# Pipeline (pilot version)

Runs the level 1 agents (S1–S4) on Claude Haiku 5.5 over the 6 pilot books. Text is split by code; Claude only labels; every reply is checked by the V1 verifier before it is saved.

| Module | Does |
| --- | --- |
| `split.py` | Book files → chapters → paragraphs → sentences (stable IDs) → windows of 5 targets with 4 before / 2 after as context. Removes editor's notes in `[brackets]`, page markers and running heads. |
| `assemble.py` | Builds each request from `agents/_base.md` + the agent card + the codebook. The system prompt is the same for every call of an agent, so it is cached. Same card + same window → same hash. |
| `verify.py` | V1: reply parses, one record per target, no records for context, labels exist in the codebook, spans are really in the text, numbers in range. |
| `ledger.py` | SQLite job ledger. A job is keyed by card + window text, so re-running skips finished work and retries only failed or partial windows (max 3 attempts). |
| `runner.py` | Sends windows (sync or Message Batches), applies the spend cap, writes outputs. |
| `report.py` | One `report.csv` per book: every sentence with its labels, for Excel. |

## Setup (once)

```
python -m pip install -r requirements.txt
copy config\pilot.example.yaml config\pilot.yaml
```
Check `corpus_root` in `config/pilot.yaml` points at your local `corpus-clean`. `ANTHROPIC_API_KEY` must be set (P2-10).

## Run

```
python -m pipeline split                                   # no API calls; prints sentence counts
python -m pipeline estimate                                # calls and expected cost for everything pending
python -m pipeline run --book daodejing --agent S2 --limit 10 --mode sync   # smoke test, under 1 cent
python -m pipeline report --book daodejing                 # writes data/pilot/daodejing/report.csv
```

Full pilot (all 6 books, all 4 agents, about $1 in batch mode):
```
python -m pipeline run --mode batch --wait
python -m pipeline report
```

- `--mode batch` is half price; results usually come back within an hour, at most 24 h. Without `--wait`, run `python -m pipeline collect` later. Ctrl+C is safe; nothing finished is redone.
- `--mode sync` is full price but returns in minutes. Use it for small tests.
- `--max-usd` (default 2.00) is a hard stop on total recorded spend. The Console's $20 workspace limit is the second line of defence.
- `python -m pipeline status` shows windows done, rejected and spend per book and agent.

## Outputs (in `data/pilot/<book>/`, never committed)

| File | Holds |
| --- | --- |
| `sentences.jsonl`, `paragraphs.jsonl`, `chapters.jsonl` | The split text with IDs |
| `out_S1.jsonl` … `out_S4.jsonl` | Accepted records, each with provenance: card, codebook, model, prompt hash, message and batch IDs |
| `rejects_S*.jsonl` | Records the verifier refused, with the reason (review these to improve the cards) |
| `report.csv` | Everything joined per sentence |

## Tests

```
python -m unittest tests.test_pipeline
```
Uses a fake Claude client; needs no API key or corpus.

## Not built yet

T1/T2 (embeddings, triage), V2 judge, the gold set and scoring, Gemma 4 for the bake-off, levels 2–4.
