from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from idioms.models import MaterialsCategories


def phone_number_btn():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="Raqamni yuborish 📞",
                                                         request_contact=True)]],
                               resize_keyboard=True, one_time_keyboard=True)


def results():
    return ReplyKeyboardMarkup(keyboard=[[
        KeyboardButton(text="📊 Natija")
    ]], resize_keyboard=True)


def user_menu():
    course = KeyboardButton(text="📝 Kurslar")
    my_courses = KeyboardButton(text="📝 Mening kurslarim")
    extra_materials = KeyboardButton(text="🎁 Qo'shimcha materiallar")
    referral = KeyboardButton(text="🔗 Referral yuborish")
    shop = KeyboardButton(text="🛒 Shop")
    informs = KeyboardButton(text="👨‍🏫 Adminlar bilan aloqa")
    return ReplyKeyboardMarkup(keyboard=[
        [course, my_courses],
        [referral, shop],
        [extra_materials],
        [informs]
    ],
        resize_keyboard=True)


def admin():
    k1 = KeyboardButton(text="👥 O'quvchilar ro‘yxati")
    send_post = KeyboardButton(text="✍️ Post yuborish")
    k2 = KeyboardButton(text="⚙️ Materiallar yuklash")
    k3 = KeyboardButton(text="📒 Qo'shimcha Video yuklash")

    return ReplyKeyboardMarkup(
        keyboard=[[k1, send_post], [k2, k3]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def back():
    k1 = KeyboardButton(text="🔙 Ortga")
    return ReplyKeyboardMarkup(
        keyboard=[[k1]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def skip():
    k1 = KeyboardButton(text="🔙 Ortga")
    skip = KeyboardButton(text="🌫 O'tkazib yuborish")
    return ReplyKeyboardMarkup(
        keyboard=[[skip], [k1]], one_time_keyboard=True, resize_keyboard=True
    )


def materials_category():
    category = MaterialsCategories.objects.all()

    keyboard = []
    row = []

    for i, item in enumerate(category, 1):
        row.append(KeyboardButton(text=item.category))
        if i % 2 == 0:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Orqaga tugmasi
    keyboard.append([KeyboardButton(text="🔙 Ortga")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True,
                               one_time_keyboard=True)
