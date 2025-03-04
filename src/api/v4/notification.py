from fastapi import APIRouter, BackgroundTasks, Depends, Form, File, UploadFile
from src.core.dependencies import (
    LarkNotificationDepends,
    GetLoggerSession,
    GetCurrentUserCredentials,
    AccountStatus,
    get_account_status
)
from src.core.dtos import (
    ScannerResponse,
    EventType,
    Detection,
    AlertNotifyGroupChat
)
from src.core.config import settings
from src.core.models import LarkAccount, User
from src.utils.plate_helper import normalize_plate
from src.utils.rate_limiter import RateLimiter
from src.utils.file_utils import store_file


router = APIRouter(prefix='/api/v4', tags=['Notification 4.0'])

rate_limiter = RateLimiter(80)

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
                detected_type=detection_type,
                user_type='internal'
            )
        elif isinstance(user, User):
            detection = Detection(
                plate_number=plate,
                file_path=file_path,
                accounts=[account],
                status='POSITIVE',
                username=user.username,
                latitude=latitude,
                longitude=longitude,
                detected_by=user.name,
                detected_type=detection_type,
                user_type='external'
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
                accounts=[account],
                status='POSITIVE',
                union_id=user.union_id,
                user_id=user.user_id,
                latitude=latitude,
                longitude=longitude,
                detected_by=user.name,
                detected_type=detection_type,
                user_type='internal'
            )
        elif isinstance(user, User):
            detection = Detection(
                plate_number=plate,
                file_path=file_path,
                accounts=[account],
                status='POSITIVE',
                username=user.username,
                latitude=latitude,
                longitude=longitude,
                detected_by=user.name,
                detected_type=detection_type,
                user_type='external'
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
        if isinstance(user, LarkAccount):
            data=Detection(
                plate_number=form.plate,
                status='POSITIVE',
                user_id=user.user_id,
                latitude=form.location[0],
                longitude=form.location[1],
                detected_by=user.name,
                detected_type=form.detected_type,
                accounts=[accounts],
                user_type='internal'
            )
        elif isinstance(user, User):
            data = Detection(
                plate_number=form.plate,
                status='POSITIVE',
                latitude=form.location[0],
                username=user.username,
                longitude=form.location[1],
                detected_by=user.username,
                detected_type=form.detected_type,
                accounts=[accounts],
                user_type='external'
            )
        background_tasks.add_task(
            lark_notification.manual_search_notify,
            data=data,
            group_chat_id=settings.MAIN_GC_ID
        )
    except Exception as err:
        print("notification err:", err)
    
    return ScannerResponse.model_validate({
        "message": "queued notification sent", 
        "type": "positive"
    })