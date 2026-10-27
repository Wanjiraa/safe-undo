"""SQLite persistence: customers, transactions, reversal cases, status history, demo clock."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers(
  id TEXT PRIMARY KEY, name TEXT NOT NULL, msisdn_masked TEXT NOT NULL, balance REAL NOT NULL);
CREATE TABLE IF NOT EXISTS transactions(
  id TEXT PRIMARY KEY, customer_id TEXT NOT NULL REFERENCES customers(id),
  tx_type TEXT NOT NULL, recipient_token TEXT NOT NULL, recipient_masked TEXT NOT NULL,
  recipient_name TEXT, amount REAL NOT NULL, ts TEXT NOT NULL, mpesa_ref TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_tx_customer_ts ON transactions(customer_id, ts);
CREATE TABLE IF NOT EXISTS cases(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ref TEXT UNIQUE NOT NULL,
  customer_id TEXT NOT NULL REFERENCES customers(id),
  transaction_id TEXT NOT NULL REFERENCES transactions(id),
  reason TEXT NOT NULL, status TEXT NOT NULL,
  submitted_at TEXT NOT NULL, status_entered_at TEXT NOT NULL,
  rejection_reason TEXT, simulated INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS status_history(
  id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER NOT NULL REFERENCES cases(id),
  status TEXT NOT NULL, ts TEXT NOT NULL, note TEXT);
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""

TABLES = ("status_history", "cases", "transactions", "customers", "meta")


@contextmanager
def conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB_PATH, timeout=10)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    try:
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def init_db(reset: bool = False) -> None:
    with conn() as c:
        if reset:
            for t in TABLES:
                c.execute(f"DROP TABLE IF EXISTS {t}")
        c.executescript(SCHEMA)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


def parse(s: str) -> datetime:
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def clock_offset_hours(c: sqlite3.Connection) -> float:
    row = c.execute("SELECT value FROM meta WHERE key='clock_offset_hours'").fetchone()
    return float(row["value"]) if row else 0.0


def now(c: sqlite3.Connection) -> datetime:
    """Demo clock: real UTC time plus an adjustable offset so demos can fast-forward."""
    return datetime.now(timezone.utc) + timedelta(hours=clock_offset_hours(c))


def set_clock_offset(c: sqlite3.Connection, hours: float) -> None:
    c.execute("INSERT INTO meta(key,value) VALUES('clock_offset_hours',?) "
              "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(hours),))
