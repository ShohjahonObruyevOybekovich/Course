import asyncio
import logging
import sys
from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from django.core.management import BaseCommand

from bot.management.commands.set_webhook import BASE_URL
from dispatcher import TOKEN, dp
from tg_bot.handlers import *


WEBHOOK_PATH = "/bot/webhook/"
WEBHOOK_URL = f"{BASE_URL}{WEBHOOK_PATH}"  # replace with real domain

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)

async def main():
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    # Create aiohttp app
    app = web.Application()

    # Register Aiogram webhook handler
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)

    # Setup aiogram + aiohttp
    setup_application(app, dp, bot=bot, on_startup=on_startup)

    # Run aiohttp app (this replaces start_polling/start_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=8080)  # match Docker port
    await site.start()

    print("Bot webhook running...")

    # Run forever
    await asyncio.Event().wait()

class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        asyncio.run(main())
