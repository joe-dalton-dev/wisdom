# Decisions

A record of decisions that shape the system. Change one only by adding a new dated entry below it, never by editing the old one.

## 2026-11-22 · Phase 0 decisions (maintainer)

| # | Decision | Answer |
| --- | --- | --- |
| 1 | v1 label set | One composite registry: the draft (72 themes, 46 topics) merged with the existing 12-domain / 84-theme file and the 20 quote-project themes |
| 2 | Context window | Sentences n−4 to n+2, stopping at chapter boundaries, 5 targets per call until the pilot tunes it |
| 3 | Discourse agent (S1) scope | Per paragraph; sentences inherit its labels unless flagged |
| 4 | Commentaries (Gill, Matthew Henry…) | Not tagged at level 1 and excluded from theme and norm statistics; linked to the verses they discuss |
| 5 | Claude API budget (€50) | 40% gold-set drafting, 30% prompt tuning (GEPA reflection), 30% adjudication |
| 6 | Maintainer review time | About 12 h across phases 0–2; full 600-item gold set, split 400 dev / 200 test |
| 7 | Learning loop | A cycle after each tier or every ~100 books; promote a label at 20+ sentences across 3 books and 2 traditions; at most 10 promotions per cycle; reject any change that lowers a label's test F1 by more than 0.02 |
| 8 | Chunks and catch-up | One book per chunk; improvements apply forward only; finished chunks get one catch-up pass after the last tier, with maintainer approval |

## 2026-11-22 · Review tool

- Argilla runs locally on the maintainer's PC in Docker. Reviewers connect over a private Tailscale network when they join. Move to a small EU cloud server only if reviewers need access while the PC is off. A Hugging Face Space was rejected because Spaces restart and new Spaces no longer get persistent storage.

## 2026-11-22 · Repository

- Method is public by choice: code, agent cards, prompts, codebook, schemas and docs, under Apache 2.0.
- Data: not published at all. Outputs stay in private Drive folders (`03 Outputs (private)`, `04 Reports (private)`, which do not inherit sharing); no data license is granted. All rights reserved.
- Repository is public. `main` is protected by the "Protect main" ruleset: pull requests only, the `validate` check must pass, no force pushes, no deletion.

## 2026-11-22 · Starting theme list

- The 72-theme draft in `codebook/themes.yaml` is the starting list. The older 84-theme `classification_taxonomy.json` and the 20 quote-project themes are not merged in; themes missing from the draft enter later through the learning loop, accepting that some labels get re-run.

## 2026-11-22 · Phase 2 API budget

- Phase 2 testing may use the Claude API (Haiku 5.5 in the bake-off against Gemma 4 26B, Sonnet for GEPA reflection) up to a hard limit of **$20**, set as a spend limit in the Claude Console. Whether Haiku runs the full level 1 is decided after the pilot, from its measured accuracy and cost per book.
