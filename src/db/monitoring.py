from sqlalchemy.orm import Session
from src.core.models import SystemUsageLog
from src.core.monitoring import get_system_usage


def store_system_usage(db: Session):
    system_usage = get_system_usage()

    log = SystemUsageLog(
        metadata=system_usage.model_dump()
    )

    db.add(log)
    db.commit()

    return system_usage