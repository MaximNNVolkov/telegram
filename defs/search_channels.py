import logger
from pyrogram import Client
from pyrogram.types import Message


log = logger.get_logger(__name__)


async def channel_search(client:Client, message: Message):
    try:
        query = message.text[8:]
    except IndexError:
        return await message.reply_text("Give a query to search.")

    results = await client.search_chats(query=query, limit=20)
    for r in results:
        await message.reply(text=', '.join([r.id, r.type, r.title]))
