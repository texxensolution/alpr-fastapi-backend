from redis import Redis
from rq import Queue
from models.notification import Notification
from .send_notification import send_notification_on_background
from lark.token_manager import TokenManager
from jobs.notify_group_chat import QueuedPlateDetected, notify_group_chat
from jobs.notify_group_chat_with_mention import QueuedPlateDetectedWithUnionId, notify_group_chat as notify_gc_with_mention


class NotificationQueue:
    def __init__(
        self, 
        token_manager: TokenManager
    ):
        self.q = Queue(connection=Redis())
        self._token_manager = token_manager

    def push(
        self,
        notification: Notification
    ):
        self.q.enqueue(
            send_notification_on_background,
            self._token_manager,
            notification
        )

    def push_v2(
        self,
        queued_task: QueuedPlateDetected
    ):
        self.q.enqueue(
            notify_group_chat,
            self._token_manager,
            queued_task
        )
        
    def push_with_mention(
        self,
        queued_task: QueuedPlateDetectedWithUnionId
    ):
        self.q.enqueue(
            notify_gc_with_mention,
            self._token_manager,
            queued_task
        )
        