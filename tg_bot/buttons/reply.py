from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def phone_number_btn():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = "Raqamni yuborish 📞",
                                                         request_contact=True) ]] ,
                               resize_keyboard=True)

def results():
    return ReplyKeyboardMarkup(keyboard=[[
        KeyboardButton(text="📊 Natija")
    ]],resize_keyboard=True)


def user_menu():
    course = KeyboardButton(text="📝 Kurslar")
    my_courses = KeyboardButton(text="📝 Mening kurslarim")
    informs = KeyboardButton(text="👨‍🏫 Adminlar bilan aloqa")
    return ReplyKeyboardMarkup(keyboard=[
        [course,my_courses],
        [informs]
    ],
        resize_keyboard=True)

def admin():
    k1 = KeyboardButton(text="👥 O'quvchilar ro‘yxati")
    # k2 = KeyboardButton(text="📊 Hisobotlar")

    return ReplyKeyboardMarkup(
        keyboard=[[k1]],
        resize_keyboard=True
    )


def back():
    k1 = KeyboardButton(text="🔙 Ortga")
    return ReplyKeyboardMarkup(
        keyboard=[[k1]],
        resize_keyboard=True
    )