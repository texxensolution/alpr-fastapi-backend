from fastapi import APIRouter
from typing import List
from src.core.dependencies import GetStatusManager
from src.core.dtos import StatusManagerDTO


router = APIRouter(prefix="/api/v3", tags=["Status Endpoint v3.0"])


@router.get('/users/status', response_model=List[StatusManagerDTO])
async def get_users_status(status_manager: GetStatusManager):
    return status_manager.get_users_status()
