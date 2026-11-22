# Review: S1-S4 smoke test, Leviticus 1-3 (JPS), first 10 windows per agent

Cards S1 0.1.0, S2 0.3.0, S3 0.1.0, S4 0.1.0; Claude Haiku 5.5, sync. Cost $0.017 for all four agents.

| Agent | Windows done / partial | Quality |
| --- | --- | --- |
| S1 discourse | 10 / 0 | Speech act right (law) almost everywhere. Speaker and addressee drop out after the first paragraphs of a speech. Conditional laws marked "hypothetical". |
| S2 themes | 8 / 2 | Sensible: Ritual & sacrifice, Repentance & atonement (1:4), Covenant (salt of the covenant, 2:13). Topics split correctly between offerings (P30) and animal sacrifice (P38). Two spans paraphrased. |
| S3 norms | 8 / 2 | Strong: obligations, prohibitions and permissions found with sensible actions. Misses some ritual steps ("he shall flay the burnt-offering", 1:6; "he shall take away its crop", 1:16). Four conditions were paraphrased, so the verifier rejected them. |
| S4 entities | 9 / 1 | Pronouns resolved well ("he" = the offerer, "it" = the offering animal). Social categories over-applied: "the children of Israel" tagged children; "any man of you" tagged men. One mention ("the LORD") taken from context. |

Also found: JPS chapter headings ("LEVITICUS CHAPTER 2") were being treated as text.

**Fixes:** S1 0.2.0 (speaker carries over through a speech, 3 paragraphs of context instead of 1, conditional law is prescriptive, speech frames are narration); S3 0.2.0 (every ritual step is a norm, conditions copied word for word or left empty); S4 0.2.0 (literal social categories only, spans must be in the target); Leviticus config drops chapter headings.

**Next:** re-split Leviticus and re-run the same 10 windows with the new cards.

## Re-run with S1 0.2.0, S3 0.2.0, S4 0.2.0 ($0.019, 37 windows, 35 done, 2 partial)

- **S3 fixed:** every condition now copied word for word (0 rejections, was 4); ritual steps such as "he shall flay the burnt-offering" are now norms. 64 norms in 43 sentences.
- **S4 fixed:** no more "children" for the children of Israel or "men" for "any man"; social categories are now priests and sacrificial animals, as they should be. Still pulls "the LORD" from context twice; the verifier rejects those and they are retried.
- **S1 improved, not fixed:** conditional law is now prescriptive and the speech frame is narration. The speaker carries over only while the opening is in view: windows that start deep inside a speech (1:6-1:17, chapter 3 start) still have no speaker. Fix in S1 0.2.1: each paragraph window now also carries the chapter's first two paragraphs as CHAPTER OPENING context.
