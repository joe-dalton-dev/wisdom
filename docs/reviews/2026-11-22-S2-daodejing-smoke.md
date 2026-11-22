# Review: S2 smoke test, Daodejing chapters 1-7 (37 sentences)

Card S2 0.2.0, codebook themes 0.1.0, Claude Haiku 5.5, sync. 10 windows, 0 verifier rejections, $0.0099.

**Result:** about 30 of 37 sentences labelled acceptably. Errors fall into four patterns, fixed in card S2 0.3.0 and codebook themes 0.1.1.

| Pattern | Examples | Fix |
| --- | --- | --- |
| Salience-0 labels were all wrong (5 of 5) | "dogs of grass" → Purity & pollution; "puts his own person last" → Honor; "work is accomplished" → Perseverance | Card: never use salience 0. Verifier drops any salience-0 label. |
| Word matching instead of meaning | "know the beauty" → Knowledge & ignorance; "good order is universal" → Cosmic order; "I do not know whose son it is" → Knowledge & ignorance | Card: tag the idea, not a word. T0204 and T0802 exclude rules sharpened. |
| Rejected values not tagged | "Heaven and earth do not act from any wish to be benevolent" missed Compassion & mercy | Card: tag a theme when the text rejects or reverses it; stance is recorded at book level. |
| Governance by "the sage" missed | Ch. 3 (the sage's government) got Mastery of emotion instead of Good rulership | Card: read who acts. T0601 include rule now covers "the sage" governing the people. |

**Proposals worth tracking for the learning loop:** "Mutual arising of opposites" (2.2), "Selflessness" (7.2, also implied in 7.4-7.5). Neither is promoted yet; the rule is 20+ sentences across 3 books and 2 traditions.

**Next:** re-run the same 10 windows with card 0.3.0 and compare.

## Re-run with card 0.3.0 (same 10 windows, $0.0098)

- **Fixed:** rulership now tagged in chapters 2-3; "not benevolent" now gets Compassion & mercy (salience 3); "I do not know whose son it is" gets no theme; "good order" no longer gets Cosmic order.
- **Still weak:** "know the beauty of the beautiful" keeps Knowledge & ignorance; "the sages… not benevolent" (5.2) misses Compassion although 5.1 gets it. These are for the gold-set examples.
- **New, structural:** 3 windows came back partial. One record had a blank `unit_id`, one listed the same theme twice, one copied a span from the neighbouring sentence. The model also still produced two salience-0 labels, which the verifier dropped. Verifier now matches a blank `unit_id` by position in a complete reply and merges a repeated label (keeping the higher salience); the wrong-span record stays rejected and is retried.
