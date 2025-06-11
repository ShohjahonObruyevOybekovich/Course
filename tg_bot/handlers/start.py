from datetime import datetime

from aiogram import Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from decouple import config
from icecream import ic

from account.models import CustomUser
from course.models import Course
from dispatcher import dp, TOKEN
from studentcourse.models import StudentCourse
from tg_bot.buttons.inline import course_navigation_buttons, admin_accept, my_course_navigation_buttons
from tg_bot.buttons.reply import phone_number_btn, results, admin, user_menu, back
from tg_bot.buttons.text import start_txt, natija_txt
from tg_bot.state.main import User
from tg_bot.utils import format_phone_number
from transaction.models import Transaction

bot = Bot(token=TOKEN)


# /start handler
@dp.message(F.text == "/start")
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    user = CustomUser.objects.filter(chat_id=message.from_user.id).first()

    # First-time user registration
    if not user:
        CustomUser.objects.create(
            chat_id=message.from_user.id,
            full_name=message.from_user.full_name,
        )
        await message.answer(start_txt)
        await state.set_state(User.full_name)
        return

    if user.role == "Admin":
        await message.answer(
            text="🔐 *Admin bo‘limiga hush kelibsiz!* 👋\nSizda to‘liq boshqaruv huquqlari mavjud.",
            reply_markup=admin(),
            parse_mode="Markdown"
        )
    if user and user.role != "Admin":
        await message.answer(natija_txt, reply_markup=user_menu())


@dp.message(User.full_name)
async def user_lang_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    data['full_name'] = message.text
    await state.set_data(data)
    await state.set_state(User.phone)
    await message.answer(
        "Telefon raqamingizni Raqamni yuborish \n📞 tugmasi orqali yuboring ! \n",
        reply_markup=phone_number_btn()
    )


@dp.message(User.phone)
async def handle_phone_number(message: Message, state: FSMContext) -> None:
    if not message.contact:
        await state.set_state(User.phone)
        await message.answer(
            "❗️Telefon raqamingizni *Raqamni yuborish 📞* tugmasi orqali yuboring!",
            reply_markup=phone_number_btn(),
            parse_mode="Markdown"
        )
        return

    phone_number = format_phone_number(message.contact.phone_number)
    user = CustomUser.objects.filter(chat_id=message.from_user.id).first()
    if user:
        user.phone = phone_number
        user.save()

    await message.answer(f"✅ <b>Telefon raqamingiz saqlandi!</b>\n📞 <b>{phone_number}</b>", parse_mode="HTML",
                         reply_markup=user_menu()
                         )
    await state.clear()

@dp.message(lambda message : message.text=="📝 Kurslar")
async def get_courses(message: Message, state: FSMContext) -> None:
    courses = Course.objects.all()
    if not courses.exists():
        await message.answer("❗️ Kurslar mavjud emas.")
        return

    await state.update_data(course_index=0)
    await send_course(message.chat.id, 0)
    await state.set_state(User.browsing_courses)


async def send_course(chat_id: int, index: int):
    courses = list(Course.objects.all())
    course = courses[index]

    caption = (
        f"<b>{course.name}</b>\n\n"
        f"{course.description or ''}\n\n"
        f"💰 Narxi: {course.price} so'm"
    )

    keyboard = course_navigation_buttons(index, len(courses), course.id)

    if course.photo and course.photo.file:
        try:
            photo_path = course.photo.file.path
            photo = FSInputFile(photo_path)
            await bot.send_photo(chat_id, photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            await bot.send_message(chat_id, f"{caption}\n\n(Rasmni yuklab bo‘lmadi)", reply_markup=keyboard, parse_mode="HTML")
    else:
        await bot.send_message(chat_id, caption, reply_markup=keyboard, parse_mode="HTML")

card_number = config("CARD_NUMBER")
card_name = config("CARD_NAME")

@dp.callback_query(lambda c: c.data.startswith(("left_", "right_", "back")))
async def handle_course_navigation(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data.get("course_index", 0)
    total = Course.objects.count()

    if call.data.startswith("left_"):
        if index > 0:
            index -= 1
            await state.update_data(course_index=index)
            await call.message.delete()
            await send_course(call.message.chat.id, index)

    elif call.data.startswith("right_"):
        if index < total - 1:
            index += 1
            await state.update_data(course_index=index)
            await call.message.delete()
            await send_course(call.message.chat.id, index)

    elif call.data.startswith("payment_"):
        await call.message.edit_reply_markup(reply_markup=None)
        course_id = str(call.data.split("_")[1])

        await state.update_data(course=course_id)

        course = Course.objects.filter(id=course_id).first()
        if course:
            await call.message.answer(
                f"💵 Siz {course.name} kursini tanladingiz.\n\n"
                f"To'lov amaliyoti kartaga pul o'tkazish yo'li bilan amalga oshiriladi.\n"
                f"💳 Kartaga pul o'tkazilganidan so'ng checkni adminga yuboring va to'lov tasdiqlanganidan so'ng bot orqali xabar beramiz!\n\n"
                f"```"
                f"{card_name}\n"
                f"{card_number}"
                f"```",
                parse_mode="Markdown",
                reply_markup=back()
            )
            await state.set_state(User.payment)

        else:
            await call.message.answer("❗️Kurs topilmadi.",reply_markup=user_menu())

    elif call.data == "back":
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer("🔙 Asosiy menyuga qaytdingiz.", reply_markup=user_menu())
        await state.clear()


from datetime import datetime

@dp.message(StateFilter(User.payment))
async def handle_payment(message: Message, state: FSMContext):
    # Handle "back" button
    if message.text == "🔙 Ortga":
        await message.answer("🔙 Asosiy menyuga qaytdingiz.", reply_markup=user_menu())
        await state.clear()
        return

    # Reject plain text
    elif message.text and message.text.isalpha():
        await message.answer(
            text="To'lov chekini faqat rasm yoki fayl ko'rinishida yuborishingiz mumkin!",
            reply_markup=back(),
            parse_mode="Markdown"
        )
        return

    # Get photo or document
    file_obj = None
    file_type = None
    if message.photo:
        file_obj = message.photo[-1]
        file_type = "document" if message.document else "photo"
    elif message.document:
        file_obj = message.document
        file_type = "document" if message.document else "photo"
    if not file_obj:
        await message.answer("❗️To'lov chekini rasm yoki fayl sifatida yuboring.", reply_markup=back())
        return

    # Get user and course
    user = await CustomUser.objects.aget(chat_id=message.from_user.id)
    data = await state.get_data()
    course_id = data.get("course")
    course = await Course.objects.filter(id=course_id).afirst()


    # Save Transaction
    transaction = await Transaction.objects.acreate(
        user=user,
        amount=course.price if course else 0,
        course=course,
        status="Pending",
        file=file_obj.file_id
    )

    # Notify admins
    admins = CustomUser.objects.filter(role="Admin").all()
    caption = "\n".join([
        f"<b>Foydalanuvchi ismi:</b> {user.full_name or 'Noma\'lum'}",
        f"<b>Telefon raqami:</b> {user.phone or 'Noma\'lum'}",
        f"<b>Kurs nomi:</b> {course.name if course else 'Noma\'lum'}",
        f"<b>Kurs summasi:</b> {course.price if course else '0'}",
        f"<b>Yuborilgan vaqti:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    ])

    file_id = file_obj.file_id
    file_type = "document" if message.document else "photo"

    for admin in admins:
        try:
            if file_type == "document":
                await bot.send_document(
                    chat_id=admin.chat_id,
                    document=file_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=admin_accept(chat_id=message.from_user.id)
                )
            else:
                await bot.send_photo(
                    chat_id=admin.chat_id,
                    photo=file_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=admin_accept(chat_id=message.from_user.id)
                )

        except Exception as e:
            print(f"Failed to send to admin {admin.chat_id}: {e}")

    await message.answer(
        "✅ To'lov cheki qabul qilindi. Tekshiruvdan so‘ng sizga xabar beramiz.",
        reply_markup=user_menu()
    )
    course = StudentCourse.objects.create(
        user=user,
        course=course,
    )
    await state.clear()



@dp.message(lambda message: message.text =="📝 Mening kurslarim")
async def my_courses(message: Message,state: FSMContext):
    courses = StudentCourse.objects.filter(user__chat_id=message.from_user.id,status="Inactive")
    if not courses.exists():
        await message.answer("❗️ Kurslar mavjud emas.")
        return

    await state.update_data(course_index=0)
    await send_course(message.chat.id, 0)
    await state.set_state(User.browsing_my_courses)


async def send_my_course_from_call(call: CallbackQuery, index: int):
    chat_id = call.message.chat.id
    courses = list(StudentCourse.objects.filter(user__chat_id=chat_id, status="Inactive"))
    course = courses[index]

    caption = (
        f"<b>{course.name}</b>\n\n"
        f"{course.description or ''}\n\n"
        f"💰 Narxi: {course.price} so'm"
    )

    keyboard = my_course_navigation_buttons(index, len(courses), course.id)

    try:
        if course.photo and course.photo.file:
            photo_path = course.photo.file.path
            photo = FSInputFile(photo_path)
            await bot.send_photo(chat_id, photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
        else:
            await call.message.answer(caption, reply_markup=keyboard, parse_mode="HTML")
    except Exception as e:
        await call.message.answer(f"{caption}\n\n(Rasmni yuklab bo‘lmadi)", reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(lambda c: c.data.startswith(("my_left_", "my_right_", "my_payment_", "my_back")))
async def handle_course_navigation(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data.get("course_index", 0)
    chat_id = call.message.chat.id
    courses = list(StudentCourse.objects.filter(user__chat_id=chat_id, status="Inactive"))
    total = len(courses)

    if call.data.startswith("my_left_"):
        if index > 0:
            index -= 1
            await state.update_data(course_index=index)
            await send_my_course_from_call(call, index)

    elif call.data.startswith("my_right_"):
        if index < total - 1:
            index += 1
            await state.update_data(course_index=index)
            await send_my_course_from_call(call, index)

    elif call.data == "my_back":
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer("🔙 Asosiy menyuga qaytdingiz.", reply_markup=user_menu())
        await state.clear()



@dp.message(F.text == "👨‍🏫 Adminlar bilan aloqa")
async def contact_admins(message: Message):

    admin = config("ADMIN_USERNAME")
    admin_full_name = config("ADMIN_FULLNAME")
    admin_number = config("ADMIN_NUMBER")

    if not admin:
        await message.answer("Hozirda administratorlar mavjud emas.")
        return

    text_lines = ["📞 <b>Administratorlar bilan aloqa</b>:\n"]
    tg_link = (
        f"<a href='https://t.me/{admin}'>"
        f"{admin_full_name or 'Admin'}"
        f"</a>" if admin else admin_full_name or "Admin"
    )
    phone = admin_number or "Nomaʼlum"

    text_lines.append(f"👤 {tg_link}\n📱 {phone}\n")

    await message.answer("\n".join(text_lines), parse_mode="HTML")