from pyrogram.handlers import MessageHandler
from defs.replay_message import raw_messages
from defs.chats import chat_link
from defs.get_chat import get_chat_link
from defs.search_channels import channel_search
from defs.messages import MessageFormChannel
from pyrogram import filters


add_chat_by_link = MessageHandler(chat_link, filters=filters.private &
                                                     filters.regex(pattern=r'https://t\.me\/+(\/\S*)?'))

add_chat_by_name = MessageHandler(chat_link, filters=filters.private &
                                             filters.regex(pattern=r'@+(\S*)?'))

get_chat_by_id = MessageHandler(get_chat_link, filters=filters.private &
                                                       filters.regex(pattern=r'^id -?\d+$'))
search_channels = MessageHandler(channel_search, filters=filters.private &
                                                    filters.regex(pattern=r'^search'))
parse_media = MessageHandler(MessageFormChannel.get_media_from_channel, filters=filters.channel & filters.media_group)
parse_messages = MessageHandler(MessageFormChannel.get_message_from_channel, filters=filters.channel)
other_message = MessageHandler(raw_messages)
