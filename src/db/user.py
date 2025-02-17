from sqlalchemy.orm import Session
from src.core.models import LarkAccount, User
from src.core.dtos import LarkAccountDTO


def find_lark_account(
    db: Session,
    union_id: str,
) -> LarkAccount | None:
    lark_account = (
        db.query(LarkAccount)
        .filter(LarkAccount.union_id == union_id)
        .first()
    )
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
    

def create_external_user(
    db: Session,
    username: str,
    hashed_password: str
) -> User:
    user = User(
        username=username,
        hashed_pwd=hashed_password
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def find_external_user(
    db: Session,
    username: str
) -> User:
    user = db.query(User) \
        .where(
            User.username == username
        ) \
        .first()
    return user


