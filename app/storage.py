"""SQLite persistence with AES (Fernet) encryption at rest.

DPDP Act compliance: clinical payloads, transcripts, beneficiary names and
field values are encrypted before they reach the disk. Only opaque ids, visit
types, weights and due dates stay in plain columns so the supervisor
dashboard and follow-up queries stay cheap - those are not identifying on
their own, and the full row is still keyed to an encrypted payload.

Key resolution order:
  1. ``SAHAYAK_ENCRYPTION_KEY`` (urlsafe base64 32-byte Fernet key)
  2. ``SAHAYAK_KEY_FILE`` (default ``app/data/fernet.key``), created on demand
"""

from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

APP_DIR = Path(__file__).resolve().parent
DEFAULT_DB = APP_DIR.parent / "sahayak.db"
DEFAULT_KEY_FILE = APP_DIR / "data" / "fernet.key"
SEED_FILE = APP_DIR / "data" / "seed_beneficiaries.json"

_lock = threading.RLock()  # reentrant: encrypt()/decrypt() run inside locked sections
_fernet = None
_fernet_source = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS beneficiaries (
    beneficiary_id TEXT PRIMARY KEY,
    name_enc       BLOB,
    village_enc    BLOB,
    created_at     TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    language    TEXT,
    started_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS visits (
    id              TEXT PRIMARY KEY,
    beneficiary_id  TEXT,
    visit_type      TEXT,
    weight_kg       REAL,
    next_visit_date TEXT,
    flagged         INTEGER NOT NULL DEFAULT 0,
    danger_count    INTEGER NOT NULL DEFAULT 0,
    language        TEXT,
    session_id      TEXT,
    payload_enc     BLOB NOT NULL,
    transcript_enc  BLOB,
    created_at      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS field_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    visit_id   TEXT NOT NULL,
    field      TEXT NOT NULL,
    value_enc  BLOB NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS follow_ups (
    id             TEXT PRIMARY KEY,
    visit_id       TEXT,
    beneficiary_id TEXT,
    kind           TEXT NOT NULL,
    due_date       TEXT,
    note_enc       BLOB,
    status         TEXT NOT NULL DEFAULT 'pending',
    created_at     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_visits_created ON visits(created_at);
CREATE INDEX IF NOT EXISTS idx_visits_beneficiary ON visits(beneficiary_id);
CREATE INDEX IF NOT EXISTS idx_followups_status ON follow_ups(status, due_date);
CREATE INDEX IF NOT EXISTS idx_history_visit ON field_history(visit_id);
"""


# --------------------------------------------------------------------------- #
# crypto
# --------------------------------------------------------------------------- #
def _key_file() -> Path:
    return Path(os.getenv("SAHAYAK_KEY_FILE") or DEFAULT_KEY_FILE)


def _load_fernet() -> Fernet:
    global _fernet, _fernet_source

    env_key = os.getenv("SAHAYAK_ENCRYPTION_KEY", "").strip()
    if env_key:
        if _fernet is None or _fernet_source != "env":
            _fernet = Fernet(env_key.encode())
            _fernet_source = "env"
        return _fernet

    path = _key_file()
    if _fernet is not None and _fernet_source == str(path) and path.exists():
        return _fernet

    with _lock:
        if path.exists():
            key = path.read_bytes().strip()
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            key = Fernet.generate_key()
            path.write_bytes(key + b"\n")
            try:
                os.chmod(path, 0o600)
            except OSError:
                pass
        _fernet = Fernet(key)
        _fernet_source = str(path)
    return _fernet


def encrypt(value) -> bytes | None:
    if value is None:
        return None
    if not isinstance(value, (str, bytes)):
        value = json.dumps(value, ensure_ascii=False)
    if isinstance(value, str):
        value = value.encode("utf-8")
    return _load_fernet().encrypt(value)


def decrypt(blob) -> str | None:
    if blob is None:
        return None
    try:
        return _load_fernet().decrypt(blob).decode("utf-8")
    except (InvalidToken, ValueError, TypeError):
        return None


def decrypt_json(blob) -> dict:
    text = decrypt(blob)
    if not text:
        return {}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def key_fingerprint() -> str:
    """Short, non-reversible identifier of the active key (for /health)."""
    key = _load_fernet()._signing_key  # noqa: SLF001 - Fernet exposes no digest
    import hashlib

    return hashlib.sha256(key).hexdigest()[:12]


# --------------------------------------------------------------------------- #
# connection
# --------------------------------------------------------------------------- #
def db_path() -> Path:
    raw = os.getenv("SAHAYAK_DB", "").strip()
    return Path(raw) if raw else DEFAULT_DB


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def _db():
    """Connection that is always closed, even when a query raises."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def init_db() -> None:
    with _lock, _db() as conn:
        conn.executescript(SCHEMA)
        conn.commit()


def seed_beneficiaries(path: Path | None = None) -> int:
    """Insert the synthetic dataset from app/data once, if the table is empty."""
    path = path or SEED_FILE
    if not path.exists():
        return 0
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0

    inserted = 0
    with _lock, _db() as conn:
        for row in rows:
            bid = str(row.get("beneficiary_id", "")).strip()
            if not bid:
                continue
            exists = conn.execute(
                "SELECT 1 FROM beneficiaries WHERE beneficiary_id = ?", (bid,)
            ).fetchone()
            if exists:
                continue
            conn.execute(
                "INSERT INTO beneficiaries (beneficiary_id, name_enc, village_enc, created_at)"
                " VALUES (?, ?, ?, ?)",
                (
                    bid,
                    encrypt(row.get("name")),
                    encrypt(row.get("village")),
                    _now(),
                ),
            )
            inserted += 1
        conn.commit()
    return inserted


DEMO_BENEFICIARIES = [
    {"beneficiary_id": "BEN-1042", "name": "Priya Sharma", "village": "Rampur"},
    {"beneficiary_id": "BEN-1043", "name": "Baby of Meena Devi", "village": "Rampur"},
    {"beneficiary_id": "BEN-1038", "name": "Anjali Verma", "village": "Chandpur"},
    {"beneficiary_id": "BEN-1035", "name": "Baby of Sunita", "village": "Chandpur"},
    {"beneficiary_id": "BEN-1029", "name": "Kavita Singh", "village": "Rampur"},
]


def seed_demo_beneficiaries() -> int:
    inserted = 0
    with _lock, _db() as conn:
        for row in DEMO_BENEFICIARIES:
            bid = row["beneficiary_id"]
            exists = conn.execute(
                "SELECT 1 FROM beneficiaries WHERE beneficiary_id = ?", (bid,)
            ).fetchone()
            if exists:
                continue
            conn.execute(
                "INSERT INTO beneficiaries (beneficiary_id, name_enc, village_enc, created_at)"
                " VALUES (?, ?, ?, ?)",
                (bid, encrypt(row["name"]), encrypt(row["village"]), _now()),
            )
            inserted += 1
        conn.commit()
    return inserted


# --------------------------------------------------------------------------- #
# beneficiaries
# --------------------------------------------------------------------------- #
def upsert_beneficiary(beneficiary_id: str, name: str | None = None,
                       village: str | None = None) -> dict:
    beneficiary_id = str(beneficiary_id).strip()
    with _lock, _db() as conn:
        existing = conn.execute(
            "SELECT * FROM beneficiaries WHERE beneficiary_id = ?", (beneficiary_id,)
        ).fetchone()
        if existing:
            conn.execute(
                "UPDATE beneficiaries SET name_enc = COALESCE(?, name_enc),"
                " village_enc = COALESCE(?, village_enc) WHERE beneficiary_id = ?",
                (encrypt(name) if name else None,
                 encrypt(village) if village else None,
                 beneficiary_id),
            )
        else:
            conn.execute(
                "INSERT INTO beneficiaries (beneficiary_id, name_enc, village_enc, created_at)"
                " VALUES (?, ?, ?, ?)",
                (beneficiary_id, encrypt(name), encrypt(village), _now()),
            )
        conn.commit()
    return get_beneficiary(beneficiary_id) or {"beneficiary_id": beneficiary_id}


def get_beneficiary(beneficiary_id: str) -> dict | None:
    with _db() as conn:
        row = conn.execute(
            "SELECT * FROM beneficiaries WHERE beneficiary_id = ?", (beneficiary_id,)
        ).fetchone()
    return _beneficiary_row(row) if row else None


def find_beneficiary_by_name(query: str) -> dict | None:
    """Find a seeded or recorded beneficiary whose name matches query."""
    if not query:
        return None
    q = query.strip().lower()
    for b in list_beneficiaries(limit=200):
        name = (b.get("name") or "").strip().lower()
        if not name:
            continue
        if q == name or q in name or name in q:
            return b
    return None


def list_beneficiaries(limit: int = 100) -> list[dict]:
    with _db() as conn:
        rows = conn.execute(
            "SELECT b.*, (SELECT COUNT(*) FROM visits v WHERE v.beneficiary_id = b.beneficiary_id)"
            " AS visit_count FROM beneficiaries b ORDER BY b.created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_beneficiary_row(r, r["visit_count"]) for r in rows]


def _beneficiary_row(row, visit_count: int | None = None) -> dict:
    bid = row["beneficiary_id"]
    return {
        "id": bid,
        "rch_id": bid,
        "beneficiary_id": bid,
        "name": decrypt(row["name_enc"]),
        "village": decrypt(row["village_enc"]),
        "created_at": row["created_at"],
        "visit_count": visit_count if visit_count is not None else 0,
    }


# --------------------------------------------------------------------------- #
# sessions / visits
# --------------------------------------------------------------------------- #
def start_session(language: str = "en") -> str:
    sid = uuid.uuid4().hex
    with _lock, _db() as conn:
        conn.execute(
            "INSERT INTO sessions (id, language, started_at) VALUES (?, ?, ?)",
            (sid, language, _now()),
        )
        conn.commit()
    return sid


def save_visit(record: dict, transcript: str | None = None,
               language: str = "en", session_id: str | None = None) -> dict:
    """Persist a saved visit, its field history and its follow-ups."""
    visit_id = uuid.uuid4().hex
    created = _now()
    payload = dict(record)
    payload["visit_id"] = visit_id
    payload["created_at"] = created

    flagged = bool(record.get("flagged"))
    danger_signs = list(record.get("danger_signs") or [])
    beneficiary_id = record.get("beneficiary_id")

    follow_ups = _build_follow_ups(visit_id, record, created)

    with _lock, _db() as conn:
        if beneficiary_id:
            existing = conn.execute(
                "SELECT 1 FROM beneficiaries WHERE beneficiary_id = ?", (beneficiary_id,)
            ).fetchone()
            if not existing:
                conn.execute(
                    "INSERT INTO beneficiaries (beneficiary_id, created_at) VALUES (?, ?)",
                    (beneficiary_id, created),
                )

        conn.execute(
            "INSERT INTO visits (id, beneficiary_id, visit_type, weight_kg, next_visit_date,"
            " flagged, danger_count, language, session_id, payload_enc, transcript_enc, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                visit_id,
                beneficiary_id,
                record.get("visit_type"),
                record.get("weight_kg"),
                record.get("next_visit_date"),
                1 if flagged else 0,
                len(danger_signs),
                language,
                session_id,
                encrypt(payload),
                encrypt(transcript) if transcript else None,
                created,
            ),
        )

        for field_name, value in record.items():
            if field_name in ("danger_signs", "flagged"):
                continue
            conn.execute(
                "INSERT INTO field_history (visit_id, field, value_enc, created_at)"
                " VALUES (?, ?, ?, ?)",
                (visit_id, field_name, encrypt(value), created),
            )

        for fu in follow_ups:
            conn.execute(
                "INSERT INTO follow_ups (id, visit_id, beneficiary_id, kind, due_date,"
                " note_enc, status, created_at) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)",
                (
                    fu["id"],
                    visit_id,
                    beneficiary_id,
                    fu["kind"],
                    fu["due_date"],
                    encrypt(fu.get("note")),
                    created,
                ),
            )
        conn.commit()

    return {
        "visit_id": visit_id,
        "beneficiary_id": beneficiary_id,
        "visit_type": record.get("visit_type"),
        "weight_kg": record.get("weight_kg"),
        "vaccinations_due": record.get("vaccinations_due") or [],
        "next_visit_date": record.get("next_visit_date"),
        "flagged": flagged,
        "danger_signs": danger_signs,
        "language": language,
        "created_at": created,
        "follow_ups": follow_ups,
    }


def _build_follow_ups(visit_id, record, created) -> list[dict]:
    out = []
    if record.get("flagged"):
        out.append({
            "id": uuid.uuid4().hex,
            "visit_id": visit_id,
            "kind": "phc_referral",
            "due_date": created[:10],
            "note": ", ".join(record.get("danger_signs") or []) or "danger sign",
            "status": "pending",
        })
    if record.get("next_visit_date"):
        out.append({
            "id": uuid.uuid4().hex,
            "visit_id": visit_id,
            "kind": "next_visit",
            "due_date": record["next_visit_date"],
            "note": "Scheduled follow-up visit",
            "status": "pending",
        })
    if record.get("vaccinations_due"):
        out.append({
            "id": uuid.uuid4().hex,
            "visit_id": visit_id,
            "kind": "immunisation",
            "due_date": record.get("next_visit_date"),
            "note": ", ".join(record["vaccinations_due"]),
            "status": "pending",
        })
    return out


def get_visit(visit_id: str) -> dict | None:
    with _db() as conn:
        row = conn.execute("SELECT * FROM visits WHERE id = ?", (visit_id,)).fetchone()
        if not row:
            return None
        history = conn.execute(
            "SELECT field, value_enc, created_at FROM field_history"
            " WHERE visit_id = ? ORDER BY id",
            (visit_id,),
        ).fetchall()
        fus = conn.execute(
            "SELECT * FROM follow_ups WHERE visit_id = ? ORDER BY created_at", (visit_id,)
        ).fetchall()

    record = decrypt_json(row["payload_enc"])
    return {
        "visit_id": row["id"],
        "beneficiary_id": row["beneficiary_id"],
        "visit_type": row["visit_type"],
        "weight_kg": row["weight_kg"],
        "next_visit_date": row["next_visit_date"],
        "flagged": bool(row["flagged"]),
        "danger_count": row["danger_count"],
        "language": row["language"],
        "created_at": row["created_at"],
        "record": record,
        "transcript": decrypt(row["transcript_enc"]),
        "field_history": [
            {
                "field": h["field"],
                "value": decrypt(h["value_enc"]),
                "created_at": h["created_at"],
            }
            for h in history
        ],
        "follow_ups": [_follow_up_row(f) for f in fus],
    }


def list_visits(limit: int = 50, beneficiary_id: str | None = None,
                flagged_only: bool = False) -> list[dict]:
    query = (
        "SELECT id, beneficiary_id, visit_type, weight_kg, next_visit_date, flagged,"
        " danger_count, language, created_at FROM visits"
    )
    clauses, params = [], []
    if beneficiary_id:
        clauses.append("beneficiary_id = ?")
        params.append(beneficiary_id)
    if flagged_only:
        clauses.append("flagged = 1")
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    with _db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [
        {
            "visit_id": r["id"],
            "beneficiary_id": r["beneficiary_id"],
            "visit_type": r["visit_type"],
            "weight_kg": r["weight_kg"],
            "next_visit_date": r["next_visit_date"],
            "flagged": bool(r["flagged"]),
            "danger_count": r["danger_count"],
            "language": r["language"],
            "created_at": r["created_at"],
        }
        for r in rows
    ]


# --------------------------------------------------------------------------- #
# follow-ups
# --------------------------------------------------------------------------- #
def _follow_up_row(row) -> dict:
    return {
        "id": row["id"],
        "visit_id": row["visit_id"],
        "beneficiary_id": row["beneficiary_id"],
        "kind": row["kind"],
        "due_date": row["due_date"],
        "note": decrypt(row["note_enc"]),
        "status": row["status"],
        "created_at": row["created_at"],
    }


def list_follow_ups(status: str | None = "pending", limit: int = 100) -> list[dict]:
    with _db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM follow_ups WHERE status = ? ORDER BY due_date IS NULL,"
                " due_date, created_at DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM follow_ups ORDER BY due_date IS NULL, due_date,"
                " created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
    return [_follow_up_row(r) for r in rows]


def complete_follow_up(follow_up_id: str, status: str = "done") -> dict | None:
    if status not in ("done", "pending", "skipped"):
        status = "done"
    with _lock, _db() as conn:
        conn.execute("UPDATE follow_ups SET status = ? WHERE id = ?", (status, follow_up_id))
        conn.commit()
        row = conn.execute("SELECT * FROM follow_ups WHERE id = ?", (follow_up_id,)).fetchone()
    return _follow_up_row(row) if row else None


def dashboard() -> dict:
    today = date.today()
    soon = (today + timedelta(days=7)).isoformat()
    with _db() as conn:
        total_visits = conn.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
        visits_today = conn.execute(
            "SELECT COUNT(*) FROM visits WHERE substr(created_at, 1, 10) = ?",
            (today.isoformat(),),
        ).fetchone()[0]
        flagged = conn.execute("SELECT COUNT(*) FROM visits WHERE flagged = 1").fetchone()[0]
        beneficiaries = conn.execute("SELECT COUNT(*) FROM beneficiaries").fetchone()[0]
        due = conn.execute(
            "SELECT COUNT(*) FROM follow_ups WHERE status = 'pending' AND due_date IS NOT NULL"
            " AND due_date <= ?",
            (today.isoformat(),),
        ).fetchone()[0]
        upcoming = conn.execute(
            "SELECT COUNT(*) FROM follow_ups WHERE status = 'pending' AND due_date IS NOT NULL"
            " AND due_date > ? AND due_date <= ?",
            (today.isoformat(), soon),
        ).fetchone()[0]
        by_type = conn.execute(
            "SELECT COALESCE(visit_type, 'unknown') AS t, COUNT(*) AS n"
            " FROM visits GROUP BY t ORDER BY n DESC"
        ).fetchall()
    return {
        "beneficiaries": beneficiaries,
        "total_visits": total_visits,
        "visits_today": visits_today,
        "flagged_visits": flagged,
        "follow_ups_due": due,
        "follow_ups_next_7_days": upcoming,
        "visits_by_type": {r["t"]: r["n"] for r in by_type},
    }


# --------------------------------------------------------------------------- #
# purge (DPDP Act deletion utility)
# --------------------------------------------------------------------------- #
def purge_all(keep_beneficiaries: bool = False, remove_db_file: bool = False) -> dict:
    """Delete every clinical artefact. Returns the row counts removed."""
    counts = {}
    tables = ["field_history", "follow_ups", "visits", "sessions"]
    if not keep_beneficiaries:
        tables.append("beneficiaries")

    with _lock, _db() as conn:
        for table in tables:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            conn.execute(f"DELETE FROM {table}")
        conn.commit()
        try:
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except sqlite3.Error:
            pass

    path = db_path()
    if remove_db_file:
        for suffix in ("", "-wal", "-shm"):
            target = Path(str(path) + suffix)
            try:
                target.unlink()
            except (FileNotFoundError, PermissionError):
                pass
        counts["db_file_removed"] = True
    return counts
