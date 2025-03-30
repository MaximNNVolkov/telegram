from pyrogram import Client
from pyrogram.types import Message
from pyrogram import enums, utils #todo - убрать

import logger


log = logger.get_logger(__name__)


from pyrogram import Client
from pyrogram.errors import ChannelInvalid, ChannelPrivate, ChatIdInvalid


class MessageLink:

    @staticmethod
    async def get_link(
            client: Client,
            id_channel: int,
            id_message: int
    ) -> str:
        """
        Возвращает ссылку на сообщение и username канала в формате @username.

        :param client: Экземпляр клиента Pyrogram
        :param id_channel: ID целевого канала/чата
        :param id_message: ID сообщения в канале
        :return: Кортеж (ссылка на сообщение, @username_канала)
        """
        log.info(f"Запрос на получение ссылки на сообщение {id_message} в канале {id_channel}")
        try:
            # Получаем информацию о канале
            chat = await client.get_chat(id_channel)

            # if not chat.username:
            #     raise ValueError("Канал не имеет username, ссылка недоступна")
            if chat.username:
                log.info(f"Канал {chat.username} имеет username")
                link = f"https://t.me/{chat.username}/{id_message}"
            else:
                log.info(f"Канал {chat.username} не имеет username")
                link = f"https://t.me/c/{str(abs(chat.id)).replace('-100', '')}/{id_message}"

            # Формируем ссылку и username
            channel_name = f"@{chat.username}"

            # Опционально: проверка существования сообщения
            await client.get_messages(chat.id, id_message)
            return f"[Сообщение]({link}), из канала {channel_name}"

        except (ChannelInvalid, ChannelPrivate, ChatIdInvalid):
            raise ValueError("Некорректный ID канала или нет доступа")
        except Exception as e:
            raise RuntimeError(f"Ошибка при получении данных: {e}")

