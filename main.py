from pyrogram import Client
from pyrogram.enums import ParseMode
from decouple import config
from handlers.handler_message import (add_chat_by_link, add_chat_by_name, get_chat_by_id, search_channels,
                                      parse_media, parse_messages, other_message)
from handlers.handler_update import all_updates, all_chat_messages
import logger


log = logger.get_logger(__name__)


# Инициализация клиента с прокси
bot = Client(name=config('LOGIN'),
             api_id=config('API_ID'),
             api_hash=config('API_HASH'),
             phone_number=config('PHONE'),
             parse_mode=ParseMode.MARKDOWN,
             no_updates=False,
             skip_updates=False,
             proxy={
                 "scheme": "http",
                 "hostname": "127.0.0.1",
                 "port": 10809,
             }) #todo: убрать, если не нужно


# Обработчики низкого приоритета (группа -1): сохранение всех обновлений
bot.add_handler(all_updates, group=-1)
bot.add_handler(all_chat_messages, group=-1)

# Обработчики среднего приоритета (группа 0): обработка сообщений из каналов
bot.add_handler(parse_media, group=0)
bot.add_handler(parse_messages, group=0)

# Обработчики высокого приоритета (группа 1): команды пользователя
bot.add_handler(add_chat_by_link, group=1)
bot.add_handler(add_chat_by_name, group=1)
bot.add_handler(get_chat_by_id, group=1)
bot.add_handler(search_channels, group=1)

# Обработчик последнего средства (группа 2): все остальное
bot.add_handler(other_message, group=2)


# Запуск клиента
log.info('Bot started')
try:
    bot.run()
except EOFError:
    log.error(
        'Pyrogram requires interactive login (confirmation code). '
        'Run the bot once in an interactive terminal to authorize the session.'
    )
