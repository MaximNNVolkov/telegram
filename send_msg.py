#!/usr/bin/env python3
"""Отправка сообщения любому пользователю Telegram через Pyrogram + SOCKS5."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ['PYTHONWARNINGS'] = 'ignore'
from pyrogram import Client
from decouple import config

LOGIN = config('LOGIN')
API_ID = config('API_ID', cast=int)
API_HASH = config('API_HASH')

def main():
    if len(sys.argv) < 3:
        print("Usage: send_msg.py <username|user_id|phone> <text>")
        print("Example: send_msg.py @username Привет!")
        print("Example: send_msg.py 123456789 Привет!")
        sys.exit(1)

    target = sys.argv[1]
    text = ' '.join(sys.argv[2:])

    client = Client(LOGIN, api_id=API_ID, api_hash=API_HASH)
    try:
        with client:
            # Если числовой ID
            if target.lstrip('-').isdigit():
                chat_id = int(target)
            else:
                chat_id = target
            msg = client.send_message(chat_id, text)
            print(f"✅ Sent to {target} (msg_id={msg.id})")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
