#!/usr/bin/env python3
"""Check news sent in the last hour — corrected for UTC timestamps."""
import sys
sys.path.insert(0, '/home/user1/telegram')
from database.db_start import SentMessages, db_conn
from datetime import datetime, timedelta
from sqlalchemy import func

with db_conn() as s:
    # DB stores UTC timestamps — use utcnow() not now() (which is MSK)
    now = datetime.utcnow()
    count = s.query(func.count(SentMessages.sent_message_id)).filter(
        SentMessages.channel_id == '-1002460211363',
        SentMessages.message_date >= now - timedelta(hours=1)
    ).scalar()
    print(count or 0)
