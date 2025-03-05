import os
import sys
import logging
import asyncio
from sqlalchemy.orm import Session
from src.core.config import settings
from dotenv import load_dotenv
from datetime import date, datetime
from lark.token_manager import TokenManager
from src.lark.lark import Lark
from src.core.models import LarkHistoryReference
from src.core.dependencies import get_db
from src.db.logger import (
    get_ids_without_lark_ref_for_today,
    get_references_by_target_date,
    get_stats_for_union_ids,
    StatisticsQueryResult
)
from typing import List, Tuple
from src.utils.loggers import logging


logger = logging.getLogger(__name__)

load_dotenv()

CHOPPER_APP_ID = os.getenv('CHOPPER_APP_ID')
CHOPPER_APP_SECRET = os.getenv('CHOPPER_APP_SECRET')
BASE_APP_TOKEN = os.getenv('BASE_LOGS_APP_TOKEN')
LOGS_TABLE_ID = "tblUzqg6jJa48WnI" # V3

token_manager = TokenManager(
    app_id=CHOPPER_APP_ID,
    app_secret=CHOPPER_APP_SECRET
)

client = Lark(
    app_id=CHOPPER_APP_ID,
    app_secret=CHOPPER_APP_SECRET
)


def get_date_timestamp(target_date: date) -> int:
    # Convert today's date to a datetime object (with time set to 00:00:00)
    today_datetime = datetime.combine(target_date, datetime.min.time())

    # Get the integer timestamp (seconds since Unix epoch)
    timestamp = int(today_datetime.timestamp()) * 1000
    return timestamp


def create_reference_map(
    references: List[Tuple[str, str]]
) -> Tuple[dict, List[str]]:
    map = {key: value for (key, value) in references}
    union_ids = [key for key, value in references]
    return map, union_ids


def create_counter_payload_for_union_ids(
    union_ids: List[str], 
    target_date: date
):
    payload = []

    target_date_timestamp = get_date_timestamp(target_date)
    
    for union_id in union_ids:
        payload.append({
            "fields": {
                "Field Agent": [
                    { "id": union_id }
                ],
                "Total Requests": 0,
                "Positive Count": 0,
                "For Confirmation Count": 0,
                "Unique Scanned Count": 0,
                "Log Date": target_date_timestamp
            }
        })

    return payload


def stats_update_payload(
    stats: List[StatisticsQueryResult],
    lookup_table: dict
):
    return {
        "records": [
            {
                "record_id": lookup_table[stat.union_id],
                "fields": {
                    "Total Requests": stat.total_requests,
                    "Positive Count": stat.positive_count,
                    "For Confirmation Count": stat.for_confirmation_count,
                    "Unique Scanned Count": stat.unique_scanned_plate,
                }
            } for stat in stats
        ]
    }
    

async def logs_lark_sync(
    client: Lark
):
    while True:
        try:
            db = next(get_db())
            TARGET_LOG_DATE = date.today()
            logger.info("logging at: %s", datetime.now())

            union_ids = get_ids_without_lark_ref_for_today(
                session=db,
                log_date=TARGET_LOG_DATE
            )
            
            total_union_ids = len(union_ids)

            if total_union_ids > 0:
                # create a payload for inserting data or row in lark base
                logger.debug("total union ids: %s", total_union_ids)
                data = create_counter_payload_for_union_ids(
                    union_ids=union_ids,
                    target_date=TARGET_LOG_DATE
                )

                response = await client.base.create_records(
                    app_token=settings.BASE_LOGS_APP_TOKEN,
                    table_id=settings.LOGS_TABLE_ID,
                    data=data
                )

                if response.code == 0:
                    for reference in response.data.records:
                        field_agent_id = reference['fields']['Field Agent'][0]['id']
                        reference = LarkHistoryReference(
                            union_id=field_agent_id,
                            log_date=TARGET_LOG_DATE,
                            lark_record_id=reference['record_id']
                        )
                        db.add(reference)
                    db.commit()

            references = get_references_by_target_date(
                target_date=TARGET_LOG_DATE,
                db=db
            )
            
            reference_lookup, union_ids = create_reference_map(references)

            if len(union_ids) > 0:
                stats = get_stats_for_union_ids(
                    union_ids=union_ids,
                    target_date=TARGET_LOG_DATE,
                    db=db
                )

                update_payload = stats_update_payload(
                    stats,
                    reference_lookup 
                )

                await client.base.update_records(
                    app_token=settings.BASE_LOGS_APP_TOKEN,
                    table_id=settings.LOGS_TABLE_ID,
                    records=update_payload
                )
                logger.debug("updated %s records", len(stats))
            db.close()
        except Exception as e:
            logger.error("Error: %s", e)
        finally:
            await asyncio.sleep(5)


async def main():
    await logs_lark_sync(client=client)
        

asyncio.run(main())