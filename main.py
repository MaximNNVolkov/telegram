from pyrogram import Client
from decouple import config
from handlers.handler_message import (add_chat_by_link, add_chat_by_name, get_chat_by_id, search_channels,
                                      parse_media, parse_messages, other_message)
import logger


log = logger.get_logger(__name__)


# Инициализация клиента
bot = Client(name=config('LOGIN'),
             api_id=config('API_ID'),
             api_hash=config('API_HASH'),
             phone_number=config('PHONE'))


bot.add_handler(add_chat_by_link)
bot.add_handler(add_chat_by_name)
bot.add_handler(get_chat_by_id)
bot.add_handler(search_channels)
bot.add_handler(parse_media)
bot.add_handler(parse_messages)
bot.add_handler(other_message)


# Запуск клиента
log.info('Bot started')
bot.run()

