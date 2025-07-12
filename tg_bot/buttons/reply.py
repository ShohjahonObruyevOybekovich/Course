from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from idioms.models import MaterialsCategories


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
    extra_materials = KeyboardButton(text="🎁 Qo'shimcha materiallar")
    shop = KeyboardButton(text="🛒 Shop")
    informs = KeyboardButton(text="👨‍🏫 Adminlar bilan aloqa")
    return ReplyKeyboardMarkup(keyboard=[
        [course,my_courses],
        [extra_materials],
        [shop],
        [informs]
    ],
        resize_keyboard=True)

def admin():
    k1 = KeyboardButton(text="👥 O'quvchilar ro‘yxati")
    k2 = KeyboardButton(text="⚙️ Materiallar yuklash")

    return ReplyKeyboardMarkup(
        keyboard=[[k1],[k2]],
        resize_keyboard=True
    )


def back():
    k1 = KeyboardButton(text="🔙 Ortga")
    return ReplyKeyboardMarkup(
        keyboard=[[k1]],
        resize_keyboard=True
    )


def materials_category():
    category = MaterialsCategories.objects.all()

    keyboard = []
    row = []

    for i, item in enumerate(category, 1):
        row.append(KeyboardButton(text=item.name))
        if i % 2 == 0:
            keyboard.append(row)
            row = []

    # Agar oxirgi tugma juft bo'lmasa, uni ham qo'shamiz
    if row:
        keyboard.append(row)


    keyboard.append([KeyboardButton(text="🔙 Ortga")])
    keyboard.append(back)

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
