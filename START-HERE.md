# Start here

Wisdom Graph reads about 1,900 public-domain religious and philosophical books, one sentence at a time, to map where traditions agree and where they differ. Every sentence, chapter and book gets metadata from a set of small, single-purpose AI agents running on local GPUs, checked against human-reviewed examples.

**Status: phase 0 (setup).** The pipeline code doesn't exist yet. The guides describe the planned workflow; steps that aren't available yet are marked *(planned)*.

## 1. Pick your role

| Role | What you do | Time | Guide |
| --- | --- | --- | --- |
| Tradition reviewer | Check AI labels for a tradition you know; propose themes and tradition terms | 1–3 h per review round | [Reviewer guide](docs/guide-reviewer.md) |
| Compute runner | Run batches of books on your own NVIDIA GPU overnight and submit the results | 10 min setup per night | [Runner guide](docs/guide-runner.md) |
| Developer | Build pipeline pieces from the plan, through pull requests | As available | [Developer guide](docs/guide-developer.md) |
| Maintainer | Approve labels, agent cards and results; run review cycles | Joseph | [Maintainer guide](docs/guide-maintainer.md) |

## 2. Where everything lives

| What | Where |
| --- | --- |
| Code, agent cards, codebook, schemas, these guides | GitHub repo `wisdom-graph` (private for now; ask Joseph for access) |
| Questions and discussion | GitHub Discussions in the repo |
| Proposing a new theme, topic or tradition term | GitHub issue → "Propose a label" form |
| Corpus texts (one file per book) | Google Drive → Wisdom Graph → 02 Corpus → public-domain |
| Submitting results | Google Drive → 03 Outputs → incoming, plus a GitHub issue "Submit results" |
| Daily progress reports | Google Drive → 04 Reports |
| Project checklist | Google Drive → 00 Start here → Project checklist (also `CHECKLIST.md` here) |
| The full plan | "Wisdom Corpus — Multi-Level Semantic Analysis Plan" (ask Joseph for the link); summary in [docs/architecture.md](docs/architecture.md) |

## 3. Five rules for everyone

1. **Don't change an agent card or the codebook to fix a result.** Open an issue instead. Cards change only through the review cycle, so every run stays comparable.
2. **Run only tagged releases with the pinned model file.** A different model or quantization gives different results, and those results will be rejected.
3. **Never share anything from the restricted corpus folder.** Only texts marked public domain leave the project.
4. **Every result carries its fingerprints** (prompt hash, card version, model hash). Results without them are discarded.
5. **Ask in GitHub Discussions, not private messages,** so the answer helps the next person.

## 4. Your first hour

1. Read [docs/architecture.md](docs/architecture.md) (10 minutes).
2. Read your role's guide.
3. Introduce yourself in GitHub Discussions → "Introductions": your role, and for reviewers the traditions you know.
