#!/usr/bin/env python3
"""Refresh dashboard cache from Telegram."""
import sys, os, json
os.environ['PYTHONWARNINGS'] = 'ignore'
from pyrogram import Client
from decouple import config

LOGIN = config('LOGIN')
API_ID = config('API_ID', cast=int)
API_HASH = config('API_HASH')
MY_USERNAME = 'anonim_cod'

DIALOGS = {
    '@PeterParkerSpm': {'name': 'Игорь', 'theme': 'Музей космонавтики', 'goal': 'Уговорить пойти'},
    '@rsgsyst': {'name': 'Стас', 'theme': 'Музей космонавтики', 'goal': 'Уговорить пойти'},
    '@kalentev': {'name': 'Калентьев', 'theme': 'aiabyron.ru / OpenClaw', 'goal': 'Расспросить про проект'},
    '@cikada33011': {'name': 'Влад', 'theme': 'Доработка агента для Игоря', 'goal': 'Узнать планы по агенту'},
}

state = {}
client = Client(LOGIN, api_id=API_ID, api_hash=API_HASH)

with client:
    for username, meta in DIALOGS.items():
        try:
            target = int(username) if username.lstrip('-').isdigit() else username
            msgs = list(client.get_chat_history(target, limit=100))
            messages = []
            for m in reversed(msgs):
                sender = m.from_user
                is_me = sender and sender.username and sender.username.lower() == MY_USERNAME.lower()
                sender_name = 'Я' if is_me else meta['name']
                messages.append({
                    'id': m.id, 'date': m.date.strftime('%d.%m %H:%M'), 'date_ts': m.date.timestamp(),
                    'sender': sender_name, 'is_me': is_me,
                    'text': m.text or m.caption or '[медиа]',
                })

            if messages and not messages[-1]['is_me']:
                st = 'pending'
            elif messages and messages[-1]['is_me']:
                lt = messages[-1]['text'].lower()
                st = 'completed_neutral' if any(w in lt for w in ['понял','окей','без проблем','жаль','в другой раз','удачи','ладно']) else 'pending'
            else:
                st = 'completed'

            state[username] = {
                'username': username, 'name': meta['name'], 'theme': meta['theme'],
                'goal': meta['goal'], 'status': st, 'messages': messages,
                'last_update': messages[-1]['date'] if messages else '-',
                'last_text': (messages[-1]['text'][:80]+'...') if messages and len(messages[-1]['text'])>80 else (messages[-1]['text'] if messages else '-'),
                'total_msgs': len(messages), 'unread': 0,
            }
            print(f'✅ {username} ({meta["name"]}): {len(messages)} msgs, status={st}')
        except Exception as e:
            print(f'⚠️ {username}: {e}')

with open(os.path.join(os.path.dirname(__file__), 'dashboard_cache.json'), 'w') as f:
    json.dump(state, f, indent=2, ensure_ascii=False)
print(f'\n✅ Кэш обновлён: {len(state)} диалогов')
