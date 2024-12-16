from fastapi import APIRouter, UploadFile, File, Depends, Form, status, HTTPException
from utils.dependencies import get_account_status
import polars as pl
from io import StringIO
from utils.account_status import AccountStatus
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1", tags=['Accounts'])


class UpdateAccountResponse(BaseModel):
    message: str
    records_size: int


@router.put("/accounts")
async def update_accounts(
    password: str = Form(...),
    csv_file: UploadFile = File(...),
    account_status: AccountStatus = Depends(get_account_status)
):
    if password != "update_records":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong password"
        )

    contents = await csv_file.read()

    csv_string = StringIO(contents.decode("utf-8"))

    df = pl.read_csv(csv_string)

    account_status.update_account_records(df)

    return UpdateAccountResponse(
        message="Successfully updated the 'accounts.csv'",
        records_size=len(df)   
    )

    
