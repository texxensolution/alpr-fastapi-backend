from pydantic import BaseModel
from typing import Optional


class LarkAccountDTO(BaseModel):
    union_id: str
    user_id: str
    name: str
    current_device: Optional[str] = None