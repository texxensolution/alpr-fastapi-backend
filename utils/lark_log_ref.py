from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date
from typing import List, Tuple
from database.models import LarkLogRef


def does_it_have_lark_ref(
    session: Session,
    name: str,
    current_date: str
) -> LarkLogRef | None:
    lark_ref = session.query(LarkLogRef).where(
        LarkLogRef.name == name,
        LarkLogRef.current_date == current_date
    ).first()

    if lark_ref:
        return lark_ref

    return None


def init_lark_ref_for(
    session: Session,
    name: str,
    current_date: str,
    lark_record_id: str
):
    lark_ref = LarkLogRef(
        name=name,
        current_date=current_date,
        lark_record_id=lark_record_id
    )

    session.add(lark_ref)
    session.commit()
    session.refresh(lark_ref)

    return lark_ref
    

def get_unregistered_names_today(session: Session, log_date: date) -> List[str]:
    query = text("""
        SELECT DISTINCT name, logs.current_date 
        FROM logs 
        WHERE name NOT IN (
            SELECT name 
            FROM lark_log_references 
            WHERE log_date = :log_date
        ) and logs.current_date = :log_date
    """)

    result = session.execute(query, {'log_date': log_date})

    rows = result.fetchall()

    return [row[0] for row in rows]


def get_registered_names_for_target_date(
    session: Session,
    target_date: date
) -> List[Tuple[str, str]]:
    names = session.query(LarkLogRef) \
        .filter(LarkLogRef.log_date == target_date) \
        .all()
    
    return [(name.name, name.lark_record_id) for name in names]


def get_stats_for_registered_names_on_target_date(
    session: Session,
    target_date: date,
    names: List[str]
):
    query = text(
        """
        SELECT count(name) AS total_requests, name, logs.current_date
        FROM logs
        WHERE logs.current_date = :target_date
        AND name IN :names
        GROUP BY name, logs.current_date;
        """
    )

    result = session.execute(query, {"target_date": target_date, "names": tuple(names)})

    # print("sql", result)
    rows = result.fetchall()

    return rows