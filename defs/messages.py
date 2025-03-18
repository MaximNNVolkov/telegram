from pyrogram import Client
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
from pyrogram.raw.functions.messages import GetMessageReactionsList
from telegram_types.base_type import ReactionType, ReactionDetails
from defs.deepseek_api import get_response
from database.db_start import Messages, ChatDetails, SentMessages
import logger


log = logger.get_logger(__name__)


class MessageFormChannel:
    @staticmethod
    async def get_message_from_channel(client: Client, message: Message) -> None:
        """
        Получает сообщение из канала.
        :param client: Клиент подключения к боту
        :param message: Сообщение из группы или канала из которого нужно получить комментарии
        :return: Сообщение из канала
        """
        topic = TopicHandler.get_message_topic(message.text or message.caption)
        category = ChatDetails.get_chat_category_by_id(str(message.chat.id))
        log.info(f'Поступило сообщение из категории {category}')
        if category == 'Новости и политика':
            res = await GroupHandler.get_messages_group(message, chat_id=str(-1002460211363))
            log.info(f'Найдены сообщения на эту же тему в истории {res}')
            if res == 'null':
                sent_message = await MessageSender.send_message(client=client, chat_id=-1002460211363, message=message)
                SaveSentMessageHandler.save_sent_message(sent_message, topic=topic)
        MessageSaveHandler.save_message_to_db(message, topic)
        return None

    @staticmethod
    async def get_media_from_channel(client: Client, message: Message) -> None:
        """
        Получает медиафайл из канала.
        :param client: Клиент подключения к боту
        :param message: Сообщение из группы или канала из которого нужно получить комментарии
        :return: Сообщение из канала
        """
        topic = TopicHandler.get_message_topic(message.text or message.caption)
        category = ChatDetails.get_chat_category_by_id(str(message.chat.id))
        log.info(f'Поступило сообщение из категории {category}')
        if category == 'Новости и политика':
            res = await GroupHandler.get_messages_group(message, chat_id=str(-1002460211363))
            log.info(f'Найдены сообщения на эту же тему в истории {res}')
            if res == 'null':
                sent_message = await MediaGroupSender.send_media(client=client, chat_id=-1002460211363, message=message)
                SaveSentMessageHandler.save_sent_message(sent_message[0], topic)
        MessageSaveHandler.save_message_to_db(message, topic)

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


class MediaGroupSender:
    @staticmethod
    async def send_media(client: Client, chat_id: int, message: Message) -> list[Message]:
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
        if not message.caption:
            return []
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
        res = await client.send_media_group(chat_id=chat_id, media=media_list)
        log.info(f'media group sent to chat result: {res[0].id}')
        return res


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
        reactions = ReactionType(count=reacts.count, reactions=reaction_details)
        return reactions


class TopicHandler:
    @staticmethod
    def get_message_topic(text: str) -> str or None:
        """Получает название темы из сообщения."""
        sys_msg = '''определи тему сообщения, тема должна отражать суть сообщения. ответ должен содержать 
только название темы без кавычек и знаков препинания. Если сообщение пустое - верни null'''
        res = ''
        try:
            res = get_response(sys_message=sys_msg, user_message=text)
            return res.choices[0].message.content
        except Exception as e:
            log.error(e)
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
Истории сообщений будет передан в виде массива сообщений в следующем формате: channel_id|message_id|message_text.
Ответ должен содержать ТОЛЬКО массив с ID этих сообщений. 
Если сообщение уникально по смыслу  - верни null.
"""

        # Получаем текст текущего сообщения
        current_text = message.text or message.caption or ""

        # Получаем историю сообщений из БД
        # history_messages = Messages.get_latest_messages_by_category(category = ['Новости и политика'])
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


class SaveSentMessageHandler:
    @staticmethod
    def save_sent_message(message: Message, topic):
        """
        Сохраняет сообщение в БД.
        :param message: Сообщение для сохранения
        :param topic: Тема сообщения
        :return: Результат сохранения сообщения
        """
        res = SentMessages.add_sent_message(
            SentMessages(channel_id = str(message.chat.id),
                         sent_message_id = message.id,
                         message_type = str(message.media).split('.')[1] if message.media else 'TEXT',
                         message_text = message.caption or message.text,
                         message_topic = topic or '',
                         message_date = message.date))
