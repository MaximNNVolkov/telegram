from pyrogram import Client
from pyrogram.types import Message

from defs.methods.message_sender import MessageSender
from defs.deepseek_api import get_response
from database.db_start import Channels
from defs.filters.messages import Filters
from telegram_types.base_type import MessageBlockType
import logger


log = logger.get_logger(__name__)


class ChannelsProcessor:

    def __init__(self, channel_id: int):
        self.channel_id = channel_id

    async def message_processor(self, client: Client, message: Message):
        """
        :param client - pyrogram client
        :param message - pyrogram message
        :return: None
        """
        log.info(f'message from channels from channel: {message.chat.title}')
        message_text = message.text if message.text else message.caption
        if message_text:

            message_blocked_type = Filters(text=message_text).apply_filters()
            if message_blocked_type != MessageBlockType.NORMAL:
                log.warning(f"""filtered message: {message.chat.id}, {message.id} is blocked/
                 message blocked type: {message_blocked_type}.""")
                return None

            mkw = MatchKeyWords(keywords=Channels().get_channel_keywords(channel_id=self.channel_id),
                                message=message_text)

            if mkw.response_match() == 'Да':
                await MessageSender().send_message(client=client, chat_id=self.channel_id, message=message)



class MatchKeyWords:

    def __init__(self, keywords: str, message: str):
        self.prompt = f"""проверь что в сообщении есть ключевые слова. Слова могут быть в разной форме, например в другом падеже.
Если хотя бы одно слово встречается в сообщении ответь "Да", если таких слов нет то ответь "Нет". ОТвет должен содержать только одно слово Да или Нет.

список ключевых слов:
{keywords}

сообщение:
{message}
"""

    def response_match(self) -> str:
        api_response = get_response(
            user_message=self.prompt
        )
        return api_response.choices[0].message.content
