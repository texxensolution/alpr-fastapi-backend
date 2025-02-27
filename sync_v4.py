import asyncio
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from src.services.synchronize import LarkSynchronizer
from src.services.analytics import LarkUsersAnalytics
from datetime import date
from src.core.dependencies import get_base_manager
from src.core.config import settings

# prod_db_url = "postgresql://repoai:repoai-repoai@172.16.1.17:5432/repo-ai-db"

# analytics.summary()
lark = get_base_manager()
engine = create_engine(settings.DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    bind=engine
)
db = SessionLocal()
analytics = LarkUsersAnalytics(db)
synchronizer = LarkSynchronizer(
    db=db,
    analytics=analytics,
    lark=lark
)
target_date = date.today(),
asyncio.run(synchronizer.start_watching())
