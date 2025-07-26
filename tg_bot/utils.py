
import hmac
import hashlib
from urllib.parse import parse_qsl

from decouple import config

BOT_TOKEN=config("BOT_TOKEN")

def format_phone_number(phone_number: str) -> str:
    # Remove all non-digits
    cleaned = ''.join(c for c in phone_number if c.isdigit())

    # Log what came in
    print(f"📞 Received raw number: {phone_number}, cleaned: {cleaned}")

    # Add +998 if needed
    if cleaned.startswith('998'):
        formatted = '+' + cleaned
    elif len(cleaned) == 9 and cleaned.startswith('9'):
        # assume local number like '901234567'
        formatted = '+998' + cleaned
    else:
        raise ValueError(f"Invalid phone number length or format: {phone_number}")

    if len(formatted) != 13:
        raise ValueError(f"Invalid phone number length after formatting: {formatted}")

    return formatted


def extract_and_split_init_data(init_data: str):
    parsed = dict(parse_qsl(init_data, strict_parsing=True))
    received_hash = parsed.pop("hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
    return data_check_string, received_hash


def compute_telegram_hash(data_check_string: str):
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=BOT_TOKEN.encode(),
        digestmod=hashlib.sha256
    ).digest()
    return hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()



from typing import Union
from aiogram.exceptions import TelegramBadRequest

async def check_user_in_channel(user_id: int, chat_id: Union[str, int], bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramBadRequest as e:
        print(f"❌ TelegramBadRequest in check_user_in_channel({chat_id}): {e}")
        return False




import mimetypes
from aiogram.types import InputFile,Message

async def send_theme_material(message: Message, theme):
    materials = theme.materials.all()

    if not materials.exists():
        return

    for material in materials:
        if not material.file:
            continue

        file_path = material.file.path
        mime_type, _ = mimetypes.guess_type(file_path)
        input_file = InputFile(file_path)

        if mime_type:
            if mime_type.startswith("image/"):
                await message.answer_photo(photo=input_file, caption="🖼 Rasm material")
            elif mime_type.startswith("video/"):
                await message.answer_video(video=input_file, caption="🎥 Video material")
            elif mime_type.startswith("audio/"):
                await message.answer_audio(audio=input_file, caption="🎧 Audio material")
            else:
                await message.answer_document(document=input_file, caption="📄 Material yuklab olish")
        else:
            await message.answer_document(document=input_file, caption="📎 Material")


def format_schreiben_result(data: dict) -> str:
    return (
        f"📝 *Schreiben natijalaringiz:*\n\n"
        f"🏗 *Tuzilishi (Aufbau):* {data.get('aufbau', 0)}/5\n"
        f"✍️ *Grammatika (Sprachrichtigkeit):* {data.get('sprachrichtigkeit', 0)}/5\n"
        f"🧠 *So'z boyligi (Wortschatz):* {data.get('wortschatz', 0)}/5\n"
        f"✅ *Topshiriqni bajarish (Aufgabenbearbeitung):* {data.get('aufgabenbearbeitung', 0)}/5\n"
        f"📊 *Umumiy ball:* {data.get('gesamtpunktzahl', 0)}/5\n"
        f"🎖 *Baholash:* {data.get('bewertung', '-')}\n\n"
        f"💬 *Izoh (o‘zbek tilida):*\n_{data.get('comment', '')}\n"
    )

def format_sriben_result(data: dict) -> str:
    return (
        f"📝 *Sprechen natijalaringiz:*\n\n"
        f"🏗 *Tuzilishi (Aufbau):* {data.get('aufbau', 0)}/5\n"
        f"✍️ *Grammatika (Sprachrichtigkeit):* {data.get('sprachrichtigkeit', 0)}/5\n"
        f"🧠 *So'z boyligi (Wortschatz):* {data.get('wortschatz', 0)}/5\n"
        f"✅ *Topshiriqni bajarish (Aufgabenbearbeitung):* {data.get('aufgabenbearbeitung', 0)}/5\n"
        f"📊 *Umumiy ball:* {data.get('gesamtpunktzahl', 0)}/5\n"
        f"🎖 *Baholash:* {data.get('bewertung', '-')}\n\n"
        f"💬 *Izoh (o‘zbek tilida):*\n_{data.get('comment', '')}\n"
    )