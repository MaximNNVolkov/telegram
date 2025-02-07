from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import ChatAction


def pars_comments(comments: list)-> str or None:
    '''Преобразует массив комментариев в строку для отправки пользователю.
    Возвращает None, если комментариев нет.'''

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
    '''
    Получает все комментарии от переданного сообщения.
    :param client: Клиент подключения к боту
    :param msg: Сообщение из группы или канала из которого нужно получить комментарии
    :return: Список комментариев к сообщению
    '''

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

async def get_group_info(client:Client, group_name:str, msg_from: Message, msg_id: int = None):

    if msg_id:
        msg = await client.get_messages(chat_id=group_name, message_ids=msg_id)
        await client.send_chat_action(chat_id=msg_from.chat.id, action=ChatAction.TYPING)
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
    async for comment in client.get_chat_history(chat.id):
        messages.append(comment)

    # Парсим полученные сообщения
    for m in messages[::-1]:
        if not m:
            print('empty')
            break
        print('___________________________________________')
        print('message_id', m.id, m.date)
        print(m.caption or m.text or m.media)
        if m.reactions:
            print(', '.join([(r.emoji or 'GIF') + ' - ' + str(r.count) for r in m.reactions.reactions]))
    return messages


# 551
# get_discussion_message()
# Client.get_chat_history()
# search_chats()
# get_chat_event_log()
