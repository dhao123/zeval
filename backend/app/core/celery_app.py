"""
Celery configuration for async tasks.
"""
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "zkh_bench",
    broker=settings.celery_broker_url,
    backend=settings.celery_backend_url,
    include=["app.tasks.export_tasks"]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    
    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 min soft limit
    
    # Result backend settings
    result_expires=86400,  # Results expire after 24 hours
    result_extended=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,  # Process one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    
    # Queue settings
    task_default_queue="default",
    task_routes={
        "app.tasks.export_tasks.*": {"queue": "export"},
    },
    
    # Broker settings
    broker_connection_retry_on_startup=True,
    broker_heartbeat=30,
)

# Beat schedule (for periodic tasks)
celery_app.conf.beat_schedule = {
    "cleanup-expired-exports": {
        "task": "app.tasks.export_tasks.cleanup_expired_exports",
        "schedule": 3600.0,  # Run every hour
    },
}


def get_celery_app():
    """Get Celery app instance."""
    return celery_app
