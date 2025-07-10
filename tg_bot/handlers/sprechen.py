import asyncio
import os
import subprocess
import tempfile

import parselmouth  # For pitch/intonation analysis
from aiogram import Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from icecream import ic
from openai import OpenAI  # ✅ Updated import for new API

from account.models import CustomUser
from dispatcher import dp, TOKEN
from studentcourse.models import UserTasks
from tg_bot.ai import GptFunctions
from tg_bot.buttons.reply import user_menu
from tg_bot.utils import format_sriben_result
from theme.models import Theme

# ✅ Instantiate OpenAI client
client = OpenAI(api_key=os.getenv("AI_TOKEN"))

bot = Bot(token=TOKEN)
gpt = GptFunctions()


def stt(path_to_audio: str) -> dict:
    try:
        with open(path_to_audio, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="de"
            )
        return {"text": transcript.text}
    except Exception as e:
        ic(e)
        return {"text": ""}


def analyze_pitch(path: str) -> dict:
    try:
        snd = parselmouth.Sound(path)
        pitch = snd.to_pitch()
        values = pitch.selected_array['frequency']
        values = values[values > 0]  # Filter out unvoiced frames (zeros)
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
        await state.update_data(sprechen=theme_sprechen, sprechen_active=True, theme_id=theme.id)

        text = f"*{theme_sprechen}* mavzusidagi sprechen uchun uz ovozli xabaringizni yuboring 👇"
        await call.message.answer(text, parse_mode="Markdown")
    else:
        await call.message.answer("Ushbu mavzu uchun sprechen topshirig'i topilmadi.")


from tg_bot.buttons.inline import return_theme


@dp.message(F.content_type == types.ContentType.VOICE)
async def handle_voice(message: Message, state: FSMContext):
    data = await state.get_data()
    if not data.get("sprechen_active"):
        return await message.answer(
            text="⚠️ Bu ovozli xabar qabul qilinmadi. Iltimos, *sprechen* topshirig'ini tanlang va qaytadan yuboring.",
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
        return await message.answer("❌ Ovozni formatga o‘tkazishda xatolik.")

    # 🎧 Loading animation
    loading_msg = await message.answer("🎧 Ovoz qabul qilindi. Tahlilga tayyorlanmoqda...")
    await asyncio.sleep(1)
    await loading_msg.edit_text("🧠 Tahlil qilinmoqda.")
    await asyncio.sleep(0.7)
    await loading_msg.edit_text("🧠 Tahlil qilinmoqda..")
    await asyncio.sleep(0.7)
    await loading_msg.edit_text("🧠 Tahlil qilinmoqda...")

    # 🎙️ Speech Analysis
    stt_result = stt(mp3_path)
    text = stt_result.get("text", "").strip()
    repetitions = detect_repetition(text)
    pitch = analyze_pitch(mp3_path)

    # ❌ No valid text
    if not text:
        await loading_msg.delete()
        return await message.reply("❌ Menga tushunarli ovoz topilmadi. Qayta urinib ko‘ring.", reply_markup=user_menu())

    await loading_msg.edit_text("✅ Tahlil yakunlandi!")

    await message.answer(f"🗣 *Sizning nutqingiz:*\n`{text}`", parse_mode="Markdown")
    theme_id = data.get("theme_id")
    theme = Theme.objects.filter(id=theme_id).first()

    theme_sprechen = theme.sprechen
    # 🧠 GPT feedback
    prompt = (
        f"Speach theme : {theme_sprechen}\n"
        f"User's transcribed German speech: \"{text}\"\n"
        f"Repeated words: {repetitions}\n"
        f"Pitch analysis: average pitch = {pitch['avg_pitch']}, variation = {pitch['variation']}\n\n"
        "Give detailed feedback on pronunciation, repeated words, and intonation. "
        "Assume the user is learning German and wants friendly, constructive feedback."
    )
    feedback = await gpt.prompt_to_json(str(user_id), prompt)

    user = CustomUser.objects.filter(chat_id=user_id).first()

    formate = ""
    if feedback:
        formate = format_sriben_result(feedback)
        ball = feedback.get("gesamtpunktzahl")
        has_done = UserTasks.objects.filter(user=user, choice="Sprichen", theme=theme).exists()

        if not has_done and ball:
            UserTasks.objects.create(user=user, choice="Sprichen", ball=ball, theme=theme)
            user.balance += int(ball)
            user.save()

        formate += f"\n\n💸 *Vazifa uchun ball:* `{ball}`"
        formate += f"\n📈 <b>Jami ballaringiz:</b> <code>{user.balance}</code>"

    motivational = f"\n\n📚 *Mavzu:* {theme.name}\n🔥 Ajoyib harakat! Har bir gap sizni B1 darajaga yaqinlashtiradi."

    await message.answer(
        text=formate + motivational,
        reply_markup=return_theme(theme.id),
        parse_mode="HTML"
    )

    await state.clear()
