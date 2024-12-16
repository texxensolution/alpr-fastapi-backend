from pydantic import BaseModel
from models.account import Account
from typing import List, Optional, Literal


class Notification(BaseModel):
    plate_number: str
    is_similar: bool
    file_path: Optional[str] = None
    accounts: List[Account]


class QueuedPlateDetected(BaseModel):
    plate_number: str
    status: Literal['POSITIVE', 'FOR_CONFIRMATION', 'NOT_FOUND']
    accounts: List[Account]
    file_path: str
    name: str


class QueuedPlateDetectedWithUnionId(QueuedPlateDetected):
    union_id: str
    user_id: Optional[str] = None