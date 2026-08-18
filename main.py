import threading
import time
from datetime import datetime, timedelta

from pyrogram import Client
from pyrogram.enums import ParseMode
from decouple import config
from handlers.handler_message import (add_chat_by_link, add_chat_by_name, get_chat_by_id, search_channels,
                                      parse_media, parse_messages, other_message)
from handlers.handler_update import all_updates, all_chat_messages
from database.cleanup import cleanup
import logger


log = logger.get_logger(__name__)


def _scheduler_loop():
    """Фоновый планировщик: запускает cleanup() каждый день в 4:00."""
    while True:
        now = datetime.now()
        target = now.replace(hour=4, minute=0, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        sleep_seconds = (target - now).total_seconds()
        log.info("⏰ Следующая очистка БД в %s (через %d мин)", target.strftime('%H:%M'), int(sleep_seconds // 60))
        time.sleep(sleep_seconds)
        try:
            cleanup()
            log.info("🧹 Плановая очистка БД завершена")
        except Exception as e:
            log.error("❌ Ошибка при плановой очистке БД: %s", e)

# SOCKS5 прокси для выхода в Telegram
PROXY = dict(
    scheme="socks5",
    hostname="127.0.0.1",
    port=10808,
)

# Инициализация клиента с прокси
bot = Client(name=config('LOGIN'),
             api_id=config('API_ID'),
             api_hash=config('API_HASH'),
             phone_number=config('PHONE'),
             parse_mode=ParseMode.MARKDOWN,
             proxy=PROXY,
             no_updates=False,
             skip_updates=False,)


# Обработчики низкого приоритета (группа -1): сохранение всех обновлений
bot.add_handler(all_updates, group=-1)
bot.add_handler(all_chat_messages, group=-1)

# Обработчики среднего приоритета (группа 0): обработка сообщений из каналов
bot.add_handler(parse_media, group=0)
bot.add_handler(parse_messages, group=0)

bot.add_handler(get_chat_by_id, group=1)
bot.add_handler(search_channels, group=1)

# Обработчик последнего средства (группа 2): все остальное
bot.add_handler(other_message, group=2)

# Обработчики высокого приоритета (группа 1): команды пользователя
bot.add_handler(add_chat_by_link, group=1)
bot.add_handler(add_chat_by_name, group=1)


# Запуск фонового планировщика очистки БД (каждый день в 4:00)
scheduler_thread = threading.Thread(target=_scheduler_loop, daemon=True)
scheduler_thread.start()
log.info("🧹 Планировщик очистки БД запущен")

# Запуск клиента
log.info('Bot started')
try:
    bot.run()
except EOFError:
    log.error(
        'Pyrogram requires interactive login (confirmation code). '
        'Run the bot once in an interactive terminal to authorize the session.'
    )