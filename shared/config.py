from pydantic_settings import BaseSettings, SettingsConfigDict


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
    SECRET_KEY: str = "DocuAISecretKey"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "DocuAI"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

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

    openai_api_key: str = ""


settings = Settings()
