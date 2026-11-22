# Reviewer guide

You make the system accurate. Every label you correct becomes a test case and a teaching example, and your proposals decide how the theme list grows.

## What you need

- Familiarity with at least one tradition in the corpus. Reading knowledge of its source language helps but isn't required.
- A browser, and an invite to Argilla *(planned, phase 1)*.
- 1–3 hours per review round. Rounds happen once for the gold set, then after each tier.

## What you review

| Queue | What you see | What you do |
| --- | --- | --- |
| Gold set (phase 1) | A target sentence with 4 sentences before and 2 after, plus draft labels | Correct the labels |
| Disagreements | Items where two models disagreed | Pick the right label, or say none fits |
| Label candidates | A proposed new theme with example passages | Approve, reject, or suggest a better name or parent |
| Tradition terms | Terms listed for a theme (Tao, Logos, ṛta…) | Add or correct terms from your tradition |

## How to label well

1. **Label the target sentence, not the window.** Context is there to help you understand the target.
2. **Use the codebook definition, not your own.** If the definition is wrong or unclear, label by the definition and leave a comment saying why.
3. **Force matters.** "Thou shalt not kill" is prescriptive; "and he slew them" is descriptive. Narration about a sin is not a rule against it.
4. **Salience:** 0 mentioned, 1 present, 2 central, 3 the point of the passage.
5. **When unsure, say so.** Mark the item uncertain instead of guessing. Uncertain items are useful data.

## Proposing a new label

Open a GitHub issue with the "Propose a label" form. Good proposals include:

- a one-line definition,
- 3 example passages (book, chapter, sentence),
- the nearest existing label and why it doesn't fit,
- terms other traditions use for the same idea, if you know them.

## Where to ask

GitHub Discussions → "Codebook" for definitions; "Introductions" to say which traditions you can cover.
