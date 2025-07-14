import asyncio
import logging
import sys
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from django.core.management import BaseCommand

from bot.management.commands.set_webhook import BASE_URL
from tg_bot.handlers import *  # make sure all routers are registered
from dispatcher import TOKEN, dp

WEBHOOK_URL = f"{BASE_URL}/bot/webhook/"  # Replace with your actual public URL

async def main():
    bot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Set webhook
    await bot.set_webhook(WEBHOOK_URL)

    # Start webhook (no polling)
    await dp.start_webhook(
        webhook_path="/bot/webhook/",
        bot=bot,
        on_startup=None,
        on_shutdown=None,
        skip_updates=True,
        host="0.0.0.0",
        port=8000,
    )

class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
