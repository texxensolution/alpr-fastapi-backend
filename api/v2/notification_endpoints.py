import os
from fastapi import APIRouter, Depends, Form, File, UploadFile
from utils import rate_limiter
from utils.dependencies import get_account_status, get_db
from utils.account_status import AccountStatus
from pydantic import BaseModel
from typing import Literal, List, Optional
from models.account import Account
from utils.file_utils import store_file
from lark.token_manager import TokenManager
from utils.notification_queue import NotificationQueue
from jobs.notify_group_chat import QueuedPlateDetected
from utils.plate_normalizer import normalize_plate
from utils.rate_limiter import RateLimiter
from utils.loggers import log_entry
from sqlalchemy.orm import Session


token_manager = TokenManager(
    app_id=os.getenv('CHOPPER_APP_ID', ""),
    app_secret=os.getenv('CHOPPER_APP_SECRET', "")
)

router = APIRouter(
    prefix='/api/v2',
    tags=['Version 2.0']
)

notification_queue = NotificationQueue(token_manager=token_manager)
rate_limiter = RateLimiter()

class LicensePlateCheckResponse(BaseModel):
    plate: str
    status: Literal['POSITIVE', 'FOR_CONFIRMATION', 'NOT_FOUND']
    accounts: List[Account]


class CheckPlateRequest(BaseModel):
    plate: str
    name: Optional[str] = None


@router.post('/plate-check', response_model=LicensePlateCheckResponse)
async def license_plate_check(
    form: CheckPlateRequest,
    account_status: AccountStatus = Depends(get_account_status)
):
    plate_number = normalize_plate(form.plate)
    if account := account_status.get_account_info_by_plate(plate_number):
        return LicensePlateCheckResponse(
            plate=plate_number,
            status='POSITIVE',
            accounts=[account]
        )
    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate_number):
        return LicensePlateCheckResponse(
            plate=plate_number,
            status='FOR_CONFIRMATION',
            accounts=similar_accounts
        )
    else:
        return LicensePlateCheckResponse(
            plate=plate_number,
            status='NOT_FOUND',
            accounts=[]
        )


@router.post('/plate-check-v2', response_model=LicensePlateCheckResponse)
async def license_plate_check_v2(
    form: CheckPlateRequest,
    account_status: AccountStatus = Depends(get_account_status),
    session: Session = Depends(get_db)
):
    log_entry(
        session=session,
        name=form.name,
        event_type='PLATE_CHECKING'
    )

    plate_number = normalize_plate(form.plate)

    if account := account_status.get_account_info_by_plate(plate_number):
        return LicensePlateCheckResponse(
            plate=plate_number,
            status='POSITIVE',
            accounts=[account]
        )
    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate_number):
        return LicensePlateCheckResponse(
            plate=plate_number,
            status='FOR_CONFIRMATION',
            accounts=similar_accounts
        )
    else:
        return LicensePlateCheckResponse(
            plate=plate_number,
            status='NOT_FOUND',
            accounts=[]
        )


@router.post('/notify-gc')
async def notify_group_chat(
    plate: str = Form(...),
    image: UploadFile = File(...),
    name: str = Form(...),
    account_status: AccountStatus = Depends(get_account_status),
    session: Session = Depends(get_db)
):
    

    plate = normalize_plate(plate)
    
    if not rate_limiter.can_proceed(plate):
        return {"message": "skipped notification", "type": "skipped"}

    if account := account_status.get_account_info_by_plate(plate):
        log_entry(
            session=session,
            name=name,
            event_type='POSITIVE_PLATE_NOTIFICATION'
        )

        file_path = store_file(image)
        queued_task = QueuedPlateDetected(
            plate_number=plate,
            file_path=file_path,
            accounts=[account],
            status='POSITIVE',
            name=name
        )
        notification_queue.push_v2(queued_task=queued_task)
        return {"message": "queued notification sent", "type": "positive"}
    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate):
        log_entry(
            session=session,
            name=name,
            event_type='FOR_CONFIRMATION_NOTIFICATION'
        )

        file_path = store_file(image)
        queued_task = QueuedPlateDetected(
            plate_number=plate,
            file_path=file_path,
            status='FOR_CONFIRMATION',
            accounts=similar_accounts,
            name=name
        )
        notification_queue.push_v2(queued_task=queued_task)
        return {"message": "queued notification sent", "type": "for_confirmation"}
