# Pilot full run: 6 books, S1-S4, batch (2026-11-22)

4,246 windows in 4 batches; all ended within 8 minutes. Cost $0.67 (whole project so far $0.73).
92% of windows fully accepted; 328 partial, 5 failed.

| Book | Sentences with S2 | Top themes | Norms | Notes |
| --- | --- | --- | --- | --- |
| Daodejing | 495 | Simplicity & non-striving, Good rulership, Cosmic order, Ultimate reality | 131, mostly recommendations | Profile fits the text |
| Dhammapada | 404 | Desire & attachment, Knowledge & ignorance, Liberation, Mindfulness, Self-discipline | 160, mostly recommendations | "Brahmana" (the true saint) tagged priests_clergy 65 times; ambiguous |
| Bhagavad Gita | 887 | Ultimate reality, Knowledge & ignorance, Liberation, Desire, Devotion | 175 | |
| Leviticus | 832 | Purity & pollution, Ritual & sacrifice, Sin, Atonement, Divine command | 864, mostly obligations and prohibitions | Women 89, sick 77, foreigners 50: the treatment questions are answerable |
| Analects | 1,649 | Good rulership, Duty & role, Wisdom, Knowledge & ignorance, Truthfulness | 386 | |
| Poetic Edda (gods) | 990 | Honor, Knowledge, Providence, Wisdom, Courage | 99 | 548 sentences with no theme (myth narrative); women 188 likely counts goddesses and giantesses |

**Rejections:** 540 records, almost all spans. 197 were the verifier's fault: Edda lines contain "|" caesura marks that the model leaves out of spans, and some curly quotes. The rest are real: the span was taken from a neighbouring sentence (frequent in the Analects, where dialogue is split into short sentences). Verifier now ignores punctuation, case and "|" when matching spans, and keeps the top 3 labels by salience instead of rejecting a record with 4 or 5.

**Watch:** Knowledge & ignorance is high in every book (41-120); the "know" word trap may persist. Goddesses counted as women in the Edda, and "son" possibly counted as children in the Analects; both are S4 card questions for the gold set.

## Retry with the looser span check ($0.07)

333 windows re-sent; 175 now complete. Coverage after the retry, sentences labelled out of total:

| Book | S1 | S2 | S3 | S4 |
| --- | --- | --- | --- | --- |
| Daodejing | 512/512 | 508/512 | 512/512 | 508/512 |
| Dhammapada | 415/415 | 414/415 | 413/415 | 413/415 |
| Bhagavad Gita | 910/910 | 904/910 | 907/910 | 905/910 |
| Leviticus | 867/867 | 842/867 | 854/867 | 862/867 |
| Analects | 1677/1677 | 1669/1677 | 1673/1677 | 1665/1677 |
| Poetic Edda | 1143/1143 | 1113/1143 | 1127/1143 | 1082/1143 |

Project spend so far: $0.80.
