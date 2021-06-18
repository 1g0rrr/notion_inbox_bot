# TODO хороший код, но уже не нужен. 

# from typing import Optional
# from telegram.chat import Chat
# from telegram.user import User
# from telegram import Update

# class GetTimezoneUpdate(Update):

#     def __init__(self, update):
#             super().__init__(
#                 update.update_id, 
#                 )
#             self._effective_user: Optional['User'] = update.effective_user
#             self._effective_chat: Optional['Chat'] = update.effective_chat

#     @property
#     def effective_user(self) -> User:
#         if self._effective_user:
#             return self._effective_user

#     @property
#     def effective_chat(self) -> Chat:
#         if self._effective_chat:
#             return self._effective_chat