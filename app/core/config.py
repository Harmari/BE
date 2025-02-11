# app/core/config.py
from pydantic_settings import BaseSettings
from datetime import datetime
import pytz
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_NAME: str
    DB_PW: str
    DB_USER: str

    # Google OAuth
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # JWT
    SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # kakopay
    KAKAO_PAY_CLIENT_ID: str
    KAKAO_PAY_CLIENT_SECRET: str
    KAKAO_PAY_SECRET_KEY_DEV: str
    KAKAO_PAY_API_HOST: str

    class Config:
        env_file = 'real.env'
        env_file_encoding = 'utf-8'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        encoded_user = quote_plus(self.DB_USER)
        encoded_pw = quote_plus(self.DB_PW)
        self.DATABASE_URL = f"mongodb://{encoded_user}:{encoded_pw}@{self.DATABASE_URL}/{self.DATABASE_NAME}?authSource=admin"

    @property
    def CURRENT_DATETIME(self) -> str:
        kst = pytz.timezone('Asia/Seoul')
        return datetime.now(kst).isoformat()


settings = Settings()
