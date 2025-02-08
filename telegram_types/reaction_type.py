from collections import namedtuple

ReactionType = namedtuple(typename="ReactionType",
                          field_names="count, reactions")

ReactionDetails = namedtuple(typename="ReactionDetails",
                             field_names="user_id, emoticon, date")

ChatDetails = namedtuple(typename="ChatDetails",
                         field_names="id, type, title, invite_link, username, members_count")
