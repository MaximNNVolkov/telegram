#!/usr/bin/env python3
"""Проверяет последние сообщения в чате с указанным пользователем."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['PYTHONWARNINGS'] = 'ignore'

from pyrogram import Client
from decouple import config

LOGIN = config('LOGIN')
API_ID = config('API_ID', cast=int)
API_HASH = config('API_HASH')

target = sys.argv[1] if len(sys.argv) > 1 else '@PeterParkerSpm'
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5

client = Client(LOGIN, api_id=API_ID, api_hash=API_HASH)
with client:
    if target.lstrip('-').isdigit():
        chat_id = int(target)
    else:
        chat_id = target
    msgs = list(client.get_chat_history(chat_id, limit=limit))
    for m in reversed(msgs):
        sender = m.from_user.username if m.from_user and m.from_user.username else m.from_user.first_name if m.from_user else '?'
        date = m.date.strftime('%H:%M')
        text = m.text or m.caption or '[media]'
        print(f"[{date}] {sender}: {text[:200]}")
