import os
import time
import asyncio
from dotenv import load_dotenv
from datetime import date, datetime
from lark.token_manager import TokenManager
from lark.base_manager import BaseManager
from database.database import SessionLocal
from utils.lark_log_ref import get_unregistered_names_today, get_registered_names_for_target_date, get_stats_for_registered_names_on_target_date
from database.models import LarkLogRef
from typing import List


load_dotenv()

CHOPPER_APP_ID = os.getenv('CHOPPER_APP_ID')
CHOPPER_APP_SECRET = os.getenv('CHOPPER_APP_SECRET')
BASE_APP_TOKEN = os.getenv('BASE_LOGS_APP_TOKEN')
LOGS_TABLE_ID = "tbll2YudcsqnNUXd"

token_manager = TokenManager(app_id=CHOPPER_APP_ID, app_secret=CHOPPER_APP_SECRET)

base_manager = BaseManager(
    app_token=BASE_APP_TOKEN,
    token_manager=token_manager
)


def get_date_timestamp(target_date: date) -> int:
    # Convert today's date to a datetime object (with time set to 00:00:00)
    today_datetime = datetime.combine(target_date, datetime.min.time())

    # Get the integer timestamp (seconds since Unix epoch)
    timestamp = int(today_datetime.timestamp()) * 1000
    return timestamp


def create_payload_references_for_names(
    names: List[str], 
    target_date: date
):
    payload = []

    target_date_timestamp = get_date_timestamp(target_date)
    
    for name in names:
        payload.append({
            "fields": {
                "name": name,
                "total_requests": 0,
                "date": target_date_timestamp
            }
        })

    return payload


while True:
    print("Start lark logs sync...")
    try:
        with SessionLocal() as session:
            CURRENT_DATE_TO_SYNC = date.today()

            names = get_unregistered_names_today(
                session=session,
                log_date=CURRENT_DATE_TO_SYNC
            )

            print(f"Unregistered names count: {len(names)}")

            if len(names) > 0:
                print("Creating payload for unregistered names...")
                data = create_payload_references_for_names(names, CURRENT_DATE_TO_SYNC)

                response = asyncio.run(base_manager.create_records(
                    table_id=LOGS_TABLE_ID,
                    data=data
                ))

                if response.code == 0:
                    for record in response.data.records:
                        lark_ref_record = LarkLogRef(
                            name=record['fields']['name'],
                            log_date=CURRENT_DATE_TO_SYNC,
                            lark_record_id=record['record_id']
                        )
                        session.add(lark_ref_record)
                    session.commit()
            
            # sync the logs from db to lark
            # get registered names for target date
            registered_names = get_registered_names_for_target_date(
                session=session,
                target_date=CURRENT_DATE_TO_SYNC
            )

            lark_ref_map = {}

            for (name, lark_ref_id) in registered_names:
                lark_ref_map[name] = lark_ref_id

            names = [registered_name[0] for registered_name in registered_names]
            lark_refs = [registered_name[1] for registered_name in registered_names]

            stats = get_stats_for_registered_names_on_target_date(
                session=session,
                target_date=CURRENT_DATE_TO_SYNC,
                names=names
            )

            update_references_records = []

            for (total_requests, name, _) in stats:
                update_references_records.append({
                    "record_id": lark_ref_map[name],
                    "fields": {
                        "total_requests": total_requests
                    }
                })

            print("Syncing from Postgresql to Lark Base...")
            response = asyncio.run(base_manager.update_records(
                table_id=LOGS_TABLE_ID,
                records={
                    "records": update_references_records
                }
            ))
            print("Done syncing...")
    except Exception as err:
        print(f"Error: {err}")

    time.sleep(5)