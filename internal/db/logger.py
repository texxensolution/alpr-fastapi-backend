from sqlalchemy.orm import Session
from sqlalchemy import text
from database.models import LogRecord, LarkHistoryReference
from models.lark_reference import CounterPayload, CounterCreateLarkPayload, PersonField
from lark.base_manager import BaseManager
from datetime import date
from pydantic import BaseModel
from typing import Literal, List, Tuple


def persist_log_entry(
    scanned_text: str,
    union_id: str,
    event_type: Literal['PLATE_CHECKING', 'POSITIVE_PLATE_NOTIFICATION', 'FOR_CONFIRMATION_NOTIFICATION'],
    db: Session
):
    
    log_record = LogRecord(
        scanned_text=scanned_text,
        union_id=union_id,
        event_type=event_type,
    )
    db.add(log_record)
    db.commit()


def get_log_ref_for(
    union_id: str,
    log_date: date,
    db: Session
) -> LarkHistoryReference | None:
    reference = db.query(
        LarkHistoryReference.union_id == union_id,
        LarkHistoryReference.log_date == log_date
    ).first()

    if not reference:
        return None

    return reference


def init_log_ref_for(
    union_id: str,
    log_date: date,
    lark_record_id: str,
    db: Session
) -> LarkHistoryReference:
    reference = LarkHistoryReference(
        union_id=union_id,
        log_date=log_date,
        lark_record_id=lark_record_id
    )
    db.add(reference)
    db.commit()
    db.refresh(reference)

    return reference


def get_ids_without_lark_ref_for_today(
    session: Session, 
    log_date: date
) -> List[str]:
    # Get all ids that dont have assigned record in lark base
    query = text("""
        SELECT DISTINCT union_id, log_date
        FROM log_records
        WHERE union_id NOT IN (
            SELECT union_id
            FROM log_history_references
            WHERE log_date = :log_date
        ) and log_date = :log_date
    """)

    result = session.execute(query, {'log_date': log_date})

    rows = result.fetchall()

    return [row[0] for row in rows]


def get_references_by_target_date(
    target_date: date,
    db: Session
) -> List[Tuple[str, str]]:
    references = db.query(
        LarkHistoryReference
    ).filter(
        LarkHistoryReference.log_date == target_date
    ).all()

    return [
        (reference.union_id, reference.lark_record_id) for reference in references
    ]


class StatisticsQueryResult(BaseModel):
    total_requests: int
    unique_scanned_plate: int
    positive_count: int
    for_confirmation_count: int
    union_id: str
    log_date: date

    

def get_stats_for_union_ids(
    union_ids: List[str],
    target_date: date,
    db: Session
) -> List[StatisticsQueryResult]:
    query = text(
        """
        SELECT count(union_id) AS total_requests, 
        COUNT (DISTINCT scanned_text) as unique_scanned_plate,
        COUNT (DISTINCT CASE WHEN log_records.event_type = 'POSITIVE_PLATE_NOTIFICATION' THEN 1 END) AS positive_count,
        COUNT (DISTINCT CASE WHEN log_records.event_type = 'FOR_CONFIRMATION_NOTIFICATION' THEN 1 END) AS for_confirmation_count,
        union_id, 
        log_records.log_date
        FROM log_records
        WHERE log_records.log_date = :target_date
        AND union_id IN :union_ids
        GROUP BY union_id, log_records.log_date;
        """
    )

    result = db.execute(query, {"target_date": target_date, "union_ids": tuple(union_ids)})

    # print("sql", result)
    rows = result.mappings().fetchall()
        
    return [
        StatisticsQueryResult.model_validate(row) for row in rows
    ]