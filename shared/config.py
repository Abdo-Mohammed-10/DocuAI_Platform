from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        )
    
    # APP
    APP_NAME: str = "DocuAI dev"
    APP_VERSION: str = "0.1.0"
    APP_DESCRIPTION: str = "A document processing and question-answering system using AI."
    SeCRET_KEY: str : ""
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "DocuAI_db"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:"
            f"{self.postgres_password}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )
        
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # AWS
    aws_region: str = "us-east-1"
    aws_s3_bucket: str = "DocuAI-Bucket"
    # LLM
    openai_api_key: str = ""

settings = Settings()