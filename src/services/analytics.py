import pandas as pd
from src.core.models import LogRecord, LarkHistoryReference
from typing import List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, Row
from datetime import date
from pydantic import BaseModel
from uuid import UUID
from src.core.dtos import DetectedType

class Log(BaseModel):
    id: UUID
    union_id: str
    scanned_text: str
    event_type: str
    detection_type: str | None
    log_date: date
    record_id: str


class LarkUsersAnalytics:
    def __init__(self, db: Session):
        self.db = db

    def get_logs_by_union_id(
        self,
        union_ids: List[str],
        target_date: date
    ) -> List[Row[Tuple[LogRecord, str]]]:
        result = (
            self.db.query(
                LogRecord,
                LarkHistoryReference.lark_record_id
            )
            .join(
                LarkHistoryReference,
                and_(
                    LogRecord.union_id == LarkHistoryReference.union_id,
                    LogRecord.log_date == LarkHistoryReference.log_date
                )
            )
            .filter(
                LogRecord.union_id.in_(union_ids),
                LogRecord.log_date == target_date
            ).all()
        )
        return self._format_logs_to_base_model(result)

    def _format_logs_to_base_model(
        self,
        logs: List[Row[Tuple[LogRecord, str]]]
    ):
        collections = []
        for row in logs:
            log, record_id = row
            log = Log(
                id=log.id,
                scanned_text=log.scanned_text,
                log_date=log.log_date,
                union_id=log.union_id,
                detection_type=log.detection_type,
                event_type=log.event_type,
                record_id=record_id
            ).model_dump()
            collections.append(log)
        return collections
    
    def summary(
        self,
        result: List[Tuple]
    ):
        df = pd.DataFrame(
            result,
            columns=[
                "id",
                "union_id",
                "scanned_text",
                "event_type",
                "log_date", 
                "record_id"
            ]
        )
        grouped_df = df.groupby("union_id")

        # Count unique scanned texts per group
        unique_plate_df = grouped_df["scanned_text"].apply(
            lambda x: len(list(x.unique()))
        )
        
        # Count positive plate notifications per group
        positive_plate_count = grouped_df["event_type"].apply(
            lambda event: (event == DetectedType.POSITIVE_PLATE_NOTIFICATION.value).sum()
        )
        
        for_confirmation_count = grouped_df["event_type"].apply(
            lambda event: (event == DetectedType.FOR_CONFIRMATION_NOTIFICATION.value).sum()
        )
        
        # Total detected count per group
        total_detected_count = grouped_df["scanned_text"].count()
        record_id = grouped_df["record_id"].first()
        
        # Create the aggregated result DataFrame
        aggregated_result_df = pd.DataFrame({
            "union_id": unique_plate_df.index,
            "unique_plate_count": unique_plate_df,
            "total_detected_count": total_detected_count,
            "for_confirmation_count": for_confirmation_count,
            "positive_plate_count": positive_plate_count,
            "record_id": record_id
        }).reset_index(drop=True)
        
        # Sort the DataFrame by total_detected_count in descending order and convert it to a list of dicts
        return (
            aggregated_result_df
                .sort_values(
                    'total_detected_count',
                    ascending=False
                )
                .to_dict(orient="records")
        )
        
        
    