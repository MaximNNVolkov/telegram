"""Модуль очистки БД: удаление старых записей.

Запуск:
    python -m database.cleanup              # разовая очистка
    python -m database.cleanup --vacuum     # только VACUUM
    python -m database.cleanup --dry-run    # показать сколько будет удалено

Автономный — не требует внешних скриптов или cron-обёрток.
"""
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Добавляем корень проекта в sys.path для импорта
_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from database.db_start import db_conn, Messages, SentMessages
import logger

log = logger.get_logger(__name__)

RETENTION_DAYS = {
    Messages: 7,
    SentMessages: 3,
}

NAMES = {
    Messages: "Messages (сырые)",
    SentMessages: "SentMessages (отправленные)",
}


def cleanup(dry_run: bool = False, vacuum: bool = True) -> dict:
    """Удаляет старые записи из БД.

    Args:
        dry_run: Если True — только подсчёт, без удаления.
        vacuum: Если True — запустить VACUUM после удаления.

    Returns:
        Словарь с результатами: {имя_таблицы: количество_удалено}
    """
    results = {}

    for model, days in RETENTION_DAYS.items():
        cutoff = datetime.utcnow() - timedelta(days=days)
        table_name = NAMES.get(model, model.__tablename__)

        with db_conn() as session:
            query = session.query(model).filter(model.message_date < cutoff)
            count = query.count()

            if dry_run:
                log.info("📊 [DRY-RUN] %s: будет удалено %d записей (старше %d дней)",
                         table_name, count, days)
            else:
                deleted = query.delete(synchronize_session=False)
                session.commit()
                if deleted:
                    log.info("🗑 Удалено %d записей из %s (старше %d дней)",
                             deleted, table_name, days)
                else:
                    log.info("✅ Старых записей для %s нет", table_name)

            results[table_name] = count

    if not dry_run and vacuum:
        _vacuum()

    return results


def _vacuum():
    """Сжатие БД через VACUUM (возвращает свободное место ОС)."""
    from sqlalchemy import text
    try:
        with db_conn() as session:
            session.execute(text("VACUUM"))
            session.commit()
        log.info("🗜 VACUUM выполнен успешно")
    except Exception as e:
        log.error("❌ VACUUM не удался: %s", e)


def main():
    parser = argparse.ArgumentParser(
        description="Очистка telegram.db от старых записей."
    )
    parser.add_argument(
        "--vacuum", action="store_true",
        help="Только VACUUM (без удаления)"
    )
    parser.add_argument(
        "--dry-run", action="store_true", dest="dry_run",
        help="Показать сколько будет удалено (без реального удаления)"
    )
    parser.add_argument(
        "--no-vacuum", action="store_true", dest="no_vacuum",
        help="Не запускать VACUUM после удаления"
    )
    args = parser.parse_args()

    if args.vacuum:
        _vacuum()
        return

    cleanup(dry_run=args.dry_run, vacuum=not args.no_vacuum)


if __name__ == "__main__":
    main()
