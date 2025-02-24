import os
import uvicorn
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy.orm import Session
from fastapi import FastAPI
from dotenv import load_dotenv
from lark.token_manager import TokenManager
# from src.core.notification_queue import NotificationQueue
from src.core.dependencies import get_db
from src.core.models import Base
from src.core.database import engine
from src.api.v1.accounts import router as accounts_router
from src.api.v1.log_router import router as log_router
from src.api.v1.user import router as user_router
from src.api.v4.auth import router as user_v4_router
from src.api.v3.scanner import router as scanner_router
from src.api.v4.scanner import router as scanner_v4_router
from src.api.v3.status import router as users_status_router
from src.ws.status import router as ws_status_router
from src.db.monitoring import store_system_usage
from logs_synchronizer_v3 import logs_lark_sync
from lark.base_manager import BaseManager
from src.core.dependencies import settings

load_dotenv()

token_manager = TokenManager(
    app_id=os.getenv('CHOPPER_APP_ID', ""),
    app_secret=os.getenv('CHOPPER_APP_SECRET', "")
)

BASE_APP_TOKEN = os.getenv('BASE_LOGS_APP_TOKEN')

Base.metadata.create_all(bind=engine)

base_manager = BaseManager(
    app_token=BASE_APP_TOKEN,
    token_manager=token_manager
)


async def run_system_monitoring(db: Session):
    while True:
        # print(f"Storing system usage at {datetime.now()}...")
        store_system_usage(db)
        await asyncio.sleep(60)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = next(get_db())
    try:
        print("Starting system monitoring...")
        system_monitoring = asyncio.create_task(
            run_system_monitoring(db)
        )
        logs_sync = asyncio.create_task(
            logs_lark_sync(
                db,
                base_manager=base_manager
            )
        )
        print("Started system monitoring.")
        yield
    finally:
        logs_sync.cancel()
        system_monitoring.cancel()
        print("Closing ")
        print("Shutting down server...")


app = FastAPI(lifespan=lifespan)

app.include_router(log_router)
app.include_router(user_router)
app.include_router(accounts_router)
app.include_router(scanner_router)
app.include_router(ws_status_router)
app.include_router(users_status_router)
app.include_router(user_v4_router)
app.include_router(scanner_v4_router)


@app.get("/")
async def healthcheck():
    return {"message": "server is running!"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(settings.APP_PORT),
        reload=True
    )
