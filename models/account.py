from pydantic import BaseModel
from typing import Optional


class Account(BaseModel):
    plate: str
    ch_code: str
    endo_date: str
    client: str
    car_model: str
    plate_number_normalized: Optional[str] = None
