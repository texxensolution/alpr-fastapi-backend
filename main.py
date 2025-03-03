import uvicorn
from fastapi import FastAPI
from src.api.v1.accounts import router as accounts_router
from src.api.v1.log_router import router as log_router
from src.api.v1.user import router as user_router
from src.api.v4.auth import router as user_v4_router
from src.api.v3.scanner import router as scanner_router
from src.api.v4.scanner import router as scanner_v4_router
from src.api.v3.status import router as users_status_router
from src.ws.status import router as ws_status_router
from src.core.dependencies import settings


app = FastAPI()

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
