from pyrogram import Client
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
from pyrogram.raw.functions.messages import GetMessageReactionsList
from typing import Optional

from telegram_types.base_type import ReactionType, ReactionDetails

from defs.channels_processor.channels import ChannelsProcessor
from defs.deepseek_api import get_response
from defs.methods.message_sender import MessageSender
from defs.methods.save_sent_message import SaveSentMessageHandler
from defs.methods.links.message_link import MessageLink

from database.db_start import Messages, ChatDetails, SentMessages, Channels
import logger


log = logger.get_logger(__name__)


class MessageFormChannel:
    @staticmethod
    def _is_message_from_tracked_source(message: Message, channel_id: int) -> bool:
        channel = Channels.get_channel_by_user_id(channel_id)
        if not channel or not channel.sources:
            return False
        return message.chat.id in channel.sources

    @staticmethod
    async def get_message_from_channel(client: Client, message: Message) -> None:
        """
        Получает сообщение из канала.
        :param client: Клиент подключения к боту
        :param message: Сообщение из группы или канала из которого нужно получить комментарии
        :return: Сообщение из канала
        """

        topic = TopicHandler.get_message_topic(message.text or message.caption)
        MessageSaveHandler.save_message_to_db(message, topic)

        category = ChatDetails.get_chat_category_by_id(str(message.chat.id))
        log.info(f'Поступило сообщение из категории {category}')

        try:
            if category == 'Новости и политика':
                res = await GroupHandler.get_messages_group(message, chat_id=str(-1002460211363))
                log.info(f'Найдены сообщения на эту же тему в истории {res}')
                if res == 'null':
                    sent_message = await MessageSender.send_message(client=client, chat_id=-1002460211363, message=message)
                    if sent_message:
                        SaveSentMessageHandler.save_sent_message(sent_message, topic=topic)
            if MessageFormChannel._is_message_from_tracked_source(message=message, channel_id=-1002560213613):
                await ChannelsProcessor(channel_id=-1002560213613).message_processor(client=client, message=message)
        except Exception as e:
            log.error(f'Failed to process channel message {message.chat.id}:{message.id}. Error: {e}')
        return None

    @staticmethod
    async def get_media_from_channel(client: Client, message: Message) -> None:
        """
        Получает медиафайл из канала.
        :param client: Клиент подключения к боту
        :param message: Сообщение из группы или канала из которого нужно получить комментарии
        :return: Сообщение из канала
        """

        if message.caption:
            topic = TopicHandler.get_message_topic(message.caption)
            MessageSaveHandler.save_message_to_db(message, topic)

            category = ChatDetails.get_chat_category_by_id(str(message.chat.id))
            log.info(f'Поступило сообщение из категории {category}')

            try:
                if category == 'Новости и политика':
                    res = await GroupHandler.get_messages_group(message, chat_id=str(-1002460211363))
                    log.info(f'Найдены сообщения на эту же тему в истории {res}')
                    if res == 'null':
                        sent_messages = await MediaGroupSender.send_media(client=client, chat_id=-1002460211363, message=message)
                        SaveSentMessageHandler.save_sent_message(sent_messages, topic)

                if MessageFormChannel._is_message_from_tracked_source(message=message, channel_id=-1002560213613):
                    await ChannelsProcessor(channel_id=-1002560213613).message_processor(client=client, message=message)
            except Exception as e:
                log.error(f'Failed to process channel media {message.chat.id}:{message.id}. Error: {e}')
        return None


class MessageSaveHandler:
    @staticmethod
    def save_message_to_db(message: Message, topic: str or None) -> str:
        """
        Сохраняет сообщение в базу данных.
        :param message: Сообщение для сохранения в базу данных
        :param topic: Тема сообщения
        :return: Результат сохранения Сообщения в базу данных
        """
        if message.media:
            res = Messages.add_message(Messages(chat_id = message.chat.id,
                                                message_id = message.id,
                                                message_type = str(message.media).split('.')[1],
                                                message_text = message.caption,
                                                message_topic = topic or '',
                                                message_date = message.date))
        else:
            res = Messages.add_message(Messages(chat_id = message.chat.id,
                                                message_id = message.id,
                                                message_type = 'TEXT',
                                                message_text = message.text,
                                                message_topic = topic or '',
                                                message_date = message.date))
        log.info(f'message saved to db result: {res}')
        return res


class MediaGroupSender:
    @staticmethod
    async def send_media(client: Client, chat_id: int, message: Message) -> list[Message] or None:
        """
        Отправляет медиа группу в чат.
        :param client: Клиент подключения к боту
        :param chat_id: ID чата куда нужно отправить медиа-группу
        :param message: Сообщение для отправки в чат
        :return: Результат отправки медиа-группы в чат
        """
        # Получаем всю медиа-группу
        media_group = await client.get_media_group(message.chat.id, message.id)
        # Подготавливаем медиафайлы для пересылки
        media_list = []
        for media in media_group:
            if media.photo:
                # Если это фото
                media_list.append(
                    InputMediaPhoto(media.photo.file_id, caption=media.caption)
                )
            elif media.video:
                # Если это видео
                media_list.append(
                    InputMediaVideo(media.video.file_id, caption=media.caption)
                )
        log.info(f'media list: {media_list}')

        # Пересылаем медиа-группу в чат с id chat_id
        try:
            res = await client.send_media_group(chat_id=chat_id, media=media_list)

            # Проверяем, что результат является списком и не пуст
            if isinstance(res, list) and res:
                message_ids = [msg.id for msg in res]
                log.info(f'Media group sent. Message IDs: {message_ids}')
                return res
            else:
                log.error('Unexpected response format from send_media_group')
                return None

        except Exception as e:
            log.error(f'Failed to send media group: {str(e)}')
            return None


class ReactionHandler:
    @staticmethod
    async def get_message_reactions(client: Client, group_name: str, message: Message) -> ReactionType:
        """
        Получает все реакции к сообщению.
        :param client: Клиент подключения к боту
        :param group_name: Имя группы или канала
        :param message: Сообщение, к которому нужно получить реакции
        :return: Реакций ReactionType
        """
        peer = await client.resolve_peer(group_name)
        reacts = await client.invoke(GetMessageReactionsList(peer=peer, id=message.id, limit=10))
        reaction_details = []
        for r in reacts.reactions:
            reaction_details.append(ReactionDetails(user_id = r.peer_id.user_id, emoticon = r.reaction.emoticon, date = r.date))
        reactions = ReactionType.create(count=reacts.count, reactions=reaction_details)
        return reactions


class TopicHandler:
#     @staticmethod
#     def get_message_topic(text: str) -> str or None:
#         """Получает название темы из сообщения."""
#         sys_msg = '''определи тему сообщения, тема должна отражать суть сообщения. ответ должен содержать 
# только название темы без кавычек и знаков препинания. Если сообщение пустое - верни null'''
#         try:
#             res = get_response(sys_message=sys_msg, user_message=text)
#             return res.choices[0].message.content
#         except Exception as e:
#             log.error(e)
#             return None

    @staticmethod
    def get_message_topic(text: Optional[str]) -> Optional[str]:
        """Получает название темы из сообщения."""
        if text is None or not str(text).strip():
            return None

        sys_msg = (
            "определи тему сообщения, тема должна отражать суть сообщения. "
            "ответ должен содержать только название темы без кавычек и знаков препинания. "
            "Если сообщение пустое - верни null"
        )
        try:
            res = get_response(sys_message=sys_msg, user_message=str(text).strip())
            content = res.choices[0].message.content
            if isinstance(content, str):
                content = content.strip()
                return None if not content or content.lower() == "null" else content
            return None
        except Exception as e:
            log.error(f"Topic detection failed: {e}")
            return None


class GroupHandler:
    @staticmethod
    async def get_messages_group(message: Message, chat_id: str) -> list:
        """
        Находит дубликаты сообщения из групп с одной темой и возвращает их.
        :param message: Сообщение которое мы будем сравнивать с историей сообщений.
        :param chat_id: ID группы или канала из которого нужно получить историю сообщений.
        :return: Сообщения из группы или канала
        """

        # Формируем системный prompt с инструкцией
        sys_prompt = """сравни семантическое содержание текущего сообщения с историей сообщений из новостных каналов.
Если в истории есть сообщения схожие с текущим по смыслу нужно вернуть список id этих сообщений.
Ответ должен содержать ТОЛЬКО массив с message_id этих сообщений. 
Если сообщение уникально по смыслу верни ТОЛЬКО null.
Истории сообщений будет передан в виде массива сообщений в следующем формате: channel_id|message_id|message_text.
"""

        # Получаем текст текущего сообщения
        current_text = message.text or message.caption or ""

        # Получаем историю сообщений из БД
        history_messages = SentMessages.get_latest_sent_messages_by_user(user_id=chat_id)
        # Формируем данные для API
        sys_message = f"{sys_prompt}\n\nТекущее сообщение для анализа:\n{current_text}"
        user_message = "\n".join(
            ['|'.join([str(x.channel_id), str(x.sent_message_id), str(x.message_text)]) for x in history_messages]
        )

        # Отправляем запрос в deepseek_api
        api_response = get_response(
            sys_message=sys_message,
            user_message=user_message
        )
        return api_response.choices[0].message.content
