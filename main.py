import os
import database.models
import uvicorn
import asyncio
from datetime import datetime
from contextlib import asynccontextmanager
from utils.loggers import log_entry
from loguru import logger
from sqlalchemy.orm import Session
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
from utils.dependencies import get_db
from contextlib import asynccontextmanager
from database.models import Base
from database.database import engine
from utils.plate_normalizer import normalize_plate
from api.v2.notification_endpoints import router as notification_v2_router
from api.accounts import router as accounts_router
from api.log_router import router as log_router
from api.user import router as user_router
from api.v3.scanner import router as scanner_router
from internal.db.monitoring import store_system_usage
from logs_synchronizer_v3 import logs_lark_sync
from lark.base_manager import BaseManager

load_dotenv()


token_manager = TokenManager(
    app_id=os.getenv('CHOPPER_APP_ID', ""),
    app_secret=os.getenv('CHOPPER_APP_SECRET', "")
)

NGROK_AUTHTOKEN = os.getenv("NGROK_AUTHTOKEN", "")
NGROK_EDGE = os.getenv("NGROK_EDGE", "edge:edghts_")
BASE_APP_TOKEN = os.getenv('BASE_LOGS_APP_TOKEN')

notification_queue = NotificationQueue(token_manager=token_manager)

APP_PORT=os.getenv('APP_PORT', 8000)

Base.metadata.create_all(bind=engine)

base_manager = BaseManager(
    app_token=BASE_APP_TOKEN,
    token_manager=token_manager
)

async def run_system_monitoring(db: Session):
    while True:
        print(f"Storing system usage at {datetime.now()}...")
        store_system_usage(db)
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())
    try:
        print("Starting system monitoring...")
        system_usage_task = asyncio.create_task(run_system_monitoring(db))
        asyncio.create_task(logs_lark_sync(db, base_manager=base_manager))
        print("Started system monitoring.")
        yield
    finally:
        print("Closing ")
        print("Shutting down server...")

app = FastAPI(lifespan=lifespan)


app.include_router(notification_v2_router)
app.include_router(log_router)
app.include_router(user_router)
app.include_router(accounts_router)
app.include_router(scanner_router)


class LicensePlateStatusResponse(BaseModel):
    plate_number: str
    is_similar: bool
    accounts: List[Account]
    file_path: Optional[str] = None


@app.get("/")
async def hello_world(session: Session = Depends(get_db)):
    return { "message": "server is running!" }


class CheckPlateExistenceRequest(BaseModel):
    plate_numbers: List[str]


class PlateStatus(BaseModel):
    plate_number: str
    is_tagged: bool


class CheckPlateExistenceResponse(BaseModel):
    items: List[PlateStatus]


@app.post("/api/check-plate-status", response_model=CheckPlateExistenceResponse)
async def check_plate_existence(
    form: CheckPlateExistenceRequest,
    account_status: AccountStatus = Depends(get_account_status)
):
    items: List[PlateStatus] = []

    for plate_number in form.plate_numbers:
        if account := account_status.get_account_info_by_plate(plate_number) and len(plate_number) >= 4:
            items.append(PlateStatus(plate_number=plate_number, is_tagged=True))
        elif similar_accounts := account_status.get_similar_accounts_by_plate(plate_number) and len(plate_number) >= 4:
            items.append(PlateStatus(plate_number=plate_number, is_tagged=True))

    return CheckPlateExistenceResponse(items=items)


@app.post('/api/license-plate-status', response_model=LicensePlateStatusResponse)
async def license_plate_status(
    plate_number: str = Form(...),
    image: UploadFile = File(...),
    account_status: AccountStatus = Depends(get_account_status)
):
    plate_number = normalize_plate(plate_number)

    if account := account_status.get_account_info_by_plate(plate_number):
        file_path = store_file(image)

        notification = Notification(
            plate_number=plate_number,
            file_path=file_path,
            is_similar=False,
            accounts=[account]
        )

        notification_queue.push(notification)

        return LicensePlateStatusResponse(
            plate_number=plate_number,
            is_similar=False,
            file_path=file_path,
            accounts=[account]
        )

    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate_number):
        file_path = store_file(image)

        notification = Notification(
            plate_number=plate_number,
            file_path=file_path,
            is_similar=True,
            accounts=similar_accounts
        )

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


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=int(APP_PORT), reload=True)
