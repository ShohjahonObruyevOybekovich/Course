import os

import openai  # ✅ New import
from aiogram import Bot, F, types
from aiogram.types import Message
from icecream import ic

from account.models import CustomUser
from dispatcher import dp, TOKEN
from tg_bot.ai import GptFunctions
from tg_bot.buttons.reply import user_menu

# 🔐 Set your OpenAI API key
openai.api_key = os.getenv("AI_TOKEN")  # Or hard-code for testing

bot = Bot(token=TOKEN)
gpt = GptFunctions()


# @dp.message(lambda msg: not msg.voice and msg.text and msg.text.isalnum())
# async def ask_for_voice(msg: Message):
#     await msg.answer("Menga ovozli xabar yuboring ...")


# ✅ Whisper STT function (German)
def stt(path_to_audio: str) -> dict:
    try:
        with open(path_to_audio, "rb") as audio_file:
            response = openai.Audio.transcribe(
                file=audio_file,
                model="whisper-1",
                language="de"  # German
            )
        return response
    except Exception as e:
        ic(e)
        return {"text": ""}


@dp.message(F.content_type == types.ContentType.VOICE)
async def handle_voice(message: Message):
    user_id = message.from_user.id
    file = await bot.get_file(message.voice.file_id)

    file_path = f"voice_{user_id}.ogg"
    destination_path = file_path.replace(".ogg", ".mp3")
    ic(file_path)

    # ✅ Download voice file
    file_bytes = await bot.download_file(file.file_path)
    with open(file_path, "wb") as f:
        f.write(file_bytes.read())

    # ✅ Convert to MP3 (required by OpenAI)
    os.system(f"ffmpeg -i {file_path} -ar 16000 -ac 1 {destination_path}")

    if not os.path.exists(destination_path):
        await message.answer("❌ Failed to convert audio.")
        return

    # ✅ Transcribe with Whisper
    result = stt(destination_path)
    text = result.get("text")
    ic(text)

    lang_user = CustomUser.objects.filter(chat_id=user_id).first()

    await message.reply(
        text=f"Response : : {text}",
        reply_markup=user_menu()
    )

    if not text:
        await message.reply("unnown command", user_menu())
        return

    # ✅ Pass transcribed text to GPT
    intent_result = await gpt.prompt_to_json(str(user_id), text)
    ic(intent_result)

    responses = []
    await message.reply(
        text=f"Response : : {intent_result}",
        reply_markup=user_menu()
    )
