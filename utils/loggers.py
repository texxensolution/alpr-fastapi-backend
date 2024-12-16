from sqlalchemy.orm import Session
from database.models import Log
from typing import Literal


def log_entry(
    session: Session, 
    name: str,
    event_type: Literal['PLATE_CHECKING', 'PLATE_NOTIFICATION']
):
    try:
        counter_entry = Log(
            name=name,
            event_type=event_type
        )
        session.add(counter_entry)
        session.commit()
    except Exception:
        session.rollback()