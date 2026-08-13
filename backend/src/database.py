"""
database.py — Persistent memory for Arthasathi (Day 4 feature)

Stores per-caller records in a local SQLite database.
ONLY scheme names checked and eligibility-related facts are stored.
NEVER store account numbers, card numbers, OTPs, PINs, or any
sensitive banking credentials.

The .db file is written to the same directory as this script so it
persists across agent restarts and is never stored in a temp directory.
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger("agent.database")

# Stable location: same directory as this source file, NOT /tmp
_DB_PATH = Path(__file__).parent / "arthasathi_users.db"


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the users table if it does not already exist."""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id           TEXT PRIMARY KEY,
                    name              TEXT,
                    language_preference TEXT,
                    facts             TEXT DEFAULT '{}',
                    last_interaction  TEXT,
                    do_not_call       BOOLEAN DEFAULT FALSE
                )
                """
            )
            # Create call_analytics table (Day 8)
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS call_analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    call_id TEXT,
                    caller_id TEXT,
                    started_at TEXT,
                    ended_at TEXT,
                    channel TEXT,
                    outcome TEXT,
                    created_at TEXT
                )
                """
            )
            # Gentle migration for Day 8 new columns
            for col, col_type in [
                ("duration_seconds", "INTEGER"),
                ("language", "TEXT"),
                ("success_reason", "TEXT"),
                ("task_type", "TEXT"),
                ("first_agent_response_latency_ms", "INTEGER")
            ]:
                try:
                    conn.execute(f"ALTER TABLE call_analytics ADD COLUMN {col} {col_type}")
                except sqlite3.OperationalError:
                    pass # Column already exists
                    
            try:
                conn.execute("ALTER TABLE users ADD COLUMN do_not_call BOOLEAN DEFAULT FALSE")
            except sqlite3.OperationalError:
                pass # Column already exists
            conn.commit()
        logger.info(f"[DB] Database initialised at {_DB_PATH}")
    except Exception as e:
        logger.error(f"[DB-ERROR] Error initialising database: {e}")


def get_user(user_id: str) -> dict | None:
    """
    Return the stored record for user_id, or None if not found.
    The returned dict has keys: user_id, name, language_preference,
    facts (already parsed from JSON), last_interaction.
    """
    try:
        with _get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
        if row is None:
            return None
        record = dict(row)
        try:
            record["facts"] = json.loads(record["facts"] or "{}")
        except (json.JSONDecodeError, TypeError):
            record["facts"] = {}
        logger.info(f"[DB] Found returning caller: user_id={user_id}")
        return record
    except Exception as e:
        logger.error(f"[DB-ERROR] Error getting user {user_id}: {e}")
        return None


def save_user(
    user_id: str,
    name: str | None,
    language_preference: str | None,
    facts: dict | None,
) -> None:
    """
    Insert a new record or update an existing one (upsert).
    facts must be a dict containing ONLY scheme/eligibility information.
    Timestamps are stored in UTC ISO-8601 format.
    """
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        facts_json = json.dumps(facts or {}, ensure_ascii=False)

        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users (user_id, name, language_preference, facts, last_interaction)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name              = COALESCE(excluded.name, name),
                    language_preference = COALESCE(excluded.language_preference, language_preference),
                    facts             = excluded.facts,
                    last_interaction  = excluded.last_interaction
                """,
                (user_id, name, language_preference, facts_json, now_iso),
            )
            conn.commit()
        logger.info(f"[DB] Saved caller: user_id={user_id}, name={name}, lang={language_preference}")
    except Exception as e:
        logger.error(f"[DB-ERROR] Error saving user {user_id}: {e}")

def set_do_not_call(user_id: str) -> None:
    """
    Mark a user's record with do_not_call = True so we never proactively call them again.
    """
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                UPDATE users SET do_not_call = TRUE WHERE user_id = ?
                """,
                (user_id,)
            )
            conn.commit()
        logger.info(f"[DB] Marked user_id={user_id} as DO NOT CALL")
    except Exception as e:
        logger.error(f"[DB-ERROR] Error setting do_not_call for user {user_id}: {e}")

def log_analytics(
    call_id: str,
    caller_id: str,
    started_at: str,
    ended_at: str,
    channel: str,
    outcome: str,
    duration_seconds: int = None,
    language: str = "Unknown",
    success_reason: str = None,
    task_type: str = "Unknown",
    first_agent_response_latency_ms: int = None
) -> None:
    """
    Day 8: Safely log exactly one call analytics record when a session ends.
    Failures here MUST NOT crash the calling function.
    """
    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO call_analytics (
                    call_id, caller_id, started_at, ended_at, channel, outcome, created_at,
                    duration_seconds, language, success_reason, task_type, first_agent_response_latency_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (call_id, caller_id, started_at, ended_at, channel, outcome, now_iso,
                 duration_seconds, language, success_reason, task_type, first_agent_response_latency_ms)
            )
            conn.commit()
        logger.info(f"[ANALYTICS] Recorded {outcome} for call {call_id} (Task: {task_type}, Duration: {duration_seconds}s)")
    except Exception as e:
        logger.error(f"[ANALYTICS-ERROR] Failed to log analytics for call {call_id}: {e}")


# Initialise the table when the module is imported
init_db()


def dump_all_users() -> None:
    """[Step 5 DB-DUMP] Print all rows in the users table to the log.
    Called immediately after every save to confirm data landed in the file.
    """
    try:
        with _get_connection() as conn:
            rows = conn.execute("SELECT user_id, name, language_preference, facts, last_interaction FROM users").fetchall()
        if not rows:
            logger.info("[DB-DUMP] users table is EMPTY — no rows found!")
        else:
            logger.info(f"[DB-DUMP] users table has {len(rows)} row(s):")
            for row in rows:
                logger.info(
                    f"[DB-DUMP]  user_id={row['user_id']!r} | name={row['name']!r} "
                    f"| lang={row['language_preference']!r} | facts={row['facts']!r} "
                    f"| last_interaction={row['last_interaction']!r}"
                )
    except Exception as e:
        logger.error(f"[DB-DUMP-ERROR] Failed to dump users table: {e}")
