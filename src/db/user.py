from sqlalchemy.orm import Session
from src.core.models import LarkAccount
from src.core.dtos import LarkAccountDTO


def find_lark_account(
    union_id: str,
    db: Session
) -> LarkAccount | None:
    lark_account = db.query(LarkAccount).filter(
        LarkAccount.union_id == union_id
    ).first()

    if not lark_account:
        return None 
    
    return lark_account


def create_lark_account(
    account_dto: LarkAccountDTO,
    db: Session   
) -> LarkAccount:
    account = LarkAccount(
        union_id=account_dto.union_id,
        user_id=account_dto.user_id,
        name=account_dto.name,
        current_device=account_dto.current_device
    )

    db.add(account)
    db.commit()
    db.refresh(account)

    return account
    
