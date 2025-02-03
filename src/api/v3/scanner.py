import os
from fastapi import (
    APIRouter,
    Depends,
    Form,
    UploadFile,
    File,
    status,
    HTTPException,
    BackgroundTasks
)
from src.core.dependencies import get_account_status, get_db, LarkNotificationDepends
from src.core.account_status import AccountStatus
from pydantic import BaseModel
from typing import Literal, List
from src.core.dtos import Account, Detection
from src.utils.file_utils import store_file
from lark.token_manager import TokenManager
from src.utils.plate_helper import normalize_plate
from src.utils.rate_limiter import RateLimiter
from src.db.logger import persist_log_entry
from src.db.user import find_lark_account
from sqlalchemy.orm import Session
from src.core.dependencies import settings


router = APIRouter(
    prefix='/api/v3',
    tags=['Scanner 3.0']
)

token_manager = TokenManager(
    app_id=os.getenv('CHOPPER_APP_ID', ""),
    app_secret=os.getenv('CHOPPER_APP_SECRET', "")
)

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


@router.post('/plate/check', response_model=LicensePlateCheckResponse)
async def plate_check(
    form: CheckPlateRequest,
    account_status: AccountStatus = Depends(get_account_status),
    session: Session = Depends(get_db),
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
        response = LicensePlateCheckResponse(
            plate=plate_number,
            status='POSITIVE',
            accounts=[account],
            latitude=form.latitude,
            longitude=form.longitude
        )
    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate_number):
        response = LicensePlateCheckResponse(
            plate=plate_number,
            status='FOR_CONFIRMATION',
            accounts=similar_accounts,
            latitude=form.latitude,
            longitude=form.longitude
        )
    else:
        response = LicensePlateCheckResponse(
            plate=plate_number,
            status='NOT_FOUND',
            accounts=[],
            latitude=form.latitude,
            longitude=form.longitude
        )

    return response


@router.post('/notify/group-chat')
async def notify_group_chat(
    background_tasks: BackgroundTasks,
    lark_notification: LarkNotificationDepends,
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
        detection = Detection(
            plate_number=plate,
            file_path=file_path,
            accounts=[account],
            status='POSITIVE',
            union_id=union_id,
            user_id=lark_account.user_id,
            latitude=latitude,
            longitude=longitude,
            detected_by=lark_account.name
        )
        background_tasks.add_task(
            lark_notification.notify,
            data=detection,
            group_chat_id=settings.MAIN_GC_ID
        )
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
        detection = Detection(
            plate_number=plate,
            file_path=file_path,
            status='FOR_CONFIRMATION',
            accounts=similar_accounts,
            union_id=union_id,
            user_id=lark_account.user_id,
            latitude=latitude,
            longitude=longitude,
            detected_by=lark_account.name
        )
        background_tasks.add_task(
            lark_notification.notify,
            data=detection,
            group_chat_id=settings.MAIN_GC_ID
        )
        return ScannerResponse.model_validate({
            "message": "queued notification sent", 
            "type": "for_confirmation"
        })
