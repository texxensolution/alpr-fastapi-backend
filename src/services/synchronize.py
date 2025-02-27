import asyncio
from sqlalchemy.orm import Session
from sqlalchemy import or_
from .analytics import LarkUsersAnalytics
from typing import List
from datetime import date, datetime
from src.core.models import LarkHistoryReference
from src.lark.lark import Lark
from src.core.config import settings
from src.lark.exceptions import LarkBaseHTTPException
from src.utils.date_utils import get_date_timestamp, timestamp_to_date
from src.utils.loggers import logging


logger = logging.getLogger(__name__)

class LarkSynchronizer:
    def __init__(
        self,
        db: Session,
        lark: Lark,
        analytics: LarkUsersAnalytics,
        waiting_period: float = 2.0
    ):
        logger.info("Initializing LarkSynchronizer")
        self.db = db
        self.lark = lark
        self.analytics = analytics
        self.syncing_event = asyncio.Event()
        self.waiting_period = waiting_period

    async def start_watching(self):
        while not self.syncing_event.is_set():
            logger.info("syncing at %s", datetime.now())
            target_date = date.today()
            
            # First check if there are any records that don't have lark_record_id
            refs_without_record_id = self.get_refs_without_remote_ref()

            if len(refs_without_record_id) > 0:
                await self.initialize_refs_without_record_id(
                    refs=refs_without_record_id,
                    target_date=target_date
                )
            else:
                logger.info("no refs without record id")
            
            # records that is not yet synchronize to remote lark base storage
            buffered_refs = self.get_buffered_refs(target_date)

            logger.info('buffered_refs_count', len(buffered_refs))
            
            # create a request payload for updating corresponding record on lark base
            def union_id_extractor(ref: LarkHistoryReference):
                return ref.union_id
            
            union_ids = list(map(union_id_extractor, buffered_refs))
            
            result = self.analytics.get_logs_by_union_id(
                union_ids=union_ids,
                target_date=target_date
            )
            
            summaries = self.analytics.summary(result)
            logger.info("done computing summary!")

            # convert the summary to lark payload
            payload = self._mass_update_ref_payload(
                summaries,
                target_date
            )

            current_timestamp = datetime.now()

            if len(payload) == 0:
                print(f"🔄 skip sync ~~ 🕒 {current_timestamp}")
                await asyncio.sleep(3)
                continue
                
            # mark the references as sync
            response = await self.lark.base.update_records(
                app_token=settings.BASE_LOGS_APP_TOKEN,
                table_id=settings.LOGS_TABLE_ID,
                records={
                    "records": payload
                }
            )
            
            record_ids = [
                record["record_id"]
                for record in response.data["records"]
            ]

            self.mass_mark_as_sync(
                record_ids,
                target_date
            )
            logger.info("synced~!")
            
            await asyncio.sleep(self.waiting_period)
    
    async def initialize_refs_without_record_id(
        self,
        refs: List[LarkHistoryReference],
        target_date: date
    ):
        union_ids = [ref.union_id for ref in refs]

        multiple_refs_payload = self.create_multiple_refs_payload(
            union_ids=union_ids, target_date=target_date
        )
        print('multiple_refs_payload', multiple_refs_payload)
        
        response = await self.lark.base.create_records(
            app_token=settings.BASE_LOGS_APP_TOKEN,
            table_id=settings.LOGS_TABLE_ID,
            data=multiple_refs_payload
        )

        created_records = response.data.records if response.code == 0 else []        
        need_to_be_updated_record = []
        for record in created_records:
            need_to_be_updated_record.append({
                "union_id": record["fields"]["Field Agent"][0]["id"],
                "lark_record_id": record["record_id"],
                "log_date": timestamp_to_date(record["fields"]["Log Date"])
            })

        self.db.bulk_update_mappings(LarkHistoryReference, need_to_be_updated_record)
        self.db.commit()
        print("updated~")
        # print('response', response.data)

    # def 
    
    def create_multiple_refs_payload(
        self,
        union_ids: List[str],
        target_date: date
    ):
        items = []
        for union_id in union_ids:
            payload = {
                "fields": {
                    "Field Agent": [
                        { "id": union_id }
                    ],
                    "Total Requests": 0,
                    "Positive Count": 0,
                    "For Confirmation Count": 0,
                    "Unique Scanned Count": 0,
                    "Log Date": get_date_timestamp(target_date)
                }
            }
            items.append(payload)
        return items

    def get_refs_without_remote_ref(self):
        return self.db.query(LarkHistoryReference).filter(
            LarkHistoryReference.lark_record_id == None
        ).all()

    def get_buffered_refs(
        self,
        target_date: date
    ):
        return self.db.query(
            LarkHistoryReference
        ).where(
            or_(
                LarkHistoryReference.updated_at > LarkHistoryReference.last_sync_at,
                LarkHistoryReference.updated_at == None,
                LarkHistoryReference.last_sync_at == None,
            ),
            LarkHistoryReference.log_date == target_date,
            LarkHistoryReference.lark_record_id != None
        ).all()
        
    def mass_mark_as_sync(
        self,
        record_ids: List[str],
        log_date: date
    ):
        rows = (
            self.db
                .query(LarkHistoryReference)
                .filter(
                    LarkHistoryReference.lark_record_id.in_(record_ids),
                    LarkHistoryReference.log_date == log_date
                )
                .all()
        )
        for row in rows:
            current = datetime.now()
            row.updated_at = current
            row.last_sync_at = current
            self.db.add(row)

        self.db.commit()
            
            
    
    async def _create_remote_ref(
        self,
        union_id: str,
        target_date: date
    ):
        try:
            response = await self.lark.base.create_record(
                app_token=settings.BASE_LOGS_APP_TOKEN,
                table_id=settings.LOGS_TABLE_ID,
                fields=self._create_ref_payload(
                    union_id=union_id,
                    target_date=target_date
                )
            )
            if response.code != 0:
                raise LarkBaseHTTPException(
                    response.code, 
                    response.msg
                )
            return response
        except Exception as err:
            print(f"Error: {err}")

    def _mass_update_ref_payload(
        self,
        summaries: List[dict],
        target_date: date
    ):
        converted_date_timestamp = self._get_date_timestamp(target_date)
        return [
            {
                "fields": {
                    "Field Agent": [
                        { "id": summary["union_id"] }
                    ],
                    "Total Requests": summary["total_detected_count"],
                    "Positive Count": summary["positive_plate_count"],
                    "For Confirmation Count": summary["for_confirmation_count"],
                    "Unique Scanned Count": summary["unique_plate_count"],
                    "Log Date": converted_date_timestamp 
                },
                "record_id": summary["record_id"]
            } for summary in summaries
        ]
        
    def _create_ref_payload(
        self,
        union_id: str, 
        target_date: date
    ):
        target_date_timestamp = self._get_date_timestamp(target_date)
        return {
            "Field Agent": [
                { "id": union_id }
            ],
            "Total Requests": 0,
            "Positive Count": 0,
            "For Confirmation Count": 0,
            "Unique Scanned Count": 0,
            "Log Date": target_date_timestamp
        }

    def _get_date_timestamp(
        self,
        target_date: date
    ) -> int:
        # Convert today's date to a datetime object (with time set to 00:00:00)
        today_datetime = datetime.combine(target_date, datetime.min.time())
        # Get the integer timestamp (seconds since Unix epoch)
        timestamp = int(today_datetime.timestamp()) * 1000
        return timestamp

    async def find_or_create_ref(
        self,
        union_id: str,
        target_date: date
    ):
        ref = self.find_ref(
            union_id=union_id,
            target_date=target_date
        )
        if not ref:
            ref = self.create_ref(union_id, target_date)
        return ref
            
    def create_ref(
        self,
        union_id: str,
        target_date: date
    ):
        ref = LarkHistoryReference(
            union_id=union_id,
            log_date=target_date
        )
        self.db.add(ref)
        self.db.commit()
        self.db.refresh(ref)
        return ref

    def find_ref(
        self,
        union_id: str,
        target_date: date
    ):
        return self.db.query(LarkHistoryReference) \
            .where(
                LarkHistoryReference.union_id == union_id,
                LarkHistoryReference.log_date == target_date
            ) \
            .first()

    async def mark_as_sync(
        self,
        union_id: str,
        target_date: date
    ) -> bool:
        ref = self.find_ref(union_id, target_date)
        if not ref:
            return False
        ref.updated_at = datetime.now()
        self.db.add(ref)
        self.db.commit()
        return True

    async def sync_required(
        self,
        union_id: str,
        target_date: date,
        autocommit: bool = True
    ) -> (LarkHistoryReference | None):
        ref = await self.find_or_create_ref(union_id, target_date)

        if not ref:
            return None

        ref.updated_at = datetime.now()
        
        self.db.add(ref)

        if autocommit:
            self.db.commit()
            self.db.refresh(ref)
        
        return ref


    