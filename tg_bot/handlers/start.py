from datetime import datetime

from aiogram import Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto, InlineKeyboardButton, \
    InlineKeyboardMarkup
from aiogram.utils.chat_action import logger
from decouple import config
from icecream import ic

from account.models import CustomUser
from channel.models import Channel
from course.models import Course
from dispatcher import dp, TOKEN
from studentcourse.models import StudentCourse
from tg_bot.buttons.inline import course_navigation_buttons, admin_accept, my_course_navigation_buttons, \
    get_theme_buttons, themes_attendance, start_btn, course_levels
from tg_bot.buttons.reply import phone_number_btn, results, admin, user_menu, back
from tg_bot.buttons.text import start_txt, natija_txt
from tg_bot.state.main import User
from tg_bot.utils import format_phone_number, check_user_in_channel, send_theme_material
from theme.models import ThemeAttendance, Theme
from transaction.models import Transaction

bot = Bot(token=TOKEN)

card_number = config("CARD_NUMBER")
card_name = config("CARD_NAME")

# /start handler
@dp.message(F.text == "/start")
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

    # 🔁 Step 1: Check forced channel join
    channels = Channel.objects.all()
    not_joined = []

    for channel in channels:
        joined = await check_user_in_channel(message.from_user.id, channel.username, bot)
        if not joined:
            not_joined.append(channel)

    if not_joined:
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"➕ {ch.name}", url=f"https://t.me/{ch.username}")]
            for ch in not_joined
        ])
        markup.inline_keyboard.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_channels")])

        await message.answer(
            "❗️ Davom etishdan oldin quyidagi kanallarga obuna bo‘ling:",
            reply_markup=markup
        )
        return

    # 🔁 Step 2: User registration and role-based greeting
    user = CustomUser.objects.filter(chat_id=message.from_user.id).first()

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
    else:
        await message.answer(natija_txt, reply_markup=user_menu())

@dp.callback_query(F.data == "check_channels")
async def recheck_channels(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    channels = Channel.objects.all()
    not_joined = []

    for channel in channels:
        joined = await check_user_in_channel(user_id, channel.username, bot)
        if not joined:
            not_joined.append(channel)

    if not_joined:
        await call.answer("❌ Hali hamma kanallarga obuna emassiz.", show_alert=True)
    else:
        await call.message.delete()
        await call.message.answer(start_txt)
        await state.set_state(User.full_name)



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


async def send_course(chat_id: int, index: int, message_to_edit=None):
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

            if message_to_edit:
                # Try to edit existing message
                try:
                    if message_to_edit.photo:
                        # Edit photo message
                        await bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=message_to_edit.message_id,
                            media=InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"),
                            reply_markup=keyboard
                        )
                    else:
                        # Delete text message and send photo
                        await message_to_edit.delete()
                        await bot.send_photo(chat_id, photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
                except Exception as e:
                    # If editing fails, delete and send new
                    await message_to_edit.delete()
                    await bot.send_photo(chat_id, photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
            else:
                # Send new photo message
                await bot.send_photo(chat_id, photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")

        except Exception as e:
            # Handle photo loading error
            if message_to_edit:
                try:
                    if message_to_edit.photo:
                        # Delete photo message and send text
                        await message_to_edit.delete()
                        await bot.send_message(chat_id, f"{caption}\n\n(Rasmni yuklab bo'lmadi)", reply_markup=keyboard,
                                               parse_mode="HTML")
                    else:
                        # Edit text message
                        await bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_to_edit.message_id,
                            text=f"{caption}\n\n(Rasmni yuklab bo'lmadi)",
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                except Exception as edit_error:
                    await message_to_edit.delete()
                    await bot.send_message(chat_id, f"{caption}\n\n(Rasmni yuklab bo'lmadi)", reply_markup=keyboard,
                                           parse_mode="HTML")
            else:
                await bot.send_message(chat_id, f"{caption}\n\n(Rasmni yuklab bo'lmadi)", reply_markup=keyboard,
                                       parse_mode="HTML")
    else:
        # No photo
        if message_to_edit:
            try:
                if message_to_edit.photo:
                    # Delete photo message and send text
                    await message_to_edit.delete()
                    await bot.send_message(chat_id, caption, reply_markup=keyboard, parse_mode="HTML")
                else:
                    # Edit text message
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_to_edit.message_id,
                        text=caption,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
            except Exception as e:
                await message_to_edit.delete()
                await bot.send_message(chat_id, caption, reply_markup=keyboard, parse_mode="HTML")
        else:
            await bot.send_message(chat_id, caption, reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(lambda c: c.data.startswith(("left_", "right_","payment_", "back")))
async def handle_course_navigation(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data.get("course_index", 0)
    total = Course.objects.count()

    ic(call.data)

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

        check =  StudentCourse.objects.filter(course__id=course_id,user__chat_id=call.from_user.id).first()

        ic("payment -------")
        if check:
            transaction = Transaction.objects.filter(
                user__chat_id=call.from_user.id,
                course=course
            ).first()

            # Properly handle None transaction
            if transaction:
                status = "Tasdiqlangan" if transaction.status == "Accepted" else "Kutilmoqda" if transaction.status == "Pending" else "Rad etilgan"
            else:
                status = "Ma'lumot topilmadi"

            await call.message.delete()
            await call.message.answer(
                f"<b>{course.name}</b> uchun siz oldin to'lov checki yuborgansiz va hozirda holati <b>{status}</b>.",
                parse_mode="HTML",
                reply_markup=user_menu()
            )
            await state.clear()
            return  # Important: return here to prevent further execution


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


@dp.message(lambda message: message.text == "📝 Mening kurslarim")
async def my_courses(message: Message, state: FSMContext):
    courses = StudentCourse.objects.filter(user__chat_id=message.from_user.id)
    if not courses.exists():
        await message.answer("❗️ Kurslar mavjud emas.")
        return

    await state.update_data(course_index1=0)  # Use course_index1 for my courses
    await send_my_course(message.chat.id, 0)
    await state.set_state(User.browsing_my_courses)


async def send_my_course(chat_id: int, index: int, message_to_edit=None):
    courses = list(StudentCourse.objects.filter(user__chat_id=chat_id))
    student_course = courses[index]
    course = student_course.course

    caption = (
        f"<b>{course.name}</b>\n\n"
        f"{course.description or ''}\n\n"
        f"💰 Narxi: {course.price} so'm"
    )
    user = CustomUser.objects.filter(chat_id=chat_id).first()
    keyboard = my_course_navigation_buttons(index, len(courses), course.id,user=user)

    if course.photo and course.photo.file:
        try:
            photo_path = course.photo.file.path
            photo = FSInputFile(photo_path)

            if message_to_edit:
                try:
                    if message_to_edit.photo:
                        # Edit photo message
                        await bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=message_to_edit.message_id,
                            media=InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"),
                            reply_markup=keyboard
                        )
                    else:
                        # Delete text message and send photo
                        await message_to_edit.delete()
                        await bot.send_photo(chat_id, photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
                except Exception as e:
                    await message_to_edit.delete()
                    await bot.send_photo(chat_id, photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
            else:
                await bot.send_photo(chat_id, photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")

        except Exception as e:
            if message_to_edit:
                try:
                    if message_to_edit.photo:
                        await message_to_edit.delete()
                        await bot.send_message(chat_id, f"{caption}\n\n(Rasmni yuklab bo'lmadi)", reply_markup=keyboard,
                                               parse_mode="HTML")
                    else:
                        await bot.edit_message_text(
                            chat_id=chat_id,
                            message_id=message_to_edit.message_id,
                            text=f"{caption}\n\n(Rasmni yuklab bo'lmadi)",
                            reply_markup=keyboard,
                            parse_mode="HTML"
                        )
                except Exception as edit_error:
                    await message_to_edit.delete()
                    await bot.send_message(chat_id, f"{caption}\n\n(Rasmni yuklab bo'lmadi)", reply_markup=keyboard,
                                           parse_mode="HTML")
            else:
                await bot.send_message(chat_id, f"{caption}\n\n(Rasmni yuklab bo'lmadi)", reply_markup=keyboard,
                                       parse_mode="HTML")
    else:
        if message_to_edit:
            try:
                if message_to_edit.photo:
                    await message_to_edit.delete()
                    await bot.send_message(chat_id, caption, reply_markup=keyboard, parse_mode="HTML")
                else:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_to_edit.message_id,
                        text=caption,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
            except Exception as e:
                await message_to_edit.delete()
                await bot.send_message(chat_id, caption, reply_markup=keyboard, parse_mode="HTML")
        else:
            await bot.send_message(chat_id, caption, reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(lambda c: c.data.startswith(("my_left_", "my_right_", "my_payment_", "my_back")))
async def handle_my_course_navigation(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    index = data.get("course_index1", 0)  # Use course_index1 for my courses
    chat_id = call.from_user.id  # Use call.from_user.id instead of call.message.chat.id
    courses = list(StudentCourse.objects.filter(user__chat_id=chat_id, status="Inactive"))
    total = len(courses)

    if call.data.startswith("my_left_"):
        new_index = index - 1
        if new_index < 0:
            await call.answer("Kurs topilmadi", show_alert=True)
            return

        await state.update_data(course_index1=new_index)
        await call.message.delete()
        await send_my_course(chat_id, new_index)

    elif call.data.startswith("my_right_"):
        new_index = index + 1
        if new_index >= total:
            await call.answer("Kurs topilmadi", show_alert=True)
            return

        await state.update_data(course_index1=new_index)
        await call.message.delete()
        await send_my_course(chat_id, new_index)

    elif call.data.startswith("my_payment_"):
        # Handle payment status display
        course_id = call.data.split("_")[2]
        course = Course.objects.filter(id=course_id).first()
        transaction = Transaction.objects.filter(
            user__chat_id=chat_id,
            course_id=course_id
        ).first()

        if transaction:
            status = (
                "✅ Tasdiqlangan" if transaction.status == "Accepted"
                else "⏳ Tasdiqlanishi kutilmoqda" if transaction.status == "Pending"
                else "❌ Bekor qilingan"
            )
        else:
            status = "Holat mavjud emas"

        await call.answer(f"To'lov holati: {status}", show_alert=True)

    elif call.data == "my_back":
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer("🔙 Asosiy menyuga qaytdingiz.", reply_markup=user_menu())
        await state.clear()



@dp.callback_query(lambda c: c.data.startswith("start_lesson_"))
async def handle_start_lesson(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    try:
        course_id = call.data.split("_")[2]
        ic(course_id)
        user = CustomUser.objects.filter(chat_id=call.from_user.id).first()

        ic(user)

        if not user:
            await call.message.answer("User not found!")
            return

        await call.message.answer(
            text="📚 Avvalo kurs darajasini tanlang:",
            reply_markup=course_levels(course_id=course_id),
        )

    except Exception as e:
        logger.error(f"Error in handle_start_lesson: {e}")
        await call.message.answer("An error occurred. Please try again.")



@dp.callback_query(lambda c: c.data.startswith(("select_level_", "go_back")))
async def handle_select_level(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)

    if call.data == "go_back":
        await call.message.answer("Siz menu bulimiga qaytingiz!",reply_markup=user_menu())
        await state.clear()
        return

    try:
        parts = call.data.split("_")
        level_id = parts[2]
        print("level",level_id)

        course = StudentCourse.objects.filter(
            user__chat_id=call.from_user.id,
            course__course_type__id=level_id
        ).first()

        print("course",course.course.id)

        if not course:
            await call.message.answer("❌ Kurs aniqlanmadi.",reply_markup=course_levels(course_id=course.course.id))
            return

        await state.update_data(level_id=level_id)

        await call.message.answer(
            text="📘 Endi mavzuni tanlang:",
            reply_markup=themes_attendance(course.course.id, call.from_user.id, level_id)
        )

    except Exception as e:
        logger.error(f"Error in handle_select_level: {e}")
        await call.message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")


@dp.callback_query(lambda c: c.data.startswith("lesson_"))
async def handle_start_lesson(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)

    try:
        # Extract theme_id directly from callback data "lesson_<theme_id>"
        theme_id = call.data.split("_")[1]  # Changed from [2] to [1]

        if not theme_id:
            await call.message.answer("❌ Mavzu topilmadi.")
            return

        # Get the theme
        theme = Theme.objects.filter(id=theme_id).first()

        if not theme:
            await call.message.answer("❌ Ushbu kursda hozircha hech qanday dars mavjud emas.")
            return

        # Mark attendance (optional or in another handler)
        theme_att = ThemeAttendance.objects.filter(
            user__chat_id=call.from_user.id,
            theme=theme
        ).first()
        if not theme_att:
            user = CustomUser.objects.filter(chat_id=call.from_user.id).first()

            ThemeAttendance.objects.create(
                user=user,
                theme=theme,
            )
        import os

        videos = theme.video.all()

        if videos.exists():
            for idx, video in enumerate(videos, start=1):
                if video.url:
                    await call.message.answer(
                        text=(
                            f"🎬 <b>{theme.name}</b> — {idx}-video\n\n"
                            f"👉 <a href='{video.url}'>Videoni tomosha qilish</a>\n\n"
                            f"📌 Diqqat bilan tomosha qiling va topshiriqlarga o'ting!"
                        ),
                        parse_mode="HTML",
                        disable_web_page_preview=False
                    )
        else:
            await call.message.answer("❌ Ushbu darsga biriktirilgan video topilmadi.")

        # Build message
        text = f"📘 <b>{theme.name}</b>\n\n"
        if theme.description:
            text += f"{theme.description}\n\n"

        if theme.materials:
            await send_theme_material(call.message, theme)


        reply_markup = get_theme_buttons(str(theme.id),call.from_user.id)
        await call.message.answer(
            text,
            reply_markup=reply_markup,
            parse_mode="HTML",
            disable_web_page_preview=False
        )

        if theme.link:
            # link = f"https://online.eduzoneuz.uz/course/?link={theme.link}"
            await call.message.answer(
                text="Mavzu buyicha testlar",
                reply_markup=start_btn(theme.link)
            )

    except IndexError:
        await call.message.answer("❌ Xato: Noto'g'ri formatdagi so'rov.")
    except Exception as e:
        logger.error(f"Error in handle_start_lesson: {e}")
        await call.message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")


@dp.callback_query(lambda c: c.data.startswith("finish_theme_"))
async def finishing_the_same(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    theme_id = call.data.split("_")[2]
    if theme_id:
        theme_att = ThemeAttendance.objects.filter(
            theme__id=theme_id,
            user__chat_id=call.from_user.id,
        ).first()

        theme = Theme.objects.filter(id=theme_id).first()
        level = theme.level.first().id
        if not theme_att:
            call.message.answer(
                text=f"👮🏻‍♂️ Siz {theme.name} mavzusini hali boshlamagansiz ⁉️",
                reply_markup=themes_attendance(course_id=theme.course.id, user=theme_att.user,level_id=level)
            )

        theme_att.is_complete_test = True
        theme_att.save()

        call.message.answer(
            text="✅ Siz mavzuni muvaffaqiyatli yakunladingiz!",
            reply_markup=themes_attendance(course_id=theme.course.id, user=theme_att.user,level_id=level)
        )


@dp.callback_query(lambda c: c.data.startswith("theme_already_completed_"))
async def finishing_the_same(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    course_id = call.data.split("_")[3]

    print(course_id)

    course= Course.objects.filter(id=course_id).first()
    level = course.course_type.first().id
    user = CustomUser.objects.filter(chat_id=call.from_user.id).first()
    ic(level)

    await call.message.answer(
        text="Kursingizning mavzularidan birini tanlang.",
        reply_markup=themes_attendance(course_id, user,level)
    )


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