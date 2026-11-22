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

## 2026-11-22 · Repository

- Code license: Apache 2.0.
- Data license: CC BY-NC 4.0 (`LICENSE-DATA.md`). Perseus-derived records stay CC BY-SA 4.0 because their source requires it.
- Repository is public. `main` is protected by the "Protect main" ruleset: pull requests only, the `validate` check must pass, no force pushes, no deletion.
