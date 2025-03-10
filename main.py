import uvicorn
import sentry_sdk
from fastapi import FastAPI
from src.api.v1.accounts import router as accounts_router
from src.api.v1.log_router import router as log_router
from src.api.v1.user import router as user_router
from src.api.v4.auth import router as user_v4_router
from src.api.v3.scanner import router as scanner_router
from src.api.v4.scanner import router as scanner_v4_router
from src.api.v3.status import router as users_status_router
from src.api.v4.notification import router as notification_v4_router
from src.api.v4.websocket import router as websocket_router
from src.ws.status import router as ws_status_router
from src.core.dependencies import settings


# initialize sentry logging
sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    traces_sample_rate=1.0,
    _experiments={
        # Set continuous_profiling_auto_start to True
        # to automatically start the profiler on when
        # possible.
        "continuous_profiling_auto_start": True,
    },
)

app = FastAPI()

app.include_router(log_router)
app.include_router(user_router)
app.include_router(accounts_router)
app.include_router(scanner_router)
app.include_router(ws_status_router)
app.include_router(users_status_router)
app.include_router(user_v4_router)
app.include_router(scanner_v4_router)
app.include_router(notification_v4_router)
app.include_router(websocket_router)


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
