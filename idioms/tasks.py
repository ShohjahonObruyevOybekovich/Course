import logging
from datetime import datetime, timedelta

from celery import shared_task

from account.models import CustomUser
from bot.tasks import TelegramBot
from .models import Idioms

bot = TelegramBot()
logger = logging.getLogger(__name__)

import random
@shared_task
def check_daily_tasks():
    now = datetime.now().time()
    one_minute_ago = (datetime.now() - timedelta(minutes=1)).time()

    # Filter idioms scheduled for now (roughly)
    current_idioms = Idioms.objects.filter(time__gte=one_minute_ago, time__lte=now)

    if not current_idioms.exists():
        logger.info("No idioms scheduled at this time.")
        return

    students = CustomUser.objects.exclude(chat_id=None)

    for student in students:
        idiom = random.choice(list(current_idioms))

        text = idiom.text

        try:
            bot.send_message(student.chat_id, text=text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send idiom to user {student.id}: {e}")

    logger.info("✅ Sent daily idioms to all users.")

