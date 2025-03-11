from pyrogram import Client
from pyrogram.types import Message, MessageEntity
from pyrogram.raw.functions.messages import GetMessageReactionsList
from telegram_types.base_type import ReactionType, ReactionDetails, ChatDetails
from defs.deepseek_api import get_response
from database.db_start import Messages, ChatDetails
import logger
import json


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
        if res == 'None':
            await message.copy(chat_id=-1002460211363)
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
    :param client: Клиент подключения к боту
    :param message: Сообщение из группы или канала из которого нужно получить комментарии
    :return: Сообщения из группы или канала
    """

    # Формируем системный промпт с инструкцией
    sys_prompt = """Найди в истории сообщений все записи с такой же новостью или информацией. 
Ответ должен содержать ТОЛЬКО JSON-массив с ID этих сообщений. 
Если дубликатов нет - верни null. Пример: [123, 456]"""

    # Получаем текст текущего сообщения
    current_text = message.text or message.caption or ""

    # Получаем историю сообщений из БД
    history_messages = Messages.get_latest_messages_by_category(category = 'Новости и политика')

    # Формируем данные для API
    sys_message = f"{sys_prompt}\n\nТекущее сообщение для анализа:\n{current_text}"
    user_message = "\n".join(
        [str((x.message_id, x.message_text)) for x in history_messages]
    )

    # Отправляем запрос в deepseek_api
    api_response = get_response(
        sys_message=sys_message,
        user_message=user_message
    )

    # Парсим результат
    try:
        result = json.loads(api_response)
        if isinstance(result, list) and all(isinstance(i, int) for i in result):
            return result
        return None
    except (json.JSONDecodeError, TypeError):
        return None
