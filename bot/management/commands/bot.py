import asyncio
import logging
import sys
import traceback

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
    print(f"[Startup] Setting webhook: {WEBHOOK_URL}")
    await bot.set_webhook(WEBHOOK_URL)
    print("[Startup] Webhook set successfully!")

async def main():
    try:
        bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
        app = web.Application()

        SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot, on_startup=on_startup)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host="0.0.0.0", port=8080)
        await site.start()

        print("[Webhook] Bot webhook server started at http://0.0.0.0:8080")
        print(f"[Webhook] Listening for updates on {WEBHOOK_PATH}")
        await asyncio.Event().wait()

    except Exception as e:
        print(f"[Fatal Error] {type(e).__name__}: {e}")
        traceback.print_exc()
