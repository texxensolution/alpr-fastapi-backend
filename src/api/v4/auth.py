from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Literal
from sqlalchemy.orm import Session
from src.db.user import find_external_user, find_lark_account, create_lark_account
from src.core.dependencies import GetDatabaseSession, get_db, GetCurrentUserCredentials, GetLarkClient
from src.core.auth import verify_password, create_access_token, TokenUser
from src.core.dtos import LarkAccountDTO
from src.core.models import User, LarkAccount
from src.lark.token_manager import UserInformationDataResponse


class GetUserRequest(BaseModel):
    code: str


class GetUserResponse(BaseModel):
    message: str
    data: UserInformationDataResponse


router = APIRouter(
    prefix="/api/v4",
    tags=['Authentication v4.0']
)


class BaseAuthRequest(BaseModel):
    username: str 
    password: str 


class RegisterUserRequest(BaseAuthRequest):
    pass


class LoginRequest(BaseAuthRequest):
    pass


class BaseResponse(BaseModel):
    status: Literal['success', 'error']
    msg: str


class TokenData(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(BaseResponse):
    data: TokenData | None = None


class LarkTokenData(BaseModel):
    access_token: str
    token_type: str


class LarkTokenResponse(BaseResponse):
    data: LarkTokenData | None = None

    
class GetUserInformation(BaseModel):
    name: str


@router.post('/auth', response_model=TokenResponse)
async def login_user(
    request: LoginRequest,
    db: GetDatabaseSession
):
    if request.username == "" or request.password == "":
        return TokenResponse(
            status='error',
            msg='The credentials you provide is invalid.'
        )
        
    user = find_external_user(db=db, username=request.username)

    if not user:
        return TokenResponse(
            status='error',
            msg='The credentials you provide is invalid.'
        )

    if verify_password(
        request.password,
        user.hashed_password
    ):
        token_user = TokenUser(
            user_id=user.username,
            user_type='external'
        )
        token = await create_access_token(token_user)
        return TokenResponse(
            status='success',
            msg='Successfully create a bearer token.',
            data=TokenData(
                access_token=token,
                token_type="bearer"
            )
        )
    return TokenResponse(status='error', msg='The credentials you provide is invalid.')


@router.get('/lark/user', response_model=LarkTokenResponse)
async def get_lark_user(
    code: str,
    client: GetLarkClient,
    db: Session = Depends(get_db)
):
    try:
        user_access_token = (
            await client.token.get_user_access_token(code)
        ).data.access_token

        user_information = (
            await client.token.get_user_information(user_access_token)
        ).data

        lark_account = find_lark_account(
            union_id=user_information.union_id,
            db=db
        )

        if not lark_account:
            lark_account_dto = LarkAccountDTO(
                union_id=user_information.union_id,
                user_id=user_information.user_id,
                name=user_information.name
            )

            lark_account = create_lark_account(
                account_dto=lark_account_dto,
                db=db
            )
        
        token = await create_access_token(
            data=TokenUser(
                user_id=lark_account.union_id,
                user_type="internal"
            )
        )
        return LarkTokenResponse(
            status="success",
            msg="Successfully created a bearer token.",
            data=LarkTokenData(
                access_token=token,
                token_type="bearer"
            )
        )
    except Exception as err:
        print("error", err)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorize")


@router.get("/user", response_model=GetUserInformation)
async def get_user_information(credentials: GetCurrentUserCredentials):
    user, _ = credentials
    if isinstance(user, LarkAccount):
        return GetUserInformation(name=user.name)
    elif isinstance(user, User):
        return GetUserInformation(name=user.username)

        
    