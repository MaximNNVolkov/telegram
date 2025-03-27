import logger
from telegram_types.base_type import MessageBlockType


log = logger.get_logger(__name__)


class Filters:

    def __init__(self, text: str):
        self.block_words = 'Реклама. '
        self.text = text
        self.advertisement = False


    def is_advertisement(self):
        if self.block_words in self.text:
            self.advertisement = True


    def apply_filters(self) -> MessageBlockType:
        self.is_advertisement()

        if self.advertisement:
            return MessageBlockType.ADVERTISEMENT

        return MessageBlockType.NORMAL
