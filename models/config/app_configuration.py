from pydantic import BaseModel
from typing import Literal


class AppFieldConfiguration(BaseModel):
    name: str
    version: str
    environment: Literal['development', 'production']


class DataSourceFieldConfiguration(BaseModel):
    path: str
    

class AppConfiguration(BaseModel):
    app: AppFieldConfiguration
    datasource: DataSourceFieldConfiguration