#!/usr/bin/env python3
"""Напоминание @rsgsyst (Стасу) о финальном решении."""
import sys, os, json, random, time as ttime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['PYTHONWARNINGS'] = 'ignore'

from pyrogram import Client
from decouple import config
import requests

LOGIN = config('LOGIN')
API_ID = config('API_ID', cast=int)
API_HASH = config('API_HASH')
DEEPSEEK_KEY = config('DEEPSEEK_API2', default='') or config('DEEPSEEK_API', default='')

SYSTEM_PROMPT = (
    "Ты — Максим. Переписываешься со Стасом (@rsgsyst). "
    "Стиль — спокойный, без наигранных эмоций. Смайлики — только 👍 или 😂. "
    "История: ты предложил музей космонавтики на ВДНХ завтра (16.05.2026) в 13:00. "
    "Стас спросил про дресс-код — ты ответил «как в прошлый раз». "
    "Прошло 2 часа. Вежливо напомни о себе и спроси финальное решение."
)

def ask_deepseek(system_prompt, user_message):
    if not DEEPSEEK_KEY:
        return None
    try:
        resp = requests.post(
            'https://api.deepseek.com/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {DEEPSEEK_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_message},
                ],
                'max_tokens': 300,
                'temperature': 0.7,
            },
            timeout=20,
        )
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ DeepSeek: {e}")
        return None

reply = ask_deepseek(SYSTEM_PROMPT, '[прошло 2 часа, напомни вежливо о музее завтра в 13:00 и спроси решение]')
if not reply:
    reply = "Стас, привет. Напомню про завтра — музей космонавтики в 13:00. Ты идёшь? 👍"

# Задержка 7-45 сек как обычно
delay = random.uniform(7, 45)
print(f"⏳ Задержка {delay:.0f} сек...")
ttime.sleep(delay)

c = Client(LOGIN, api_id=API_ID, api_hash=API_HASH)
with c:
    sent = c.send_message('@rsgsyst', reply)
    print(f"✅ Напоминание Стасу: {reply[:150]}")
