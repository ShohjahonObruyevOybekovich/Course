import logging
from datetime import datetime, timedelta

from celery import shared_task

from account.models import CustomUser
from bot.tasks import TelegramBot
from .models import Idioms

bot = TelegramBot()
logger = logging.getLogger(__name__)


@shared_task
def check_daily_tasks():
    idioms = Idioms.objects.all()

    now = datetime.now().time()
    one_minute_ago = (datetime.now() - timedelta(minutes=1)).time()

    for idiom in idioms:
        time = idiom.time

        if one_minute_ago <= time <= now:

            students = CustomUser.objects.all()

            for student in students:
                text = f"""
                📘 <b>Kun hikmati</b>

                <i>{idiom.text}</i>

                """.strip()
                # 💡 < b > Meaning < / b >: {idiom.meaning}
                bot.send_message(student.chat_id, text=text)

    logger.info("Completed checking daily tasks for expiration.")
