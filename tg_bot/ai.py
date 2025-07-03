import json
import re
from datetime import datetime
import os

from decouple import config
from openai import AsyncOpenAI
from django.utils import timezone
from icecream import ic


class GptFunctions:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=config("AI_TOKEN"))

    def load_instruction(self) -> str:

        file_path = "tg_bot/instruction.txt"

        with open(file_path, "r", encoding="utf-8") as f:
            template = f.read()

        return template

    async def prompt_to_json(self, user_id, text: str):
        instruction = self.load_instruction()

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": instruction},
                {"role": "user", "content": text},
            ],
            temperature=0.2,
        )

        raw_content = response.choices[0].message.content.strip()
        ic("RAW GPT OUTPUT:", raw_content)

        if raw_content.startswith("```"):
            raw_content = re.sub(r"^```(?:json)?\n?", "", raw_content)
            raw_content = re.sub(r"\n?```$", "", raw_content)

        try:
            result = json.loads(raw_content)
            return result

        except json.JSONDecodeError as e:
            ic("❌ JSON decoding failed:", e)
            return {"action": ""}
