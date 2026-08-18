#!/bin/bash
cd /home/user1/telegram || exit 1
source venv/bin/activate
exec python -m database.cleanup "$@"
