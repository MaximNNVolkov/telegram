from pyrogram.handlers import MessageHandler
from defs.replay_message import function_replay


my_handler = MessageHandler(function_replay)
