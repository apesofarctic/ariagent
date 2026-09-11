"""SQLite persistence for consent, audit log, imported transactions and inferences.

Demo data stays in memory (data_generator); only Mode-B state and compliance
records live here. The DB file sits next to the backend package and is wiped
entirely by DELETE /api/data (DPDP erasure).
"""
import json
import os
import sqlite3
import threading
from datetime import date, datetime, timezone
from pathlib import Path

from .schemas import Transaction

DB_PATH = os.getenv("ARIAGENT_DB", str(Path(__file__).resolve().parent.parent / "ariagent.db"))

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS consent (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    granted_at TEXT NOT NULL,
    scopes TEXT NOT NULL,          -- json {"protect": bool, "grow": bool, "guide": bool}
    adult INTEGER NOT NULL,
    revoked_at TEXT
);
CREATE TABLE IF NOT EXISTS audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    actor TEXT NOT NULL,           -- which agent / "user" / "system"
    action TEXT NOT NULL,
    detail TEXT NOT NULL,
    why TEXT NOT NULL,
    reversible INTEGER NOT NULL,
    mode TEXT NOT NULL,            -- protect | grow | guide | system
    status TEXT NOT NULL           -- executed | prepared | held | suppressed | blocked | info
);
CREATE TABLE IF NOT EXISTS real_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    amount REAL NOT NULL,
    merchant TEXT NOT NULL,
    category TEXT NOT NULL,
    source TEXT NOT NULL           -- filename it came from
);
CREATE TABLE IF NOT EXISTS inferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    type TEXT NOT NULL UNIQUE,
    mode TEXT NOT NULL,
    title TEXT NOT NULL,
    statement TEXT NOT NULL,       -- plain-language "what we think"
    evidence TEXT NOT NULL,        -- json list[str]
    confidence REAL NOT NULL,
    deleted INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.executescript(_SCHEMA)
    return con


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---------------------------------------------------------------- consent

def save_consent(scopes: dict, adult: bool) -> dict:
    with _lock, _conn() as con:
        con.execute(
            "INSERT INTO consent (id, granted_at, scopes, adult, revoked_at) VALUES (1, ?, ?, ?, NULL) "
            "ON CONFLICT(id) DO UPDATE SET granted_at=excluded.granted_at, "
            "scopes=excluded.scopes, adult=excluded.adult, revoked_at=NULL",
            (_now(), json.dumps(scopes), int(adult)),
        )
    return get_consent()


def get_consent() -> dict:
    with _lock, _conn() as con:
        row = con.execute("SELECT * FROM consent WHERE id = 1").fetchone()
    if not row or row["revoked_at"]:
        return {"granted": False, "scopes": {}, "granted_at": None,
                "revoked_at": row["revoked_at"] if row else None}
    return {"granted": True, "scopes": json.loads(row["scopes"]),
            "granted_at": row["granted_at"], "revoked_at": None}


def revoke_consent() -> None:
    with _lock, _conn() as con:
        con.execute("UPDATE consent SET revoked_at = ? WHERE id = 1", (_now(),))
        con.execute(
            "INSERT INTO settings (key, value) VALUES ('data_mode', 'demo') "
            "ON CONFLICT(key) DO UPDATE SET value='demo'")


# ---------------------------------------------------------------- audit

def audit(actor: str, action: str, detail: str, why: str,
          reversible: bool, mode: str, status: str) -> None:
    with _lock, _conn() as con:
        con.execute(
            "INSERT INTO audit (ts, actor, action, detail, why, reversible, mode, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (_now(), actor, action, detail, why, int(reversible), mode, status))


def get_audit(limit: int = 200) -> list[dict]:
    with _lock, _conn() as con:
        rows = con.execute("SELECT * FROM audit ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [{**dict(r), "reversible": bool(r["reversible"])} for r in rows]


# ---------------------------------------------------------------- real transactions

def save_transactions(txns: list[Transaction], source: str) -> int:
    with _lock, _conn() as con:
        con.execute("DELETE FROM real_transactions")   # one imported statement at a time
        con.executemany(
            "INSERT INTO real_transactions (date, amount, merchant, category, source) "
            "VALUES (?, ?, ?, ?, ?)",
            [(str(t.date), t.amount, t.merchant, t.category, source) for t in txns])
        n = con.execute("SELECT COUNT(*) FROM real_transactions").fetchone()[0]
    return n


def get_transactions() -> list[Transaction]:
    with _lock, _conn() as con:
        rows = con.execute(
            "SELECT date, amount, merchant, category FROM real_transactions ORDER BY date").fetchall()
    return [Transaction(date=date.fromisoformat(r["date"]), amount=r["amount"],
                        merchant=r["merchant"], category=r["category"]) for r in rows]


def real_data_meta() -> dict:
    with _lock, _conn() as con:
        row = con.execute(
            "SELECT COUNT(*) AS n, MIN(date) AS first, MAX(date) AS last, MAX(source) AS source "
            "FROM real_transactions").fetchone()
    return {"count": row["n"], "first": row["first"], "last": row["last"], "source": row["source"]}


# ---------------------------------------------------------------- inferences

def upsert_inference(type_: str, mode: str, title: str, statement: str,
                     evidence: list[str], confidence: float) -> None:
    with _lock, _conn() as con:
        deleted = con.execute(
            "SELECT deleted FROM inferences WHERE type = ?", (type_,)).fetchone()
        if deleted and deleted["deleted"]:
            return  # user said "this is wrong" — don't resurrect it
        con.execute(
            "INSERT INTO inferences (ts, type, mode, title, statement, evidence, confidence) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(type) DO UPDATE SET ts=excluded.ts, statement=excluded.statement, "
            "evidence=excluded.evidence, confidence=excluded.confidence",
            (_now(), type_, mode, title, statement, json.dumps(evidence), confidence))


def get_inferences(include_deleted: bool = False) -> list[dict]:
    q = "SELECT * FROM inferences" + ("" if include_deleted else " WHERE deleted = 0")
    with _lock, _conn() as con:
        rows = con.execute(q + " ORDER BY id DESC").fetchall()
    return [{**dict(r), "evidence": json.loads(r["evidence"]), "deleted": bool(r["deleted"])}
            for r in rows]


def delete_inference(inference_id: int) -> str | None:
    """Marks an inference wrong/deleted; returns its type (for future suppression)."""
    with _lock, _conn() as con:
        row = con.execute("SELECT type FROM inferences WHERE id = ?", (inference_id,)).fetchone()
        if not row:
            return None
        con.execute("UPDATE inferences SET deleted = 1 WHERE id = ?", (inference_id,))
    return row["type"]


def deleted_inference_types() -> set[str]:
    with _lock, _conn() as con:
        rows = con.execute("SELECT type FROM inferences WHERE deleted = 1").fetchall()
    return {r["type"] for r in rows}


# ---------------------------------------------------------------- settings / mode

def set_setting(key: str, value: str) -> None:
    with _lock, _conn() as con:
        con.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))


def get_setting(key: str) -> str | None:
    with _lock, _conn() as con:
        row = con.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def set_data_mode(mode: str) -> None:
    with _lock, _conn() as con:
        con.execute("INSERT INTO settings (key, value) VALUES ('data_mode', ?) "
                    "ON CONFLICT(key) DO UPDATE SET value = ?", (mode, mode))


def get_data_mode() -> str:
    with _lock, _conn() as con:
        row = con.execute("SELECT value FROM settings WHERE key = 'data_mode'").fetchone()
    return row["value"] if row else "demo"


# ---------------------------------------------------------------- export / erase

def export_all() -> dict:
    with _lock, _conn() as con:
        txns = [dict(r) for r in con.execute("SELECT * FROM real_transactions ORDER BY date")]
        infs = [{**dict(r), "evidence": json.loads(r["evidence"])}
                for r in con.execute("SELECT * FROM inferences ORDER BY id")]
        aud = [dict(r) for r in con.execute("SELECT * FROM audit ORDER BY id")]
        cons = con.execute("SELECT * FROM consent WHERE id = 1").fetchone()
    return {
        "exported_at": _now(),
        "consent": dict(cons) if cons else None,
        "transactions": txns,
        "inferences": infs,
        "audit_log": aud,
    }


def delete_everything() -> None:
    with _lock, _conn() as con:
        for table in ("consent", "audit", "real_transactions", "inferences", "settings"):
            con.execute(f"DELETE FROM {table}")
