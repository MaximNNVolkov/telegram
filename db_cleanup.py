#!/usr/bin/env python3
"""Очистка БД telegram.db: удаление старых записей.

- Messages (сырые): старше 7 дней
- SentMessages (отправленные): старше 3 дней
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))
from database.db_start import db_conn, Messages, SentMessages  # noqa: E402
import logger  # noqa: E402

log = logger.get_logger(__name__)

RETENTION_DAYS = {
    Messages: 7,
    SentMessages: 3,
}


def vacuum():
    """Сжатие БД через VACUUM (возвращает свободное место ОС)."""
    from sqlalchemy import text
    try:
        with db_conn() as s:
            s.execute(text("VACUUM"))
            s.commit()
        log.info("🗜 VACUUM выполнен успешно")
    except Exception as e:
        log.error("❌ VACUUM не удался: %s", e)


def cleanup():
    for model, days in RETENTION_DAYS.items():
        cutoff = datetime.utcnow() - timedelta(days=days)
        with db_conn() as s:
            deleted = s.query(model).filter(model.message_date < cutoff).delete()
            s.commit()
            if deleted:
                log.info("🗑 Удалено %d записей из %s (старше %d дней)", deleted, model.__tablename__, days)
            else:
                log.info("✅ Старых записей для %s нет", model.__tablename__)

    vacuum()


if __name__ == "__main__":
    cleanup()
