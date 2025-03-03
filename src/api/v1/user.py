from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from src.core.dependencies import get_token_manager, get_db
from src.lark.token_manager import TokenManager, UserInformationDataResponse
from src.db.user import find_lark_account, create_lark_account
from src.core.dtos import LarkAccountDTO


router = APIRouter(prefix='/api', tags=['User'])


class GetUserRequest(BaseModel):
    code: str


class GetUserResponse(BaseModel):
    message: str
    data: UserInformationDataResponse


@router.get('/user', response_model=GetUserResponse)
async def get_user(
    code: str,
    token_manager: TokenManager = Depends(get_token_manager),
    db: Session = Depends(get_db)
):
    try:
        user_access_token = (
            await token_manager.get_user_access_token(code)
        ).data.access_token

        user_information = (await token_manager.get_user_information(user_access_token)).data

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

        return {
            "message": "success", 
            "data": user_information
        }
    except Exception as err:
        print("err: ", err)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorize"
        )


    

