from pyrogram.types import Message
from pyrogram import Client
import logger


log = logger.get_logger(__name__)


async def raw_messages(client:Client, message: Message):
    # if message.from_user.username == 'MaximVolkov' or message.from_user.username == 'kalentev':
    #     await message.reply(gigachat_dialog(message.text))
    # else:
    log.info(f"поступило необработанное сообщение message = \
{message.chat.id}, {message.chat.title}, {message.text}")
