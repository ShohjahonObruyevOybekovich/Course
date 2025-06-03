from os import getenv
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from decouple import config

TOKEN = config("BOT_TOKEN")


print(TOKEN)

dp = Dispatcher(storage=MemoryStorage())