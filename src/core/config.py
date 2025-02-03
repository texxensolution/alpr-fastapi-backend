from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    # Lark Base
    CHOPPER_APP_ID: str
    CHOPPER_APP_SECRET: str
    BASE_LOGS_APP_TOKEN: str
    MAIN_GC_ID: str

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int

    # Postgres env
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str

    ENDORSEMENT_FILE_PATH: str

    # App port
    APP_PORT: int

    class Config:
        env_file: str = ".env"
