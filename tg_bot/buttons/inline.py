from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from decouple import config

from transaction.models import Transaction


def degree():
    payment_date = InlineKeyboardButton(text="✏️ Sanani o'zgartirish", callback_data="Sanani o'zgartirish")
    accept = InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="accepted")
    cancel = InlineKeyboardButton(text="🗑 Buyurtmani bekor qilish", callback_data="cancelled")
    return InlineKeyboardMarkup(inline_keyboard=[[accept], [payment_date], [cancel]])


MINI_APP_URL = config("MINI_APP_URL")


def start_btn():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🚀 Imtihonni boshlash",
            web_app=WebAppInfo(url=MINI_APP_URL)  # ← replace with your real Mini App URL
        )]
    ])


def course_navigation_buttons(index: int, total: int, course_id: int):
    left = InlineKeyboardButton(text="⬅️", callback_data=f"left_{index}")
    right = InlineKeyboardButton(text="➡️", callback_data=f"right_{index}")
    payment = InlineKeyboardButton(text="💳 Sotib olish", callback_data=f"payment_{course_id}")
    back = InlineKeyboardButton(text="🔙 Ortga", callback_data="back")

    nav_row = [left, right]

    return InlineKeyboardMarkup(inline_keyboard=[
        nav_row,
        [payment],
        [back],
    ])


def admin_accept(chat_id):
    accept = InlineKeyboardButton(text="✅ To'lovni tasdiqlash", callback_data=f"accepted:{chat_id}")
    cancel = InlineKeyboardButton(text = "🗑 To'lovni bekor qilish", callback_data=f"cancelled:{chat_id}")
    return InlineKeyboardMarkup(inline_keyboard=[[accept], [cancel]])



def my_course_navigation_buttons(index: int, total: int, course_id: int):
    left = InlineKeyboardButton(text="⬅️", callback_data=f"my_left_{index}")
    right = InlineKeyboardButton(text="➡️", callback_data=f"my_right_{index}")
    back = InlineKeyboardButton(text="🔙 Ortga", callback_data="my_back")

    transaction = Transaction.objects.filter(course_id=course_id).first()
    status_text = "Holat mavjud emas"
    if transaction:
        status_text = (
            "✅ Tasdiqlangan" if transaction.status == "Accepted"
            else "⏳ Tasdiqlanishi kutilmoqda" if transaction.status == "Pending"
            else "❌ Bekor qilingan"
        )

    status_button = InlineKeyboardButton(text=status_text, callback_data=f"my_payment_{course_id}")

    nav_row = []
    if index > 0:
        nav_row.append(left)
    if index < total - 1:
        nav_row.append(right)

    return InlineKeyboardMarkup(inline_keyboard=[
        nav_row,
        [status_button],
        [back],
    ])
