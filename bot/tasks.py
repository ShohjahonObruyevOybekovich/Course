import os
import logging

from decouple import config
from requests import post


from icecream import ic

# load_dotenv()
# Celery setup
# app = Celery('tasks', broker='redis://localhost:6378/0')
token = config("BOT_TOKEN")
# Logger setup
logging.basicConfig(level=logging.INFO)


class TelegramBot:
    HOST = "https://api.telegram.org/bot"

    def __init__(self):
        # Get token from environment variables



        if not token:
            raise ValueError("Telegram bot TOKEN is missing! Set the TOKEN environment variable.")
        self.base_url = self.HOST + token

    def send_message(
            self,
            chat_id,
            text,
            reply_markup=None,
            parse_mode="HTML",
    ):
        """
        Sends a message via Telegram Bot API.
        """
        url = self.base_url + "/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        if reply_markup:
            try:
                data["reply_markup"] = reply_markup.to_json()
            except Exception as e:
                logging.error(f"Failed to serialize reply_markup: {e}")
                return

        try:
            ic(f"Sending message to chat_id={chat_id}, text={text}")
            res = post(url, json=data)
            res.raise_for_status()  # Raises HTTPError for bad responses (4xx, 5xx)
            logging.info(f"Message sent successfully to chat_id {chat_id}")
        except Exception as e:
            logging.error(f"Failed to send message to chat_id {chat_id}: {e}")



# Instantiate the Telegram bot
bot = TelegramBot()

