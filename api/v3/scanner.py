import os
from fastapi import APIRouter, Depends, Form, UploadFile, File, status, HTTPException
from utils.dependencies import get_account_status, get_db
from utils.account_status import AccountStatus
from pydantic import BaseModel
from typing import Literal, List, Optional
from models.account import Account
from utils.file_utils import store_file
from lark.token_manager import TokenManager
from utils.notification_queue import NotificationQueue
from jobs.notify_group_chat_with_mention import QueuedPlateDetectedWithUnionId, notify_group_chat
from utils.plate_normalizer import normalize_plate
from utils.rate_limiter import RateLimiter
from internal.db.logger import persist_log_entry
from internal.db.user import find_lark_account
from sqlalchemy.orm import Session

router = APIRouter(
    prefix='/api/v3',
    tags=['Scanner 3.0']
)

token_manager = TokenManager(
    app_id=os.getenv('CHOPPER_APP_ID', ""),
    app_secret=os.getenv('CHOPPER_APP_SECRET', "")
)

notification_queue = NotificationQueue(token_manager=token_manager)
rate_limiter = RateLimiter()

class LicensePlateCheckResponse(BaseModel):
    plate: str
    status: Literal['POSITIVE', 'FOR_CONFIRMATION', 'NOT_FOUND']
    accounts: List[Account]
    latitude: float
    longitude: float


class CheckPlateRequest(BaseModel):
    plate: str
    union_id: str
    latitude: float
    longitude: float

class ScannerResponse(BaseModel):
    message: str
    type: str


# class LicensePlateCheckBatchRequest(BaseModel):
#     plates: List[str]
#     union_id: str
#     latitude: float
#     longitude: float


# class LicensePlateResult(BaseModel):
#     plate: str
#     status: Literal['POSITIVE', 'FOR_CONFIRMATION', 'NOT_FOUND'],
#     accounts: List[Account]


# class LicensePlateCheckBatchResponse(BaseModel):
#     results: List[LicensePlateResult]
#     latitude: float
#     longitude: float
#     # accounts: List[Account]


# @router.post('/batch/plate/check', response_model=LicensePlateCheckBatchResponse)
# async def batch_license_plate_check(
#     form: LicensePlateCheckBatchRequest,
#     account_status: AccountStatus = Depends(get_account_status),
#     session: Session = Depends(get_db)
# ):
    
#     pass

    

@router.post('/plate/check', response_model=LicensePlateCheckResponse)
async def plate_check(
    form: CheckPlateRequest,
    account_status: AccountStatus = Depends(get_account_status),
    session: Session = Depends(get_db)
):

    lark_account = find_lark_account(
        union_id=form.union_id,
        db=session
    )

    if not lark_account:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorize"
        )

    plate_number = normalize_plate(form.plate)

    persist_log_entry(
        scanned_text=plate_number,
        union_id=lark_account.union_id,
        latitude=form.latitude,
        longitude=form.longitude,
        event_type='PLATE_CHECKING',
        db=session
    )
   

    if account := account_status.get_account_info_by_plate(plate_number):
        return LicensePlateCheckResponse(
            plate=plate_number,
            status='POSITIVE',
            accounts=[account],
            latitude=form.latitude,
            longitude=form.longitude
        )
    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate_number):
        return LicensePlateCheckResponse(
            plate=plate_number,
            status='FOR_CONFIRMATION',
            accounts=similar_accounts,
            latitude=form.latitude,
            longitude=form.longitude
        )
    else:
        return LicensePlateCheckResponse(
            plate=plate_number,
            status='NOT_FOUND',
            accounts=[],
            latitude=form.latitude,
            longitude=form.longitude
        )


@router.post('/notify/group-chat')
async def notify_group_chat(
    plate: str = Form(...),
    image: UploadFile = File(...),
    union_id: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    account_status: AccountStatus = Depends(get_account_status),
    session: Session = Depends(get_db)
):
    lark_account = find_lark_account(
        union_id=union_id,
        db=session
    )

    if not lark_account:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorize"
        )
        
    plate = normalize_plate(plate)
    
    if not rate_limiter.can_proceed(plate):
        return ScannerResponse.model_validate({
            "message": "skipped notification", 
            "type": "skipped"
        })

    if account := account_status.get_account_info_by_plate(plate):
        file_path = store_file(image)
        persist_log_entry(
            scanned_text=plate,
            union_id=lark_account.union_id,
            latitude=latitude,
            longitude=longitude,
            event_type='POSITIVE_PLATE_NOTIFICATION',
            db=session
        )
        queued_task = QueuedPlateDetectedWithUnionId(
            plate_number=plate,
            file_path=file_path,
            accounts=[account],
            status='POSITIVE',
            union_id=union_id,
            user_id=lark_account.user_id,
            latitude=latitude,
            longitude=longitude
        )
        notification_queue.push_with_mention(queued_task=queued_task)

        return ScannerResponse.model_validate({
            "message": "queued notification sent", 
            "type": "positive"
        })

    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate):
        file_path = store_file(image)

        persist_log_entry(
            scanned_text=plate,
            union_id=lark_account.union_id,
            latitude=latitude,
            longitude=longitude,
            event_type='FOR_CONFIRMATION_NOTIFICATION',
            db=session
        )

        queued_task = QueuedPlateDetectedWithUnionId(
            plate_number=plate,
            file_path=file_path,
            status='FOR_CONFIRMATION',
            accounts=similar_accounts,
            union_id=union_id,
            user_id=lark_account.user_id,
            latitude=latitude,
            longitude=longitude
        )
        notification_queue.push_with_mention(queued_task=queued_task)
        
        return ScannerResponse.model_validate({
            "message": "queued notification sent", 
            "type": "for_confirmation"
        })
