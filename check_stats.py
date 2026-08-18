import sys
sys.path.insert(0, '/home/user1/telegram')
from database.db_start import SentMessages, Messages, db_conn
from datetime import datetime, timedelta
from sqlalchemy import func
with db_conn() as s:
    total_sent = s.query(func.count(SentMessages.sent_message_id)).scalar()
    total_msgs = s.query(func.count(Messages.message_id)).scalar()
    recent = s.query(func.count(Messages.message_id)).filter(
        Messages.message_date >= datetime.utcnow() - timedelta(hours=1)
    ).scalar()
    news_sent_total = s.query(func.count(SentMessages.sent_message_id)).filter(
        SentMessages.channel_id == '-1002460211363'
    ).scalar()
    print(f'STATS: sent_total={total_sent} msgs_total={total_msgs} msgs_last_hour={recent} news_sent_total={news_sent_total}')
