from fastapi import (
    APIRouter,
    Depends,
    Form,
    File,
    UploadFile,
    BackgroundTasks,
    HTTPException
)
from src.core.config import settings
from typing import List, Tuple
from pydantic import BaseModel
from enum import Enum
from src.core.dtos import ScannerResponse, Detection
from src.core.models import LarkAccount
from src.core.dependencies import (
    AccountStatus,
    get_account_status,
    GetLoggerSession,
    GetCurrentUserCredentials,
    LarkNotificationDepends,
)
from src.utils.file_utils import store_file
from src.utils.plate_helper import normalize_plate
from src.core.account_status import Account
from src.utils.rate_limiter import RateLimiter


router = APIRouter(
    prefix='/api/v4',
    tags=['Scanner 4.0']
)

rate_limiter = RateLimiter(80)

class DetectedType(Enum):
    PLATES = 'plates'
    STICKER = 'sticker'


class EventType(Enum):
    PLATE_CHECKING = 'PLATE_CHECKING'
    POSITIVE_PLATE_NOTIFICATION = 'POSITIVE_PLATE_NOTIFICATION'
    FOR_CONFIRMATION_NOTIFICATION = 'FOR_CONFIRMATION_NOTIFICATION'


class Status(Enum):
    POSITIVE = 'POSITIVE'
    NEGATIVE = 'NEGATIVE'
    FOR_CONFIRMATION = 'FOR_CONFIRMATION'
    

class PlateCheckingRequest(BaseModel):
    plate: str
    detected_type: str
    location: Tuple[float, float]


class AccountDTO(BaseModel):
    plate_no: str
    vehicle_model: str
    ch_code: str
    endo_date: str


class AlertNotifyGroupChat(BaseModel):
    plate: str
    detected_type: str
    location: Tuple[float, float]


class PlateCheckingResponse(BaseModel):
    plate: str
    detected_type: str
    status: Status
    accounts: List[AccountDTO]
    location: Tuple[float, float] 
    count: int


def convert_account_to_dto(account: Account) -> AccountDTO:
    return AccountDTO(
        plate_no=account.plate,
        ch_code=account.ch_code,
        endo_date=account.endo_date,
        vehicle_model=account.car_model
    )


@router.post('/plate/check', response_model=PlateCheckingResponse)
async def plate_checking(
    body: PlateCheckingRequest,
    logger: GetLoggerSession,
    credentials: GetCurrentUserCredentials,
    account_status: AccountStatus = Depends(get_account_status)
):
    _, user_id = credentials
    plate = normalize_plate(body.plate)
    detected_type = body.detected_type
    (lat, lon) = body.location

    response = PlateCheckingResponse(
        plate=plate,
        detected_type=detected_type,
        location=(lat, lon),
        status=Status.NEGATIVE.value,
        accounts=[],
        count=0
    )

    if _account := account_status.get_account_info_by_plate(plate):
        response = PlateCheckingResponse(
            plate=plate,
            detected_type=detected_type,
            location=(lat, lon),
            status=Status.POSITIVE.value,
            accounts=[convert_account_to_dto(_account)],
            count=1
        )

    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate):
        response = PlateCheckingResponse(
            plate=plate,
            detected_type=detected_type,
            location=(lat, lon),
            status=Status.FOR_CONFIRMATION.value,
            accounts=[
                convert_account_to_dto(account)
                for account in similar_accounts
            ],
            count=len(similar_accounts)
        )

    await logger.request(
        detection_type=response.detected_type,
        event_type=EventType.PLATE_CHECKING.value,
        plate_no=response.plate,
        location=response.location,
        user_id=user_id
    )

    return response
    

@router.post('/notify/group-chat')
async def notify_group_chat(
    background_tasks: BackgroundTasks,
    lark_notification: LarkNotificationDepends,
    logger: GetLoggerSession,
    credentials: GetCurrentUserCredentials,
    plate: str = Form(...),
    image: UploadFile = File(...),
    detection_type: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    account_status: AccountStatus = Depends(get_account_status)
):
    user, user_id = credentials

    plate = normalize_plate(plate)
    
    if not rate_limiter.can_proceed(plate):
        return ScannerResponse.model_validate({
            "message": "skipped notification", 
            "type": "skipped"
        })

    if account := account_status.get_account_info_by_plate(plate):
        file_path = store_file(image)
        await logger.request(
            plate_no=plate,
            user_id=user_id,
            detection_type=detection_type,
            event_type=EventType.POSITIVE_PLATE_NOTIFICATION.value,
            location=[latitude, longitude]
        )
        if isinstance(user, LarkAccount):
            detection = Detection(
                plate_number=plate,
                file_path=file_path,
                accounts=[account],
                status='POSITIVE',
                union_id=user.union_id,
                user_id=user.user_id,
                latitude=latitude,
                longitude=longitude,
                detected_by=user.name,
                detected_type=detection_type
            )
            background_tasks.add_task(
                lark_notification.detection_notify,
                data=detection,
                group_chat_id=settings.MAIN_GC_ID
            )
        return ScannerResponse.model_validate({
            "message": "queued notification sent", 
            "type": "positive"
        })

    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate):
        file_path = store_file(image)
        await logger.request(
            plate_no=plate,
            user_id=user_id,
            detection_type=detection_type,
            event_type=EventType.FOR_CONFIRMATION_NOTIFICATION.value,
            location=[latitude, longitude]
        )
        if isinstance(user, LarkAccount):
            detection = Detection(
                plate_number=plate,
                file_path=file_path,
                status='FOR_CONFIRMATION',
                accounts=similar_accounts,
                user_id=user.user_id,
                latitude=latitude,
                longitude=longitude,
                detected_by=user.name,
                detected_type=detection_type
            )
            background_tasks.add_task(
                lark_notification.detection_notify,
                data=detection,
                group_chat_id=settings.MAIN_GC_ID
            )
        return ScannerResponse.model_validate({
            "message": "queued notification sent", 
            "type": "for_confirmation"
        })

@router.post("/notify/group-chat/manual")
async def alert_group_chat_manual_search(
    credentials: GetCurrentUserCredentials,
    form: AlertNotifyGroupChat,
    logger: GetLoggerSession,
    lark_notification: LarkNotificationDepends,
    background_tasks: BackgroundTasks,
    account_status: AccountStatus = Depends(get_account_status)
):
    if not rate_limiter.can_proceed(form.plate):
        return ScannerResponse.model_validate({
            "message": "skipped notification", 
            "type": "skipped"
        })

    user, user_id = credentials

    await logger.request(
        plate_no=form.plate,
        user_id=user_id,
        detection_type=form.detected_type,
        event_type=EventType.POSITIVE_PLATE_NOTIFICATION.value,
        location=form.location
    )
    
    try:
        accounts = account_status.get_account_info_by_plate(form.plate)
        background_tasks.add_task(
            lark_notification.manual_search_notify,
            data=Detection(
                plate_number=form.plate,
                status='POSITIVE',
                user_id=user.user_id,
                latitude=form.location[0],
                longitude=form.location[1],
                detected_by=user.name,
                detected_type=form.detected_type,
                accounts=[accounts],
            ),
            group_chat_id=settings.MAIN_GC_ID
        )
    except Exception as err:
        print("notification err:", err)
    
    return ScannerResponse.model_validate({
        "message": "queued notification sent", 
        "type": "positive"
    })