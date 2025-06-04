from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.types import Message
from pyrogram.types import LinkPreviewOptions
import logger
from defs.filters.messages import Filters
from defs.methods.links.message_link import MessageLink
from defs.parser.markdown_parse import MarkdownParse
from telegram_types.base_type import MessageBlockType

log = logger.get_logger(__name__)


class MessageSender:

    @staticmethod
    async def send_message(client: Client, chat_id: int, message: Message) -> Message or None:
        """
        Отправляет сообщение в чат.
        :param client: Клиент подключения к боту
        :param chat_id: ID чата куда нужно отправить
        :param message: Сообщение для отправки в чат
        :return: Результат отправки сообщения в чат
        """

        md_parse = MarkdownParse(message)
        md_parse.parse_hashtags_and_links()
        print(md_parse.links)
        print(md_parse.hashtags)
        md_parse.parse_markdown()
        print(md_parse.markdown)
        new_text = md_parse.markdown + '\n\n' + await MessageLink().get_link(client=client,
                                                                             id_message=message.id,
                                                                             id_channel=message.chat.id)
        sended_msg = await client.send_message(chat_id=175431079, text=new_text,
                                  link_preview_options=LinkPreviewOptions(is_disabled=True))



        message_text = message.text if message.text else message.caption
        message_blocked_type = Filters(text=message_text).apply_filters()
        if message_blocked_type != MessageBlockType.NORMAL:
            log.warning(f"""filtered message: {message.chat.id}, {message.id} is blocked\
                 message blocked type: {message_blocked_type}.""")
            return None

        caption = message.caption if message.caption else None
        if not caption or len(caption) <= 1024:
            res = await message.copy(chat_id, caption=caption)
        else:
            res = await message.copy(chat_id, caption=caption[0:1024])
            for i in range(1024, len(caption), 1024):
                if i<len(caption):
                    res = await client.send_message(chat_id=chat_id, text=caption[i:i+1024])
        log.info(f'message sent to chat result: {res.id}')
        return res
