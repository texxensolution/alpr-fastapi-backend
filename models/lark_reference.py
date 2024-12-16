from typing import List
from pydantic import BaseModel, Field


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

    

