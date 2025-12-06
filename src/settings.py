import fnmatch
import os
import re
from enum import StrEnum
from typing import Annotated

from pydantic import Field, PostgresDsn, ValidationInfo, field_validator, BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict
from starlette.config import Config as StarletteConfig

from src.utils.files import ensure_exists


# The @property decorator is used to define methods that can be accessed like attributes.


class Environment(StrEnum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
    sandbox = "sandbox"
    production = "production"

class Settings(BaseSettings):
    ENV: Environment = Field(Environment.DEVELOPMENT, validation_alias="ASKOBI_ENV")
    DEBUG: bool = False
    LOG_LEVEL: str = "DEBUG"
    ROOT_PATH: str = ""
    DATADIR: str = Field(default="data", validation_alias="DATADIR")

    SENTRY_DSN: str | None = None

    IS_WORKER: bool = False
    LOG_FILE_NAME: str | None = Field(None, validation_alias="LOG_FILE")

    # Auth Settings
    AUTH_JWT_SECRET_KEY: str = Field(..., validation_alias="AUTH_JWT_SECRET_KEY")
    AUTH_JWT_ALGORITHM: str = "HS256"
    AUTH_JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived for HIPAA compliance
    AUTH_JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    AUTH_PASSWORD_SALT: str = Field(..., validation_alias="AUTH_PASSWORD_SALT")
    AUTH_PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 48  # 48 hours
    AUTH_EMAIL_VERIFY_TOKEN_EXPIRE_HOURS: int = 48  # 48 hours
    AUTH_CORS_ORIGINS: list[str] = Field(default=["http://localhost", "http://localhost:3000"])
    AUTH_TRUSTED_CLIENTS: list[str] = Field(default=[])

    @field_validator("AUTH_CORS_ORIGINS", "AUTH_TRUSTED_CLIENTS", mode="before")
    @classmethod
    def parse_comma_separated(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, list):
            return v
        if not v or not v.strip():
            return []
        return [item.strip() for item in v.split(",") if item.strip()]
    AUTH_ENABLE_EMAIL_VERIFICATION: bool = True
    AUTH_ENABLE_PASSWORD_RESET: bool = True
    AUTH_ENABLE_USER_REGISTRATION: bool = True

    DB_USER: str = "askobi_user"
    DB_PASSWORD: str = "askobi_password"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_DATABASE: str = Field(default="askobi_db", validation_alias="DB_DATABASE")
    DB_POOL_SIZE: int = 5
    DB_POOL_RECYCLE_SECONDS: int = 600  # 10 minutes to prevent "server closed the connection" errors
    

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    SENTRY_DSN: str | None = None

    model_config = SettingsConfigDict(
        env_file="src/conf/.env",
        extra="ignore"
    )

    config: StarletteConfig = Field(
        default_factory=lambda: StarletteConfig("src/conf/.env" if os.path.exists("src/conf/.env") else None)
    )

    # Database URL property
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            user=self.DB_USER,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=str(self.DB_PORT),
            path="/askobi_db",
        )
    
    @property
    def log_file(self) -> str | None:
        if not self.LOG_FILE_NAME:
            return None
        return os.path.join(self.log_dir, self.LOG_FILE_NAME)
    
    @property
    def log_file_regex(self) -> re.Pattern[str] | None:
        if not self.LOG_FILE_NAME:
            return None
        filename_no_ext, _, file_extension = self.LOG_FILE_NAME.partition(".")
        return re.compile(fnmatch.translate(f"{filename_no_ext}*{file_extension}"))

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @field_validator("DB_DATABASE", mode="before")
    @classmethod
    def validate_db_database(cls, v: str, info: ValidationInfo) -> str:
        env = info.data.get("ENV", Environment.DEVELOPMENT)
        if env == Environment.TESTING:
            return "askobi_test_db"
        return v

    @property
    def files_dir(self) -> str:

        path = os.path.join(self.DATADIR, "files")
        ensure_exists(path)
        return path

    @property
    def log_dir(self) -> str:

        path = os.path.join(self.DATADIR, "logs")
        ensure_exists(path)
        return path
    
    def build_postgres_dsn(self, db_name: str | None = None, driver: str = "asyncpg") -> str:
        return str(
            PostgresDsn.build(
                scheme=f"postgresql+{driver}",
                username=self.DB_USER,
                password=self.DB_PASSWORD,
                host=self.DB_HOST,
                port=int(self.DB_PORT),
                path=self.DB_DATABASE if db_name is None else db_name,
            )
        )
    
    @property
    def postgres_dsn(self) -> str:
        return self.build_postgres_dsn()
    
    def is_environment(self, envs: set[Environment]) -> bool:
        return self.ENV in envs
    
    def is_production(self) -> bool:
        return self.ENV == Environment.PRODUCTION
    
    def is_development(self) -> bool:
        return self.ENV == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        return self.ENV == Environment.TESTING