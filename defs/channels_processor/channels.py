from pyrogram import Client
from pyrogram.types import Message
import json
from typing import Optional

from defs.methods.message_sender import MessageSender
from defs.methods.save_sent_message import SaveSentMessageHandler

from defs.deepseek_api import get_response
from database.db_start import Channels, SentMessages
import logger


log = logger.get_logger(__name__)


class ChannelsProcessor:

    def __init__(self, channel_id: int):
        self.channel_id = channel_id

    async def message_processor(self, client: Client, message: Message):
        """
        :param client - pyrogram client
        :param message - pyrogram message
        :return: None
        """
        message_text = message.text if message.text else message.caption
        log.info(
            f'ChannelsProcessor.message_processor start: '
            f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
            f'target_channel_id={self.channel_id}, message_text_present={bool(message_text)}'
        )

        if not message_text:
            log.info(
                f'ChannelsProcessor.message_processor stop: '
                f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
                f'target_channel_id={self.channel_id}, reason=no message text'
            )
            return None

        duplicate_checker = DuplicateMessageChecker(
            target_channel_id=self.channel_id,
            message_text=message_text
        )
        duplicate_messages = duplicate_checker.find_duplicate_sent_messages()
        log.info(
            f'ChannelsProcessor.message_processor duplicate check: '
            f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
            f'target_channel_id={self.channel_id}, duplicate_messages={duplicate_messages}'
        )
        if duplicate_messages is None:
            log.info(
                f'ChannelsProcessor.message_processor stop: '
                f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
                f'target_channel_id={self.channel_id}, '
                f'reason=deepseek duplicate check failed or returned unparseable data'
            )
            return None
        if duplicate_messages:
            log.info(
                f'ChannelsProcessor.message_processor stop: '
                f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
                f'target_channel_id={self.channel_id}, '
                f'reason=duplicate messages found, duplicates={duplicate_messages}'
            )
            return None

        keywords = Channels.get_channel_keywords(channel_id=self.channel_id)
        log.info(
            f'ChannelsProcessor.message_processor keywords loaded: '
            f'target_channel_id={self.channel_id}, keywords={keywords}'
        )
        keyword_match = MatchKeyWords(
            keywords=keywords,
            message=message_text
        ).response_match()
        log.info(
            f'ChannelsProcessor.message_processor keyword check: '
            f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
            f'target_channel_id={self.channel_id}, keyword_match={keyword_match}'
        )
        if keyword_match != 'Да':
            log.info(
                f'ChannelsProcessor.message_processor stop: '
                f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
                f'target_channel_id={self.channel_id}, '
                f'reason=keyword check did not pass'
            )
            return None

        sent_message = await MessageSender().send_message(
            client=client,
            chat_id=self.channel_id,
            message=message
        )
        log.info(
            f'ChannelsProcessor.message_processor send_message result: '
            f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
            f'target_channel_id={self.channel_id}, sent_message_id={sent_message.id if sent_message else None}'
        )
        if not sent_message:
            log.info(
                f'ChannelsProcessor.message_processor stop: '
                f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
                f'target_channel_id={self.channel_id}, reason=send_message returned None'
            )
            return None

        topic = ''
        save_result = SaveSentMessageHandler.save_sent_message(sent_message, topic=topic)
        log.info(
            f'ChannelsProcessor.message_processor save_sent_message result: '
            f'source_chat_id={message.chat.id}, source_message_id={message.id}, '
            f'target_channel_id={self.channel_id}, save_result={save_result}'
        )
        return sent_message


class DuplicateMessageChecker:
    BATCH_SIZE = 50

    def __init__(self, target_channel_id: int, message_text: str):
        self.target_channel_id = target_channel_id
        self.message_text = message_text

    @staticmethod
    def _extract_content(raw_response) -> str:
        if raw_response is None:
            return ''
        content = str(raw_response).strip()
        if content.startswith("```") and content.endswith("```"):
            lines = content.splitlines()
            if len(lines) >= 3:
                content = '\n'.join(lines[1:-1]).strip()
        return content

    @classmethod
    def _normalize_duplicate_response(cls, raw_response) -> Optional[list]:
        content = cls._extract_content(raw_response)
        if not content:
            return []
        if content.lower() == 'null':
            return []

        decoder = json.JSONDecoder()
        try:
            parsed, end_index = decoder.raw_decode(content)
        except json.JSONDecodeError:
            log.warning(
                f'DuplicateMessageChecker._normalize_duplicate_response failed to parse JSON: '
                f'raw_response={raw_response}'
            )
            return None

        trailing_content = content[end_index:].strip()
        if trailing_content:
            log.warning(
                'DuplicateMessageChecker._normalize_duplicate_response ignored trailing '
                f'non-JSON content: trailing_content={trailing_content}'
            )

        if parsed is None:
            return []
        if isinstance(parsed, list):
            return parsed

        log.warning(
            f'DuplicateMessageChecker._normalize_duplicate_response unexpected payload type: '
            f'parsed={parsed}'
        )
        return None

    def find_duplicate_sent_messages(self) -> Optional[list]:
        history_messages = SentMessages.get_sent_messages_by_user(
            user_id=str(self.target_channel_id), limit=50
        )
        log.info(
            f'DuplicateMessageChecker.find_duplicate_sent_messages history: '
            f'target_channel_id={self.target_channel_id}, history_count={len(history_messages)}'
        )
        if not history_messages:
            log.info(
                f'DuplicateMessageChecker.find_duplicate_sent_messages -> [] '
                f'(no sent history for target_channel_id={self.target_channel_id})'
            )
            return []

        sys_prompt = """сравни семантическое содержание текущего сообщения с историей ранее отправленных сообщений.
Если в истории есть сообщения, схожие с текущим по смыслу, верни JSON-массив с message_id этих сообщений.
Если похожих сообщений нет, верни только пустой JSON-массив [].
Ответ должен содержать только JSON-массив.
История сообщений будет передана в формате: channel_id|message_id|message_text.
"""
        sys_message = (
            f"{sys_prompt}\n\n"
            f"Текущее сообщение для анализа:\n{self.message_text}"
        )

        for batch_start in range(0, len(history_messages), self.BATCH_SIZE):
            batch = history_messages[batch_start:batch_start + self.BATCH_SIZE]
            history_payload = "\n".join(
                [
                    '|'.join(
                        [
                            str(message.channel_id),
                            str(message.sent_message_id),
                            str(message.message_text),
                        ]
                    )
                    for message in batch
                ]
            )
            batch_number = batch_start // self.BATCH_SIZE + 1
            log.info(
                f'DuplicateMessageChecker.find_duplicate_sent_messages batch request: '
                f'target_channel_id={self.target_channel_id}, batch_number={batch_number}, '
                f'batch_size={len(batch)}'
            )

            try:
                api_response = get_response(
                    sys_message=sys_message,
                    user_message=history_payload
                )
                raw_result = api_response.choices[0].message.content
                normalized_result = self._normalize_duplicate_response(raw_result)
                log.info(
                    f'DuplicateMessageChecker.find_duplicate_sent_messages batch result: '
                    f'target_channel_id={self.target_channel_id}, batch_number={batch_number}, '
                    f'raw_result={raw_result}, normalized_result={normalized_result}'
                )
                if normalized_result is None:
                    return None
                if normalized_result:
                    return normalized_result
            except Exception as e:
                log.error(
                    f'DuplicateMessageChecker.find_duplicate_sent_messages error: '
                    f'target_channel_id={self.target_channel_id}, batch_number={batch_number}, '
                    f'{type(e).__name__}: {e}'
                )
                return None

        log.info(
            f'DuplicateMessageChecker.find_duplicate_sent_messages final result: '
            f'target_channel_id={self.target_channel_id}, normalized_result=[]'
        )
        return []



class MatchKeyWords:

    def __init__(self, keywords: str, message: str):
        self.keywords = keywords
        self.message = message
        self.prompt = f"""проверь что в сообщении есть ключевые слова. Слова могут быть в разной форме, например в другом падеже.
Если хотя бы одно слово встречается в сообщении ответь "Да", если таких слов нет то ответь "Нет". ОТвет должен содержать только одно слово Да или Нет.

список ключевых слов:
{keywords}

сообщение:
{message}
"""

    def response_match(self) -> str:
        if not self.keywords:
            log.info("MatchKeyWords.response_match -> Да (no keywords filter — all messages pass)")
            return "Да"
        try:
            api_response = get_response(
                user_message=self.prompt
            )
            result = (api_response.choices[0].message.content or '').strip()
            log.info(
                f'MatchKeyWords.response_match(keywords={self.keywords}) -> {result}'
            )
            return result
        except Exception as e:
            log.error(f"Error in MatchKeyWords.response_match(): {type(e).__name__}: {e}")
            return "Нет"
