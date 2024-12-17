from sqlalchemy import TIMESTAMP, DateTime, Column, Integer, String, text, Date, func
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped
from sqlalchemy.schema import PrimaryKeyConstraint
from datetime import date, datetime
from sqlalchemy.dialects.postgresql import UUID
from typing import Literal, Optional, Union
import uuid

class Base(DeclarativeBase):
    pass


class LarkLogRef(Base):
    __tablename__ = 'lark_log_references'

    name: Mapped[str] = mapped_column(
        primary_key=True
    )

    log_date: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
        default=func.current_date()
    )

    lark_record_id: Mapped[str]

    def __init__(
        self, 
        name: str, 
        log_date: str,
        lark_record_id: str
    ):
        self.name = name
        self.log_date = log_date 
        self.lark_record_id = lark_record_id

    __table_args__ = (
        PrimaryKeyConstraint(
            'name',
            'log_date'
        ),
    )

class LarkHistoryReference(Base):
    __tablename__ = 'log_history_references'

    union_id: Mapped[str] = mapped_column(
        primary_key=True
    )

    log_date: Mapped[date] = mapped_column(
        Date,
        primary_key=True,
        default=func.current_date()
    )

    lark_record_id: Mapped[str]

    def __init__(
        self, 
        union_id: str, 
        log_date: str,
        lark_record_id: str
    ):
        self.union_id = union_id 
        self.log_date = log_date 
        self.lark_record_id = lark_record_id

    __table_args__ = (
        PrimaryKeyConstraint(
            'union_id',
            'log_date'
        ),
    )


class LogRecord(Base):
    __tablename__ = 'log_records'

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True,
        unique=True,
        default=uuid.uuid4
    )

    scanned_text: Mapped[Union[str, None]] = mapped_column(nullable=True)

    union_id: Mapped[str]
    
    event_type: Mapped[str]
    
    log_date: Mapped[date] = mapped_column(
        Date,
        nullable=False, 
        default=date.today
    )

    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=text('CURRENT_TIMESTAMP'), 
        nullable=False
    )

    def __init__(
        self, 
        scanned_text: str,
        union_id: str,
        event_type: Literal['PLATE_CHECKING', 'POSITIVE_PLATE_NOTIFICATION', 'FOR_CONFIRMATION_NOTIFICATION']
    ):
        self.scanned_text = scanned_text
        self.union_id = union_id
        self.event_type = event_type



class LarkAccount(Base):
    __tablename__ = 'lark_accounts'
    union_id: Mapped[str] = mapped_column(
        primary_key=True
    )
    user_id: Mapped[str] = mapped_column(
        unique=True, 
        index=True
    )
    name: Mapped[str]
    current_device: Mapped[str] = mapped_column(nullable=True)

    def __init__(
        self, 
        union_id: str,
        user_id: str,
        name: str,
        current_device: Optional[str] = None
    ):
        self.union_id = union_id
        self.user_id = user_id
        self.name = name
        self.current_device = current_device



    

class Log(Base):
    __tablename__ = 'logs'

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True,
        unique=True,
        default=uuid.uuid4
    )

    scanned_text: Mapped[Optional[str]] = mapped_column(nullable=True)

    name: Mapped[str] = mapped_column(
        nullable=False
    )

    event_type: Mapped[str]

    current_date: Mapped[date] = mapped_column(
        Date,
        nullable=False, 
        default=date.today
    )

    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        server_default=text('CURRENT_TIMESTAMP'), 
        nullable=False
    )

    def __repr__(self):
        return f"<Counter(id={self.id}, name='{self.name}', date={self.current_date}, timestamp={self.timestamp})>"

    def __init__(
        self, 
        scanned_text: str,
        name: str, 
        event_type: Literal['PLATE_CHECKING', 'PLATE_NOTIFICATION']
    ):
        self.name = name
        self.scanned_text = scanned_text
        self.event_type = event_type