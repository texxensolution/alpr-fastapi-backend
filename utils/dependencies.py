from fastapi import Depends
from functools import lru_cache
from utils.account_status import AccountStatus
from utils.get_app_configuration import get_app_configuration
from models.config.app_configuration import AppConfiguration


@lru_cache()
def get_app_config() -> AppConfiguration:
    return get_app_configuration()


@lru_cache()
def get_account_status() -> AccountStatus:
    app_config = get_app_config()
    return AccountStatus(
        path=app_config.datasource.path
    )
    