import os
from fastapi import FastAPI, Form, File, UploadFile, Depends
from pydantic import BaseModel
from utils.account_status import AccountStatus
from typing import List, Optional
from models.account import Account
from models.notification import Notification
from utils.dependencies import get_account_status
from dotenv import load_dotenv
from lark.token_manager import TokenManager
from utils.notification_queue import NotificationQueue
from utils.file_utils import store_file

load_dotenv()


token_manager = TokenManager(
    app_id=os.getenv('APP_ID'),
    app_secret=os.getenv('APP_SECRET')
)

notification_queue = NotificationQueue(token_manager=token_manager)

app = FastAPI()


class LicensePlateStatusResponse(BaseModel):
    plate_number: str
    is_similar: bool
    accounts: List[Account]
    file_path: Optional[str] = None


@app.post('/api/license-plate-status', response_model=LicensePlateStatusResponse)
async def license_plate_status(
    plate_number: str = Form(...),
    image: UploadFile = File(...),
    account_status: AccountStatus = Depends(get_account_status)
):
    print(f"Received Plate Number: {plate_number}")

    file_path = store_file(image)
    print(f"File path: {file_path}")

    if account := account_status.get_account_info_by_plate(plate_number):
        notification = Notification(
            plate_number=plate_number,
            file_path=file_path,
            is_similar=False,
            accounts=[account]
        )

        print(f"Queued: {notification}")

        notification_queue.push(notification)

        return LicensePlateStatusResponse(
            plate_number=plate_number,
            is_similar=False,
            file_path=file_path,
            accounts=[account]
        )

    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate_number):
        notification = Notification(
            plate_number=plate_number,
            file_path=file_path,
            is_similar=True,
            accounts=similar_accounts
        )
        print(f"Queued: {notification}")

        notification_queue.push(notification)
        return LicensePlateStatusResponse(
            plate_number=plate_number,
            is_similar=True,
            file_path=file_path,
            accounts=similar_accounts
        )

    else:
        return LicensePlateStatusResponse(
            plate_number=plate_number,
            is_similar=False,
            accounts=[]
        )

