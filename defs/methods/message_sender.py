from pyrogram import Client
from pyrogram.types import Message
import logger


log = logger.get_logger(__name__)


class MessageSender:
    @staticmethod
    async def send_message(client: Client, chat_id: int, message: Message) -> Message:
        """
        Отправляет сообщение в чат.
        :param client: Клиент подключения к боту
        :param chat_id: ID чата куда нужно отправить
        :param message: Сообщение для отправки в чат
        :return: Результат отправки сообщения в чат
        """
        caption = message.caption if message.caption else None
        if not caption:
            res = await message.copy(chat_id, caption=caption)
            log.info(f'message sent to chat result: {res.id}')
            return res
        if len(caption) > 1024:
            res = await message.copy(chat_id, caption=caption[0:1024])
            for i in range(1024, len(caption), 1024):
                if i<len(caption):
                    res = await client.send_message(chat_id=chat_id, text=caption[i:i+1024])
        else:
            res = await message.copy(chat_id, caption=caption)
        log.info(f'message sent to chat result: {res.id}')
        return res
