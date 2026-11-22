# Team, access and workflows

The maintainer approves anything that changes what the system believes: labels, agent cards and accepted results. Everyone else proposes, runs and reviews.

## Roles and access

| Role | GitHub | Google Drive | Argilla |
| --- | --- | --- | --- |
| Maintainer | Admin | Owner of the Wisdom Graph folder | Owner |
| Developer | Write (branches and PRs; `main` is protected) | Viewer on 00–02, 04 | None |
| Tradition reviewer | Triage (issues, discussions) | Viewer on 00, 01, 05 | Annotator, own workspace |
| Compute runner | Triage | Viewer on 00–02; contributor on 03 Outputs/incoming | None |

Nobody except the maintainer gets access to `02 Corpus/restricted (do not share)`, which does not inherit the parent folder's sharing.

## The five workflows

### 1. Run a chunk *(planned, phase 3)*

1. Claim a book: open a PR that adds your name to `chunks/claims.csv`.
2. Download that book's tier archive from Drive `02 Corpus/public-domain`.
3. Run `wg run --chunk <chunk_id>` with the current release.
4. Upload the result bundle to Drive `03 Outputs/incoming/<your-name>/`.
5. Open a "Submit results" issue with the bundle's manifest. CI checks it, and the maintainer moves accepted bundles to `03 Outputs/accepted`.

### 2. Review labels *(planned, phase 1)*

1. Accept your Argilla invite.
2. Read the codebook entries for your queue.
3. Work through your queue. Flag anything the codebook doesn't cover with a comment.
4. Post questions about definitions in Discussions → "Codebook".

### 3. Propose a label

1. Open an issue with the "Propose a label" form.
2. Give the label, a one-line definition, 3 example passages with book and chapter, and the nearest existing label.
3. The maintainer decides at the next learning cycle.

### 4. Change code or an agent card

1. Pick or open an issue.
2. Branch, change, open a PR using the template.
3. CI must pass. A card or codebook change also needs the regression report (frozen test set, no label's F1 down more than 0.02).
4. The maintainer merges. Card changes take effect from the next tagged release.

### 5. Learning cycle (after each tier)

1. The system writes a review packet to Drive `05 Review packets`.
2. Reviewers check the candidates for their traditions (about 1 hour).
3. The maintainer approves or rejects each change.
4. Approved changes are merged, regression-tested and released as the next card version.

## Communication

| For | Use |
| --- | --- |
| Questions, ideas, introductions | GitHub Discussions |
| Work items and label proposals | GitHub Issues |
| Progress | Daily report in Drive `04 Reports` |
| Anything about access or rights | The maintainer directly |

## Release naming

`cards-vMAJOR.MINOR` for agent cards and codebook together, for example `cards-v1.0`. Runners always run a tagged release, never `main`.
