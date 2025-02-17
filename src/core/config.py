from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
    # Lark Base
    CHOPPER_APP_ID: str
    CHOPPER_APP_SECRET: str
    BASE_LOGS_APP_TOKEN: str
    MAIN_GC_ID: str
    LOGS_TABLE_ID: str

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
    JWT_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    JWT_ALGORITHM: str = 'HS256'

    class Config:
        env_file: str = ".env"


settings = Settings()