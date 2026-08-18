from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait
import asyncio
import logger
from defs.filters.messages import Filters
from telegram_types.base_type import MessageBlockType

log = logger.get_logger(__name__)


class MessageSender:

    @staticmethod
    async def send_message(client: Client, chat_id: int, message: Message) -> Message or None:
        """
        Отправляет сообщение в чат с повторными попытками при FloodWait.
        :param client: Клиент подключения к боту
        :param chat_id: ID чата куда нужно отправить
        :param message: Сообщение для отправки в чат
        :return: Результат отправки сообщения в чат
        """

        message_text = message.text if message.text else message.caption
        message_blocked_type = Filters(text=message_text).apply_filters()
        log.info(
            f'MessageSender.send_message('
            f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
            f'target_chat_id={chat_id}) filter_result={message_blocked_type}'
        )
        if message_blocked_type != MessageBlockType.NORMAL:
            log.warning(f"""filtered message: {message.chat.id}, {message.id} is blocked\
                 message blocked type: {message_blocked_type}.""")
            return None

        caption = message.caption if message.caption else None

        send_attempts = 0
        max_attempts = 5
        while send_attempts < max_attempts:
            try:
                if not caption or len(caption) <= 1024:
                    res = await message.copy(chat_id, caption=caption)
                else:
                    res = await message.copy(chat_id, caption=caption[0:1024])
                    for i in range(1024, len(caption), 1024):
                        if i < len(caption):
                            res = await client.send_message(chat_id=chat_id, text=caption[i:i+1024])

                log.info(
                    f'MessageSender.send_message('
                    f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
                    f'target_chat_id={chat_id}) -> sent_message_id={res.id}'
                )
                return res

            except FloodWait as e:
                send_attempts += 1
                wait = e.value if hasattr(e, 'value') else 5
                log.warning(
                    f'FloodWait {wait}s при отправке в {chat_id} (попытка {send_attempts}/{max_attempts})'
                )
                await asyncio.sleep(wait + 1)

            except Exception as e:
                log.error(
                    f'MessageSender.send_message('
                    f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
                    f'target_chat_id={chat_id}) error: {type(e).__name__}: {e}'
                )
                return None

        log.error(f'MessageSender.send_message исчерпал попытки отправки в {chat_id} (FloodWait)')
        return None
