"""
Achille — Consolidation State Manager
Manages pending consolidation questions (oui/non from Telegram) stored as JSON on disk.
"""
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Optional

from config import settings


def _default_path() -> str:
    return settings.CONSOLIDATION_PENDING_PATH


def _default_expiry_hours() -> int:
    return settings.PENDING_EXPIRY_HOURS


def load_pending(path: Optional[str] = None) -> list[dict]:
    """Load pending items from JSON file. Returns empty list if file doesn't exist."""
    path = path or _default_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("pending", [])
    except (json.JSONDecodeError, OSError):
        return []


def save_pending(items: list[dict], path: Optional[str] = None) -> None:
    """Write pending items to JSON file."""
    path = path or _default_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"pending": items}, f, ensure_ascii=False, indent=2)


def add_pending(
    id: str,
    type: str,
    data: dict,
    message_text: str,
    path: Optional[str] = None,
) -> None:
    """Add a pending question entry."""
    path = path or _default_path()
    items = load_pending(path)
    entry = {
        "id": id,
        "type": type,
        "data": data,
        "message_text": message_text,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    items.append(entry)
    save_pending(items, path)


def get_last_pending(path: Optional[str] = None) -> Optional[dict]:
    """Get the most recently added pending item, or None if empty."""
    path = path or _default_path()
    items = load_pending(path)
    if not items:
        return None
    return items[-1]


def remove_pending(id: str, path: Optional[str] = None) -> None:
    """Remove a pending item by its id."""
    path = path or _default_path()
    items = load_pending(path)
    items = [item for item in items if item.get("id") != id]
    save_pending(items, path)


def cleanup_expired(
    path: Optional[str] = None,
    expiry_hours: Optional[int] = None,
) -> None:
    """Remove entries older than expiry_hours."""
    path = path or _default_path()
    expiry_hours = expiry_hours if expiry_hours is not None else _default_expiry_hours()
    items = load_pending(path)
    cutoff = datetime.now(timezone.utc) - timedelta(hours=expiry_hours)
    kept = []
    for item in items:
        created_at_str = item.get("created_at", "")
        try:
            created_at = datetime.fromisoformat(created_at_str)
            # If no timezone info, assume UTC
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            if created_at >= cutoff:
                kept.append(item)
        except (ValueError, TypeError):
            # Keep items with unparseable dates to avoid silent data loss
            kept.append(item)
    save_pending(kept, path)
