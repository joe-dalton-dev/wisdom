# Project checklist

The live copy is the "Project checklist" sheet in Google Drive → Wisdom Graph → 00 Start here. This file is regenerated from `project/checklist.csv`; edit the CSV, not this file.

## 0 Setup

- [x] **P0-01** Create Google Drive folder structure · Claude
    - Done when: Wisdom Graph folder with 00–05 and 99 exists · Created 2026-11-22
- [x] **P0-02** Write onboarding guides and architecture summary · Claude
    - Done when: START HERE + 4 role guides in Drive and repo · Created 2026-11-22
- [x] **P0-03** Connect GitHub to Claude · Joseph
    - Done when: Claude can create repos in your account · Connected 2026-11-22
- [x] **P0-04** Push skeleton to github.com/joe-dalton-dev/wisdom · Claude
    - Done when: Repo exists with the skeleton on main · Pushed 2026-11-22
- [x] **P0-05** Protect main branch and enable Discussions · Joseph
    - Done when: PRs required on main; Discussions categories Introductions and Codebook exist · Repo public; Protect main ruleset active; Discussions on (2026-11-22)
- [x] **P0-06** Answer the 8 open decisions in the plan · Joseph
    - Done when: Every row in Decisions needed has an answer · All 8 answered 2026-11-22; see docs/decisions.md
- [ ] **P0-07** Choose license for output data (code is Apache 2.0) · Joseph *(In progress)*
    - Done when: Data license recorded in README · Code: Apache 2.0 chosen. Suggested for data: CC BY 4.0
- [ ] **P0-08** Decide where Argilla runs · Joseph
    - Done when: Argilla reachable by reviewers · Options: your PC or a Hugging Face Space
- [ ] **P0-09** Share classification_taxonomy.json and the 20 quote-project themes · Joseph
    - Done when: Both files attached in chat or in Drive 01
- [ ] **P0-10** Merge taxonomy into codebook v1 · Claude
    - Done when: codebook/*.yaml merged and reviewed · Needs P0-09
- [ ] **P0-11** Write definitions and 3+3 examples per label · Joseph + Claude
    - Done when: Every core label has a definition and examples · 2–3 h of your time
- [ ] **P0-12** Upload public-domain corpus-books to Drive · Joseph
    - Done when: One folder per tradition in 02 Corpus/public-domain · Use Google Drive desktop app
- [ ] **P0-13** Move non-public-domain editions to restricted · Joseph
    - Done when: Restricted folder holds every non-PD edition
- [ ] **P0-14** Upload manifest with SHA-256 per book · Joseph + Claude
    - Done when: 02 Corpus/manifests has books.csv with hashes

## 1 Gold set

- [ ] **P1-01** Select 600 stratified windows · Claude
    - Done when: 600 windows across ~12 traditions and 5 genres
- [ ] **P1-02** Draft gold labels with Claude Batch API · Claude
    - Done when: Draft labels loaded into Argilla · Within the €50 cap
- [ ] **P1-03** Review the 600 gold items · Joseph + reviewers
    - Done when: All 600 reviewed · 6–8 h
- [ ] **P1-04** Freeze 400 dev / 200 test split · Claude
    - Done when: Split committed; test set locked

## 2 Pilot

- [ ] **P2-01** Build ledger and chunk runner · Developer
    - Done when: Runner resumes after Ctrl+C without redoing jobs
- [ ] **P2-02** Build prompt assembler and verifier V1 · Developer
    - Done when: Same card + input gives identical prompt hash; V1 rejects bad spans
- [ ] **P2-03** Install llama-server and pin 2 candidate models · Joseph
    - Done when: models.lock has hashes; wg doctor passes
- [ ] **P2-04** Run bake-off on 6 pilot books · Joseph
    - Done when: Scores for 2 models x K=1/5/10 · 2–3 nights
- [ ] **P2-05** Tune prompts with DSPy GEPA · Developer
    - Done when: Tuned cards beat baseline on dev set
- [ ] **P2-06** Gate review: targets met and 36 records spot-checked · Joseph
    - Done when: Ship targets met on test set · Tag cards-v1.0
- [ ] **P2-07** Set up nightly Task Scheduler run · Joseph
    - Done when: Run starts at 23:00 unattended
- [ ] **P2-08** Set up morning report scheduled task · Claude
    - Done when: Report appears in 04 Reports each morning
- [ ] **P2-09** Invite first 1–2 tradition reviewers · Joseph
    - Done when: Reviewers have access and have introduced themselves

## 3 Encoder pass

- [ ] **P3-01** Run embeddings and triage on whole corpus · Joseph
    - Done when: All sentences have T1/T2 records · 1 night
- [ ] **P3-02** Check triage recall on gold · Claude
    - Done when: Recall at least 0.90

## 4 Level 1

- [ ] **P4-01** Run tier 1 (canon) · Runners
    - Done when: All tier 1 chunks accepted
- [ ] **P4-02** Learning cycle after tier 1 · Joseph + reviewers
    - Done when: Packet reviewed; next release tagged · 30–60 min
- [ ] **P4-03** Run remaining tiers with a cycle after each · Runners
    - Done when: All tiers accepted · ~6 nights total

## 5 Chapters and books

- [ ] **P5-01** Run chapter and book synthesis · Runners
    - Done when: Citation checks pass · ~1 night
- [ ] **P5-02** Spot-check 20 chapter and book records · Joseph
    - Done when: 20 records reviewed

## 6 Cross-tradition

- [ ] **P6-01** Run parallels and comparator · Runners
    - Done when: Convergence table built · ~1 night
- [ ] **P6-02** Review 50 convergence claims · Joseph + reviewers
    - Done when: 50 claims reviewed

## 7 Load

- [ ] **P7-01** Decide on and run the catch-up pass · Joseph
    - Done when: Catch-up done or explicitly skipped
- [ ] **P7-02** Load Neo4j and LanceDB · Developer
    - Done when: Graph and vectors queryable

## Recurring

- [ ] **R-01** Read the morning report · Joseph
    - Done when: Daily · 5 min
- [ ] **R-02** Accept or reject submitted bundles · Joseph
    - Done when: No bundle waits more than 3 days
- [ ] **R-03** Check Claude spend and monitoring sample · Joseph
    - Done when: Weekly · 15 min
- [ ] **R-04** Back up ledger and accepted outputs; review access · Joseph
    - Done when: Monthly · 15 min
