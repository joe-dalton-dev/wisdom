# Gold set and first scores (2026-11-22)

Silver standard: Opus 5.5 and Sonnet 5.5 labelled 300 windows (1,371 sentences) with S2 0.3.0 and S3 0.2.0; Opus (A1) adjudicated 387 disputed windows. Cost $9.59; project total $10.39.

**Agreement between the two reference models:** themes and topics, exact same set, 56% of sentences (Leviticus 44%, Edda 74%); norms, same modalities, 86%.

**Haiku 5.5 (pilot cards) against the gold set**

| Agent | Measure | Score |
| --- | --- | --- |
| S2 themes | F1 (precision / recall) | 0.54 (0.58 / 0.51) |
| S2 topics | F1 | 0.56 |
| S3 norms | modality F1 | 0.69; Leviticus 0.87, other books 0.44-0.57 |
| S3 | norm / no norm F1 | 0.79 |

For comparison on themes: Sonnet 0.85, Opus 0.93. Opus is inflated because it also adjudicated, so the gold set leans toward Opus.

**Where Haiku falls short**
- Themes: it labels fewer themes than the gold set in every book, so recall is the main gap. Weakest books: Poetic Edda 0.38, Analects 0.43. Weakest labels (5+ gold uses): Gender roles, Forgiveness, Fate & free will, Purpose of life, The outsider, Magic & invocation, Self-cultivation, Providence, Priesthood (topic), Mystical union.
- Norms outside Leviticus: almost all errors are "recommendation". Haiku misses 128 recommendations and adds 61 that the gold set does not have. The line between general teaching and advice is the problem, not rule-finding.

**Caveats:** the gold set measures agreement with the strongest Claude models, not scholarly truth; the two reference models themselves disagree on half the theme sets, which suggests some themes overlap.
