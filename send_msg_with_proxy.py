"""
Отправка сообщения через Pyrogram с SOCKS5 прокси
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['PYTHONWARNINGS'] = 'ignore'
from pyrogram import Client
from decouple import config

LOGIN = config('LOGIN')
API_ID = config('API_ID', cast=int)
API_HASH = config('API_HASH')
PHONE_NUMBER = config('PHONE_NUMBER')

proxy = {
    "scheme": "socks5",
    "hostname": "127.0.0.1",
    "port": 10808,
}

async def main():
    if len(sys.argv) < 3:
        print("Usage: send_msg_with_proxy.py <username|user_id|phone> <text>")
        sys.exit(1)

    target = sys.argv[1]
    text = ' '.join(sys.argv[2:])

    app = Client(
        LOGIN,
        api_id=API_ID,
        api_hash=API_HASH,
        phone_number=PHONE_NUMBER,
        proxy=proxy,
        workdir="/home/user1/ai_hub/session"
    )

    async with app:
        try:
            # Если числовой ID
            if target.lstrip('-').isdigit():
                chat_id = int(target)
                await app.send_message(chat_id, text)
            else:
                await app.send_message(target, text)
            print(f"Сообщение отправлено {target}")
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())