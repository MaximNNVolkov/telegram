import logger
from pyrogram.types import Message, MessageEntity
from pyrogram.enums import MessageEntityType


log = logger.get_logger(__name__)


class MarkdownParse:
    """Parse markdown from message.
    Returns markdown string, hashtags, links from message."""

    def __init__(self, message: Message):
        self.message = message
        self.text = message.text or message.caption
        self.entities = message.entities or None
        self.markdown = None
        self.hashtags = []
        self.links = []

    def parse_hashtags_and_links(self):
        if self.entities:
            for entity in self.entities:
                if entity.type == MessageEntityType.HASHTAG:
                    self.hashtags.append({'text':self.get_entities_text(entity),
                                          'offset':entity.offset, 'length':entity.length})
                elif entity.type == MessageEntityType.TEXT_LINK:
                    self.links.append({'text':self.get_entities_text(entity), 'url':entity.url,
                                       'offset':entity.offset, 'length':entity.length})

    def parse_markdown(self):
        if not self.entities:
            self.markdown = self.text
            return

        # Сортируем сущности: сначала по убыванию начала, затем по возрастанию длины
        sorted_entities = sorted(
            self.entities,
            key=lambda e: (-e.offset, e.offset + e.length)
        )

        text = list(self.text)
        edits = []

        for idx, entity in enumerate(sorted_entities):
            start = entity.offset
            end = entity.offset + entity.length
            md = None

            if entity.type == MessageEntityType.TEXT_LINK:
                # Обработка ссылок как в исходном коде
                text_segment = self.text[start:end]
                md = f'[{text_segment}]({entity.url})'
                # Замена текста на ссылку
                edits.append((start, end, md))
            else:
                # Определяем теги для других типов
                if entity.type == MessageEntityType.BOLD:
                    open_md, close_md = '**', '**'
                elif entity.type == MessageEntityType.ITALIC:
                    open_md, close_md = '_', '_'
                elif entity.type == MessageEntityType.UNDERLINE:
                    open_md, close_md = '__', '__'
                elif entity.type == MessageEntityType.BLOCKQUOTE:
                    # Для цитат обрабатываем каждую строку
                    lines = self.text[start:end].split('\n')
                    quoted = '\n'.join(f'> {line}' for line in lines)
                    edits.append((start, end, quoted))
                    continue
                else:
                    continue  # Неподдерживаемый тип

                # Добавляем теги как вставки
                edits.append((end, end, close_md))
                edits.append((start, start, open_md))

        # Сортируем правки: сначала более поздние позиции
        edits.sort(reverse=True, key=lambda x: (x[0], -x[1]))

        # Применяем все изменения к тексту
        for start, end, replacement in edits:
            text[start:end] = list(replacement)

        self.markdown = ''.join(text)

    def get_entities_text(self, entity: MessageEntity):
        """Return text of entity"""
        return self.text[entity.offset:entity.offset + entity.length]
