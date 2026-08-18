#!/usr/bin/env python3
"""
Event-driven listener для Telegram. Отвечает только на ЛС от целевых пользователей.
Не мониторит каналы. Отвечает с задержкой 7-45 сек (рандом).
"""
import sys, os, json, random, time as ttime
import threading
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['PYTHONWARNINGS'] = 'ignore'

from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.enums import ChatType
from decouple import config

LOGIN = config('LOGIN')
API_ID = config('API_ID', cast=int)
API_HASH = config('API_HASH')
MY_USERNAME = 'anonim_cod'
DEEPSEEK_KEY = config('DEEPSEEK_API2', default='') or config('DEEPSEEK_API', default='')

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dialog_state.json')

# Только ЛС — никаких каналов и групп
TARGETS = {
    '@PeterParkerSpm': {
        'name': 'Игорь',
        'system_prompt': (
            "Ты — Максим. Переписываешься с Игорем (@PeterParkerSpm). "
            "Стиль — спокойный, без наигранных эмоций. Смайлики — только 👍 или 😂. "
            "История: ты приглашал в музей космонавтики, но Игорь отказался. Тема закрыта. "
            "ТЕКУЩАЯ ЗАДАЧА: диалог завершён. Если пишет — отвечай дружелюбно, больше не предлагай ничего."
        ),
    },
    '@rsgsyst': {
        'name': 'Стас',
        'system_prompt': (
            "Ты — Максим. Переписываешься со Стасом (@rsgsyst). "
            "Стиль — спокойный, без наигранных эмоций. Смайлики — только 👍 или 😂. "
            "История: ты предлагал музей космонавтики, Стас так и не ответил. Тема закрыта. "
            "ТЕКУЩАЯ ЗАДАЧА: диалог завершён. Если пишет — отвечай дружелюбно, больше не предлагай ничего."
        ),
    },
    '@kalentev': {
        'name': 'Калентьев',
        'system_prompt': (
            "Ты — Максим. Переписываешься с @kalentev. "
            "Стиль — спокойный, без наигранных эмоций. Смайлики — только 👍 или 😂. "
            "История: ты спрашивал про проект aiabyron.ru и как он использует OpenClaw. "
            "Он сказал, что будет вне города. "
            "Твоя цель: если ответит — расспросить про проект, иначе не беспокоить."
        ),
    },
    '@cikada33011': {
        'name': 'Влад',
        'system_prompt': (
            "Ты — Максим. Переписываешься с Владом (@cikada33011). "
            "Стиль — коротко, по делу. Без лишних эмоций. Можно немного сленга. Смайлики — только 👍 или 😂. "
            "История: ты написал про агента для Игоря — спросил что не устраивает и что планирует менять. "
            "Твоя цель: выяснить что конкретно не нравится в текущем агенте и какие планы по доработке. "
            "Задавай короткие уточняющие вопросы."
        ),
    },
}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

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
                    {'role': 'user', 'content': f"Собеседник написал: {user_message}\n\nТвой ответ (только текст сообщения, без кавычек и пояснений):"},
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

PENDING_REMINDERS = {}  # username -> timer

def _is_interested(text):
    """Проверяет, проявил ли собеседник интерес, но не дал финального ответа."""
    tl = text.lower()
    # Прямое согласие — не надо напоминать
    if any(w in tl for w in ['да', 'ок', 'ok', 'хорошо', 'буду', 'договорились', 'погнали', 'го', 'yes', 'yeah']):
        return False, 'accepted'
    # Прямой отказ — тоже
    if any(w in tl for w in ['нет', 'не', 'не могу', 'не получится', 'занят']):
        return False, 'declined'
    # Заинтересованность / размышление
    if any(w in tl for w in ['думаю', 'обсужу', 'подумаю', 'согласен', 'предварительно', 'посмотрю', 'уточню', 'может', 'наверное', 'возможно', 'предположительно', 'созвон', 'спрошу', 'соглас']):
        return True, 'thinking'
    # Вопросы про детали — тоже интерес
    if '?' in text:
        return True, 'details'
    return False, None

def schedule_reminder(client, username, chat_id, delay_hours=2):
    """Планирует напоминание через N часов, если ещё нет активного."""
    # Отменяем предыдущий таймер для этого пользователя
    if username in PENDING_REMINDERS:
        PENDING_REMINDERS[username].cancel()
    
    def remind():
        conv = TARGETS.get(username)
        if not conv:
            return
        # Проверяем, не ответил ли уже пользователь
        reply = ask_deepseek(
            conv['system_prompt'],
            '[системное: прошло 2 часа, собеседник не дал финального ответа. Напомни вежливо, спроси решение]'
        )
        if reply:
            try:
                sent = client.send_message(chat_id, reply)
                print(f"⏰ Напоминание {conv['name']}: {reply[:150]}")
                state = load_state()
                if username in state:
                    state[username]['last_our_id'] = sent.id
                    save_state(state)
            except Exception as e:
                print(f"❌ Ошибка напоминания: {e}")
        PENDING_REMINDERS.pop(username, None)
    
    delay_sec = delay_hours * 3600
    timer = threading.Timer(delay_sec, remind)
    timer.daemon = True
    timer.start()
    PENDING_REMINDERS[username] = timer
    print(f"⏰ Напоминание {conv['name']} через {delay_hours}ч (через {delay_sec}с)")

def handle_message(client, message):
    # Только ЛС, не каналы и не группы
    if message.chat.type != ChatType.PRIVATE:
        return
    
    sender = message.from_user
    if not sender:
        return
    
    username = f"@{sender.username}" if sender.username else None
    if username not in TARGETS:
        return
    
    # Игнорируем свои сообщения
    if sender.username and sender.username.lower() == MY_USERNAME.lower():
        return
    
    # Отменяем напоминание — пользователь написал
    if username in PENDING_REMINDERS:
        PENDING_REMINDERS[username].cancel()
        del PENDING_REMINDERS[username]
        print(f"❌ Напоминание {TARGETS[username]['name']} отменено — ответил")
    
    chat_id = message.chat.id
    conv = TARGETS[username]
    text = message.text or message.caption or ''
    
    print(f"📩 {conv['name']} ({username}): {text[:200]}")
    
    # Проверяем заинтересованность
    interested, interest_type = _is_interested(text)
    
    # Рандомная задержка 7-45 секунд
    delay = random.uniform(7, 45)
    print(f"⏳ Задержка {delay:.0f} сек...")
    ttime.sleep(delay)
    
    # Генерируем ответ
    reply = ask_deepseek(conv['system_prompt'], text)
    if not reply:
        print(f"⚠️ Не удалось ответить {username}")
        return
    
    try:
        sent = client.send_message(chat_id, reply)
        print(f"✅ {conv['name']}: {reply[:150]}")
        
        # Обновляем state
        state = load_state()
        if username not in state:
            state[username] = {}
        state[username]['last_our_id'] = sent.id
        state[username]['last_their_id'] = message.id
        state[username]['pending'] = True
        save_state(state)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Если проявил интерес — планируем напоминание через 2 часа
    if interested:
        schedule_reminder(client, username, chat_id, 2)
    elif interest_type == 'accepted':
        print(f"✅ {conv['name']} согласился!")
    elif interest_type == 'declined':
        print(f"❌ {conv['name']} отказался.")

def main():
    print("🚀 Listener started. Watching for DMs...")
    print(f"   Targets: {', '.join(TARGETS.keys())}")
    
    bot = Client(
        name=LOGIN,
        api_id=API_ID,
        api_hash=API_HASH,
        no_updates=False,
        skip_updates=False,
    )
    
    # Любое ЛС от любого пользователя — дальше фильтруем внутри
    bot.add_handler(MessageHandler(handle_message, filters.private))
    
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\n👋 Stopped")
    except EOFError:
        print("❌ Need interactive login. Run once manually.")

if __name__ == '__main__':
    main()
