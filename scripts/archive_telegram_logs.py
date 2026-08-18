#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

LOG_PATH = Path('/home/user1/telegram/telegram.loger')
BACKUP_PATH = Path('/home/user1/telegram/telegram.loger.backup')
LOCK_PATH = Path('/home/user1/telegram/.telegram_log_cleanup.lock')
TMP_PATH = Path('/home/user1/telegram/telegram.loger.tmp')
TIMESTAMP_RE = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})')
TS_FORMAT = '%Y-%m-%d %H:%M:%S,%f'


def parse_timestamp(line: str):
    match = TIMESTAMP_RE.match(line)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), TS_FORMAT)
    except ValueError:
        return None


def main() -> int:
    if not LOG_PATH.exists():
        print(f'No log file found: {LOG_PATH}')
        return 0

    cutoff = datetime.utcnow() - timedelta(days=7)

    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open('w', encoding='utf-8') as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

        moved_lines = 0
        kept_lines = 0
        current_bucket = 'keep'

        with LOG_PATH.open('r', encoding='utf-8', errors='replace') as src, \
             TMP_PATH.open('w', encoding='utf-8') as dst, \
             BACKUP_PATH.open('a', encoding='utf-8') as backup:

            for line in src:
                ts = parse_timestamp(line)
                if ts is not None:
                    current_bucket = 'old' if ts < cutoff else 'keep'

                if current_bucket == 'old':
                    backup.write(line)
                    moved_lines += 1
                else:
                    dst.write(line)
                    kept_lines += 1

        os.replace(TMP_PATH, LOG_PATH)

    print(
        f'cleanup complete: cutoff={cutoff.strftime(TS_FORMAT)}, '
        f'moved_lines={moved_lines}, kept_lines={kept_lines}'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
