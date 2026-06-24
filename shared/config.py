import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()
from sqlalchemy.ext.asyncio import create_async_engine  

LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_PASSWORD = os.getenv("DB_PASSWORD")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "DocuAI dev"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    secret_key: str = "DocuAISecretKey"
    internal_api_key: str = "DocuAIInternalKey"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "DocuAI"
    postgres_user: str = "postgres"
    postgres_password: str = DB_PASSWORD
    # LangSmith
    langchain_tracing_v2: str = "false"
    langchain_endpoint: str = "https://api.smith.langchain.com"
    langchain_api_key: str = LANGCHAIN_API_KEY
    langchain_project: str = "DocuAI"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )

    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    aws_region: str = "us-east-1"
    aws_s3_bucket: str = "DocuAI-Bucket"

    openai_api_key: str = OPENAI_API_KEY


settings = Settings()

engine = create_async_engine(
    settings.database_url, echo=False, pool_pre_ping=True, connect_args={"ssl": False}
)