# Improvement round 1: S2 0.4.0 and S3 0.3.0

## Split
`project/gold_split.json` freezes the gold windows: 33 dev and 17 test per book (102 test windows, about
460 sentences). Card examples and rules come from dev only. Test is only scored. A check confirms no
test sentence appears in either card.

## Baseline (Haiku, pilot cards, pilot outputs)

| | dev | test |
|---|---|---|
| Themes F1 (P / R) | 0.554 (0.59 / 0.52) | 0.523 (0.56 / 0.49) |
| Norm modality F1 | 0.685 | 0.697 |

## What dev showed
- Themes: Haiku gives 3 themes to 3% of sentences; the gold set does so for 15%. The old rule
  "Most sentences carry 0 to 2 themes. Do not stretch" held recall down. Most missed: Simplicity,
  Self-cultivation (missed 34 of 39), Wisdom, Retribution. Most over-used: Knowledge & ignorance (37 extra).
- Norms outside Leviticus: almost all misses are implicit recommendations (ideal-person portraits,
  conduct tied to its result, "if we could ... it would be better"). Extras are self-reports, what
  others praise, and one-off acts.
- Leviticus: Haiku joins several ritual steps into one norm and tags past-tense narrative as law.

## Changes
- S2 0.4.0: check for a second and third idea; narrower rule for Knowledge & ignorance; pointers for
  Self-cultivation, Magic, and Retribution vs Liberation; 7 dev examples.
- S3 0.3.0: a three-part definition of recommendation and what doesn't count; one norm per action;
  past-tense rites are no norm; direct commands are obligations; 6 dev examples.

## Result on test
(fill in after `gold-haiku`)
