import os
from datetime import datetime

from aiogram import Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, InputMediaPhoto
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, \
    InlineKeyboardMarkup
from aiogram.utils.chat_action import logger
from decouple import config
from icecream import ic

from account.models import CustomUser
from channel.models import Channel
from course.models import Course
from dispatcher import dp, TOKEN
from idioms.models import MaterialsCategories, Materials
from studentcourse.models import StudentCourse
from tg_bot.buttons.inline import course_navigation_buttons, admin_accept, my_course_navigation_buttons, \
    get_theme_buttons, themes_attendance, start_btn, course_levels
from tg_bot.buttons.reply import phone_number_btn, admin, user_menu, back, materials_category
from tg_bot.buttons.text import start_txt, natija_txt
from tg_bot.state.main import User, MaterialState
from tg_bot.utils import format_phone_number, check_user_in_channel, send_theme_material
from theme.models import ThemeAttendance, Theme, ThemeExamples
from transaction.models import Transaction

bot = Bot(token=TOKEN)

card_number = config("CARD_NUMBER")
card_name = config("CARD_NAME")


# /start handler
@dp.message(F.text == "/start")
async def command_start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()

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


@dp.message(lambda message: message.text == "📝 Kurslar")
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


@dp.callback_query(lambda c: c.data.startswith(("left_", "right_", "payment_", "examples_", "back")))
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
        await call.message.delete()
        course_id = str(call.data.split("_")[1])

        await state.update_data(course=course_id)

        course = Course.objects.filter(id=course_id).first()

        check = StudentCourse.objects.filter(course__id=course_id, user__chat_id=call.from_user.id).first()

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
            await call.message.answer("❗️Kurs topilmadi.", reply_markup=user_menu())

    elif call.data.startswith("examples_"):
        await call.message.delete()
        examples = ThemeExamples.objects.all()
        if not examples:
            await call.message.answer("🚫 Hozircha misollar mavjud emas.")
            return
        bot = call.bot
        for theme in examples:
            text = f"📚 <b>{theme.name}</b>\n\n"
            if theme.description:
                text += f"📝 {theme.description}\n\n"
            if theme.video:
                await bot.send_video(
                    chat_id=call.message.chat.id,
                    video=theme.video,
                    caption=text,
                    reply_markup=start_btn(link=theme.link),
                    parse_mode="HTML",
                    protect_content=True
                )
            else:
                await bot.send_message(
                    chat_id=call.message.chat.id,
                    text=text,
                    reply_markup=start_btn(link=theme.link),
                    parse_mode="HTML",
                    protect_content=True
                )

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
    # Get file
    file_obj = None
    file_type = None
    if message.photo:
        file_obj = message.photo[-1]
        file_type = "photo"
    elif message.document:
        file_obj = message.document
        file_type = "document"
    else:
        await message.answer("❗️To'lov chekini rasm yoki fayl sifatida yuboring.", reply_markup=back())
        return

    # Get user and course
    user = await CustomUser.objects.aget(chat_id=message.from_user.id)
    data = await state.get_data()
    course_id = data.get("course")
    course = await Course.objects.filter(id=course_id).afirst()

    if not course:
        await message.answer("❌ Kurs topilmadi. Iltimos, qaytadan urinib ko'ring.")
        await state.clear()
        return

    # Save transaction
    transaction = await Transaction.objects.acreate(
        user=user,
        amount=course.price,
        course=course,
        status="Pending",
        file=file_obj.file_id
    )

    # Notify admins
    admins = CustomUser.objects.filter(role="Admin").all()

    caption = "\n".join([
        f"<b>Foydalanuvchi ismi:</b> {user.full_name if user.full_name else 'Nomaʼlum'}",
        f"<b>Telefon raqami:</b> {user.phone if user.phone else 'Nomaʼlum'}",
        f"<b>Kurs nomi:</b> {course.name if course else 'Nomaʼlum'}",
        f"<b>Kurs summasi:</b> {course.price if course else '0'}",
        f"<b>Yuborilgan vaqti:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    ])

    for admin in admins:
        try:
            if file_type == "document":
                await bot.send_document(
                    chat_id=admin.chat_id,
                    document=file_obj.file_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=admin_accept(chat_id=message.from_user.id)
                )
            else:
                await bot.send_photo(
                    chat_id=admin.chat_id,
                    photo=file_obj.file_id,
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

    await StudentCourse.objects.acreate(
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
    if index < 0 or index >= len(courses):
        await bot.send_message(chat_id, "❗️ Noto‘g‘ri kurs indexi.")
        return

    student_course = courses[index]
    course = student_course.course
    user = CustomUser.objects.filter(chat_id=chat_id).first()

    caption = (
        f"<b>{course.name}</b>\n\n"
        f"{course.description or ''}\n\n"
        f"💰 Narxi: {course.price} so'm"
    )
    keyboard = my_course_navigation_buttons(index, len(courses), course.id, user=user)

    # Check for attached photo
    has_photo = bool(course.photo and course.photo.file and os.path.exists(course.photo.file.path))
    photo_path = course.photo.file.path
    photo = FSInputFile(photo_path)

    async def send_as_photo():
        try:
            await bot.send_photo(chat_id, photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
        except Exception as e:
            print("Photo sending error:", e)
            await bot.send_message(chat_id, f"{caption}\n\n(Rasmni yuklab bo'lmadi)", reply_markup=keyboard,
                                   parse_mode="HTML")

    async def edit_as_photo():
        try:
            input_file = FSInputFile(photo_path)
            await bot.edit_message_media(
                chat_id=chat_id,
                message_id=message_to_edit.message_id,
                media=InputMediaPhoto(media=input_file, caption=caption, parse_mode="HTML"),
                reply_markup=keyboard
            )
        except Exception as e:
            print("Edit photo failed:", e)
            await message_to_edit.delete()
            await send_as_photo()

    async def edit_as_text(extra_caption=""):
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_to_edit.message_id,
                text=f"{caption}{extra_caption}",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception as e:
            print("Edit text failed:", e)
            await message_to_edit.delete()
            await bot.send_message(chat_id, f"{caption}{extra_caption}", reply_markup=keyboard, parse_mode="HTML")

    # Handle sending or editing
    if has_photo:
        if message_to_edit:
            if message_to_edit.photo:
                await edit_as_photo()
            else:
                await message_to_edit.delete()
                await send_as_photo()
        else:
            await send_as_photo()
    else:
        if message_to_edit:
            if message_to_edit.photo:
                await message_to_edit.delete()
                await bot.send_message(chat_id, caption, reply_markup=keyboard, parse_mode="HTML")
            else:
                await edit_as_text()
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
        await call.message.delete()
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer("🔙 Asosiy menyuga qaytdingiz.", reply_markup=user_menu())
        await state.clear()


@dp.callback_query(lambda call: call.data.startswith("start_lesson_"))
async def handle_start_lesson(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    try:
        user_id = call.from_user.id
        course_id = call.data.split("_")[2]

        channels = Channel.objects.all()
        not_joined = []

        for channel in channels:
            if not channel.chat_id:
                print(f"⚠️ Channel {channel.name} missing chat_id.")
                continue

            joined = await check_user_in_channel(user_id, channel.chat_id, bot)
            if not joined:
                not_joined.append(channel)

        if not_joined:
            await state.update_data(next_action="start_lesson", course_id=course_id)

            markup = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text=f"➕ {ch.name}",
                            url=ch.invite_link  # ✅ Always a full valid invite link
                        )
                    ]
                    for ch in not_joined if ch.invite_link
                ]
            )
            markup.inline_keyboard.append([
                InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_channels")
            ])

            await call.message.answer(
                "❗️ Davom etishdan oldin quyidagi kanallarga obuna bo‘ling:",
                reply_markup=markup
            )
            return

        user = CustomUser.objects.filter(chat_id=user_id).first()
        if not user:
            await call.message.answer("❗️ Foydalanuvchi topilmadi.")
            return

        await call.message.answer(
            text="📚 Avvalo kurs darajasini tanlang:",
            reply_markup=course_levels(course_id=course_id),
        )

    except Exception as e:
        logger.error(f"Error in handle_start_lesson: {e}")
        await call.message.answer("Xatolik yuz berdi. Qayta urinib ko‘ring.")


@dp.callback_query(lambda c: c.data == "check_channels")
async def recheck_channels(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    try:
        user_id = call.from_user.id
        channels = Channel.objects.all()
        not_joined = []

        for channel in channels:
            if channel.username and not channel.username.startswith("+"):
                chat_id = f"@{channel.username}"
            elif channel.chat_id:
                chat_id = channel.chat_id
            else:
                print(f"⚠️ Channel {channel.name} has invalid username/chat_id.")
                continue

            joined = await check_user_in_channel(user_id, chat_id, bot)
            if not joined:
                not_joined.append(channel)

        if not_joined:
            await call.answer("❌ Hali hamma kanallarga obuna emassiz.", show_alert=True)
            return

        data = await state.get_data()
        next_action = data.get("next_action")
        course_id = data.get("course_id")

        if next_action == "start_lesson" and course_id:
            await call.message.answer(
                text="📚 Avvalo kurs darajasini tanlang:",
                reply_markup=course_levels(course_id=course_id),
            )
            return

        courses = StudentCourse.objects.filter(user__chat_id=user_id)
        if not courses.exists():
            await call.message.answer("❗️ Kurslar mavjud emas.")
            return

        await state.update_data(current_course_index=0)
        await send_my_course(call.message.chat.id, 0)
        await state.set_state(User.browsing_my_courses)

    except Exception as e:
        logger.error(f"Error in recheck_channels: {e}")
        await call.message.answer("Xatolik yuz berdi. Qayta urinib ko‘ring.")


@dp.callback_query(lambda c: c.data.startswith("theme_page:"))
async def handle_theme_page(call: CallbackQuery, state: FSMContext):
    try:
        page = int(call.data.split(":")[1])
        data = await state.get_data()

        logger.info(f"FSM State Data: {data}")

        course_id = data.get("course_id")
        level_id = data.get("level_id")

        if not course_id or not level_id:
            await call.message.answer("❗️ Ma'lumotlar topilmadi. Iltimos, qayta urinib ko'ring.")
            return

        markup = themes_attendance([course_id], call.from_user.id, level_id, page=page)
        await call.message.edit_reply_markup(reply_markup=markup)

    except Exception as e:
        logger.error(f"Error in handle_theme_page: {e}")
        await call.message.answer("❌ Xatolik yuz berdi.")


@dp.callback_query(lambda c: c.data.startswith(("select_level_", "go_back")))
async def handle_select_level(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)

    if call.data == "go_back":
        await call.message.answer("Siz menu bulimiga qaytingiz!", reply_markup=user_menu())
        await call.message.delete()
        await state.clear()
        return

    try:
        parts = call.data.split("_")
        level_id = parts[2]
        print("level", level_id)

        course = StudentCourse.objects.filter(
            user__chat_id=call.from_user.id,
            course__course_type__id=level_id
        ).first()

        if not course:
            await call.message.answer("❌ Kurs aniqlanmadi.", reply_markup=course_levels(course_id="fallback"))
            return

        course_id = str(course.course.id)  # ✅ ensure it's a string

        # ✅ FIX HERE: Store BOTH course_id and level_id into state
        await state.update_data(course_id=course_id, level_id=level_id)

        await call.message.answer(
            text="📘 Endi mavzuni tanlang:",
            reply_markup=themes_attendance([course_id], call.from_user.id, level_id)
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

        reply_markup = get_theme_buttons(str(theme.id), call.from_user.id)
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

    theme = Theme.objects.filter(id=theme_id).first()
    if not theme:
        await call.message.answer("❌ Mavzu topilmadi.")
        return

    course_ids = list(theme.course.values_list("id", flat=True))
    level = theme.course_type.first()
    if not level:
        await call.message.answer("❌ Kurs darajasi aniqlanmadi.")
        return

    theme_att = ThemeAttendance.objects.filter(
        theme_id=theme_id,
        user__chat_id=call.from_user.id,
    ).first()

    if not theme_att:
        await call.message.answer(
            text=f"👮🏻‍♂️ Siz {theme.name} mavzusini hali boshlamagansiz ⁉️",
            reply_markup=themes_attendance(
                course_id=course_ids,
                user_id=call.from_user.id,
                level_id=level.id
            )
        )
        return

    theme_att.is_complete_test = True
    theme_att.save()

    await call.message.answer(
        text="✅ Siz mavzuni muvaffaqiyatli yakunladingiz!",
        reply_markup=themes_attendance(
            course_id=course_ids,
            user_id=call.from_user.id,
            level_id=level.id
        )
    )


@dp.callback_query(lambda c: c.data.startswith("theme_already_completed_"))
async def finishing_the_same(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    course_id = call.data.split("_")[3]

    print(course_id)

    course = Course.objects.filter(id=course_id).first()
    level = course.course_type.first().id
    user = CustomUser.objects.filter(chat_id=call.from_user.id).first()
    ic(level)

    await call.message.answer(
        text="Kursingizning mavzularidan birini tanlang.",
        reply_markup=themes_attendance([course_id], user, level)
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


@dp.message(lambda msg: msg.text == "🎁 Qo'shimcha materiallar")
async def examples(message: Message, state: FSMContext):
    await message.answer(
        text="Quyidagi kategoriyalardan birini tanlang:",
        reply_markup=materials_category()
    )
    await state.set_state(MaterialState.selecting_category)


@dp.message(MaterialState.selecting_category)
async def select_category(message: Message, state: FSMContext):
    if message.text == "🔙 Ortga":
        await message.answer("Bosh menyuga qaytdingiz.", reply_markup=user_menu())
        await state.clear()
        return

    try:
        category = MaterialsCategories.objects.get(category=message.text.strip())
    except MaterialsCategories.DoesNotExist:
        await message.answer("❌ Bunday kategoriya mavjud emas.")
        return

    materials = Materials.objects.filter(choice=category).order_by("-created_at")
    if not materials.exists():
        await message.answer("❗ Bu kategoriyada hech qanday material mavjud emas.")
        return

    await state.update_data(category_id=category.id, page=0)
    await state.set_state(MaterialState.file)

    await send_paginated_material(message, category.id, page=0, state=state)


async def send_paginated_material(msg_obj, category_id, page, state):
    from aiogram.types import CallbackQuery, Message

    if isinstance(msg_obj, CallbackQuery):
        sender = msg_obj.message
        user = msg_obj.from_user
        if msg_obj.data == "🔙 Ortga":
            await msg_obj.message.answer(
                "Bosh menyuga qaytdingiz.",
                reply_markup=user_menu()
            )
    else:
        sender = msg_obj
        user = msg_obj.from_user

        if msg_obj.text == "🔙 Ortga":
            await msg_obj.answer(
                "Bosh menyuga qaytdingiz.",
                reply_markup=user_menu()
            )


    materials = Materials.objects.filter(choice_id=category_id).order_by("-created_at")
    total = materials.count()

    if page < 0 or page >= total:
        if isinstance(msg_obj, CallbackQuery):
            await msg_obj.answer("⛔ Bu sahifa mavjud emas.", show_alert=True)
        else:
            await msg_obj.answer("⛔ Bu sahifa mavjud emas.")
        return

    material = materials[page]
    caption = f"📌 {material.title}"
    file_type = material.choice.type

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Oldingi", callback_data="material_prev"),
            InlineKeyboardButton(text="Keyingi ➡️", callback_data="material_next"),
        ],
        [InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_list")]
    ])

    # Support both CallbackQuery and Message
    if isinstance(msg_obj, CallbackQuery):
        sender = msg_obj.message
    else:
        sender = msg_obj

    if file_type == "Video":
        await sender.answer_video(video=material.telegram_id, caption=caption, reply_markup=keyboard, protect_content=True)
    elif file_type == "Audio":
        await sender.answer_audio(audio=material.telegram_id, caption=caption, reply_markup=keyboard, protect_content=True)
    elif file_type == "Document":
        await sender.answer_document(document=material.telegram_id, caption=caption, reply_markup=keyboard, protect_content=True)
    elif file_type == "Image":
        await sender.answer_photo(photo=material.telegram_id, caption=caption, reply_markup=keyboard, protect_content=True)
    else:
        await sender.answer(f"{caption}\n❓ Noma'lum fayl turi.")



@dp.callback_query(lambda c: c.data in ["material_next", "material_prev","back_to_list"], StateFilter(MaterialState.file))
async def paginate_materials(callback: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    category_id = data.get("category_id")
    page = data.get("page", 0)

    print(callback.data)

    if callback.data == "back_to_list":
        await callback.message.delete()
        await callback.message.answer(
            text="Quyidagi kategoriyalardan birini tanlang:",
            reply_markup=materials_category()
        )
        await state.clear()
        await state.set_state(MaterialState.selecting_category)
        return

    page += 1 if callback.data == "material_next" else -1

    materials_count = Materials.objects.filter(choice_id=category_id).count()
    if page < 0 or page >= materials_count:
        await callback.answer("⛔ Bu yo‘nalishda boshqa material yo‘q.", show_alert=True)
        return
    await callback.message.delete()
    await state.update_data(page=page)
    await send_paginated_material(callback, category_id, page, state)



@dp.callback_query(lambda c: c.data == "back_to_list", StateFilter(MaterialState.file))
async def back_to_material_list(callback: CallbackQuery, state: FSMContext):

    print(callback.data)

    await callback.message.delete()
    if callback.data == "back_to_list":
        await callback.message.answer(
            text="Quyidagi kategoriyalardan birini tanlang:",
            reply_markup=materials_category()
        )
        await state.clear()
        await state.set_state(MaterialState.selecting_category)


    data = await state.get_data()
    category_id = data.get("category_id")

    try:
        category = MaterialsCategories.objects.get(id=category_id)
        materials = Materials.objects.filter(choice=category).order_by("-created_at")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{i + 1}. {m.title}", callback_data=f"material_index:{i}")]
            for i, m in enumerate(materials)
        ])
        keyboard.inline_keyboard.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="back_to_list")])

        await callback.message.answer(f"📂 *{category.category}* kategoriyasidagi materiallar:",
                                      reply_markup=keyboard, parse_mode="Markdown")
    except:
        await callback.message.answer("❌ Ro'yxatga qaytishda xatolik.")
