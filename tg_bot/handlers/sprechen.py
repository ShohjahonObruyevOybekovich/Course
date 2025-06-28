import os

from aiogram import Bot, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from icecream import ic

from account.models import CustomUser
from dispatcher import dp, TOKEN
from tg_bot.ai import GptFunctions
from tg_bot.state.main import User

bot = Bot(token=TOKEN)
gpt = GptFunctions()



@dp.message(lambda msg: not msg.voice and msg.text and msg.text.isalnum())
async def ask_for_voice(msg: Message):
    await msg.answer("Menga ovozli xabar yuboring ...")


# Voice message handler

@dp.message(F.content_type == types.ContentType.VOICE)
async def handle_voice(message: Message, bot: Bot):
    # Save voice to file

    file = await bot.get_file(message.voice.file_id)
    file_path = f"voice_{message.from_user.id}.ogg"
    destination_path = file_path.replace(".ogg", ".mp3")
    ic(file_path)

    file_bytes = await bot.download_file(file.file_path)
    with open(file_path, "wb") as f:
        f.write(file_bytes.read())

    # Convert to MP3 using ffmpeg
    os.system(f"ffmpeg -i {file_path} -ar 16000 -ac 1 {destination_path}")

    if not os.path.exists(destination_path):
        await message.answer("❌ Failed to convert audio.")
        return

    # Transcribe audio
    result = stt(destination_path)
    text = result.get("result", {}).get("text") if isinstance(result, dict) else result

    lang_user = CustomUser.objects.filter(chat_id=message.from_user.id).first()

    await message.reply(
        text=f"{get_text(lang_user, 'message')} : {text}",
        reply_markup=cancel(lang=lang_user, id=message.from_user.id),
    )

    if not text:
        await message.reply(get_text(lang_user, "unknown_command"))
        return

    intent_result = await gpt.prompt_to_json(str(message.from_user.id), text)
    ic(intent_result)

    responses = []

    if isinstance(intent_result, list):
        for entry in intent_result:
            result = await route_intent(message.from_user.id, entry)
            if isinstance(result, BufferedInputFile):
                await message.answer_document(result, caption="📊 Hisobot tayyor!")
            elif result:
                responses.append(result)
    else:
        result = await route_intent(message.from_user.id, intent_result)
        if isinstance(result, BufferedInputFile):
            await message.answer_document(result, caption="📊 Hisobot tayyor!")
        elif result:
            responses.append(result)

    for chunk in responses:
        await message.answer(chunk)

    # Cleanup
    for path in [file_path, destination_path]:
        try:
            os.remove(path)
        except FileNotFoundError:
            pass