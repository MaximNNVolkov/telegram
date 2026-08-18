import logger as loger
import json
from pathlib import Path
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy import create_engine, ForeignKey, func, desc
from sqlalchemy.engine.url import URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, aliased
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta


log = loger.get_logger(__name__)
_project_root = Path(__file__).resolve().parents[1]
_db_path = _project_root / "telegram.db"


url_object = URL.create(
    "sqlite",
    username="",
    password="",
    host="",
    database=str(_db_path),
)


engine = create_engine(url_object)
DeclarativeBase = declarative_base()


class Users(DeclarativeBase):
    __tablename__ = 'users'

    date = Column(DateTime(), default=datetime.utcnow)
    user_id = Column('user_id', Integer, primary_key=True)
    first_name = Column('first_name', String)
    last_name = Column('last_name', String)
    user_name = Column('user_name', String)

    # Метод для добавления нового пользователя с проверкой на существование
    @classmethod
    def add_user(cls, session, user_id, first_name, last_name, user_name):
        try:
            # Проверяем, существует ли пользователь с таким user_id
            existing_user = cls.get_user_by_id(session, user_id)
            if existing_user:
                print(f"User with id {user_id} already exists.")
                return existing_user

            # Если пользователь не существует, создаем нового
            new_user = cls(
                user_id=user_id,
                first_name=first_name,
                last_name=last_name,
                user_name=user_name
            )
            session.add(new_user)
            session.commit()
            print(f"User {user_name} added successfully.")
            return new_user

        except IntegrityError as e:
            # Обработка нарушения уникальности ключей
            session.rollback()  # Откатываем транзакцию
            print(f"IntegrityError: User with id {user_id} already exists or other constraint violation.")
            return None

        except SQLAlchemyError as e:
            # Общая обработка ошибок SQLAlchemy
            session.rollback()  # Откатываем транзакцию
            print(f"SQLAlchemyError: {e}")
            return None

    # Метод для получения информации о пользователе по его user_id
    @classmethod
    def get_user_by_id(cls, session, user_id):
        try:
            return session.query(cls).filter(cls.user_id == user_id).first()
        except SQLAlchemyError as e:
            # Обработка ошибок при запросе к базе данных
            print(f"SQLAlchemyError: {e}")
            return None


class ChatDetails(DeclarativeBase):
    __tablename__ = 'chatdetails'

    date = Column(DateTime(), default=datetime.utcnow)
    id = Column(String, primary_key=True)
    type = Column(String)
    title = Column(String)
    username = Column(String, nullable=True)
    invite_link = Column(String, nullable=True)
    members_count = Column(String)
    chat_category = Column(Text, nullable=True)
    chat_term = Column(Text, nullable=True)

    @classmethod
    def get_chat_category_by_id(cls, chat_id: str) -> str or None:
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

    date = Column(DateTime(), default=datetime.utcnow)
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
                f'{message.chat_id}, {message.message_id}, {message.message_type},'
                f'{message.message_topic}, {message.message_date}')

        conn = db_conn()
        existing_message = conn.query(cls).filter((cls.message_id == message.message_id) &
                                                  (cls.chat_id == message.chat_id)).first()
        if existing_message is None:
            m = message
            conn.add(m)
            conn.commit()
            log.info(f'Сообщение с id {message.message_id} из чата {message.chat_id} успешно добавлено.')
            return 'success'
        else:
            log.info(f'Сообщение с id {message.message_id} из чата {message.chat_id} уже существует.')
            return 'no_new_message'

    @classmethod
    def get_latest_messages_by_category(cls, category: list = None, limit: int = 5):
        """
        Получает последние сообщения из чатов с указанной категорией.

        :param category: Категория чата (например, 'Новости и политика')
        :param limit: Количество сообщений (по умолчанию 50)
        :return: Список сообщений
        """
        session = db_conn()
        if not category:
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
        else:
            return (
                session.query(cls)
                .order_by(cls.message_date) # Сортируем по убыванию даты
                .limit(limit)  # Ограничиваем количество результатов
                .all()  # Возвращаем результат в виде списка
            )


class SentMessages(DeclarativeBase):
    __tablename__ = 'sent_messages'

    date = Column(DateTime(), default=datetime.utcnow)
    channel_id = Column(String, ForeignKey('chatdetails.id'), primary_key=True)  # Идентификатор канала в который
    sent_message_id = Column(Integer, primary_key=True)  # Идентификатор отправленного сообщения
    message_type = Column(String)
    message_text = Column(Text)
    message_topic = Column(String)
    message_date = Column(DateTime())

    @classmethod
    def add_sent_message(cls, sent_message) -> str:
        log.info(
            f'Запрос на добавление нового отправленного сообщения для пользователя '
            f'{sent_message.channel_id}, {sent_message.sent_message_id}, {sent_message.message_type}, '
            f'{sent_message.message_topic}, {sent_message.message_date}')

        conn = db_conn()
        existing_message = conn.query(cls).filter(cls.sent_message_id == sent_message.sent_message_id).first()
        if existing_message is None:
            m = sent_message
            conn.add(m)
            conn.commit()
            log.info(f'Сообщение с id {sent_message.sent_message_id} для пользователя {sent_message.channel_id} успешно добавлено.')
            return 'success'
        else:
            log.info(f'Сообщение с id {sent_message.sent_message_id} уже существует.')
            return 'no_new_message'

    @classmethod
    def get_latest_sent_messages_by_user(cls, user_id: str, limit: int = 30):
        """
        Получает последние сообщения, отправленные конкретному пользователю.

        :param user_id: Идентификатор пользователя
        :param limit: Количество сообщений (по умолчанию 30)
        :return: Список сообщений
        """
        two_hours_ago = datetime.utcnow() - timedelta(hours=2)

        with db_conn() as session:
            messages = (
                session.query(cls)
                .filter(cls.channel_id == user_id)
                .filter(cls.message_date >= two_hours_ago)  # Фильтр по времени (UTC)
                .order_by(desc(cls.message_date))
                .limit(limit)  # Ограничение на количество сообщений
                .all()
            )
            log.info(
                f'SentMessages.get_latest_sent_messages_by_user(user_id={user_id}, limit={limit}) -> '
                f'count={len(messages)}, ids={[message.sent_message_id for message in messages[:10]]}'
            )
            return messages

    @classmethod
    def get_sent_messages_by_user(cls, user_id: str, limit: int = None):
        """
        Получает отправленные сообщения конкретного канала без ограничения по времени.

        :param user_id: Идентификатор канала
        :param limit: Необязательное ограничение количества сообщений
        :return: Список сообщений
        """
        with db_conn() as session:
            query = (
                session.query(cls)
                .filter(cls.channel_id == user_id)
                .order_by(desc(cls.message_date))
            )
            if limit is not None:
                query = query.limit(limit)
            messages = query.all()
            log.info(
                f'SentMessages.get_sent_messages_by_user(user_id={user_id}, limit={limit}) -> '
                f'count={len(messages)}, ids={[message.sent_message_id for message in messages[:10]]}'
            )
            return messages


class Channels(DeclarativeBase):
    """
    Модель для хранения информации о подписках пользователей на телеграм-каналы с ключевыми словами.
    Каждая запись содержит информацию о пользователе, ключевых словах и источниках (ID телеграм-каналов).
    """

    __tablename__ = 'channels'

    date = Column(DateTime(), default=datetime.utcnow)
    id = Column(Integer, primary_key=True)
    keywords = Column(JSON)  # Список ключевых слов
    sources = Column(JSON)  # Список источников (ID телеграм-каналов)

    @staticmethod
    def _normalize_json_field(value):
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value


    # Метод для добавления нового канала
    @classmethod
    def add_channel(cls, new_channel):
        """
        Добавляет новый канал в базу данных для указанного пользователя.
        :param new_channel: Объект нового канала.
        :return: Созданный объект канала или None в случае ошибки.
        """
        with db_conn() as conn:
            try:
            # Проверяем, существует ли пользователь

                existing_message = conn.query(cls).filter(cls.id == new_channel.id).first()

                # Создаем новый канал
                conn.add(new_channel)
                conn.commit()
                log.info(f"Channel {new_channel.id} added successfully.")
                return new_channel

            except IntegrityError as e:
                # Обработка ошибок уникальности
                conn.rollback()
                log.info(f"IntegrityError: {e}")
                return None

            except SQLAlchemyError as e:
                # Общая обработка ошибок SQLAlchemy
                conn.rollback()
                log.info(f"SQLAlchemyError: {e}")
                return None

    # Метод для получения каналов пользователя
    @classmethod
    def get_channel_by_user_id(cls, channel_id):
        """
        Получает канал по его id.

        :param channel_id: Идентификатор канала.
        :return: Список каналов или None в случае ошибки.
        """

        try:
            with db_conn() as session:
                channel = session.query(cls).filter(cls.id == channel_id).first()
                if channel:
                    channel.keywords = cls._normalize_json_field(channel.keywords)
                    channel.sources = cls._normalize_json_field(channel.sources)
                log.info(
                    f'Channels.get_channel_by_user_id(channel_id={channel_id}) -> '
                    f'{channel.id if channel else None}'
                )
                return channel
        except SQLAlchemyError as e:
            # Обработка ошибок при запросе к базе данных
            log.info(f"SQLAlchemyError: {e}")
            return None

    @classmethod
    def get_channel_keywords(cls, channel_id: int):
        """
        Получает список ключевых слов для указанного канала.

        :param channel_id: Идентификатор канала.
        :return: Список ключевых слов или None в случае ошибки.
        """
        try:
            with db_conn() as session:
                channel = session.query(cls).filter(cls.id == channel_id).first()
                keywords = cls._normalize_json_field(channel.keywords) if channel else None
                log.info(f'Channels.get_channel_keywords(channel_id={channel_id}) -> {keywords}')
                return keywords
        except SQLAlchemyError as e:
            # Обработка ошибок при запросе к базе данных
            log.info(f"SQLAlchemyError: {e}")

    @classmethod
    def get_channels_by_source(cls, source_chat_id: int):
        """
        Возвращает каналы, в которых source_chat_id присутствует в поле sources.

        :param source_chat_id: ID исходного чата/группы
        :return: Список каналов
        """
        try:
            with db_conn() as session:
                channels = session.query(cls).all()
                matched_channels = []
                for channel in channels:
                    normalized_sources = cls._normalize_json_field(channel.sources) or []
                    if source_chat_id in normalized_sources:
                        channel.sources = normalized_sources
                        channel.keywords = cls._normalize_json_field(channel.keywords)
                        matched_channels.append(channel)
                log.info(
                    f'Channels.get_channels_by_source(source_chat_id={source_chat_id}) -> '
                    f'{[channel.id for channel in matched_channels]}'
                )
                return matched_channels
        except SQLAlchemyError as e:
            log.info(f"SQLAlchemyError: {e}")
            return []


def db_conn():
    engine = create_engine(url_object)
    DeclarativeBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session
