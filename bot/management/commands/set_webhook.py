import asyncio

from decouple import config
from django.core.management.base import BaseCommand
from aiogram import Bot
from dispatcher import TOKEN
BASE_URL = config('BASE_URL')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        bot = Bot(TOKEN)
        webhook_url = f"{BASE_URL}/bot/webhook/"
        asyncio.run(bot.set_webhook(webhook_url))
        self.stdout.write("Webhook set!")
