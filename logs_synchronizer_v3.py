import os
import time
import asyncio
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from datetime import date, datetime
from lark.token_manager import TokenManager
from lark.base_manager import BaseManager
from database.database import SessionLocal
from database.models import LarkHistoryReference
from internal.db.logger import get_ids_without_lark_ref_for_today, get_references_by_target_date, get_stats_for_union_ids, StatisticsQueryResult
from typing import List, Tuple
from loguru import logger


load_dotenv()

CHOPPER_APP_ID = os.getenv('CHOPPER_APP_ID')
CHOPPER_APP_SECRET = os.getenv('CHOPPER_APP_SECRET')
BASE_APP_TOKEN = os.getenv('BASE_LOGS_APP_TOKEN')
LOGS_TABLE_ID = "tblUzqg6jJa48WnI" # V3

token_manager = TokenManager(app_id=CHOPPER_APP_ID, app_secret=CHOPPER_APP_SECRET)


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
        "records":[
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
    db: Session,
    base_manager: BaseManager
):
    while True:
        TARGET_LOG_DATE = date.today()

        syncing_timestamp = datetime.now()
        # print("lark synchronization starting...")

        # print(f"Syncing timestamp: {datetime.now()}")

        union_ids = get_ids_without_lark_ref_for_today(
            session=db,
            log_date=TARGET_LOG_DATE
        )
        
        total_union_ids = len(union_ids)

        if total_union_ids > 0:
            # create a payload for inserting data or row in lark base
            data = create_counter_payload_for_union_ids(
                union_ids=union_ids,
                target_date=TARGET_LOG_DATE
            )

            response = await base_manager.create_records(
                table_id=LOGS_TABLE_ID,
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

        # print("Getting all references for synchronization...")
        references = get_references_by_target_date(
            target_date=TARGET_LOG_DATE,
            db=db
        )
        
        no_of_references = len(references)

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
            print(update_payload)
            # print("Updating references on lark...")
            await base_manager.update_records(
                LOGS_TABLE_ID,
                update_payload
            )
            print(f"LarkLogsSync at: {syncing_timestamp} - {no_of_references} references updated. {total_union_ids} new references added.", end="")
            # print("Done updating references.")
            # print("Synchronization ended...")
        else:
            print("No references to update.", end="")

        print(" Wait for 5 secs... \n", end="")
        db.close()
        await asyncio.sleep(5)

        
        
