from pyrogram.types import Message
from pyrogram import Client
from defs.read_group import get_group_info
from defs.gigachat_api import gigachat_dialog


async def function_replay(client:Client, message: Message):
    if message.text.startswith('Группа'):
        text_split = message.text.split(' ')
        if len(text_split) == 2:
            await get_group_info(client, text_split[1], message)
        else:
            await get_group_info(client, text_split[1], message, int(text_split[2]))
    elif message.from_user.username == 'MaximVolkov' or message.from_user.username == 'kalentev':
        await message.reply(gigachat_dialog(message.text))
    else:
        await message.reply(text='Не понятно к чему ты написал: '+message.text, quote=False)
        print(await client.get_users(message.chat.id))
