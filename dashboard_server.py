#!/usr/bin/env python3
"""
Dashboard — статическая HTML-страница без JS, данные встроены в HTML.
Работает в любом браузере, включая встроенный браузер Telegram.
"""
import sys, os, json, http.server, urllib.parse, threading, time as ttime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ['PYTHONWARNINGS'] = 'ignore'

from pyrogram import Client
from decouple import config

LOGIN = config('LOGIN')
API_ID = config('API_ID', cast=int)
API_HASH = config('API_HASH')
MY_USERNAME = 'anonim_cod'

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard_cache.json')
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dialog_state.json')
PORT = int(os.environ.get('DASHBOARD_PORT', 8899))

DIALOGS_META = {
    '@PeterParkerSpm': {'name': 'Игорь', 'theme': 'Музей космонавтики', 'goal': 'Уговорить пойти', 'auto': True},
    '@rsgsyst': {'name': 'Стас', 'theme': 'Музей космонавтики', 'goal': 'Уговорить пойти', 'auto': True},
    '@kalentev': {'name': 'Калентьев', 'theme': 'aiabyron.ru / OpenClaw', 'goal': 'Расспросить про проект', 'auto': True},
    '@cikada33011': {'name': 'Влад', 'theme': 'Доработка агента для Игоря', 'goal': 'Узнать планы по агенту', 'auto': True},
}

def esc(s):
    """Escapes text for safe HTML output."""
    if s is None:
        return ''
    return (str(s)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
        .replace("'", '&#x27;'))

MSG_LIMIT = 100

_cache = {}

def load_cache():
    global _cache
    if _cache:
        return _cache
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            _cache = json.load(f)
    return _cache

def fetch_history_async():
    """Фоновая загрузка истории из Telegram."""
    global _cache
    print("⏳ Фоновая загрузка истории...")
    try:
        client = Client(LOGIN, api_id=API_ID, api_hash=API_HASH)
        state = load_cache()
        
        with client:
            for username, meta in DIALOGS_META.items():
                try:
                    target_id = int(username) if username.lstrip('-').isdigit() else username
                    msgs = list(client.get_chat_history(target_id, limit=MSG_LIMIT))
                    messages = []
                    for m in reversed(msgs):
                        sender = m.from_user
                        is_me = sender and sender.username and sender.username.lower() == MY_USERNAME.lower()
                        sender_name = 'Я' if is_me else meta['name']
                        messages.append({
                            'id': m.id,
                            'date': m.date.strftime('%d.%m %H:%M'),
                            'date_ts': m.date.timestamp(),
                            'sender': sender_name,
                            'is_me': is_me,
                            'text': m.text or m.caption or '[медиа]',
                        })
                    
                    dialog_state = state.get(username, {}) if state else {}
                    last_our = dialog_state.get('last_our_id', 0)
                    unread = sum(1 for m in messages if not m['is_me'] and m['id'] > last_our)
                    
                    if messages and not messages[-1]['is_me']:
                        status = 'pending'
                    elif messages and messages[-1]['is_me']:
                        last_text = messages[-1]['text'].lower()
                        if any(w in last_text for w in ['понял', 'окей', 'без проблем', 'жаль', 'в другой раз', 'удачи']):
                            status = 'completed_neutral'
                        else:
                            status = 'pending'
                    else:
                        status = 'completed'
                    
                    state[username] = {
                        'username': username, 'name': meta['name'], 'theme': meta['theme'],
                        'goal': meta['goal'], 'status': status,
                        'messages': messages,
                        'last_update': messages[-1]['date'] if messages else '-',
                        'last_text': (messages[-1]['text'][:80] + '...') if messages and len(messages[-1]['text']) > 80 else (messages[-1]['text'] if messages else '-'),
                        'total_msgs': len(messages), 'unread': unread,
                    }
                    print(f"  ✅ {username}: {len(messages)} msgs")
                except Exception as e:
                    print(f"  ⚠️ {username}: {e}")
                    state[username] = {
                        'username': username, 'name': meta['name'], 'theme': meta['theme'],
                        'goal': meta['goal'], 'status': 'error', 'error': str(e), 'messages': [],
                    }
        
        with open(CACHE_FILE, 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        _cache = state
        print(f"✅ Кэш обновлён: {len(state)} диалогов")
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")

STATUS_LABELS = {
    'pending': 'в процессе',
    'completed': 'завершён',
    'completed_neutral': 'завершён',
    'error': 'ошибка',
}

def generate_page():
    """Генерирует полностью статическую HTML-страницу."""
    data = load_cache()
    
    cards = []
    status_order = {'pending': 0, 'completed_neutral': 1, 'completed': 2, 'error': 3}
    items = sorted(data.values(), key=lambda x: status_order.get(x.get('status', 'completed'), 99))
    
    for d in items:
        status = d.get('status', 'completed')
        badge_class = {'pending': 'badge-pending', 'completed': 'badge-done', 'completed_neutral': 'badge-neutral', 'error': 'badge-error'}.get(status, 'badge-neutral')
        status_text = STATUS_LABELS.get(status, status)
        unread_dot = '<span class="udot"></span>' if d.get('unread', 0) > 0 else ''
        
        msgs_html = ''
        for m in d.get('messages', []):
            me_class = ' msg-me' if m.get('is_me') else ''
            media_class = ' msg-media' if m.get('text') == '[медиа]' else ''
            sender_class = ' sender-me' if m.get('is_me') else ''
            msgs_html += f'''<div class="msg{me_class}{media_class}">
<div class="msg-meta"><span class="sender{sender_class}">{esc(m.get('sender', ''))}</span><span class="msg-time">{esc(m.get('date', ''))}</span></div>
<div class="msg-text">{esc(m.get('text', ''))}</div>
</div>'''
        
        expand_id = 'e-' + d.get('username', '').replace('@', '')
        card = f'''<div class="card">
<div class="card-header" onclick="toggle('{expand_id}')">
<div class="card-info">
<div class="card-name">{esc(d.get('name', ''))} <span class="card-username">{esc(d.get('username', ''))}</span>{unread_dot}</div>
<div class="card-theme">{esc(d.get('theme', ''))}</div>
<div class="card-goal">{esc(d.get('goal', ''))}</div>
</div>
<span class="badge {badge_class}">{esc(status_text)}</span>
</div>
<div class="card-preview">{esc(d.get('last_update', ''))} — {esc(d.get('last_text', ''))}</div>
<div class="card-msgs" id="{expand_id}">
{msgs_html}
</div>
</div>'''
        cards.append(card)
    
    cards_html = '\n'.join(cards) if cards else '<div class="empty">нет диалогов</div>'
    
    html = f'''<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dialogs 🦞</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#0d1117;color:#c9d1d9;padding:12px;font-size:14px;line-height:1.4}}
a{{color:#58a6ff;text-decoration:none}}
.header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #30363d}}
.header h1{{font-size:1.2rem;color:#58a6ff}}
.header h1 span{{color:#8b949e;font-weight:400}}
.update-btn{{display:inline-block;padding:5px 12px;background:#238636;color:#fff;border-radius:5px;font-size:13px;text-decoration:none}}
.update-btn:hover{{background:#2ea043}}
.cards{{display:flex;flex-direction:column;gap:8px}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:8px;overflow:hidden}}
.card-header{{padding:10px 12px;display:flex;justify-content:space-between;align-items:flex-start;cursor:pointer;border-bottom:1px solid #21262d;-webkit-tap-highlight-color:transparent;user-select:none}}
.card-header:active{{background:#1c2128}}
.card-info{{flex:1;min-width:0}}
.card-name{{font-weight:600;font-size:14px;margin-bottom:1px}}
.card-name span{{color:#8b949e;font-weight:400;font-size:12px}}
.card-theme{{color:#8b949e;font-size:12px}}
.card-goal{{color:#58a6ff;font-size:11px;margin-top:1px}}
.card-preview{{color:#8b949e;font-size:12px;padding:8px 12px;border-bottom:1px solid #21262d;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.badge{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;white-space:nowrap;flex-shrink:0}}
.badge-pending{{background:#1f6feb22;color:#58a6ff;border:1px solid #1f6feb44}}
.badge-done{{background:#23863622;color:#3fb950;border:1px solid #23863644}}
.badge-neutral{{background:#8b949e22;color:#8b949e;border:1px solid #8b949e44}}
.badge-error{{background:#da363322;color:#f85149;border:1px solid #da363344}}
.udot{{display:inline-block;width:7px;height:7px;border-radius:50%;background:#f85149;margin-left:5px;vertical-align:middle}}
.card-msgs{{display:none;max-height:60vh;overflow-y:auto;-webkit-overflow-scrolling:touch}}
.card-msgs.open{{display:block}}
.msg{{padding:8px 12px;border-bottom:1px solid #21262d;font-size:13px}}
.msg:last-child{{border-bottom:none}}
.msg-me{{background:#1f6feb08}}
.msg-media .msg-text{{color:#8b949e;font-style:italic}}
.msg-meta{{display:flex;justify-content:space-between;margin-bottom:3px;font-size:11px;color:#484f58}}
.sender{{color:#58a6ff;font-weight:500}}
.sender-me{{color:#3fb950}}
.msg-time{{color:#484f58}}
.msg-text{{white-space:pre-wrap;word-break:break-word}}
.empty{{color:#8b949e;text-align:center;padding:40px;font-size:15px}}
.status-bar{{color:#8b949e;font-size:11px;text-align:center;padding:8px 0;border-top:1px solid #21262d;margin-top:12px}}
@media(prefers-color-scheme:light){{body{{background:#fff;color:#24292f}}.header{{border-color:#d0d7de}}.card{{background:#fff;border-color:#d0d7de}}.card-header{{border-color:#e8ecef}}.card-preview,.msg{{border-color:#e8ecef}}.header h1{{color:#0969da}}.card-goal{{color:#0969da}}.badge-pending{{background:#ddf4ff;color:#0969da;border-color:#b6e3ff}}.badge-done{{background:#dafbe1;color:#1a7f37;border-color:#b6e3ff}}.badge-neutral{{background:#f6f8fa;color:#656d76;border-color:#d0d7de}}.sender{{color:#0969da}}.sender-me{{color:#1a7f37}}.status-bar{{border-color:#d0d7de;color:#656d76}}}}
</style>
</head>
<body>
<div class="header">
<h1>🦞 <span>диалоги</span></h1>
<a href="/" class="update-btn">⟳</a>
</div>
<div class="cards">
{cards_html}
</div>
<div class="status-bar">обновлено: {ttime.strftime('%d.%m %H:%M')}</div>
<script>
function toggle(id){{var e=document.getElementById(id);if(e)e.classList.toggle('open')}}
<\/script>
</body>
</html>'''
    return html

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.end_headers()
        html = generate_page()
        self.wfile.write(html.encode('utf-8'))
    
    def log_message(self, format, *args):
        pass

def main():
    print(f"🚀 Dashboard: http://localhost:{PORT}")
    
    cache = load_cache()
    if not cache:
        print("⏳ Кэш пуст, запускаю фоновую загрузку...")
        threading.Thread(target=fetch_history_async, daemon=True).start()
    else:
        print(f"✅ Кэш: {len(cache)} диалогов")
    
    server = http.server.HTTPServer(('0.0.0.0', PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Остановлен")

if __name__ == '__main__':
    main()
