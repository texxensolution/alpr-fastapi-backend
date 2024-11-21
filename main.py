from fastapi import FastAPI, Form, File, UploadFile
from pydantic import BaseModel
from utils.get_app_configuration import get_app_configuration
from utils.account_status import AccountStatus
from typing import List
from models.account import Account

app = FastAPI()

app_config = get_app_configuration()

account_status = AccountStatus(
    path=app_config.datasource.path
)


class LicensePlateStatusResponse(BaseModel):
    plate_number: str
    is_similar: bool
    accounts: List[Account]



@app.post('/api/license-plate-status', response_model=LicensePlateStatusResponse)
async def license_plate_status(
    plate_number: str = Form(...),
    image: UploadFile = File(...)
):
    print(f"Received Plate Number: {plate_number}")
    print(f"Received File: {image.filename}")

    if account := account_status.get_account_info_by_plate(plate_number):
        return LicensePlateStatusResponse(
            plate_number=plate_number,
            is_similar=False,
            accounts=[account]
        )
    elif similar_accounts := account_status.get_similar_accounts_by_plate(plate_number):
        return LicensePlateStatusResponse(
            plate_number=plate_number,
            is_similar=True,
            accounts=similar_accounts
        )
    else:
        return LicensePlateStatusResponse(
            plate_number=plate_number,
            is_similar=False,
            accounts=[]
        )

