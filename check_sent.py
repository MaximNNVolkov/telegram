import sys
sys.path.insert(0, '/home/user1/telegram')
from database.db_start import SentMessages, db_conn
from datetime import datetime, timedelta
from sqlalchemy import func
with db_conn() as s:
    count = s.query(func.count(SentMessages.sent_message_id)).filter(
        SentMessages.channel_id == '-1002460211363',
        SentMessages.message_date >= datetime.utcnow() - timedelta(hours=1)
    ).scalar()
    print('SENT_LAST_HOUR=' + str(count or 0))
