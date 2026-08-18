#!/usr/bin/env python3
"""Генерирует HTML-дашборд со статистикой новостного агрегатора."""
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parent))
from database.db_start import db_conn, Messages, SentMessages, ChatDetails, Channels
from sqlalchemy import func, desc

import logger
log = logger.get_logger("dashboard")


def get_stats():
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)

    with db_conn() as s:
        # Общие счётчики
        total_msgs = s.query(func.count(Messages.message_id)).scalar() or 0
        total_sent = s.query(func.count(SentMessages.sent_message_id)).scalar() or 0
        total_channels = s.query(func.count(ChatDetails.id)).scalar() or 0
        total_targets = s.query(func.count(Channels.id)).scalar() or 0

        # За последний час
        msgs_hour = s.query(func.count(Messages.message_id)).filter(
            Messages.message_date >= hour_ago).scalar() or 0
        sent_hour = s.query(func.count(SentMessages.sent_message_id)).filter(
            SentMessages.message_date >= hour_ago).scalar() or 0

        # За последние 24 часа — почасово
        hourly = []
        for h in range(23, -1, -1):
            start = now - timedelta(hours=h+1)
            end = now - timedelta(hours=h)
            recv = s.query(func.count(Messages.message_id)).filter(
                Messages.message_date.between(start, end)).scalar() or 0
            sn = s.query(func.count(SentMessages.sent_message_id)).filter(
                SentMessages.message_date.between(start, end)).scalar() or 0
            hourly.append((start.strftime("%H:%M"), recv, sn))

        # Топ чатов по активности
        top_chats = s.query(
            Messages.chat_id, ChatDetails.title, func.count(Messages.message_id).label('cnt')
        ).join(ChatDetails, Messages.chat_id == ChatDetails.id, isouter=True
        ).filter(Messages.message_date >= day_ago
        ).group_by(Messages.chat_id).order_by(desc('cnt')).limit(10).all()

        # Новости за последний час
        recent_news = s.query(SentMessages).filter(
            SentMessages.channel_id == '-1002460211363',
            SentMessages.message_date >= hour_ago
        ).order_by(desc(SentMessages.message_date)).limit(10).all()

        return dict(
            now=now.strftime("%Y-%m-%d %H:%M:%S"),
            total_msgs=total_msgs,
            total_sent=total_sent,
            total_channels=total_channels,
            total_targets=total_targets,
            msgs_hour=msgs_hour,
            sent_hour=sent_hour,
            hourly=hourly,
            top_chats=top_chats,
            recent_news=recent_news,
            news_channel_id="-1002460211363",
        )


def render_html(stats: dict):
    top_chats_rows = "".join(
        f"<tr><td>{r[0]}</td><td>{r[1] or '—'}</td><td>{r[2]}</td></tr>"
        for r in stats['top_chats']
    ) or "<tr><td colspan='3'>Нет данных</td></tr>"

    recent_rows = "".join(
        f"<tr><td>{n.message_date.strftime('%H:%M')}</td>"
        f"<td>{str(n.message_text or '')[:60]}</td></tr>"
        for n in stats['recent_news']
    ) or "<tr><td colspan='2'>Нет новостей за час</td></tr>"

    hourly_bars = "".join(
        f"<div class='bar-row'><span class='bar-label'>{h}</span>"
        f"<div class='bar-container'><div class='bar bar-recv' style='width:{max(recv*3,2)}px'>{recv}</div>"
        f"<div class='bar bar-sent' style='width:{max(sent*3,2)}px'>{sent}</div></div></div>"
        for h, recv, sent in stats['hourly']
    )

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>News Aggregator Dashboard</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0d1117; color: #c9d1d9; padding: 20px; }}
  h1 {{ color: #58a6ff; font-size: 1.5rem; margin-bottom: 20px; }}
  h2 {{ color: #8b949e; font-size: 1rem; margin: 20px 0 10px; text-transform: uppercase; letter-spacing: .05em; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px; }}
  .card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 16px; }}
  .card .value {{ font-size: 2rem; font-weight: 700; color: #f0f6fc; }}
  .card .label {{ font-size: .8rem; color: #8b949e; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .85rem; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #21262d; }}
  th {{ color: #8b949e; font-weight: 500; }}
  .bar-row {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; font-size: .8rem; }}
  .bar-label {{ width: 50px; color: #8b949e; text-align: right; flex-shrink: 0; }}
  .bar-container {{ display: flex; gap: 2px; flex-grow: 1; }}
  .bar {{ height: 20px; border-radius: 3px; display: flex; align-items: center; padding-left: 6px;
         font-size: .7rem; color: #fff; min-width: 2px; overflow: hidden; }}
  .bar-recv {{ background: #1f6feb; }}
  .bar-sent {{ background: #238636; }}
  .legend {{ display: flex; gap: 20px; margin: 10px 0; font-size: .85rem; }}
  .legend-item {{ display: flex; align-items: center; gap: 6px; }}
  .legend-dot {{ width: 12px; height: 12px; border-radius: 3px; }}
  .update-time {{ color: #484f58; font-size: .75rem; margin-top: 20px; text-align: right; }}
</style>
</head>
<body>
<h1>📊 News Aggregator &mdash; @anonim_cod</h1>

<div class="grid">
  <div class="card"><div class="value">{stats['total_msgs']:,}</div><div class="label">Всего получено</div></div>
  <div class="card"><div class="value">{stats['total_sent']:,}</div><div class="label">Всего отправлено</div></div>
  <div class="card"><div class="value">{stats['msgs_hour']}</div><div class="label">Получено за час</div></div>
  <div class="card"><div class="value">{stats['sent_hour']}</div><div class="label">Отправлено за час</div></div>
  <div class="card"><div class="value">{stats['total_channels']}</div><div class="label">Каналов в БД</div></div>
  <div class="card"><div class="value">{stats['total_targets']}</div><div class="label">Целевых каналов</div></div>
</div>

<h2>⏱ Почасовая активность (24ч)</h2>
<div class="legend">
  <div class="legend-item"><div class="legend-dot" style="background:#1f6feb"></div> Получено</div>
  <div class="legend-item"><div class="legend-dot" style="background:#238636"></div> Отправлено</div>
</div>
<div class="card" style="padding:12px">
{hourly_bars}
</div>

<h2>🔥 Топ каналов за сутки</h2>
<table>
  <tr><th>Chat ID</th><th>Название</th><th>Сообщений</th></tr>
  {top_chats_rows}
</table>

<h2>📰 Последние новости в AI новости</h2>
<table>
  <tr><th>Время</th><th>Текст</th></tr>
  {recent_rows}
</table>

<div class="update-time">Обновлено: {stats['now']}</div>
</body>
</html>"""


def main():
    stats = get_stats()
    html = render_html(stats)
    out_path = Path(__file__).resolve().parent / "dashboard.html"
    out_path.write_text(html, encoding="utf-8")
    log.info("Дашборд сохранён: %s", out_path)
    print(out_path)


if __name__ == "__main__":
    main()
