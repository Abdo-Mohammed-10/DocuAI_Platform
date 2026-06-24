from celery import Celery

from shared.config import settings

celery_app = Celery(
    "smart_doc",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "services.ingestion_service.tasks.celery_tasks",
    ],
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # retry failed tasks
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # result expiry
    result_expires=3600,
)
