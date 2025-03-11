import logger
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.raw.types import ForumTopic, Chat
import re


log = logger.get_logger(__name__)


async def get_chat_link(client: Client, message: Message) -> Chat:
    log.debug(f'get_chat_link, from: {message.from_user.id}, message: {message.text}')
    chat_id = message.text.split(' ')[1]
    # chat_id = -(1000000000000 + int(chat_id))
    log.info(f'chat_id parsed from link: {chat_id}')
    try:
        gch = get_chat(client)
        chat = await gch.get_chat(chat_id=chat_id)
        link = await gch.get_chat_link(chat=chat)
        await message.reply(f'{chat.title} ({chat.id})\n{link}')
    except:
        pass
    return None


class get_chat():

    def __init__(self, client: Client):
        self.bot = client

    async def get_chat(self, chat_id: str) -> Chat:
        try:
            chat = await self.bot.get_chat(chat_id)
            self.chat = chat
            await self.channel_subscribe()
            return self.chat
        except Exception as e:
            log.error(f'[get_chat].get_chat. Error get chat {chat_id} {e}')
            return None

    async def get_chat_link(self, chat: Chat) -> str:
        log.debug(f'get_chat_link. chat_id: {chat.id}')
        try:
            if chat.username:
                return f"https://t.me/{chat.username}"
            else:
                return f"https://t.me/c/{str(chat.id).replace('-100', '')}"
        except Exception as e:
            log.error(f'Error get chat link {chat.id} {e}')
            return None

    async def channel_subscribe(self) -> bool:
        log.debug(f'channel_subscribe. chat_id: {self.chat.id}')
        try:
            await self.bot.join_chat(self.chat.id)
            return True
        except Exception as e:
            log.error(f'Error subscribe to chat {self.chat.id} {e}')
            return False
