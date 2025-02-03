from fastapi import APIRouter, Depends, Query
from datetime import date
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from src.core.dependencies import get_db
from fastapi.responses import StreamingResponse
from io import StringIO
import pandas as pd

router = APIRouter(
    prefix="/api",
    tags=["Logs"]
)

EXPORT_LOG_BY_DATE_QUERY = f"""
SELECT count(name) as total_requests, name, current_date FROM logs
WHERE current_date = ?
GROUP BY name
"""

class ExportLogsRequest(BaseModel):
    current_date: date
    

@router.get("/logs/export")
async def export_logs(
    current_date: date = Query(description="Filter the logs by the date provided"),
    session: Session = Depends(get_db)
):
    query = text(
        "SELECT count(name) as total_requests, name, logs.current_date FROM logs WHERE logs.current_date = :current_date GROUP BY name, logs.current_date;"
    )

    df = pd.read_sql(
        query, 
        session.bind,
        params={"current_date": current_date}
    )
    # Convert DataFrame to CSV in memory using StringIO
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    generated_filename = f"{current_date.strftime("%Y-%m-%d")}-logs.csv"

    # Return the CSV as a StreamingResponse with the appropriate content type
    return StreamingResponse(csv_buffer, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={generated_filename}"})

@router.get("/logs/export/v2")
async def export_logs_with_unique_detection(
    current_date: date = Query(description="Filter the logs by the date provided"),
    session: Session = Depends(get_db)
):
    query = text(
        f"""
            SELECT name,
            scanned_text as plate,
            logs.current_date as log_date,
            timestamp
            from logs
            WHERE logs.current_date = '{current_date.strftime('%Y-%m-%d')}' 
            AND scanned_text IS NOT NULL
        """
    )
    
    df = pd.read_sql(
        query, 
        session.bind,
        params={"current_date": current_date}
    )

    # Convert DataFrame to CSV in memory using StringIO
    csv_buffer = StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    generated_filename = f"{current_date.strftime("%Y-%m-%d")}-logs-with-scanned-text.csv"

    # Return the CSV as a StreamingResponse with the appropriate content type
    return StreamingResponse(csv_buffer, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={generated_filename}"})
    