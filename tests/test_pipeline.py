"""End-to-end test with a fake Claude client: split -> plan -> sync and batch runs -> verify -> report.

Run: python -m unittest tests.test_pipeline
Uses a tiny built-in sample, so it needs neither the corpus nor an API key.
"""
from __future__ import annotations

import json
import pathlib
import re
import tempfile
import types
import unittest

from pipeline import gold, report
from pipeline.runner import Runner
from pipeline.split import run_split, split_sentences

SAMPLE = """# Sample: Chapter 1
Source: test
Category: test
Words: 0
============================================================

1
And the LORD spoke unto Moses, saying:
2
Speak unto the children of Israel, and say unto them: Ye shall not steal. Ye shall love the
stranger as thyself; for ye were strangers in the land of Egypt.
[1. An editor's note that must never reach the model.]
3
And when ye reap the harvest of your land, thou shalt not wholly reap the corner of thy field.
4
Thou shalt leave them for the poor and for the stranger: I am the LORD your God.
p. 12
5
Ye shall do no unrighteousness in judgment. Just balances shall ye have.
"""


def _targets(user: str) -> list[tuple[str, str]]:
    block = user.split("TARGETS:\n", 1)[1].split("\n\nCONTEXT AFTER:", 1)[0]
    return re.findall(r"^\[([^\]]+)\] (.*)$", block, re.M)


def fake_reply(system: str, user: str, break_one: bool, model: str = "") -> str:
    recs = []
    if "A1_themes" in system or "A1_norms" in system:
        assert "CANDIDATES:" in user and "Annotator 1:" in user
        for uid, text in _targets(user):
            if "A1_themes" in system:
                recs.append({"unit_id": uid, "themes": [{"id": "T0501", "salience": 2, "span": " ".join(text.split()[:2])},
                                                        {"id": "T1205", "salience": 1, "span": text.split()[0]}],
                             "topics": [], "reason": "kept divine command", "confidence": 0.8})
            else:
                recs.append({"unit_id": uid, "norms": [], "reason": "no rule stated", "confidence": 0.7})
        return json.dumps({"records": recs})
    for i, (uid, text) in enumerate(_targets(user)):
        words = " ".join(text.split()[:3])
        if "S1_discourse" in system:
            recs.append({"unit_id": uid, "speech_act": "Law", "force": "prescriptive", "speaker": "the LORD",
                         "addressee": "Moses", "confidence": 0.8})
        elif "S2_theme_tagger" in system:
            span = "words that are not there" if (break_one and i == 1) else words
            tid = "T0607" if (model == "claude-sonnet-5-5" and i % 2) else "T0501"  # sonnet disagrees on odd targets
            recs.append({"unit_id": uid, "themes": [{"id": tid, "salience": 2, "span": span}],
                         "topics": [], "proposal": {"label": "", "reason": "", "span": ""}, "confidence": 0.7})
        elif "S3_norm_extractor" in system:
            norms = [{"modality": "prohibition", "action": "steal", "addressee": "Israel", "target": "",
                      "condition": "", "sanction": "", "topic": "P27", "span": "Ye shall not steal"}] \
                if "steal" in text else []
            recs.append({"unit_id": uid, "norms": norms, "confidence": 0.9})
        else:
            recs.append({"unit_id": uid, "mentions": [{"span": words.split()[0], "type": "person", "referent": "x",
                                                        "social_category": "none", "role": "none"}],
                         "confidence": 0.6})
    return json.dumps({"records": recs})


class FakeClient:
    """Mimics the parts of anthropic.Anthropic the runner uses."""

    def __init__(self):
        self.calls = 0
        self._batches = {}
        self.messages = types.SimpleNamespace(create=self._create, batches=types.SimpleNamespace(
            create=self._bcreate, retrieve=self._bretrieve, results=self._bresults))

    def _message(self, params, break_one):
        self.calls += 1
        text = fake_reply(params["system"][0]["text"], params["messages"][0]["content"], break_one, params["model"])
        usage = types.SimpleNamespace(input_tokens=300, output_tokens=200, cache_read_input_tokens=2000,
                                      cache_creation_input_tokens=0)
        return types.SimpleNamespace(id=f"msg_{self.calls}", model=params["model"], stop_reason="end_turn",
                                     usage=usage, content=[types.SimpleNamespace(type="text", text=text)])

    def _create(self, **params):
        assert "temperature" not in params and params["output_config"]["format"]["type"] == "json_schema"
        return self._message(params, break_one=self.calls == 0)

    def _bcreate(self, requests):
        bid = f"msgbatch_{len(self._batches) + 1}"
        for r in requests:
            assert re.fullmatch(r"[A-Za-z0-9_-]{1,64}", r["custom_id"]), r["custom_id"]
        self._batches[bid] = requests
        return types.SimpleNamespace(id=bid)

    def _bretrieve(self, bid):
        return types.SimpleNamespace(id=bid, processing_status="ended")

    def _bresults(self, bid):
        for r in self._batches[bid]:
            msg = self._message(r["params"], break_one=False)
            yield types.SimpleNamespace(custom_id=r["custom_id"],
                                        result=types.SimpleNamespace(type="succeeded", message=msg))


class PipelineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())
        corpus = self.tmp / "corpus" / "bib"
        corpus.mkdir(parents=True)
        (corpus / "lev001.txt").write_text(SAMPLE.replace("\n", "\r\n"), encoding="utf-8")
        self.cfg = {"corpus_root": str(self.tmp / "corpus"), "out_dir": str(self.tmp / "out"),
                    "books": [{"id": "sample", "title": "Sample", "tradition": "bib",
                               "files": ["bib/lev{001..001}.txt"], "chapters": "file", "units": "number_line"}]}

    def test_split(self):
        meta = run_split(self.cfg)[0]
        self.assertEqual(meta["note_lines"], 1)
        sents = [json.loads(line) for line in (self.tmp / "out/sample/sentences.jsonl").read_text().splitlines()]
        texts = " ".join(s["text"] for s in sents)
        self.assertNotIn("editor's note", texts)
        self.assertNotIn("p. 12", texts)
        self.assertEqual(sents[0]["id"], "sample.001.0001")
        self.assertEqual([s["ref"] for s in sents][:3], ["1", "2", "2"])
        self.assertEqual(len(split_sentences("Mr. Smith came. He left! Did he? Yes.")), 4)

    def test_runs_verify_and_report(self):
        run_split(self.cfg)
        client = FakeClient()
        r = Runner(self.cfg, client=client)
        jobs = r.plan(["S2"], ["sample"], None)
        self.assertEqual(len(jobs), 2)  # 9 sentences -> windows of 5
        self.assertGreater(r.estimate(jobs, "sync")["usd"], 0)
        res = r.run_sync(jobs, max_usd=1.0, workers=1)
        self.assertEqual(res["counts"].get("partial", 0), 1)    # one bad span in the first window
        # Re-plan: only the partial window comes back; finished work is skipped.
        again = r.plan(["S2"], ["sample"], None)
        self.assertEqual(len(again), 1)
        r.run_sync(again, max_usd=1.0, workers=1)
        self.assertEqual(r.plan(["S2"], ["sample"], None), [])
        rejects = (self.tmp / "out/sample/rejects_S2.jsonl").read_text()
        self.assertIn("span not in text", rejects)
        # Batch mode for the other agents.
        jobs = r.plan(["S1", "S3", "S4"], ["sample"], None)
        r.submit_batches(jobs)
        counts = r.collect(wait=True, poll_seconds=0)
        self.assertEqual(counts.get("done"), len(jobs))
        rep = report.build(self.tmp / "out", "sample")
        self.assertEqual(rep["covered"]["S2"], rep["sentences"])
        self.assertEqual(rep["covered"]["S1"], rep["sentences"])
        self.assertEqual(rep["norms"], {"prohibition": 1})
        csv_text = (self.tmp / "out/sample/report.csv").read_text(encoding="utf-8-sig")
        self.assertIn("law", csv_text)  # enum case normalised: "Law" -> "law"
        self.assertGreater(r.ledger.spent(), 0)

    def test_gold_flow(self):
        run_split(self.cfg)
        client = FakeClient()
        main = Runner(self.cfg, client=client)
        main.run_sync(main.plan(["S2", "S3"], ["sample"], None), max_usd=1.0, workers=1)
        sel = gold.select(self.cfg, per_book=2)
        self.assertEqual(sel["sample"]["windows"], 2)
        g = Runner(gold.gold_cfg(self.cfg), client=client)
        jobs = []
        for model, effort in gold.REF_MODELS:
            jobs += g.plan(gold.GOLD_AGENTS, ["sample"], None, model=model, effort=effort)
        self.assertEqual(len(jobs), 8)  # 2 windows x 2 agents x 2 models
        self.assertEqual(jobs[0]["window"]["id"], jobs[4]["window"]["id"])
        g.submit_batches(jobs)
        g.collect(wait=True, poll_seconds=0, windows_for=gold.windows_for(self.cfg))
        out = self.tmp / "out/gold/sample"
        self.assertTrue((out / "out_S2@claude-opus-5-5.jsonl").exists())
        self.assertTrue((out / "out_S2@claude-sonnet-5-5.jsonl").exists())
        stats = gold.disputes(self.cfg)["sample"]
        self.assertGreater(stats["S2_disputed"], 0)
        self.assertGreater(stats["S2_agreed"], 0)
        wf = gold.windows_for(self.cfg)
        items = [(adj, "sample", w) for adj in gold.DISPUTE_FILES for w in wf(adj, "sample").values()]
        g.run_sync(g.plan_windows(items), max_usd=1.0, workers=1)
        fin = gold.finalize(self.cfg)["sample"]
        self.assertEqual(fin["S2"]["unresolved"], 0)
        self.assertEqual(fin["S2"]["agreed"] + fin["S2"]["adjudicated"], sel["sample"]["sentences"])
        gs2 = [json.loads(x) for x in (out / "gold_S2.jsonl").read_text().splitlines()]
        adj = [r for r in gs2 if r["_gold"] == "adjudicated"]
        # T1205 was proposed by neither annotator, so finalize removes it
        self.assertTrue(adj and all(t["id"] != "T1205" for r in adj for t in r["themes"]))
        self.assertTrue(gold.sample(self.cfg, n=5).endswith("sanity_sample.csv"))
        sc = gold.score(self.cfg, "S2")
        self.assertEqual(sc["sentences"] + sc["unlabelled"], sel["sample"]["sentences"])
        self.assertGreater(sc["themes"]["f1"], 0)
        self.assertIn("has_norm", gold.score(self.cfg, "S3"))
        # Dev/test split, then the current cards (Haiku) on the test windows only.
        orig = gold.SPLIT_FILE
        gold.SPLIT_FILE = self.tmp / "gold_split.json"
        try:
            sp = gold.make_split(self.cfg)["sample"]
            self.assertEqual((sp["dev"], sp["test"]), (1, 1))
            with self.assertRaises(SystemExit):
                gold.make_split(self.cfg)  # frozen
            tw = gold.test_windows(self.cfg, "sample")
            items = [(ag, "sample", w) for ag in gold.GOLD_AGENTS for w in tw]
            g.run_sync(g.plan_windows(items), max_usd=1.0, workers=1)
            self.assertTrue((out / "out_S2.jsonl").exists())
            t = gold.score(self.cfg, "S2", split="test", source="gold")
            d = gold.score(self.cfg, "S2", split="dev")
            self.assertEqual(t["sentences"], len(tw[0]["targets"]))
            self.assertEqual(t["split"], "test")
            self.assertEqual(t["sentences"] + d["sentences"] + d["unlabelled"] + t["unlabelled"],
                             sel["sample"]["sentences"])
        finally:
            gold.SPLIT_FILE = orig
        # Spend is shared: the main runner sees the gold ledger's spend too.
        both = Runner({**self.cfg, "spend_ledgers": [str(self.tmp / "out/gold/ledger.sqlite")]}, client=client)
        self.assertAlmostEqual(both.spent(), main.ledger.spent() + g.ledger.spent(), places=6)

    def test_spend_cap(self):
        run_split(self.cfg)
        r = Runner(self.cfg, client=FakeClient())
        r.ledger.db.execute("INSERT INTO jobs(job_key, status, cost_usd) VALUES ('old', 'done', 5.0)")
        jobs = r.plan(["S2"], ["sample"], None)
        res = r.run_sync(jobs, max_usd=1.0, workers=1)
        self.assertTrue(res["stopped_by_cap"])
        self.assertEqual(r._client.calls, 0)


if __name__ == "__main__":
    unittest.main()
