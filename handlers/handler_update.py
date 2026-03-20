import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Any

from pyrogram import filters
from pyrogram.handlers import RawUpdateHandler
from pyrogram.handlers import MessageHandler

import logger


log = logger.get_logger(__name__)
_updates_file = Path("telegram_updates.jsonl")
_write_lock = Lock()
_ignored_update_types = {"UpdateUserStatus"}


def _format_mapping(data: Any) -> Any:
    if not isinstance(data, dict):
        return repr(data)

    return {str(key): repr(value) for key, value in data.items()}


def _write_payload(payload: dict[str, Any]) -> None:
    line = json.dumps(payload, ensure_ascii=False)
    with _write_lock:
        with _updates_file.open("a", encoding="utf-8") as update_log:
            update_log.write(f"{line}\n")


async def _save_latest_channel_message(client, channel_id: int) -> None:
    chat_id = int(f"-100{channel_id}")
    latest_message = None

    async for message in client.get_chat_history(chat_id=chat_id, limit=1):
        latest_message = message
        break

    if latest_message is None:
        return

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "update_type": "MessageEvent",
        "source": "channel_too_long_backfill",
        "chat_id": latest_message.chat.id,
        "chat_type": str(latest_message.chat.type),
        "chat_title": latest_message.chat.title,
        "message_id": latest_message.id,
        "media": str(latest_message.media) if latest_message.media else None,
        "text": latest_message.text or latest_message.caption,
    }
    _write_payload(payload)


async def save_update_to_file(client, update, users, chats):
    update_type = type(update).__name__
    if update_type in _ignored_update_types:
        return

    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "update_type": update_type,
        "update": repr(update),
        "users": _format_mapping(users),
        "chats": _format_mapping(chats),
    }

    try:
        _write_payload(payload)

        if update_type == "UpdateChannelTooLong":
            channel_id = getattr(update, "channel_id", None)
            if channel_id:
                await _save_latest_channel_message(client=client, channel_id=channel_id)
    except Exception:
        log.exception("Failed to save incoming update to %s", _updates_file)


async def save_channel_group_message(_, message):
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "update_type": "MessageEvent",
        "source": "message_handler",
        "chat_id": message.chat.id,
        "chat_type": str(message.chat.type),
        "chat_title": message.chat.title,
        "message_id": message.id,
        "media": str(message.media) if message.media else None,
        "text": message.text or message.caption,
    }

    try:
        _write_payload(payload)
    except Exception:
        log.exception(
            "Failed to save message event %s:%s to %s",
            message.chat.id,
            message.id,
            _updates_file,
        )


all_updates = RawUpdateHandler(save_update_to_file)
all_chat_messages = MessageHandler(save_channel_group_message, filters=filters.channel | filters.group)
