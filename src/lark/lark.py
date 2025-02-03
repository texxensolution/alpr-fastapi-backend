import logging
from .group_chat_manager import GroupChatManager
from .token_manager import TokenManager
from .base_manager import BaseManager
from .messenger import LarkMessenger
from .lark_drive import LarkDrive

logger = logging.getLogger(__name__)


class Lark:
    def __init__(self, app_id: str, app_secret: str):
        logger.info("Lark client initialization...")
        self.token = TokenManager(app_id=app_id, app_secret=app_secret)
        self.group_chat = GroupChatManager(token_manager=self.token)
        self.base = BaseManager(token_manager=self.token)
        self.messenger = LarkMessenger(token_manager=self.token)
        self.drive = LarkDrive(token_manager=self.token)

        logger.info("Lark client initialized!")
