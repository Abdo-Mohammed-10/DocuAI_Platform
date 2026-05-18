from shared.config import settings


def test_settings_loading():
    assert settings.postgres_db == "DocuAI_db"
    assert settings.redis_port == 6379

def test_database_url_format():
    url = settings.database_url
    assert url.startswith("postgresql+asyncpg://")

def test_redis_url_format():
    url = settings.redis_url
    assert url.startswith("redis://")