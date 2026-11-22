# Architecture in brief

Code does the counting; small AI agents do the interpreting; every output is checked before it is stored. This page summarizes the full plan document.

## The four levels

| Level | Unit | What gets recorded |
| --- | --- | --- |
| 1 · Sentence | One sentence (a verse is never split) | Speech act, speaker, force, up to 3 themes and 3 topics, social categories, norms (what is required, forbidden or allowed), entities |
| 2 · Chapter | A chapter or equivalent division | Computed theme and topic distributions, plus a short synthesis whose every claim cites sentence IDs |
| 3 · Book | A whole book | The book's position on each theme, and a treatment profile per social category |
| 4 · Cross-tradition | Pairs and clusters across traditions | Parallels, contrasts and claim clusters, with copying and translation filtered out |

## Focus windows

Each level 1 call labels 5 target sentences and shows the 4 sentences before and 2 after as read-only context. Every sentence is labelled exactly once. Windows stop at chapter boundaries.

## Agents ("specialists")

Each agent has one job, one output schema and one agent card (see [agents/README.md](../agents/README.md)).

| ID | Job | Level |
| --- | --- | --- |
| T1 | Embeddings | 1 |
| T2 | Triage: candidate themes, normative flag, social-category mentions | 1 |
| S1 | Discourse: speech act, speaker, addressee, force | 1 |
| S2 | Theme and topic tagger | 1 |
| S3 | Norm extractor | 1 |
| S4 | Entity and pronoun resolver | 1 |
| V1 | Verifier (code): schema, IDs, verbatim spans, allowed labels | all |
| V2 | Second-opinion judge on a sample | all |
| A1 | Adjudicator for disagreements (Claude, maintainer only) | all |
| C1 | Chapter synthesizer | 2 |
| B1 | Book synthesizer | 3 |
| X1 | Cross-tradition comparator | 4 |
| X2 | Theme discoverer (new label candidates) | 4 |

## The label registry

One versioned list of themes, topics and facets lives in [codebook/](../codebook/). Agents pick only from it. New labels arrive as candidates (from S2's "none fit" proposals, C1 and X2) and become core only after maintainer review.

## How the system improves

Between tiers of books there is a learning cycle: collect signals → propose changes → maintainer review → regression test on a frozen test set → apply to the next chunks. Finished chunks are never reprocessed mid-run; changes for them wait for one catch-up pass at the end.

## Running in chunks

Work is tracked in a ledger, one row per job, keyed by input hash plus card version. A chunk is one book. Runs can stop and resume at any time; finished jobs are never redone.

## Storage

| What | Where |
| --- | --- |
| Raw model replies | JSONL |
| Records | Parquet, queried with DuckDB |
| Graph and vectors (later) | Neo4j and LanceDB, loaded from Parquet |
| Corpus and shared outputs | Google Drive |
| Code and configuration | GitHub |
