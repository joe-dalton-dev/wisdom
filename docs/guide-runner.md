# Runner guide

You lend your GPU overnight: download a book, run the pinned agents on it, and submit the results. Everything here is *(planned, phase 3)*; until then you can help test the setup.

## What you need

| Item | Minimum |
| --- | --- |
| GPU | NVIDIA with 16 GB VRAM for LLM jobs. 8 GB can run embedding and triage jobs only. |
| Disk | 50 GB free (model files, corpus archives, outputs) |
| Software | Git, Docker Desktop (on Windows with WSL2), a Google account with access to the Wisdom Graph Drive folder |
| Time | About 10 minutes to start a night's run and 5 minutes to submit |

## One-time setup *(planned)*

1. Clone the repo and check out the latest release tag: `git checkout cards-v1.0` (or newer).
2. Pull the container: `docker pull <image named in the release notes>`.
3. Download the pinned model file listed in `agents/models.lock` and check its SHA-256 matches.
4. Run `wg doctor`. It checks GPU, VRAM, model hash and disk space, and prints what job types your machine can run.

## Each run

1. Pick an unclaimed book in `chunks/claims.csv` and open a PR adding your name and today's date. Wait for it to be merged.
2. Download the book's archive from Drive `02 Corpus/public-domain` and check its hash against `02 Corpus/manifests`.
3. Start the run: `wg run --chunk <chunk_id> --hours 8`. You can stop with Ctrl+C at any time; finished jobs are kept and the next run resumes.
4. When the chunk is done, `wg bundle --chunk <chunk_id>` writes one zip plus `manifest.json`.
5. Upload the zip to Drive `03 Outputs/incoming/<your-name>/`.
6. Open a GitHub issue with the "Submit results" form and paste `manifest.json`.

## Why results get rejected

| Reason | Fix |
| --- | --- |
| Model hash doesn't match the lock file | Re-download the pinned model |
| Card version isn't a tagged release | Check out the release tag, not `main` |
| Verifier failures above 1% | Run `wg doctor`; report it in Discussions |
| Missing or edited manifest | Re-run `wg bundle`; never edit the manifest by hand |
| Same chunk claimed by someone else | Check the claims file before starting |

## Rules

- Don't change agent cards, prompts or the codebook locally.
- Don't keep or share texts from outside `public-domain`.
- One chunk at a time per person unless the maintainer agrees otherwise.
