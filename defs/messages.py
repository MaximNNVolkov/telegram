from pyrogram import Client
from pyrogram.types import Message, InputMediaPhoto, InputMediaVideo
from pyrogram.raw.functions.messages import GetMessageReactionsList
from telegram_types.base_type import ReactionType, ReactionDetails, ChatDetails
from defs.deepseek_api import get_response
from database.db_start import Messages, ChatDetails
import logger


log = logger.get_logger(__name__)


async def get_message_from_channel(client:Client, message: Message) -> Message:
    """
    Получает сообщение из канала.
    :param client: Клиент подключения к боту
    :param message: Сообщение из группы или канала из которого нужно получить комментарии
    :return: Сообщение из канала
    """
    topic = get_message_topic(message.text or message.caption)
    category = ChatDetails.get_chat_category_by_id(message.chat.id)
    log.info(f'Поступило сообщение из категории {category}')
    if category == 'Новости и политика':
        res = await get_messages_group(message)
        log.info(f'Найдены сообщения на эту же тему в истории {res}')
        if res == 'null':
            if message.media_group_id:
                # Получаем всю медиагруппу
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

                # Пересылаем медиагруппу в чат с id -1002460211363
                await client.send_media_group(chat_id=-1002460211363, media=media_list)
            else:
                caption = message.caption if message.caption else None
                await message.copy(chat_id=-1002460211363, caption=caption)
    try:
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
    except Exception as e:
        log.error(e)
        return None


async def get_message_reactions(client:Client, group_name: str, message: Message) -> ReactionType:
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


def get_message_topic(text: str) -> str:
    """Получает название темы из сообщения."""
    sys_msg = '''определи тему сообщения, тема должна отражать суть сообщения. ответ должен содержать только название темы без кавычек и знаков препинания'''
    try:
        res = get_response(sys_message=sys_msg, user_message=text)
        return res.choices[0].message.content
    except Exception as e:
        log.error(e)
        return None


async def get_messages_group(message: Message) -> list:
    """
    Находит дубликаты сообщения из групп с одной темой и возвращает их.
    :param message: Сообщение из группы или канала из которого нужно получить комментарии
    :return: Сообщения из группы или канала
    """

    # Формируем системный промпт с инструкцией
    sys_prompt = """сравни семантическое содержание текущего сообщения с историей сообщений из новостных каналов.
Если в истории есть сообщения схожие с текущим по смыслу нужно вернуть список id этих сообщений.
Ответ должен содержать ТОЛЬКО JSON-массив с ID этих сообщений. 
Если сообщение уникально по смыслу  - верни null."""

    # Получаем текст текущего сообщения
    current_text = message.text or message.caption or ""

    # Получаем историю сообщений из БД
    history_messages = Messages.get_latest_messages_by_category(category = ['Новости и политика'])
    # Формируем данные для API
    sys_message = f"{sys_prompt}\n\nТекущее сообщение для анализа:\n{current_text}"
    user_message = "\n".join(
        ['|'.join([str(x.message_id), str(x.message_text)]) for x in history_messages]
    )

    # Отправляем запрос в deepseek_api
    api_response = get_response(
        sys_message=sys_message,
        user_message=user_message
    )
    return api_response.choices[0].message.content
