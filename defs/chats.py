from pyrogram.raw.functions.channels import GetForumTopics
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.enums import MessageEntityType
from pyrogram.raw.types import ForumTopic, Chat
from pyrogram.errors import NotAcceptable
import logger
from defs.gigachat_api import giga, HumanMessage, SystemMessage
from defs.deepseek_api import get_response
from database.defs_base import add_chat_details
from database.db_start import ChatDetails
from database.defs_base import get_chat_details
from defs.get_chat import get_chat


prompt_classified = """это история сообщений в телеграм канале.
сообщения приведены записями в формате:
message_id|date|text|chat_id|chat_title

message_id - id сообщения
date - дата сообщения
text - текст сообщения
chat_id - id чата
chat_title - название чата

тебе нужно определить:
Определить основную тематику сообщений. 
Отнести тематику к одной из следующих категорий:
Новости и политика
Бизнес и финансы
Технологии и IT
Наука и образование
Здоровье и фитнес
Развлечения и досуг
Культура и искусство
Путешествия и туризм
Дом, семья и лайфстайл
Авто и транспорт
Профессиональные и деловые сообщества
Социальные и местные сообщества
Хобби и творчество
Экология и природа
Дом и ремонт
Если категории не соответствуют тематике, категория должна быть «Общая тематика».

ничего не добавляй, не придумывай, не нужно обсуждать сообщения с пользователем.
В ответ пользователю необходимо ответить кратким структурированным сообщением
chat_id|chat_title|Категория чата|Тематика чата."""


log = logger.get_logger(__name__)


async def chat_link(client:Client, message: Message):

    log.info(f'add_chat_link, from: {message.from_user.id}, message: {message.text}')

    if message.entities:
        for entity in message.entities:
            if entity.type in [MessageEntityType.URL, MessageEntityType.MENTION]:
                entity_text = message.text[entity.offset:entity.offset+entity.length]
                chat = await get_chat(client=client).get_chat(entity_text)
            log.debug(f'chat_id parsed from link: {chat.id}')

            if get_chat_details(chat.id) != 'no_chat_details':
                log.info(f'chat {chat.id} details already exists')
                await message.reply_text(f'Чат {chat.title} уже добавлен')
                continue


            try:
                msgs = await get_last_messages(client=client, chat_id=chat.id, limit=10)
                msgs_for_giga = '\n'.join([str('|'.join(map(str, v)).replace('\n', ' '))
                                       for v in map(dict.values, msgs)])
            except NotAcceptable as e:
                log.error(f'Chat {chat.id} is unavailable. Error args: {e.args}')
            answ_giga = await get_deepseek_classified('|'.join(msgs[0].keys()) + '\n' + msgs_for_giga)
            save_channel(chat, answ_giga)
            await message.reply_text(answ_giga)


def save_channel(chat: Chat, message: str):
    log.info('received text for save channel info')
    if message is not None:
        category = str(message.split('|')[2])
        term = str(message.split('|')[3])
        res = add_chat_details(ChatDetails(id=str(chat.id),
                                       title=chat.title,
                                       type=str(chat.type),
                                       username='' if chat.username is None else chat.username,
                                       invite_link='' if chat.invite_link is None else chat.invite_link,
                                       members_count=chat.members_count,
                                       chat_category=category,
                                       chat_term=term))
        return res
    return message


async def get_giga_classified(messages: str) -> str:
    log.info('received text for analysis via Gigachat')
    m = [SystemMessage(content=prompt_classified)]
    m.append(HumanMessage(content='Таблица с сообщениями: ' + messages))
    answ = giga(messages=m)
    return answ.content


async def get_deepseek_classified(messages: str) -> str:
    log.info('received text for analysis via DeepSeek')
    sys_msg = prompt_classified
    res = get_response(sys_message=sys_msg, user_message=messages)
    res.choices[0].message.content
    return res.choices[0].message.content


def get_messages_for_save(message):
    if message.from_user:
        try:
            return {
            'message_id': message.id,
            'date': message.date,
            'text': message.text or message.caption,
            # 'sender_id': message.from_user.id,
            # 'first_name': message.from_user.first_name,
            # 'last_name': message.from_user.last_name,
            # 'username': message.from_user.username,
            'chat_id': message.chat.id,
            'chat_title': message.chat.title
        }
        except Exception as e:
            log.error(f'get_messages_for_save error: {e.args}')
            print(message)
    else:
        try:
            return{
            'message_id': message.id,
            'date': message.date,
            'text': message.text or message.caption,
            'sender_id': message.sender_chat.id,
            'first_name': message.sender_chat.title,
            'last_name': None,
            'username': None,
            'chat_id': message.chat.id,
            'chat_title': message.chat.title
        }
        except Exception as e:
            log.error(f'get_messages_for_save error: {e.args}')
            print(message)


async def get_last_messages(client:Client, chat_id: int, limit: int = 50):
    messages_data = []
    try:
        messages = client.get_chat_history(chat_id, limit=limit)
    except Exception as e:
        log.error(f'get_last_messages error: {e.args}')
        print(messages)
    async for message in messages:
        if message:
            messages_data.append(get_messages_for_save(message))
    return messages_data


class Forum():

    def __init__(self, client: Client, chat: Chat):
        self.client = client
        self.chat = chat

    async def get_forum_topics(self) -> list[ForumTopic]:
        peer = await self.client.resolve_peer(peer_id=self.chat.id)
        res = await self.client.invoke(GetForumTopics(channel=peer,
                                                      offset_date=0,
                                                      offset_id=0,
                                                      offset_topic=0,
                                                      limit=100))
        return res.topics

    async def get_topics_messages(self) -> list:
        return None
