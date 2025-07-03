import os
import tempfile
import subprocess

import openai
import parselmouth  # For pitch/intonation analysis
from aiogram import Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from icecream import ic

from account.models import CustomUser
from dispatcher import dp, TOKEN
from tg_bot.ai import GptFunctions
from tg_bot.buttons.reply import user_menu
from tg_bot.state.main import Theme_State
from theme.models import Theme

# Set OpenAI API key
openai.api_key = os.getenv("AI_TOKEN")

bot = Bot(token=TOKEN)
gpt = GptFunctions()


def stt(path_to_audio: str) -> dict:
    try:
        with open(path_to_audio, "rb") as audio_file:
            return openai.Audio.transcribe(
                file=audio_file,
                model="whisper-1",
                language="de"
            )
    except Exception as e:
        ic(e)
        return {"text": ""}


def analyze_pitch(path: str) -> dict:
    try:
        snd = parselmouth.Sound(path)
        pitch = snd.to_pitch()
        values = pitch.selected_array['frequency']
        values = values[values > 0]  # Filter out 0s
        if not values.any():
            return {"avg_pitch": 0, "variation": "flat"}
        return {
            "avg_pitch": float(values.mean()),
            "variation": "normal" if values.std() > 20 else "flat"
        }
    except Exception as e:
        ic(e)
        return {"avg_pitch": 0, "variation": "error"}


def detect_repetition(text: str) -> list:
    words = text.lower().split()
    return [words[i] for i in range(len(words) - 1) if words[i] == words[i + 1]]


@dp.callback_query(lambda call: call.data.startswith("sprechen_"))
async def voice_callback_handler(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)

    try:
        theme_id = call.data.split("_")[1]
    except IndexError:
        return await call.message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

    theme = Theme.objects.filter(id=theme_id).first()
    if theme is None:
        return await call.message.answer("Mavzu topilmadi.")

    theme_sprechen = theme.sprechen
    if theme_sprechen:
        await state.update_data(sprechen=theme_sprechen, sprechen_active=True)

        text = f"*{theme_sprechen}* mavzusidagi sprechen uchun uz ovozli xabaringizni yuboring 👇"
        await call.message.answer(text, parse_mode="Markdown")
    else:
        await call.message.answer("Ushbu mavzu uchun sprechen topshirig'i topilmadi.")



@dp.message(F.content_type == types.ContentType.VOICE)
async def handle_voice(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("sprechen_active"):
        return await message.answer(
            text="Bu ovozli xabar qabul qilinmadi. Iltimos, sprechen topshirig'ini tanlang va qaytadan yuboring.",
            parse_mode="Markdown"
        )

    user_id = message.from_user.id
    voice = message.voice

    temp_dir = tempfile.gettempdir()
    ogg_path = os.path.join(temp_dir, f"voice_{user_id}.ogg")
    mp3_path = ogg_path.replace(".ogg", ".mp3")

    file = await bot.get_file(voice.file_id)
    voice_data = await bot.download_file(file.file_path)
    with open(ogg_path, "wb") as f:
        f.write(voice_data.read())

    subprocess.run(["ffmpeg", "-y", "-i", ogg_path, "-ar", "16000", "-ac", "1", mp3_path], capture_output=True)
    if not os.path.exists(mp3_path):
        return await message.answer("❌ Failed to convert audio.")

    stt_result = stt(mp3_path)
    text = stt_result.get("text", "").strip()
    repetitions = detect_repetition(text)
    pitch = analyze_pitch(mp3_path)

    ic(text, repetitions, pitch)

    if not text:
        return await message.reply("❌ Menga tushunarli ovoz topilmadi. Qayta urinib ko‘ring.", reply_markup=user_menu())

    prompt = (
        f"User's transcribed German speech: \"{text}\"\n"
        f"Repeated words: {repetitions}\n"
        f"Pitch analysis: average pitch = {pitch['avg_pitch']}, variation = {pitch['variation']}\n\n"
        "Give detailed feedback on pronunciation, repeated words, and intonation. "
        "Assume the user is learning German and wants friendly, constructive feedback."
    )
    feedback = await gpt.prompt_to_json(str(user_id), prompt)

    await message.reply(
        text=f"🗣 Transcribed: {text}\n\n🧠 Feedback:\n{feedback}",
        reply_markup=user_menu()
    )

    # ✅ Optional: reset the state after one submission
    await state.clear()

