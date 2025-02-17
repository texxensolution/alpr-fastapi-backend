from typing import Optional, List, Literal
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


class Detection(BaseModel):
    plate_number: str
    status: Literal[
        'POSITIVE',
        'FOR_CONFIRMATION',
        'NOT_FOUND'
    ]
    accounts: List[Account]
    file_path: str
    union_id: str
    user_id: Optional[str] = None
    latitude: float
    longitude: float
    detected_by: str


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