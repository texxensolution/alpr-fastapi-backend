import os
from dotenv import load_dotenv
from redis import Redis
from rq import Queue
from src.core.dtos import Notification
from src.utils.send_notification import send_notification_on_background
from lark.token_manager import TokenManager
# from jobs.notify_group_chat import notify_group_chat
from src.core.dtos import QueuedPlateDetected
# from jobs.notify_group_chat_with_mention import QueuedPlateDetectedWithUnionId, notify_group_chat as notify_gc_with_mention


# class NotificationQueue:
#     def __init__(
#         self, 
#         token_manager: TokenManager
#     ):
#         load_dotenv()
#         redis_host = os.getenv('REDIS_HOST', 'localhost')
#         redis_port = os.getenv('REDIS_PORT', 6379)

#         self.q = Queue(connection=Redis(
#             host=redis_host,
#             port=redis_port

#         ))
#         self._token_manager = token_manager

#     def push(
#         self,
#         notification: Notification
#     ):
#         self.q.enqueue(
#             send_notification_on_background,
#             self._token_manager,
#             notification
#         )

#     def push_v2(
#         self,
#         queued_task: QueuedPlateDetected
#     ):
#         self.q.enqueue(
#             notify_group_chat,
#             self._token_manager,
#             queued_task
#         )
        
#     def push_with_mention(
#         self,
#         queued_task: QueuedPlateDetectedWithUnionId
#     ):
#         self.q.enqueue(
#             notify_gc_with_mention,
#             self._token_manager,
#             queued_task
#         )
        