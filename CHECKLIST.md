# Project checklist

The live copy is the "Project checklist" sheet in Google Drive → Wisdom Graph → 00 Start here. This file is regenerated from `project/checklist.csv`; edit the CSV, not this file.

## 0 Setup

- [x] **0.01** Create Google Drive folder structure · Claude
    - Done when: Wisdom Graph folder with 00–05 and 99 exists · Created 2026-11-22
- [x] **0.02** Write onboarding guides and architecture summary · Claude
    - Done when: START HERE + 4 role guides in Drive and repo · Created 2026-11-22
- [ ] **0.03** Connect GitHub to Claude · Joseph
    - Done when: Claude can create repos in your account · claude.ai Settings > Connectors > GitHub
- [ ] **0.04** Create private wisdom-graph repo and push skeleton · Claude *(Blocked)*
    - Done when: Repo exists with the skeleton on main · Waits for 0.03
- [ ] **0.05** Protect main branch and enable Discussions · Joseph
    - Done when: PRs required on main; Discussions categories Introductions and Codebook exist
- [ ] **0.06** Answer the 8 open decisions in the plan · Joseph
    - Done when: Every row in Decisions needed has an answer
- [ ] **0.07** Choose licenses for code and output data · Joseph
    - Done when: LICENSE files in repo · Suggested: MIT for code; CC BY 4.0 for data
- [ ] **0.08** Decide where Argilla runs · Joseph
    - Done when: Argilla reachable by reviewers · Options: your PC or a Hugging Face Space
- [ ] **0.09** Share classification_taxonomy.json and the 20 quote-project themes · Joseph
    - Done when: Both files attached in chat or in Drive 01
- [ ] **0.10** Merge taxonomy into codebook v1 · Claude
    - Done when: codebook/*.yaml merged and reviewed · Needs 0.09
- [ ] **0.11** Write definitions and 3+3 examples per label · Joseph + Claude
    - Done when: Every core label has a definition and examples · 2–3 h of your time
- [ ] **0.12** Upload public-domain corpus-books to Drive · Joseph
    - Done when: One folder per tradition in 02 Corpus/public-domain · Use Google Drive desktop app
- [ ] **0.13** Move non-public-domain editions to restricted · Joseph
    - Done when: Restricted folder holds every non-PD edition
- [ ] **0.14** Upload manifest with SHA-256 per book · Joseph + Claude
    - Done when: 02 Corpus/manifests has books.csv with hashes

## 1 Gold set

- [ ] **1.01** Select 600 stratified windows · Claude
    - Done when: 600 windows across ~12 traditions and 5 genres
- [ ] **1.02** Draft gold labels with Claude Batch API · Claude
    - Done when: Draft labels loaded into Argilla · Within the €50 cap
- [ ] **1.03** Review the 600 gold items · Joseph + reviewers
    - Done when: All 600 reviewed · 6–8 h
- [ ] **1.04** Freeze 400 dev / 200 test split · Claude
    - Done when: Split committed; test set locked

## 2 Pilot

- [ ] **2.01** Build ledger and chunk runner · Developer
    - Done when: Runner resumes after Ctrl+C without redoing jobs
- [ ] **2.02** Build prompt assembler and verifier V1 · Developer
    - Done when: Same card + input gives identical prompt hash; V1 rejects bad spans
- [ ] **2.03** Install llama-server and pin 2 candidate models · Joseph
    - Done when: models.lock has hashes; wg doctor passes
- [ ] **2.04** Run bake-off on 6 pilot books · Joseph
    - Done when: Scores for 2 models x K=1/5/10 · 2–3 nights
- [ ] **2.05** Tune prompts with DSPy GEPA · Developer
    - Done when: Tuned cards beat baseline on dev set
- [ ] **2.06** Gate review: targets met and 36 records spot-checked · Joseph
    - Done when: Ship targets met on test set · Tag cards-v1.0
- [ ] **2.07** Set up nightly Task Scheduler run · Joseph
    - Done when: Run starts at 23:00 unattended
- [ ] **2.08** Set up morning report scheduled task · Claude
    - Done when: Report appears in 04 Reports each morning
- [ ] **2.09** Invite first 1–2 tradition reviewers · Joseph
    - Done when: Reviewers have access and have introduced themselves

## 3 Encoder pass

- [ ] **3.01** Run embeddings and triage on whole corpus · Joseph
    - Done when: All sentences have T1/T2 records · 1 night
- [ ] **3.02** Check triage recall on gold · Claude
    - Done when: Recall at least 0.90

## 4 Level 1

- [ ] **4.01** Run tier 1 (canon) · Runners
    - Done when: All tier 1 chunks accepted
- [ ] **4.02** Learning cycle after tier 1 · Joseph + reviewers
    - Done when: Packet reviewed; next release tagged · 30–60 min
- [ ] **4.03** Run remaining tiers with a cycle after each · Runners
    - Done when: All tiers accepted · ~6 nights total

## 5 Chapters and books

- [ ] **5.01** Run chapter and book synthesis · Runners
    - Done when: Citation checks pass · ~1 night
- [ ] **5.02** Spot-check 20 chapter and book records · Joseph
    - Done when: 20 records reviewed

## 6 Cross-tradition

- [ ] **6.01** Run parallels and comparator · Runners
    - Done when: Convergence table built · ~1 night
- [ ] **6.02** Review 50 convergence claims · Joseph + reviewers
    - Done when: 50 claims reviewed

## 7 Load

- [ ] **7.01** Decide on and run the catch-up pass · Joseph
    - Done when: Catch-up done or explicitly skipped
- [ ] **7.02** Load Neo4j and LanceDB · Developer
    - Done when: Graph and vectors queryable

## Recurring

- [ ] **R.01** Read the morning report · Joseph
    - Done when: Daily · 5 min
- [ ] **R.02** Accept or reject submitted bundles · Joseph
    - Done when: No bundle waits more than 3 days
- [ ] **R.03** Check Claude spend and monitoring sample · Joseph
    - Done when: Weekly · 15 min
- [ ] **R.04** Back up ledger and accepted outputs; review access · Joseph
    - Done when: Monthly · 15 min
