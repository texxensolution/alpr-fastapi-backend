from pydantic import BaseModel
from models.account import Account
from typing import List, Optional


class Notification(BaseModel):
    plate_number: str
    is_similar: bool
    file_path: Optional[str] = None
    accounts: List[Account]