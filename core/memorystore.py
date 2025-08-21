from datetime import datetime
from core.db import msgs_db

_state = msgs_db["chat_state"]

def set_last_order_id(user_id: str, order_id: str):
    if not (user_id and order_id):
        return
    _state.update_one(
        {"user_id": user_id},
        {"$set": {"last_order_id": order_id, "updated_at": datetime.utcnow()}},
        upsert=True,
    )

def get_last_order_id(user_id: str) -> str | None:
    doc = _state.find_one({"user_id": user_id}, {"last_order_id": 1})
    return (doc or {}).get("last_order_id")
