# Codebook (label registry)

One versioned list of every label agents may use. Agents pick only from here; anything else is rejected by the verifier.

| File | Holds | Kind |
| --- | --- | --- |
| `themes.yaml` | 12 domains, 72 themes | What a passage means (Compassion, Cosmic order) |
| `topics.yaml` | 46 topics in 8 groups | What a passage is literally about (Fasting, Marriage) |
| `facets.yaml` | 7 closed value lists | Attributes such as speech act, force, stance |

**Status: v0.1.0 draft.** It must be merged with the existing 12-domain / 84-theme framework and the 20 quote-project themes, and every core label needs include/exclude rules plus 3 positive and 3 negative examples, before phase 0 closes.

## How labels change

1. Anyone proposes a label with the GitHub "Propose a label" issue form. Agents propose through S2's proposal slot.
2. At each learning cycle the maintainer reviews candidates that are seen in at least 20 sentences across 3 books and 2 traditions.
3. Approved labels get a version bump here, a CHANGELOG entry and a regression test before release.
4. At most 10 promotions per cycle.

Entry statuses: `core`, `candidate`, `retired`. Retired IDs are never reused.
