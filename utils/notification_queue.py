from redis import Redis
from rq import Queue
from models.notification import Notification
from .send_notification import send_notification_on_background
from lark.token_manager import TokenManager

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
        