import logger as loger
from .db_start import db_conn, Users, ChatDetails, Messages
import time


log = loger.get_logger(__name__)
date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
date = time.strftime('%Y-%m-%d', time.localtime())


def add_user(user):
    log.info(
        f'Запрос на добавление нового пользователя с '
        f'{user.id}, {user.first_name}, {user.last_name}, {user.username}.')

    conn = db_conn()
    existing_user = conn.query(Users).filter(Users.user_id == user.id).first()

    if existing_user is None:
        u = Users(user_id=user.id,
                  first_name=user.first_name,
                  last_name=user.last_name,
                  user_name=user.username)
        conn.add(u)
        conn.commit()
    else:
        log.info(f'Пользователь с id {user.id} уже существует.')


def get_user(user):
    log.info(f'Запрос на поиск пользователя {user.id}.')
    conn = db_conn()
    s = conn.query(Users).filter(Users.user_id == user.id).first()
    if s is not None:
        res = s
    else:
        res = 'no_user'
    return res


def add_chat_details(chat_details):
    log.info(
        f'Запрос на добавление новых деталей чата с '
        f'{chat_details.id}, {chat_details.type}, {chat_details.title}, {chat_details.invite_link},'
        f'{chat_details.username}, {chat_details.members_count}, {chat_details.chat_category},'
        f'{chat_details.chat_term}')

    conn = db_conn()
    existing_chat_details = conn.query(ChatDetails).filter(ChatDetails.id == chat_details.id).first()

    if existing_chat_details is None:
        cd = ChatDetails(id=chat_details.id,
                         type=chat_details.type,
                         title=chat_details.title,
                         invite_link=chat_details.invite_link,
                         username=chat_details.username,
                         members_count=chat_details.members_count,
                         chat_category=chat_details.chat_category,
                         chat_term=chat_details.chat_term)
        conn.add(cd)
        conn.commit()
    else:
        log.info(f'Детали чата с id {chat_details.id} уже существуют.')


def get_message(message_id, chat_id):
    log.info(f'Запрос на поиск сообщения {message_id}.')
    conn = db_conn()
    s = conn.query(Messages).filter(Messages.message_id == message_id).first()
    if s is not None:
        res = s
    else:
        res = 'no_message'
    return res


def get_chat_details(chat_id):
    log.info(f'Запрос на поиск деталей чата {chat_id}.')
    conn = db_conn()
    cd = conn.query(ChatDetails).filter(ChatDetails.id == chat_id).first()
    if cd is not None:
        res = cd
    else:
        res = 'no_chat_details'
    return res
