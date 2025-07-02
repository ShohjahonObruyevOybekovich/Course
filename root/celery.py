import os
from celery.schedules import crontab
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "root.settings")

app = Celery("root")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # Frequent tasks (Runs every minute)
    "send-daily-messages": {
        "task": "idioms.tasks.check_daily_tasks",
        "schedule": crontab(minute="*/1"),
    }
}


app.conf.timezone = "Asia/Tashkent"
