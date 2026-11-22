# Maintainer guide

The maintainer (Joseph) is the final approver for labels, agent cards, releases and accepted results, and the only person holding the Claude API key.

## Routines

| When | Task | Time |
| --- | --- | --- |
| Every morning | Read the daily report in Drive `04 Reports`; act on anything under "Needs you" | 5 min |
| As results arrive | Check CI on "Submit results" issues; move passing bundles from `incoming` to `accepted` | 5 min per bundle |
| After each tier | Learning cycle: review the packet in `05 Review packets`, approve or reject, merge, tag a release | 30–60 min |
| Weekly | Check Claude spend against the €50 cap; check the monitoring sample; update the checklist | 15 min |
| Monthly | Back up the ledger and `03 Outputs/accepted`; review access lists | 15 min |

## Approving a new label

Approve only if all of these hold:

1. Seen in at least 20 sentences across 3 books and 2 traditions.
2. Not a near-duplicate of an existing label.
3. A clear one-line definition and 3 positive plus 3 negative examples exist.
4. No more than 10 promotions in this cycle.

## Accepting results

A bundle is accepted when CI passes (schema, hashes, verbatim spans), its card version is a tagged release, and its verifier failure rate is under 1%. About 5–10% of chunks are assigned to two runners; compare those before accepting either.

## Corpus upload (phase 0)

1. The corpus is in Drive as `corpus-clean.zip` (plain .txt) in the [Wisdom Corpus](https://drive.google.com/drive/folders/1NgoZKQOwmgWHijhpxnSQ1Cakp3o0zajo) folder, uploaded 2026-11-22. `FullSacredTextHTML.zip` next to it is the original HTML mirror; it keeps some translator and date metadata the .txt files lack. Replace the zip when the corpus changes.
2. Put non-public-domain editions in `02 Corpus/restricted (do not share)`.
3. Build the manifest on your PC and upload it to `02 Corpus/manifests`:
   `python tools/make_manifest.py build "C:/Users/joseph dalton/Documents/ClaudeMemory/SacredTexts/corpus-books" books_manifest.csv`
   Runners check their download with `python tools/make_manifest.py check <their copy> books_manifest.csv`.
4. Later, add one zip per tier so runners download one file instead of hundreds.

## Argilla on your PC (review tool)

Argilla runs locally in Docker, so review data never leaves your machine. It needs no GPU; reviewing happens in the daytime while the GPU runs at night.

### Install (about 30 minutes, once)

1. Install Docker Desktop for Windows with the WSL2 backend. In Settings → Resources, give it at least 4 GB of memory (Elasticsearch needs it).
2. Make a folder, for example `C:\argilla`, and open a terminal there.
3. Download the official compose file:
   `curl https://raw.githubusercontent.com/argilla-io/argilla/main/examples/deployments/docker/docker-compose.yaml -o docker-compose.yaml`
4. Open `docker-compose.yaml` and replace the default owner username, password and API key with your own. Keep the API key in your password manager; scripts use it to load data.
5. Start it: `docker compose up -d`. First start takes a few minutes while Elasticsearch and PostgreSQL initialise.
6. Open http://localhost:6900 and sign in with your new credentials.

### Day to day

| Task | Command or step |
| --- | --- |
| Start | `docker compose up -d` in `C:\argilla` |
| Stop | `docker compose stop` |
| Check it's healthy | `docker compose ps`; logs with `docker compose logs -f` |
| Never run | `docker compose down -v` (the `-v` deletes every dataset and review) |

### Backups

Export every dataset weekly to Drive `03 Outputs (private)/argilla-backups/` with the Argilla Python SDK (`tools/argilla_backup.py`, *planned*). Until that script exists, export from the dataset's settings page before and after every review session.

### Giving reviewers access (when they join)

1. Install Tailscale on your PC and invite the reviewer to your Tailscale network. Never forward port 6900 on your router.
2. Create an Argilla user for them with the annotator role, in their own workspace.
3. They open `http://<your-pc-name>:6900` while your PC is on.
4. If reviewers need access while your PC is off, move Argilla to a small EU cloud server: export, set up there, re-import.

## Access

Share the Wisdom Graph folder per the table in [team.md](team.md). Never share `restricted (do not share)`. Remove access when someone leaves.
