from src.db.user import LarkAccount, find_lark_account
from sqlalchemy.orm import Session
from typing import Dict, List
from src.core.dtos import StatusManagerDTO


class StatusManager:
    def __init__(self, db: Session):
        self._active_users: Dict[str, LarkAccount] = {}
        self._db = db
    
    def add_user(
        self,
        union_id: str,
    ):
        account = find_lark_account(
            union_id=union_id,
            db=self._db
        )
        self._active_users[union_id] = account

    def remove_user(self, union_id: str):
        self._active_users.pop(union_id)

    def get_users_status(self) -> List[StatusManagerDTO]:
        return [StatusManagerDTO(name=account.name, union_id=account.union_id) for (account) in self._active_users.values()]
