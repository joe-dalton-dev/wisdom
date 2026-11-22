"""SQLite job ledger: one row per (agent, window). Lets any run stop and resume without redoing work."""
from __future__ import annotations

import sqlite3
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  job_key      TEXT PRIMARY KEY,   -- hash of card + base + codebook + model + window text
  custom_id    TEXT UNIQUE,        -- id sent to the API (letters, digits, - and _ only)
  agent        TEXT, card TEXT, book TEXT, window_id TEXT,
  status       TEXT,               -- pending | submitted | done | partial | failed
  attempts     INTEGER DEFAULT 0,
  batch_id     TEXT,
  prompt_hash  TEXT,
  model        TEXT,
  mode         TEXT,               -- sync | batch
  input_tokens INTEGER DEFAULT 0, cache_read INTEGER DEFAULT 0, cache_write INTEGER DEFAULT 0,
  output_tokens INTEGER DEFAULT 0, cost_usd REAL DEFAULT 0,
  accepted INTEGER DEFAULT 0, rejected INTEGER DEFAULT 0, missing INTEGER DEFAULT 0,
  error TEXT,
  updated REAL
);
CREATE TABLE IF NOT EXISTS batches (
  batch_id TEXT PRIMARY KEY, agent TEXT, books TEXT, requests INTEGER,
  status TEXT, created REAL, collected REAL
);
"""

MAX_ATTEMPTS = 3


class Ledger:
    def __init__(self, path):
        self.db = sqlite3.connect(str(path))
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def ensure(self, job_key, custom_id, agent, card, book, window_id, prompt_hash, model):
        self.db.execute(
            "INSERT OR IGNORE INTO jobs(job_key, custom_id, agent, card, book, window_id, status, prompt_hash,"
            " model, updated) VALUES (?,?,?,?,?,?, 'pending', ?, ?, ?)",
            (job_key, custom_id, agent, card, book, window_id, prompt_hash, model, time.time()))

    def get(self, job_key):
        return self.db.execute("SELECT * FROM jobs WHERE job_key=?", (job_key,)).fetchone()

    def by_custom_id(self, custom_id):
        return self.db.execute("SELECT * FROM jobs WHERE custom_id=?", (custom_id,)).fetchone()

    def runnable(self, job_key) -> bool:
        row = self.get(job_key)
        return row is not None and row["status"] in ("pending", "partial", "failed") \
            and row["attempts"] < MAX_ATTEMPTS

    def mark_submitted(self, job_key, batch_id, mode):
        self.db.execute("UPDATE jobs SET status='submitted', batch_id=?, mode=?, attempts=attempts+1, updated=?"
                        " WHERE job_key=?", (batch_id, mode, time.time(), job_key))

    def record(self, job_key, status, usage: dict, cost, accepted, rejected, missing, error=None):
        self.db.execute(
            "UPDATE jobs SET status=?, input_tokens=input_tokens+?, cache_read=cache_read+?,"
            " cache_write=cache_write+?, output_tokens=output_tokens+?, cost_usd=cost_usd+?,"
            " accepted=?, rejected=?, missing=?, error=?, updated=? WHERE job_key=?",
            (status, usage.get("input", 0), usage.get("cache_read", 0), usage.get("cache_write", 0),
             usage.get("output", 0), cost, accepted, rejected, missing, error, time.time(), job_key))

    def add_batch(self, batch_id, agent, books, n):
        self.db.execute("INSERT INTO batches VALUES (?,?,?,?, 'in_progress', ?, NULL)",
                        (batch_id, agent, ",".join(sorted(books)), n, time.time()))

    def open_batches(self):
        return self.db.execute("SELECT * FROM batches WHERE collected IS NULL").fetchall()

    def close_batch(self, batch_id, status):
        self.db.execute("UPDATE batches SET status=?, collected=? WHERE batch_id=?", (status, time.time(), batch_id))

    def spent(self) -> float:
        return self.db.execute("SELECT COALESCE(SUM(cost_usd),0) FROM jobs").fetchone()[0]

    def summary(self):
        return self.db.execute(
            "SELECT book, agent, status, COUNT(*) n, SUM(accepted) acc, SUM(rejected) rej, SUM(missing) miss,"
            " ROUND(SUM(cost_usd), 4) usd FROM jobs GROUP BY book, agent, status ORDER BY book, agent, status"
        ).fetchall()

    def commit(self):
        self.db.commit()
