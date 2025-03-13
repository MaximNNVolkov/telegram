import logger as loger
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy import create_engine, ForeignKey, func, desc
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, aliased
from datetime import datetime


log = loger.get_logger(__name__)


url_object = URL.create(
    "sqlite",
    username="",
    password="",
    host="",
    database="telegram.db",
)


engine = create_engine(url_object)
DeclarativeBase = declarative_base()


class Users(DeclarativeBase):
    __tablename__ = 'users'

    date = Column(DateTime(), default=datetime.now)
    user_id = Column('user_id', Integer, primary_key=True)
    first_name = Column('first_name', String)
    last_name = Column('last_name', String)
    user_name = Column('user_name', String)

    def __repr__(self):
        return f"<user_id={self.user_id}," \
               f"first_name={self.first_name}," \
               f"last_name={self.last_name}," \
               f"user_name={self.user_name}>"

    @property
    def serialize(self):
        return {
            'user_id': self.user_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'user_name': self.user_name
        }


class ChatDetails(DeclarativeBase):
    __tablename__ = 'chatdetails'

    date = Column(DateTime(), default=datetime.now)
    id = Column(String, primary_key=True)
    type = Column(String)
    title = Column(String)
    username = Column(String, nullable=True)
    invite_link = Column(String, nullable=True)
    members_count = Column(String)
    chat_category = Column(Text, nullable=True)
    chat_term = Column(Text, nullable=True)

    @classmethod
    def get_chat_category_by_id(cls, chat_id: str) -> str:
        """
        Получает категорию чата (chat_category) по его ID.

        :param chat_id: ID чата
        :return: Категория чата (chat_category) или None, если чат не найден
        """
        chat = db_conn().query(cls).filter(cls.id == chat_id).first()
        if chat:
            return chat.chat_category
        return None


class Messages(DeclarativeBase):
    __tablename__ = 'messages'

    date = Column(DateTime(), default=datetime.now)
    chat_id = Column(String, ForeignKey('chatdetails.id'), primary_key=True)
    message_id = Column(Integer, primary_key=True)
    message_type = Column(String)
    message_text = Column(Text)
    message_topic = Column(String)
    message_date = Column(DateTime())

    @classmethod
    def add_message(cls, message) -> str:
        log.info(
                f'Запрос на добавление нового сообщения с '
                f'{message.chat_id}, {message.message_id}, {message.message_type}, {message.message_text},'
                f'{message.message_topic}, {message.message_date}')

        conn = db_conn()
        existing_message = conn.query(cls).filter(cls.message_id == message.message_id).first()
        if existing_message is None:
            m = message
            conn.add(m)
            conn.commit()
            log.info(f'Сообщение с id {message.message_id} из чата {message.chat_id} успешно добавлено.')
            return 'success'
        else:
            log.info(f'Сообщение с id {message.message_id} уже существует.')
            return 'no_new_message'

    @classmethod
    def get_latest_messages_by_category(cls, category: list = [], limit: int = 5):
        """
        Получает последние сообщения из чатов с указанной категорией.

        :param category: Категория чата (например, 'Новости и политика')
        :param limit: Количество сообщений (по умолчанию 50)
        :return: Список сообщений
        """
        session = db_conn()
        if len(category) > 0:
            subquery = (
                session.query(
                cls,
                func.row_number()
                .over(partition_by=cls.chat_id, order_by=desc(cls.message_date))
                .label("row_number")
            )
             .join(ChatDetails)
                .filter(ChatDetails.chat_category.in_(category))
                .subquery())

            # Алиас для подзапроса
            subquery_alias = aliased(cls, subquery)

            # Основной запрос: выбираем только первые N сообщений для каждой группы
            return (
                session.query(subquery_alias)
                .filter(subquery.c.row_number <= limit)
                .all()
            )
            # return (
            #     db_conn().query(cls)
            #     .join(ChatDetails)  # Присоединяем таблицу chatdetails
            #     .filter(ChatDetails.chat_category.in_(category))  # Фильтруем по категории
            #     .order_by(cls.message_date) # Сортируем по убыванию даты
            #     .limit(limit)  # Ограничиваем количество результатов
            #     .all()  # Возвращаем результат в виде списка
            # )
        else:
            return (
                session.query(cls)
                .order_by(cls.message_date) # Сортируем по убыванию даты
                .limit(limit)  # Ограничиваем количество результатов
                .all()  # Возвращаем результат в виде списка
            )


def db_conn():
    engine = create_engine(url_object)
    DeclarativeBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
