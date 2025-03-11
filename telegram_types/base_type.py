from collections import namedtuple


ReactionType = namedtuple(typename="ReactionType",
                          field_names="count, reactions")

ReactionDetails = namedtuple(typename="ReactionDetails",
                             field_names="user_id, emoticon, date")

ChatDetails = namedtuple(typename="ChatDetails",
                         field_names="id, type, title, invite_link, username, members_count")

Message = namedtuple(typename="Message",
                     field_names="chat_id, message_id, message_type, message_text, message_topic, message_date")