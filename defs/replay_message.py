from pyrogram.types import Message
from pyrogram import Client
import logger


log = logger.get_logger(__name__)


async def raw_messages(client: Client, message: Message):
    log.info(f"НЕОБРАБОТАННОЕ СООБЩЕНИЕ: chat_id={message.chat.id}, chat_type={message.chat.type}, title={message.chat.title}, text={message.text[:50] if message.text else 'NO_TEXT'}")
    # if message.from_user.username == 'MaximVolkov' or message.from_user.username == 'kalentev':
    #     await message.reply(gigachat_dialog(message.text))
    # else:
