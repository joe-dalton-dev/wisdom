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

1. Upload `SacredTexts/corpus-books` public-domain files to `02 Corpus/public-domain`, one folder per tradition, using the Google Drive desktop app.
2. Put non-public-domain editions in `02 Corpus/restricted (do not share)`.
3. Upload `_books.csv` plus a SHA-256 per file to `02 Corpus/manifests`.
4. Later, add one zip per tier so runners download one file instead of hundreds.

## Access

Share the Wisdom Graph folder per the table in [team.md](team.md). Never share `restricted (do not share)`. Remove access when someone leaves.
