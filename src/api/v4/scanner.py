from fastapi import APIRouter, Depends
from typing import List, Tuple
from pydantic import BaseModel
from enum import Enum
from src.core.dependencies import AccountStatus, get_account_status, GetLoggerSession
from src.core.account_status import Account
from src.core.dependencies import GetCurrentUserCredentials


router = APIRouter(
    prefix='/api/v4',
    tags=['Scanner 4.0']
)


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
    detected_type: DetectedType
    location: Tuple[float, float]


class AccountDTO(BaseModel):
    plate_no: str
    vehicle_model: str
    ch_code: str
    endo_date: str


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
    plate = body.plate
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
    