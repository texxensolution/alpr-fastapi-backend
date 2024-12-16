import os
from fastapi import Depends
from functools import lru_cache
from dotenv import load_dotenv
from lark.token_manager import TokenManager
from utils.account_status import AccountStatus
from utils.get_app_configuration import get_app_configuration
from models.config.app_configuration import AppConfiguration
from database.database import SessionLocal


app_config = get_app_configuration()


def get_account_status() -> AccountStatus:
    return AccountStatus(
        path=app_config.datasource.path
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