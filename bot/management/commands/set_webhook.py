import asyncio

from decouple import config
from django.core.management.base import BaseCommand
from aiogram import Bot
from dispatcher import TOKEN

BASE_URL = config("BASE_URL")


async def set_webhook():
    async with Bot(TOKEN) as bot:
        webhook_url = f"{BASE_URL}/bot/webhook/"
        await bot.set_webhook(webhook_url)


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        asyncio.run(set_webhook())
        self.stdout.write("Webhook set!")
