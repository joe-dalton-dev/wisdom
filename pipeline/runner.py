"""Runner: windows -> Claude (sync or Message Batches) -> verifier -> JSONL outputs + ledger.

Every job is keyed by card + window text, so re-running skips finished work. A hard spend cap
(--max-usd) is checked against the ledger before anything is sent.
"""
from __future__ import annotations

import concurrent.futures as cf
import json
import pathlib
import time

import yaml

from .assemble import ROOT, Agent, Codebook, sha256
from .ledger import Ledger
from .verify import verify

# Rough output tokens per target unit, used only for estimates before a run.
EST_OUT_PER_UNIT = {"S1": 60, "S2": 90, "S3": 70, "S4": 130}
BATCH_CHUNK = 5000


def load_prices() -> dict:
    return yaml.safe_load((ROOT / "agents/models.lock").read_text(encoding="utf-8"))["models"]


def cost_usd(usage: dict, model: str, mode: str, prices: dict) -> float:
    p = prices[model]["batch" if mode == "batch" else "standard"]
    return (usage.get("input", 0) * p["input"] + usage.get("output", 0) * p["output"]
            + usage.get("cache_read", 0) * p["cache_read"] + usage.get("cache_write", 0) * p["cache_write"]) / 1e6


def usage_of(message) -> dict:
    u = getattr(message, "usage", None)
    g = (lambda k: getattr(u, k, 0) or 0) if u is not None else (lambda k: 0)
    return {"input": g("input_tokens"), "output": g("output_tokens"),
            "cache_read": g("cache_read_input_tokens"), "cache_write": g("cache_creation_input_tokens")}


def text_of(message) -> str:
    return "".join(getattr(b, "text", "") for b in message.content if getattr(b, "type", "") == "text")


def custom_id(agent_short: str, job_key: str) -> str:
    return f"{agent_short}-{job_key[:48]}"


class Runner:
    def __init__(self, cfg: dict, client=None):
        self.cfg = cfg
        self.out = pathlib.Path(cfg["out_dir"])
        self.out.mkdir(parents=True, exist_ok=True)
        self.ledger = Ledger(self.out / "ledger.sqlite")
        self.codebook = Codebook()
        self.enums = self.codebook.enums()
        self.prices = load_prices()
        self._client = client
        self._agents: dict[str, Agent] = {}

    @property
    def client(self):
        if self._client is None:
            import anthropic
            self._client = anthropic.Anthropic(max_retries=4)
        return self._client

    def agent(self, short: str) -> Agent:
        if short not in self._agents:
            self._agents[short] = Agent(short, self.codebook)
        return self._agents[short]

    # ---------- planning ----------
    def windows(self, book: str, agent: Agent, limit: int | None = None) -> list[dict]:
        path = self.out / book / agent.card["windows"]
        if not path.exists():
            raise SystemExit(f"{path} not found. Run `python -m pipeline split` first.")
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        return rows[:limit] if limit else rows

    def plan(self, agents: list[str], books: list[str], limit: int | None) -> list[dict]:
        jobs = []
        for a in agents:
            ag = self.agent(a)
            for b in books:
                for w in self.windows(b, ag, limit):
                    key = ag.job_key(w)
                    self.ledger.ensure(key, custom_id(a, key), a, ag.version_tag, b, w["id"],
                                       ag.prompt_hash(w), ag.model)
                    if self.ledger.runnable(key):
                        jobs.append({"key": key, "agent": a, "book": b, "window": w})
        self.ledger.commit()
        return jobs

    def estimate(self, jobs: list[dict], mode: str) -> dict:
        usd, calls, by_agent = 0.0, 0, {}
        for j in jobs:
            ag = self.agent(j["agent"])
            sys_tok = len(ag.system) // 4
            user_tok = len(ag.user_message(j["window"])) // 4 + 50
            out_tok = EST_OUT_PER_UNIT[j["agent"]] * len(j["window"]["targets"]) + 40
            # Assume half the calls read the cached system prompt and half write it (batches don't
            # guarantee cache hits); a pessimistic but simple rule.
            usage = {"input": user_tok, "output": out_tok, "cache_read": sys_tok // 2, "cache_write": sys_tok // 2}
            c = cost_usd(usage, ag.model, mode, self.prices)
            usd += c
            calls += 1
            by_agent[j["agent"]] = by_agent.get(j["agent"], 0) + c
        return {"calls": calls, "usd": usd, "by_agent": by_agent}

    # ---------- results ----------
    def _write(self, book: str, name: str, rows: list[dict]):
        if not rows:
            return
        with (self.out / book / name).open("a", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def process(self, job: dict, message, mode: str, batch_id: str | None = None) -> str:
        ag = self.agent(job["agent"])
        usage = usage_of(message)
        cost = cost_usd(usage, ag.model, mode, self.prices)
        reply = text_of(message)
        res = verify(job["agent"], job["window"], reply, self.enums)
        if getattr(message, "stop_reason", None) == "max_tokens":
            res["fatal"] = (res["fatal"] or "") + " (reply cut off at max_tokens)"
        prov = {"agent": job["agent"], "card": ag.version_tag, "base": ag.card["base"],
                "codebook": self.codebook.version, "model": getattr(message, "model", ag.model),
                "message_id": getattr(message, "id", None), "batch_id": batch_id,
                "prompt_hash": ag.prompt_hash(job["window"]), "window_id": job["window"]["id"],
                "mode": mode, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        self._write(job["book"], f"out_{job['agent']}.jsonl", [{**r, "_prov": prov} for r in res["accepted"]])
        rej = [{**r, "_prov": prov} for r in res["rejected"]]
        if res["fatal"]:
            rej.append({"fatal": res["fatal"], "reply": reply[:2000], "_prov": prov})
        self._write(job["book"], f"rejects_{job['agent']}.jsonl", rej)
        status = "done" if not res["missing"] and not res["rejected"] and not res["fatal"] else (
            "partial" if res["accepted"] else "failed")
        self.ledger.record(job["key"], status, usage, cost, len(res["accepted"]), len(res["rejected"]),
                           len(res["missing"]), res["fatal"])
        return status

    # ---------- sync mode ----------
    def run_sync(self, jobs: list[dict], max_usd: float, workers: int = 4) -> dict:
        counts: dict[str, int] = {}
        stopped = False

        def call(job):
            ag = self.agent(job["agent"])
            try:
                return job, self.client.messages.create(**ag.request(job["window"])), None
            except Exception as e:  # noqa: BLE001 - API errors are recorded and the run continues
                return job, None, e

        with cf.ThreadPoolExecutor(max_workers=workers) as pool:
            pending = list(jobs)
            futures = set()
            while pending or futures:
                while pending and len(futures) < workers:
                    if self.ledger.spent() >= max_usd:
                        stopped = True
                        pending = []
                        break
                    job = pending.pop(0)
                    self.ledger.mark_submitted(job["key"], None, "sync")
                    futures.add(pool.submit(call, job))
                if not futures:
                    break
                done, futures = cf.wait(futures, return_when=cf.FIRST_COMPLETED)
                for f in done:
                    job, msg, err = f.result()
                    if err is not None:
                        st = "failed"
                        self.ledger.record(job["key"], "failed", {}, 0, 0, 0, len(job["window"]["targets"]),
                                           f"API error: {type(err).__name__}: {err}"[:300])
                        print(f"  API error on {job['window']['id']}: {type(err).__name__}: {str(err)[:200]}")
                    else:
                        st = self.process(job, msg, "sync")
                    counts[st] = counts.get(st, 0) + 1
                    self.ledger.commit()
        return {"counts": counts, "stopped_by_cap": stopped}

    # ---------- batch mode ----------
    def submit_batches(self, jobs: list[dict]) -> list[str]:
        ids = []
        by_agent: dict[str, list[dict]] = {}
        for j in jobs:
            by_agent.setdefault(j["agent"], []).append(j)
        for a, js in by_agent.items():
            ag = self.agent(a)
            for i in range(0, len(js), BATCH_CHUNK):
                chunk = js[i:i + BATCH_CHUNK]
                reqs = [{"custom_id": custom_id(a, j["key"]), "params": ag.request(j["window"])} for j in chunk]
                batch = self.client.messages.batches.create(requests=reqs)
                self.ledger.add_batch(batch.id, a, {j["book"] for j in chunk}, len(chunk))
                for j in chunk:
                    self.ledger.mark_submitted(j["key"], batch.id, "batch")
                self.ledger.commit()
                ids.append(batch.id)
        return ids

    def _window_index(self, book: str, agent: Agent) -> dict:
        return {w["id"]: w for w in self.windows(book, agent)}

    def collect(self, wait: bool = False, poll_seconds: int = 30) -> dict:
        counts: dict[str, int] = {}
        while True:
            open_ = self.ledger.open_batches()
            if not open_:
                break
            still_running = 0
            for b in open_:
                info = self.client.messages.batches.retrieve(b["batch_id"])
                if info.processing_status != "ended":
                    still_running += 1
                    continue
                ag = self.agent(b["agent"])
                index = {bk: self._window_index(bk, ag) for bk in b["books"].split(",")}
                for entry in self.client.messages.batches.results(b["batch_id"]):
                    row = self.ledger.by_custom_id(entry.custom_id)
                    if row is None:
                        continue
                    job = {"key": row["job_key"], "agent": row["agent"], "book": row["book"],
                           "window": index[row["book"]][row["window_id"]]}
                    if entry.result.type == "succeeded":
                        st = self.process(job, entry.result.message, "batch", b["batch_id"])
                    else:
                        st = "failed"
                        err = getattr(entry.result, "error", None)
                        self.ledger.record(job["key"], "failed", {}, 0, 0, 0, len(job["window"]["targets"]),
                                           f"{entry.result.type}: {err}"[:300])
                    counts[st] = counts.get(st, 0) + 1
                self.ledger.close_batch(b["batch_id"], "ended")
                self.ledger.commit()
            if not still_running or not wait:
                if still_running:
                    counts["still_running_batches"] = still_running
                break
            print(f"  {still_running} batch(es) still running; checking again in {poll_seconds}s (Ctrl+C is safe)")
            time.sleep(poll_seconds)
        return counts


def book_ids(cfg: dict, wanted: list[str] | None) -> list[str]:
    ids = [b["id"] for b in cfg["books"]]
    if not wanted or wanted == ["all"]:
        return ids
    bad = [w for w in wanted if w not in ids]
    if bad:
        raise SystemExit(f"Unknown book(s): {', '.join(bad)}. Known: {', '.join(ids)}")
    return wanted


def fingerprint_cfg(cfg: dict) -> str:
    return sha256(cfg)[:12]
