from collections import namedtuple
from typing import NamedTuple

# ReactionType = namedtuple(typename="ReactionType",
#                           field_names="count, reactions")

ReactionDetails = namedtuple(typename="ReactionDetails",
                             field_names="user_id, emoticon, date")

ChatDetails = namedtuple(typename="ChatDetails",
                         field_names="id, type, title, invite_link, username, members_count")

Message = namedtuple(typename="Message",
                     field_names="chat_id, message_id, message_type, message_text, message_topic, message_date")


class ReactionType(NamedTuple):

    count: int
    reactions: list[ReactionDetails]

    @classmethod
    def create(
            cls,
            count: int,
            reactions: list[ReactionDetails],
    ) -> "ReactionType":

        return cls(
            cls._assert_int(count),
            cls._assert_str(reactions, "reactions"),
        )

    @classmethod
    def _assert_str(cls, v: list[ReactionDetails], paramname: str) -> list[ReactionDetails]:
        for reaction in v:
            if not isinstance(reaction, ReactionDetails):
                raise TypeError(f"{paramname} must be a list of ReactionDetails")
        return v

    @classmethod
    def _assert_int(cls, count: int) -> int:
        try:
            return int(count)
        except TypeError:
            raise TypeError("Count argument must be an integer")


class MessageBlockType:
    NORMAL = 0
    ADVERTISEMENT = 1
