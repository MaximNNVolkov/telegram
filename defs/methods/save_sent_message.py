from pyrogram.types import Message
from database.db_start import SentMessages
import logger


log = logger.get_logger(__name__)


class SaveSentMessageHandler:

    @staticmethod
    def save_sent_message(message: Message or list[Message], topic: str = ''):
        """
        Сохраняет сообщение в БД.
        :param message: Сообщение для сохранения
        :param topic: Тема сообщения
        :return: Результат сохранения сообщения
        """

        if isinstance(message, list):
            if len(message) > 0:
                message = message[0]
        res = SentMessages.add_sent_message(
            SentMessages(channel_id = str(message.chat.id),
                         sent_message_id = message.id,
                         message_type = str(message.media).split('.')[1] if message.media else 'TEXT',
                         message_text = message.caption or message.text,
                         message_topic = topic or '',
                         message_date = message.date))
        log.info(
            f'SaveSentMessageHandler.save_sent_message('
            f'channel_id={message.chat.id}, sent_message_id={message.id}, topic={topic}) -> {res}'
        )
        return res
