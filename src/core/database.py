import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from src.core.config import settings

load_dotenv()

MAX_POOL_SIZE = 100

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=MAX_POOL_SIZE,        # Adjust based on active queries
    max_overflow=50,      # Allow some flexibility for traffic spikes
    pool_timeout=30,      # Wait before timing out if the pool is full
    pool_recycle=1800,    # Prevents stale connections (30 min)
)

SessionLocal = sessionmaker(
    bind=engine
)
