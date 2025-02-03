import os
from dotenv import load_dotenv
from lark.token_manager import TokenManager
from src.lark.lark import Lark
from src.core.account_status import AccountStatus
from src.core.database import SessionLocal
from .websocket_manager import WebsocketManager
from src.core.config import Settings 
from src.core.lark_notification import LarkNotification
from typing import Annotated
from fastapi import Depends


settings = Settings()

print("loaded environment settings.", settings)

lark = Lark(
    settings.CHOPPER_APP_ID,
    settings.CHOPPER_APP_SECRET
)

websocket_manager = WebsocketManager()

lark_notification = LarkNotification(lark=lark)

def get_lark_notification() -> LarkNotification:
    return lark_notification

def get_lark_client() -> Lark:
    return lark

def get_websocket_manager() -> WebsocketManager:
    return websocket_manager

def get_account_status() -> AccountStatus:
    return AccountStatus(
        path=settings.ENDORSEMENT_FILE_PATH
    )

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
        

def get_token_manager():
    load_dotenv()
    app_id = os.getenv('CHOPPER_APP_ID')
    app_secret = os.getenv('CHOPPER_APP_SECRET')

    return TokenManager(
        app_id=app_id,
        app_secret=app_secret
    )


LarkNotificationDepends = Annotated[LarkNotification, Depends(get_lark_notification)]
