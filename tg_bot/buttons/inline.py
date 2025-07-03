from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from decouple import config

from course.models import Course
from studentcourse.models import StudentCourse, UserTasks
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
    examples = InlineKeyboardButton(text="📒 Darslardan parchalar",callback_data=f"examples_{course_id}")
    payment = InlineKeyboardButton(text="💳 Sotib olish", callback_data=f"payment_{course_id}")
    back = InlineKeyboardButton(text="🔙 Ortga", callback_data="back")

    nav_row = [left, right]

    return InlineKeyboardMarkup(inline_keyboard=[
        nav_row,
        [examples],
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

from math import ceil
def themes_attendance(course_id: list, user, level_id, page=1):
    page_size = 18
    start_index = (page - 1) * page_size
    end_index = start_index + page_size

    themes_qs = Theme.objects.filter(
        course__id__in=course_id,
        course_type__id=level_id
    ).distinct()

    total_themes = themes_qs.count()
    total_pages = ceil(total_themes / page_size)

    themes = themes_qs[start_index:end_index]

    keyboard = []
    row = []

    for i, theme in enumerate(themes, start=start_index + 1):
        attendance = ThemeAttendance.objects.filter(
            user=user,
            theme=theme,
            is_attendance=True,
            is_complete_test=True
        ).first()

        check_icon = " ✅" if attendance else ""

        row.append(InlineKeyboardButton(
            text=f"{i}-dars{check_icon}",
            callback_data=f"lesson_{theme.id}"
        ))

        if len(row) == 3:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Add pagination navigation
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton(
            text="⬅️ Previous",
            callback_data=f"themepage:{page - 1}:{level_id}:{course_id[0]}"
        ))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton(
            text="Next ➡️",
            callback_data=f"themepage:{page + 1}:{level_id}:{course_id[0]}"
        ))

    if nav_row:
        keyboard.append(nav_row)

    keyboard.append([
        InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"start_lesson_{course_id[0]}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def course_levels(course_id):
    try:
        course = Course.objects.prefetch_related("course_type").filter(id=course_id).first()

        if not course:
            raise Course.DoesNotExist
    except Course.DoesNotExist:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Kurs topilmadi!", callback_data="noop")]
        ])

    keyboard = []
    row = []

    course_types = course.course_type.all()

    for i, course_type in enumerate(course_types, start=1):
        course_type_id = str(course_type.id)
        course_type_name = str(course_type.name)  # Ensure it's a plain string!
        data = f"select_level_{course_type_id}"
        print(data)
        row.append(
            InlineKeyboardButton(
                text=course_type_name,
                callback_data=data
            )
        )

        if i % 2 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    keyboard.append([InlineKeyboardButton(text="⬅️ Orqaga", callback_data="go_back")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_theme_buttons(theme_id: str, user_chat_id: int) -> InlineKeyboardMarkup:
    theme_att = ThemeAttendance.objects.filter(
        user__chat_id=user_chat_id,
        theme__id=theme_id
    ).first()

    has_sprechen = UserTasks.objects.filter(
        user__chat_id=user_chat_id,
        choice="Sprichen",
        theme__id=theme_id
    ).first()

    has_schreiben = UserTasks.objects.filter(
        user__chat_id=user_chat_id,
        choice="Schreiben",
        theme__id=theme_id
    ).first()

    # ✅ Over button logic
    if theme_att and theme_att.is_complete_test:
        course_id = theme_att.theme.course.first().id if theme_att.theme and theme_att.theme.course.exists() else "0"
        over_button = InlineKeyboardButton(
            text="✅ Dars bajarilgan",
            callback_data=f"theme_already_completed_{course_id}"
        )
    else:
        over_button = InlineKeyboardButton(
            text="✅ Darsni tugatdim",
            callback_data=f"finish_theme_{theme_id}"
        )

    # ✅ Sprechen button
    sprechen = InlineKeyboardButton(
        text="🗣 Sprechen topshirish" if not has_sprechen else f"🗣 ✅ {has_sprechen.ball} ball",
        callback_data=f"sprechen_{theme_id}" if not has_sprechen else "no_action"
    )

    # ✅ Schreiben button
    schreiben = InlineKeyboardButton(
        text="📝 Schreiben topshirish" if not has_schreiben else f"📝 ✅ {has_schreiben.ball} ball",
        callback_data=f"schreiben_{theme_id}" if not has_schreiben else "no_action"
    )

    back_button = InlineKeyboardButton(text="🔙 Ortga", callback_data="back")

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [schreiben, sprechen],
            [over_button],
            [back_button]
        ]
    )



def order_accept(product,user):
    accept_button = InlineKeyboardButton(
        text="✅ Tasdiqlash",callback_data=f"ac_{product.id}_{user.id}"
    )
    cancel_button = InlineKeyboardButton(
        text=":❌ Bekor qilish",callback_data=f"can_{product.id}_{user.id}"
    )
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [accept_button], [cancel_button]
        ]
    )