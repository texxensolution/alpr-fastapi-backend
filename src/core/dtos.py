from typing import Optional, List, Literal, Tuple
from enum import Enum
from pydantic import BaseModel, Field


class Account(BaseModel):
    plate: str
    ch_code: str
    endo_date: str
    client: str
    car_model: str
    plate_number_normalized: Optional[str] = None


class PersonField(BaseModel):
    id: str


class CounterPayload(BaseModel):
    field_agent: List[PersonField] = Field(alias='Field Agent')
    total_requests: int = Field(alias='Total Requests')
    positive_count: int = Field(alias='Positive Count')
    for_confirmation_count: int = Field(alias='For Confirmation Count')
    log_date: int = Field(alias='Log Date')


class CounterCreateLarkPayload(BaseModel):
    fields: CounterPayload

    
class LarkAccountDTO(BaseModel):
    union_id: str
    user_id: str
    name: str
    current_device: Optional[str] = None


class Notification(BaseModel):
    plate_number: str
    is_similar: bool
    file_path: Optional[str] = None
    accounts: List[Account]


class QueuedPlateDetected(BaseModel):
    plate_number: str
    status: Literal[
        'POSITIVE',
        'FOR_CONFIRMATION',
        'NOT_FOUND'
    ]
    accounts: List[Account]
    file_path: str
    name: str


NotificationStatus = Literal['POSITIVE', 'FOR_CONFIRMATION', 'NOT_FOUND']
class Detection(BaseModel):
    plate_number: str
    status: NotificationStatus
    accounts: List[Account]
    file_path: Optional[str] = None
    union_id: Optional[str] = None
    user_id: Optional[str] = None
    username: Optional[str] = None
    latitude: float
    longitude: float
    detected_by: str
    detected_type: Optional[str] = None
    user_type: Literal['internal', 'external'] = 'internal'


class CardTemplateDataField(BaseModel):
    template_id: str
    template_variable: dict


class CardTemplatePayload(BaseModel):
    data: CardTemplateDataField
    type: Literal['template'] = 'template'


class StatusManagerDTO(BaseModel):
    name: str
    union_id: str


TokenUserType = Literal['internal', 'external']
TokenStatusType = Literal['success', 'error', 'invalid token']


class DetectedType(Enum):
    POSITIVE_PLATE_NOTIFICATION = 'POSITIVE_PLATE_NOTIFICATION'
    FOR_CONFIRMATION_NOTIFICATION = 'FOR_CONFIRMATION_NOTIFICATION'
    PLATE_CHECKING = 'PLATE_CHECKING'


class ScannerResponse(BaseModel):
    message: str
    type: str


class DetectionType(Enum):
    PLATES = 'plates'
    STICKER = 'sticker'


class EventType(Enum):
    PLATE_CHECKING = 'PLATE_CHECKING'
    POSITIVE_PLATE_NOTIFICATION = 'POSITIVE_PLATE_NOTIFICATION'
    FOR_CONFIRMATION_NOTIFICATION = 'FOR_CONFIRMATION_NOTIFICATION'



class AlertNotifyGroupChat(BaseModel):
    plate: str
    detected_type: str
    location: Tuple[float, float]
    