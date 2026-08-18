#!/usr/bin/env python3
"""
Мониторинг диалогов — проверяет новые ответы каждые 5 мин (через cron).
Использует DeepSeek API для генерации осмысленных ответов.
"""
import sys, os, json, time as ttime
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['PYTHONWARNINGS'] = 'ignore'

from pyrogram import Client
from decouple import config

LOGIN = config('LOGIN')
API_ID = config('API_ID', cast=int)
API_HASH = config('API_HASH')
DEEPSEEK_KEY = config('DEEPSEEK_API2', default='') or config('DEEPSEEK_API', default='')
MY_USERNAME = 'anonim_cod'

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dialog_state.json')

# Контекст переписок — кто есть кто
CONVERSATIONS = {
    '@PeterParkerSpm': {
        'name': 'Питер',
        'pending': True,
        'system_prompt': (
            "Ты — Максим. Переписываешься с @PeterParkerSpm в Telegram. Стиль — спокойный, без наигранных эмоций. "
            "Твоя ЦЕЛЬ: уговорить его пойти с тобой в музей космонавтики на ВДНХ завтра (суббота 16.05.2026) в 13:00. "
            "Можешь предложить коньяк от себя как мотивацию. "
            "История: 1) ты спросил \"чем завтра занят?\" — он ответил \"Х.з. С женой погулять пойду куда-нибудь. Есть предложения?\" "
            "2) ты предложил музей + коньяк — он не ответил "
            "3) ты предложил прийти с женой втроём — он не ответил. "
            "Отвечай коротко, по-русски. Из смайликов — только 👍 или 😂. Никаких заискиваний, напора, неестественного энтузиазма."
        ),
    },
    '@rsgsyst': {
        'name': 'РСГСИСТ',
        'pending': True,
        'system_prompt': (
            "Ты — Максим. Переписываешься с @rsgsyst в Telegram. Стиль — спокойный, без наигранных эмоций. "
            "Твоя ЦЕЛЬ: уговорить его пойти с тобой в музей космонавтики на ВДНХ завтра (суббота 16.05.2026) в 13:00. "
            "Можешь предложить коньяк от себя как мотивацию. "
            "История: 1) ты предложил музей — он сказал \"я уже был там, летал в космос\" "
            "2) ты ответил \"с компанией второй раз интереснее + коньяк\" — он игнорит. "
            "Отвечай коротко, по делу. Из смайликов — только 👍 или 😂. Никакого наигранного энтузиазма."
        ),
    },
    '@kalentev': {
        'name': 'Калентьев',
        'pending': True,
        'system_prompt': (
            "Ты — Максим. Переписываешься с @kalentev в Telegram. Стиль — спокойный, без наигранных эмоций. "
            "Интересуешься его проектом aiabyron.ru — как он использует OpenClaw, какие фишки появились. "
            "История: 1) ты спросил \"как дела с проектом, что по планам?\" — он ответил \"Ты решил меня подбодрить?))\" "
            "2) дальше он рассказал \"Я его с опенклоу подружил\", потом сказал \"буду вне города\" "
            "3) ты написал \"а кстати, как ты OpenClaw встроил, какие фишки?\" — ждём ответ. "
            "Продолжай диалог про проект, выясни как именно он использует OpenClaw. Из смайликов — только 👍 или 😂."
        ),
    },
}

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            data = json.load(f)
            for k in data:
                if k in CONVERSATIONS:
                    CONVERSATIONS[k].update(data[k])

def save_state():
    out = {}
    for k, v in CONVERSATIONS.items():
        out[k] = {
            'last_our_id': v.get('last_our_id', 0),
            'last_their_id': v.get('last_their_id', 0),
            'pending': v.get('pending', True),
        }
    with open(STATE_FILE, 'w') as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

def ask_deepseek(system_prompt, user_message):
    """Генерирует ответ через DeepSeek API."""
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
                    {'role': 'user', 'content': f"Собеседник написал: {user_message}\n\nТвой ответ (только текст сообщения, без пояснений):"},
                ],
                'max_tokens': 300,
                'temperature': 0.7,
            },
            timeout=20,
        )
        data = resp.json()
        return data['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"⚠️ DeepSeek error: {e}")
        return None

def main():
    load_state()
    client = Client(LOGIN, api_id=API_ID, api_hash=API_HASH)
    any_new = False
    
    with client:
        for target, conv in CONVERSATIONS.items():
            if not conv.get('pending', True):
                continue
            
            try:
                target_id = int(target) if target.lstrip('-').isdigit() else target
                msgs = list(client.get_chat_history(target_id, limit=5))
                
                last_our = conv.get('last_our_id', 0)
                last_their = conv.get('last_their_id', 0)
                new_last_our = last_our
                new_last_their = last_their
                
                for m in reversed(msgs):
                    sender = m.from_user
                    is_me = sender and sender.username and sender.username.lower() == MY_USERNAME.lower()
                    
                    if is_me:
                        if m.id > new_last_our:
                            new_last_our = m.id
                    else:
                        if m.id > new_last_their:
                            new_last_their = m.id
                            if m.id > last_their:
                                text = m.text or m.caption or ''
                                print(f"📩 {target}: {text[:200]}")
                                any_new = True
                                
                                # Генерируем ответ через DeepSeek
                                reply = ask_deepseek(conv['system_prompt'], text)
                                if reply:
                                    ttime.sleep(3)
                                    try:
                                        sent = client.send_message(target_id, reply)
                                        print(f"✅ {target}: {reply[:150]}")
                                        new_last_our = sent.id if sent.id > new_last_our else new_last_our
                                    except Exception as e:
                                        print(f"❌ Ошибка отправки {target}: {e}")
                                else:
                                    print(f"⚠️ {target}: не удалось сгенерировать ответ")
                
                conv['last_our_id'] = new_last_our
                conv['last_their_id'] = new_last_their
                
            except Exception as e:
                print(f"⚠️ {target}: {e}")
        
        save_state()
    
    if any_new:
        print("✅ Есть новые ответы!")
    else:
        print("📭 Новых сообщений нет")

if __name__ == '__main__':
    main()
