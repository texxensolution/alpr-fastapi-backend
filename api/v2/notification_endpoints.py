import os
from fastapi import APIRouter, Depends, Form, File, UploadFile
from utils.dependencies import get_account_status
from utils.account_status import AccountStatus
from pydantic import BaseModel
from typing import Literal, List
from models.account import Account
from utils.file_utils import store_file
from lark.token_manager import TokenManager
from utils.notification_queue import NotificationQueue
from jobs.notify_group_chat import QueuedPlateDetected


token_manager = TokenManager(
    app_id=os.getenv('CHOPPER_APP_ID', ""),
    app_secret=os.getenv('CHOPPER_APP_SECRET', "")
)

router = APIRouter(
    prefix='/api/v2',
    tags=['Version 2.0']
)

notification_queue = NotificationQueue(token_manager=token_manager)

class LicensePlateCheckResponse(BaseModel):
    plate: str
    status: Literal['POSITIVE', 'FOR_CONFIRMATION', 'NOT_FOUND']
    accounts: List[Account]


@router.post('/plate-check', response_model=LicensePlateCheckResponse)
async def license_plate_check(
    plate: str,
    account_status: AccountStatus = Depends(get_account_status)
):
    if account := account_status.get_account_info_by_plate(plate):
        return LicensePlateCheckResponse(
            plate=plate,
            status='POSITIVE',
            accounts=[account]
        )
    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate):
        return LicensePlateCheckResponse(
            plate=plate,
            status='FOR_CONFIRMATION',
            accounts=similar_accounts
        )
    else:
        return LicensePlateCheckResponse(
            plate=plate,
            status='NOT_FOUND',
            accounts=[]
        )


@router.post('/notify-gc')
async def notify_group_chat(
    plate: str = Form(...),
    image: UploadFile = File(...),
    name: str = Form(...),
    account_status: AccountStatus = Depends(get_account_status)
):
    if account := account_status.get_account_info_by_plate(plate):
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