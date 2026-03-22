import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timezone, timedelta
import json
import pytest
from memory.consolidation_state import (
    add_pending,
    get_last_pending,
    remove_pending,
    cleanup_expired,
    load_pending,
    save_pending,
)


def test_add_and_get_pending(tmp_path):
    path = str(tmp_path / "pending.json")
    add_pending(
        id="abc123",
        type="belief_shift",
        data={"belief": "foo", "old": 3, "new": 5},
        message_text="Axel, tu sembles avoir changé d'avis sur foo. Confirmes-tu ?",
        path=path,
    )
    items = load_pending(path)
    assert len(items) == 1
    item = items[0]
    assert item["id"] == "abc123"
    assert item["type"] == "belief_shift"
    assert item["data"]["belief"] == "foo"
    assert item["message_text"] == "Axel, tu sembles avoir changé d'avis sur foo. Confirmes-tu ?"
    assert "created_at" in item

    # get_last_pending returns the item
    last = get_last_pending(path)
    assert last is not None
    assert last["id"] == "abc123"


def test_remove_pending(tmp_path):
    path = str(tmp_path / "pending.json")
    add_pending(id="id1", type="t", data={}, message_text="msg1", path=path)
    add_pending(id="id2", type="t", data={}, message_text="msg2", path=path)

    remove_pending("id1", path=path)
    items = load_pending(path)
    assert len(items) == 1
    assert items[0]["id"] == "id2"

    # Removing a non-existent id is a no-op
    remove_pending("nonexistent", path=path)
    items = load_pending(path)
    assert len(items) == 1


def test_get_last_pending_empty(tmp_path):
    path = str(tmp_path / "pending.json")
    result = get_last_pending(path)
    assert result is None


def test_cleanup_expired(tmp_path):
    path = str(tmp_path / "pending.json")

    # Add one recent and one old entry manually
    now = datetime.now(timezone.utc)
    old_time = (now - timedelta(hours=72)).isoformat()
    recent_time = now.isoformat()

    items = [
        {
            "id": "old1",
            "type": "t",
            "data": {},
            "message_text": "old",
            "created_at": old_time,
        },
        {
            "id": "recent1",
            "type": "t",
            "data": {},
            "message_text": "recent",
            "created_at": recent_time,
        },
    ]
    save_pending(items, path)

    cleanup_expired(path=path, expiry_hours=48)

    remaining = load_pending(path)
    assert len(remaining) == 1
    assert remaining[0]["id"] == "recent1"
