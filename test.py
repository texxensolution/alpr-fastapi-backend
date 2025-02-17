import asyncio
from src.services.synchronize import LarkSynchronizer
from src.services.analytics import LarkUsersAnalytics
from datetime import date
from src.core.dependencies import get_db, get_base_manager
# from sqlalchemy import create_engine

# prod_db_url = "postgresql://repoai:repoai-repoai@172.16.1.17:5432/repo-ai-db"

# prod_engine = create_engine(prod_db_url, echo=False)

# analytics = LarkUsersAnalytics(prod_engine)

# analytics.summary()
lark = get_base_manager()
db = next(get_db())

analytics = LarkUsersAnalytics(db)

synchronizer = LarkSynchronizer(
    db=db,
    target_date=date.today(),
    analytics=analytics,
    lark=lark
)

# response = synchronizer.start_watching()
asyncio.run(synchronizer.start_watching())

# result = synchronizer.get_buffered_refs()
# print('buffered refs:', result)