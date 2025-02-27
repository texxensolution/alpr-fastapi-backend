import jwt
from dotenv import load_dotenv
from lark.token_manager import TokenManager
from src.core.status_manager import StatusManager
from src.core.logger import Logger
from src.lark.lark import Lark
from src.core.account_status import AccountStatus
from src.core.database import SessionLocal
from src.core.models import LarkAccount, User
from .websocket_manager import WebsocketManager
from src.core.config import settings
from src.core.lark_notification import LarkNotification
from sqlalchemy.orm import Session
from typing import Annotated, Tuple, Union
from fastapi import Depends, status, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from src.core.dtos import TokenUserType
from src.db.user import find_external_user, find_lark_account
from src.services.synchronize import LarkSynchronizer
from src.services.analytics import LarkUsersAnalytics


print("loaded environment settings.", settings)

lark = Lark(
    settings.CHOPPER_APP_ID,
    settings.CHOPPER_APP_SECRET
)

websocket_manager = WebsocketManager()

lark_notification = LarkNotification(lark=lark)

def get_base_manager() -> Lark:
    return lark

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

    return TokenManager(
        app_id=settings.CHOPPER_APP_ID,
        app_secret=settings.CHOPPER_APP_SECRET
    )

    
status_manager = StatusManager(
    db=next(get_db())
)


def get_status_manager() -> StatusManager:
    return status_manager

bearer_scheme = HTTPBearer()

def get_token_from_headers(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    return credentials.credentials

GetBearerTokenFromHeaders = Annotated[HTTPAuthorizationCredentials, Depends(get_token_from_headers)]
GetStatusManager = Annotated[StatusManager, Depends(get_status_manager)]
LarkNotificationDepends = Annotated[LarkNotification, Depends(get_lark_notification)]
GetDatabaseSession = Annotated[Session, Depends(get_db)]
GetLarkClient = Annotated[Lark, Depends(get_lark_client)]


def get_synchronizer(
    db: GetDatabaseSession,
    lark: GetLarkClient,
):
    return LarkSynchronizer(
        db=db,
        lark=lark,
        analytics=LarkUsersAnalytics(db)
    )


def get_logger(
    db: GetDatabaseSession,
    synchronizer: LarkSynchronizer = Depends(get_synchronizer)
) -> Logger:
    return Logger(db, synchronizer)

GetLoggerSession = Annotated[Logger, Depends(get_logger)]

async def get_current_user(
    db: GetDatabaseSession,
    token: GetBearerTokenFromHeaders
) -> Tuple[Union[LarkAccount | User | None], str]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate":"Bearer"}
    )
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_type: TokenUserType = payload.get('user_type')
        user_id = payload.get('user_id')
    except jwt.exceptions.InvalidTokenError:
        raise credentials_exception

    if user_type == 'internal':
        user = find_lark_account(
            union_id=user_id,
            db=db
        )
    elif user_type == 'external':
        user = find_external_user(
            db=db,
            username=user_id
        )

    return user, user_id
 
GetCurrentUserCredentials = Annotated[Tuple[Union[LarkAccount | User | None], str], Depends(get_current_user)]
