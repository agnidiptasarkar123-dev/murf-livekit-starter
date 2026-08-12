"""
escalation.py — Human Escalation Tool (Day 7 feature)

Handles escalating sensitive issues (fraud, human decisions) to a human team via
a local SQLite table and a Discord webhook.
"""

import logging
import os
import uuid
import aiohttp
from datetime import datetime, timezone
from dotenv import load_dotenv
from database import _get_connection

# Ensure .env is loaded so the webhook URL is available
load_dotenv(".env")
load_dotenv(".env.local")

logger = logging.getLogger("agent.escalation")

def init_escalations_db() -> None:
    """Create the escalations table if it does not already exist."""
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS escalations (
                    reference_id        TEXT PRIMARY KEY,
                    reason              TEXT,
                    summary             TEXT,
                    urgency             TEXT,
                    caller_language     TEXT,
                    preferred_followup  TEXT,
                    caller_id           TEXT,
                    status              TEXT DEFAULT 'open',
                    created_at          TEXT
                )
                """
            )
            conn.commit()
        logger.info("[DB] Escalations table initialised")
    except Exception as e:
        logger.error(f"[DB-ERROR] Error initialising escalations table: {e}")

# Initialise on import
init_escalations_db()

async def send_escalation(
    reason: str,
    summary: str,
    urgency: str,
    caller_language: str,
    preferred_followup: str,
    caller_id: str
) -> str:
    """
    Saves the escalation to the local database and attempts to POST it to Discord.
    Returns the reference_id generated.
    """
    reference_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # 1. Save to SQLite
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO escalations (
                    reference_id, reason, summary, urgency, caller_language,
                    preferred_followup, caller_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    reference_id, reason, summary, urgency, caller_language,
                    preferred_followup, caller_id, now_iso
                )
            )
            conn.commit()
        logger.info(f"[ESCALATION] Saved locally: {reference_id}")
    except Exception as e:
        logger.error(f"[ESCALATION-ERROR] Failed to save escalation {reference_id} to DB: {e}")
        # Even if DB fails, we should still try the webhook.

    # 2. Send to Discord Webhook
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.warning(f"[ESCALATION] No DISCORD_WEBHOOK_URL set. Escalation {reference_id} stored locally only.")
        return reference_id
        
    logger.info("DISCORD WEBHOOK: URL configured")
    logger.info(f"DISCORD WEBHOOK: sending {reference_id}")
    
    formatted_message = (
        f"🚨 **New Escalation:** {reference_id}\n"
        f"**Reason:** {reason}\n"
        f"**Urgency:** {urgency.title()}\n"
        f"**Language:** {caller_language}\n"
        f"**Follow-up:** {preferred_followup}\n"
        f"**Status:** Open\n"
        f"**Created Time:** {now_iso}\n\n"
        f"**Summary:** {summary}"
    )

    payload = {
        "content": formatted_message
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload, timeout=10.0) as response:
                logger.info(f"DISCORD WEBHOOK: status={response.status}")
                if response.status in (200, 204):
                    logger.info("DISCORD WEBHOOK: delivery successful")
                else:
                    body = await response.text()
                    logger.error(f"[ESCALATION-ERROR] Discord webhook failed for {reference_id}: HTTP {response.status} - Body: {body}")
    except Exception as e:
        logger.error(f"[ESCALATION-ERROR] Exception sending webhook for {reference_id}: {e}")
        # Never crash the conversation on a network failure
        
    return reference_id
