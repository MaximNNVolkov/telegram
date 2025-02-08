from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums.chat_type import ChatType
from pyrogram.raw.functions.messages import GetMessageReactionsList
from telegram_types.reaction_type import ReactionType, ReactionDetails, ChatDetails
from telegram_types.error_types import UnsupportedChatType


def pars_comments(comments: list)-> str or None:
    """Преобразует массив комментариев в строку для отправки пользователю.
    Возвращает None, если комментариев нет."""

    if len(comments) == 0:
        return None
    else:
        text = []
        for c in comments[::-1]:
            if hasattr(c, 'reactions'):
                text.append(''.join([c['user_name'], ', ', c['comment_date'].strftime('%d.%m.%Y %H:%M'),
                                       '\n', c['comment_text'],
                                       '\n', c['comment_reactions']]))
            else:
                text.append(''.join([c['user_name'], ', ', c['comment_date'].strftime('%d.%m.%Y %H:%M'),
                                       '\n', c['comment_text']]))
        return '\n\n'.join(text)


async def get_discussion_message(client:Client, msg: Message) -> list:
    """
    Получает все комментарии от переданного сообщения.
    :param client: Клиент подключения к боту
    :param msg: Сообщение из группы или канала из которого нужно получить комментарии
    :return: Список комментариев к сообщению
    """

    comments = []
    async for comment in client.get_discussion_replies(msg.chat.id, msg.id):
        if comment.from_user:
            if comment.from_user.username:
                user_name = '@' + comment.from_user.username
            else:
                user_name = comment.from_user.first_name + ' ' + comment.from_user.last_name
            comment_dict = {'user_id':comment.from_user.id,
                            'user_name':user_name}
        else:
            comment_dict = {'user_id':msg.sender_chat.id,
                            'user_name':'@'+msg.sender_chat.username or msg.sender_chat.first_name + ' ' + msg.sender_chat.last_name}
        comment_dict['comment_id'] = comment.id
        comment_dict['comment_date'] = comment.date
        comment_dict['comment_text'] = comment.text
        if comment.reactions:
            comment_dict['comment_reactions'] = ', '.join([(r.emoji or 'GIF') + ' ' + str(r.count)
                                                           for r in comment.reactions.reactions])
        comments.append(comment_dict)
    return comments


async def get_messages_from_group(client:Client, group_name:str, msg_from: Message, msg_id: int = None):

    print(await get_group_parameters(client, group_name))

    if msg_id:
        msg = await client.get_messages(chat_id=group_name, message_ids=msg_id)
        comments = await get_discussion_message(client, msg)
        if len(comments) == 0:
            await msg_from.reply(text='К этому сообщению нет комментариев.')
        else:
            await msg_from.reply(text=pars_comments(comments))
        return None

    messages = []
    # Получаем ID чата по его имени
    chat = await client.get_chat(group_name)
    # Используем итератор для получения всех сообщений
    async for message in client.get_chat_history(chat_id=chat.id, offset_id=738, offset=-1, limit=1):
        messages.append(message)

    # Парсинг полученных сообщения
    for m in messages:
        if not m:
            print('empty')

        print('___________________________________________')
        print('message_id', m.id, m.date)
        print(m.caption or m.text or m.media)
        if m.reactions:
            print(await get_message_reactions(client, group_name, m))
    return messages


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


async def get_group_parameters(client:Client, group_name:str) -> ChatDetails:
    """
    Получает информацию о группе или канале.
    :param client: Клиент подключения к боту
    :param group_name: Имя группы или канала
    :return:ChatDetails
    """

    chat = await client.get_chat(group_name)
    if chat.type == ChatType.GROUP:
        chat_info = ChatDetails(id=chat.id, type=chat.type, title=chat.title, username=None,
                                invite_link=chat.invite_link, members_count=chat.members_count)
    elif chat.type == ChatType.CHANNEL:
        chat_info = ChatDetails(id=chat.id, type=chat.type, title=chat.title, username=chat.username,
                                invite_link=None, members_count=chat.members_count)
    else:
        raise UnsupportedChatType(chat_type=chat.type, error_message='Неизвестный тип чата')
    return chat_info

# search_chats()
# get_chat_event_log()
