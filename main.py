from pyrogram import Client
from decouple import config
from handlers.handler_message import my_handler


# Инициализация клиента
bot = Client(name=config('LOGIN'),
             api_id=config('API_ID'),
             api_hash=config('API_HASH'),
             phone_number=config('PHONE'))

bot.add_handler(my_handler)

# Запуск клиента
bot.run()