import jwt
from src.db.user import find_lark_account, find_external_user
from pydantic import BaseModel
from src.core.config import settings
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from datetime import timedelta, datetime, timezone
from src.core.dtos import TokenUserType


class TokenData(BaseModel):
    username: str | None = None
    union_id: str | None = None
    user_type: TokenUserType


class UserData(BaseModel):
    username: str
    user_type: TokenUserType


class TokenUser(BaseModel):
    user_id: str
    user_type: TokenUserType


password_ctx = CryptContext(schemes=['bcrypt'], deprecated="auto")


def verify_password(plain_pwd: str, hashed_pwd: str):
    return password_ctx.verify(plain_pwd, hashed_pwd)


def get_password_hash(pwd: str):
    return password_ctx.hash(pwd)


async def create_access_token(
    data: TokenUser,
    expires_in: int  = settings.ACCESS_TOKEN_EXPIRE_MINUTES
):
    to_encode = data.model_dump()
    expire = datetime.now(timezone.utc) + timedelta(minutes=expires_in)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )


def get_user_type(
    db: Session,
    user_id: str
):
    if find_external_user(db, user_id):
        return "external"
    elif find_lark_account(db, user_id):
        return "internal"
    else:
        return None
