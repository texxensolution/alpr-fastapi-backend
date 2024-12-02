from redis import Redis
from rq import Queue
from models.notification import Notification
from .send_notification import send_notification_on_background
from lark.token_manager import TokenManager
from jobs.notify_group_chat import QueuedPlateDetected, notify_group_chat


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
        