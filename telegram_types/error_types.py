from pyrogram.enums.chat_type import ChatType


class UnsupportedChatType(Exception):
    def __init__(self, chat_type:ChatType, error_message:str = ''):
        self.chat_type = chat_type
        self.error_message = error_message

    def __str__(self):
        return f'Unsupported chat type: {self.chat_type}. '\
               f'Supported types: {ChatType.GROUP}, {ChatType.GROUP}. '\
               f'{self.error_message}'