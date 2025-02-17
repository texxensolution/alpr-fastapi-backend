from sqlalchemy.orm import Session
from typing import Tuple, Literal
from src.core.auth import get_user_type
from src.core.models import LogRecord
from src.services.synchronize import LarkSynchronizer
from datetime import date


EventType = Literal[
    'PLATE_CHECKING',
    'POSITIVE_PLATE_NOTIFICATION',
    'FOR_CONFIRMATION_NOTIFICATION'
]


class Logger:
    """
    Responsible for logging incoming request to the database
    """
    def __init__(
        self,
        db: Session,
        synchronizer: LarkSynchronizer
    ):
        self.db = db
        self.synchronizer = synchronizer

    async def request(
        self,
        plate_no: str,
        user_id: str,
        location: Tuple[float, float],
        event_type: EventType,
        detection_type: str
    ):
        user_type = get_user_type(self.db, user_id)

        if user_type is None:
            return

        lat, lon = location 

        if user_type == 'external':
            log_record = LogRecord(
                username=user_id,
                scanned_text=plate_no,
                event_type=event_type,
                latitude=lat,
                longitude=lon,
                detection_type=detection_type
            )
        elif user_type == 'internal':
            await self.synchronizer.sync_required(
                union_id=user_id,
                target_date=date.today()
            )
            log_record = LogRecord(
                union_id=user_id,
                scanned_text=plate_no,
                event_type=event_type,
                latitude=lat,
                longitude=lon,
                detection_type=detection_type
            )
        self.db.add(log_record)
        self.db.commit()