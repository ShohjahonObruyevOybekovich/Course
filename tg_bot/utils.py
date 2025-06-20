
import hmac
import hashlib
from urllib.parse import parse_qsl

from decouple import config

BOT_TOKEN=config("BOT_TOKEN")

def format_phone_number(phone_number: str) -> str:

    phone_number = ''.join(c for c in phone_number if c.isdigit())

    # Prepend +998 if missing
    if phone_number.startswith('998'):
        phone_number = '+' + phone_number
    elif not phone_number.startswith('+998'):
        phone_number = '+998' + phone_number

    # Check final phone number length
    if len(phone_number) == 13:
        return phone_number
    else:
        raise ValueError("Invalid phone number length")


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

from aiogram.exceptions import TelegramBadRequest

async def check_user_in_channel(user_id: int, channel_username: str, bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=f"@{channel_username}", user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except TelegramBadRequest:
        return False



import mimetypes
from aiogram.types import InputFile,Message

async def send_theme_material(message: Message, theme):
    if not theme.materials or not theme.materials.file:
        return

    file_path = theme.materials.file.path  # assumes file is stored locally
    file_url = theme.materials.file.url

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
