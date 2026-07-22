"""MongoDB integration for OpenDemon.

Stores conversations, messages and logs in MongoDB Atlas.
Connection string is read from MONGODB_URI environment variable.

Usage:
    Set MONGODB_URI=mongodb+srv://user:pass@cluster0.pu3hvlg.mongodb.net/opendemon
    in your Render environment variables.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_client = None
_db = None


def get_db():
    """Get or create the MongoDB database connection."""
    global _client, _db
    if _db is not None:
        return _db

    uri = os.environ.get("MONGODB_URI", "")
    if not uri:
        return None

    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi

        _client = MongoClient(uri, server_api=ServerApi("1"), serverSelectionTimeoutMS=5000)
        # Ping to confirm connection
        _client.admin.command("ping")
        db_name = os.environ.get("MONGODB_DB", "opendemon")
        _db = _client[db_name]
        logger.info("[MongoDB] Connected to database: %s", db_name)
        print(f"[OpenDemon] MongoDB connected — database: {db_name}", flush=True)
        return _db
    except Exception as exc:
        logger.warning("[MongoDB] Connection failed: %s", exc)
        print(f"[OpenDemon] MongoDB unavailable: {exc}", flush=True)
        return None


# ── Conversations ──────────────────────────────────────────────────────────

def save_conversation(conversation_id: str, data: Dict[str, Any]) -> bool:
    """Save or update a conversation in MongoDB."""
    db = get_db()
    if db is None:
        return False
    try:
        db.conversations.update_one(
            {"_id": conversation_id},
            {"$set": {**data, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
        return True
    except Exception as exc:
        logger.debug("[MongoDB] save_conversation error: %s", exc)
        return False


def load_conversation(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Load a conversation from MongoDB."""
    db = get_db()
    if db is None:
        return None
    try:
        doc = db.conversations.find_one({"_id": conversation_id})
        return doc
    except Exception as exc:
        logger.debug("[MongoDB] load_conversation error: %s", exc)
        return None


def list_conversations(limit: int = 100) -> List[Dict[str, Any]]:
    """List all conversations sorted by most recent."""
    db = get_db()
    if db is None:
        return []
    try:
        cursor = db.conversations.find({}).sort("updated_at", -1).limit(limit)
        return list(cursor)
    except Exception as exc:
        logger.debug("[MongoDB] list_conversations error: %s", exc)
        return []


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation from MongoDB."""
    db = get_db()
    if db is None:
        return False
    try:
        db.conversations.delete_one({"_id": conversation_id})
        return True
    except Exception as exc:
        logger.debug("[MongoDB] delete_conversation error: %s", exc)
        return False


# ── Messages ───────────────────────────────────────────────────────────────

def save_message(conversation_id: str, message: Dict[str, Any]) -> bool:
    """Append a message to a conversation's message list."""
    db = get_db()
    if db is None:
        return False
    try:
        db.conversations.update_one(
            {"_id": conversation_id},
            {
                "$push": {"messages": message},
                "$set": {"updated_at": datetime.now(timezone.utc)},
            },
            upsert=True,
        )
        return True
    except Exception as exc:
        logger.debug("[MongoDB] save_message error: %s", exc)
        return False


# ── Logs ───────────────────────────────────────────────────────────────────

def save_log(entry: Dict[str, Any]) -> bool:
    """Save a log entry to MongoDB."""
    db = get_db()
    if db is None:
        return False
    try:
        db.logs.insert_one({**entry, "timestamp": datetime.now(timezone.utc)})
        return True
    except Exception as exc:
        logger.debug("[MongoDB] save_log error: %s", exc)
        return False


# ── Health ─────────────────────────────────────────────────────────────────

def ping() -> bool:
    """Check if MongoDB is reachable."""
    db = get_db()
    if db is None:
        return False
    try:
        db.client.admin.command("ping")
        return True
    except Exception:
        return False


__all__ = [
    "get_db",
    "save_conversation",
    "load_conversation",
    "list_conversations",
    "delete_conversation",
    "save_message",
    "save_log",
    "ping",
]
