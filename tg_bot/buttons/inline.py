from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from decouple import config

from studentcourse.models import StudentCourse
from theme.models import Theme, ThemeAttendance
from transaction.models import Transaction


def degree():
    payment_date = InlineKeyboardButton(text="✏️ Sanani o'zgartirish", callback_data="Sanani o'zgartirish")
    accept = InlineKeyboardButton(text="✅ Buyurtmani tasdiqlash", callback_data="accepted")
    cancel = InlineKeyboardButton(text="🗑 Buyurtmani bekor qilish", callback_data="cancelled")
    return InlineKeyboardMarkup(inline_keyboard=[[accept], [payment_date], [cancel]])


MINI_APP_URL = config("MINI_APP_URL")


def start_btn(link):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🚀 Imtihonni boshlash",
            web_app=WebAppInfo(url=link)  # ← replace with your real Mini App URL
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



def my_course_navigation_buttons(index: int, total: int, course_id: int, user):
    left = InlineKeyboardButton(text="⬅️", callback_data=f"my_left_{index}")
    right = InlineKeyboardButton(text="➡️", callback_data=f"my_right_{index}")
    back = InlineKeyboardButton(text="🔙 Ortga", callback_data="my_back")

    # Payment status check
    transaction = Transaction.objects.filter(course_id=course_id, user=user).first()
    status_text = "Holat mavjud emas"
    if transaction:
        status_text = (
            "✅ Tasdiqlangan" if transaction.status == "Accepted"
            else "⏳ Tasdiqlanishi kutilmoqda" if transaction.status == "Pending"
            else "❌ Bekor qilingan"
        )

    status_button = InlineKeyboardButton(text=status_text, callback_data=f"my_payment_{course_id}")

    # Check if the user has active course
    start_lesson_button = None
    student_course = StudentCourse.objects.filter(course_id=course_id, user=user, status="Active").first()
    if student_course:
        start_lesson_button = InlineKeyboardButton(text="📘 Darsni boshlash", callback_data=f"start_lesson_{course_id}")

    # Build keyboard layout
    keyboard = [
        [left, right],
        [status_button],
    ]

    if start_lesson_button:
        keyboard.append([start_lesson_button])

    keyboard.append([back])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def themes_attendance(course_id, user):
    themes = Theme.objects.filter(course__id=course_id).all()
    keyboard = []

    row = []
    for i, theme in enumerate(themes, start=1):
        # Check if user attended the theme
        attendance = ThemeAttendance.objects.filter(
            user=user,
            theme=theme,
            is_attendance=True,
            is_complete_test=True
        ).first()
        check_icon = " ✅" if attendance else ""

        button = InlineKeyboardButton(
            text=f"{i}-dars{check_icon}",
            callback_data=f"lesson_{theme.id}"
        )
        row.append(button)

        # Add row when it reaches 6 buttons
        if len(row) == 6:
            keyboard.append(row)
            row = []

    # Add the last row if not empty
    if row:
        keyboard.append(row)

    # For aiogram v3.x, use this:
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_theme_buttons(theme_id: str) -> InlineKeyboardMarkup:
    over = InlineKeyboardButton(text="✅ Darsni tugatdim", callback_data=f"finish_theme_{theme_id}")
    back = InlineKeyboardButton(text="🔙 Ortga", callback_data="back")

    return InlineKeyboardMarkup(inline_keyboard=[[over], [back]])