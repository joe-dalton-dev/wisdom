# Pipeline (not started)

Code begins once the plan's open decisions are answered (checklist P0-06). Planned components, in build order:

1. `adapters/` — deterministic source → canonical JSON per edition (sacred-texts HTML, Gutenberg, Perseus TEI…)
2. `split/` — sentence and unit splitting with stable unit IDs
3. `ledger/` — SQLite job ledger, chunk runner, resume and skip logic
4. `assemble/` — prompt assembly from agent cards, prompt hashing
5. `verify/` — V1 verifier: schema, IDs, verbatim spans, allowed labels
6. `rollup/` — chapter and book rollups computed in code
7. `report/` — status and daily report output
