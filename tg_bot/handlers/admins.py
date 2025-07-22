from aiogram import Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, \
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist
from icecream import ic

from account.models import CustomUser
from dispatcher import dp, TOKEN
from idioms.models import MaterialsCategories, Materials
from shop.models import Product, Order
from studentcourse.models import StudentCourse
from tg_bot.buttons.inline import start_btn
from tg_bot.buttons.reply import phone_number_btn, results, admin, user_menu, materials_category, back
from tg_bot.buttons.text import start_txt, natija_txt
from tg_bot.state.main import User, Materials_State, CourseMaterials_State
from tg_bot.utils import format_phone_number
from theme.models import ThemeExamples
from transaction.models import Transaction

bot = Bot(token=TOKEN)

@dp.message(lambda message: message.text == "Admin_parol")
async def admin_btn(message: Message):
    user = CustomUser.objects.filter(chat_id=message.chat.id).first()
    if user:
        user.role = "Admin"
        user.save()
        await message.answer(
            text="Sizning rolingiz <b>Admin</b> darajasiga oshirildi.",
            reply_markup=admin()
        )


@dp.message(lambda msg:msg.text == "👥 O'quvchilar ro‘yxati")
async def handle_users(message: Message, state: FSMContext) -> None:
    await state.set_state(User.user)
    button = InlineKeyboardButton(
        text="Qidirish 🔍",  # Button text
        switch_inline_query_current_chat=""
        # This will be used to handle the button press
    )
    back = InlineKeyboardButton(
        text = "🔙 Ortga",
        callback_data="back_to_admin"
    )
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[[button], [back]])
    await message.answer("👤 Talabalarni tanlang yoki qidiring:",
                         reply_markup=inline_keyboard)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@dp.message(F.text.startswith("loc:"))
async def send_maps_button(message: Message):
    try:
        # coords = message.text[4:].strip().split(",")
        lat, lon = float(39.954143), float(65.890482)
        url = f"https://www.google.com/maps?q={lat},{lon}"

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[
                InlineKeyboardButton(text="📍 Ko'rish Google Maps’da", url=url)
            ]]
        )

        await message.answer("Tanlangan lokatsiya:", reply_markup=keyboard)
    except Exception:
        await message.answer("❌ Noto‘g‘ri format. Foydalanish: loc:41.2995,69.2401")

@dp.callback_query(lambda c: c.data == "back_to_admin")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("🔙 Asosiy admin menyuga qaytdingiz.",reply_markup=admin())
    return


@dp.inline_query()
async def search_customers(inline_query: InlineQuery):
    raw_query = inline_query.query.strip()

    # Default pagination
    page = 1
    page_size = 50

    if "#page=" in raw_query:
        try:
            query_part, page_str = raw_query.split("#page=")
            page = int(page_str)
            query = query_part.strip()
        except Exception:
            query = raw_query
    else:
        query = raw_query

    offset = (page - 1) * page_size
    users = CustomUser.objects.filter(role="User", full_name__icontains=query)[offset:offset + page_size]

    results = []
    for user in users:
        results.append(
            InlineQueryResultArticle(
                id=str(user.chat_id),
                title=f"{user.full_name} ({user.phone})",
                input_message_content=InputTextMessageContent(
                    message_text=f"👤 Tanlangan talaba:\nID: {user.chat_id} \n{user.full_name} ({user.phone})"
                ),
                description="Talaba haqida ma'lumot"
            )
        )

    # Add "Next page" dummy result
    if users.count() == page_size:
        results.append(
            InlineQueryResultArticle(
                id=f"next-page-{page + 1}",
                title=f"➡️ Show more results (Page {page + 1})",
                input_message_content=InputTextMessageContent(
                    message_text=f"Type: <code>{query} #page={page + 1}</code>"
                ),
                description="Click to copy pagination query",
            )
        )

    await inline_query.answer(results[:50], cache_time=0, is_personal=True)


@dp.message(User.user)
async def handle_customer_selection(message: Message, state: FSMContext):

    parts = message.text.split()
    if "ID:" in parts:
        phone_index = parts.index("ID:")
        user_id: int = parts[phone_index + 1]
        user = CustomUser.objects.filter(chat_id=user_id).first()

        if not user:
            await message.answer("❌ Bunday foydalanuvchi topilmadi.")
            await state.clear()
            return

        courses = StudentCourse.objects.filter(user=user).all()
        if not courses:
            await message.answer("❌ Talaba uchun hech qanday kurs topilmadi.")
            await state.clear()
            return

        transaction = Transaction.objects.filter(user=user).first()
        status = transaction.status if transaction else None
        status_txt = (
            "To'lov kutilmoqda" if status == "Pending"
            else "To'lov amalga oshirilgan" if status == "Accepted"
            else "To'lov bekor qilingan" if status == "Rejected"
            else "Holat mavjud emas"
        )

        caption_text = "\n\n".join(
            "\n".join([
                "📋 <b>Talabaning kursi</b>\n",
                f"👤 <b>Talaba ismi:</b> {user.full_name}",
                f"📞 <b>Telefon raqami:</b> {user.phone if user.phone else 'Nomaʼlum'}",
                f"🎯 <b>Kursi:</b> {course.course.name if course.course.name else 'Nomaʼlum'}",
                f"💵 <b>Kurs summasi:</b> {course.course.price or 0}",
                f"⚙️ <b>Kurs holati:</b> {status_txt}",
                f"🕒 <b>Sotib olgan vaqti:</b> {course.created_at.strftime('%d.%m.%Y %H:%M')}"
            ])
            for course in courses
        )

        await message.answer(text=caption_text, reply_markup=admin(), parse_mode="HTML")
        await state.clear()


@dp.callback_query(lambda c: c.data.startswith("accepted:") or c.data.startswith("cancelled:"))
async def handle_admin_decision(callback: CallbackQuery):
    await callback.message.edit_reply_markup(reply_markup=None)
    action, user_id = callback.data.split(":")
    user = await CustomUser.objects.aget(chat_id=user_id)

    # Get the latest pending transaction
    transaction = await Transaction.objects.filter(user=user, status="Pending").afirst()

    if not transaction:
        await callback.answer("❗ Bu to'lov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    if action == "accepted":
        transaction.status = "Accepted"
        transaction.save()

        course = StudentCourse.objects.filter(user=user,status="Inactive").first()
        course.status = "Active"
        course.save()

        # Notify user
        await bot.send_message(
            chat_id=user.chat_id,
            text=f"✅ {transaction.amount} to‘lovingiz admin tomonidan tasdiqlandi.\n {course.course.name} kursiga yozildingiz.",
            reply_markup=user_menu()
        )
        await callback.message.edit_reply_markup()  # Remove buttons
        await callback.answer("✅ To'lov tasdiqlandi.")
    else:
        transaction.status = "Rejected"
        transaction.save()

        await bot.send_message(
            chat_id=user.chat_id,
            text="❌ To‘lovingiz admin tomonidan bekor qilindi. Iltimos, qayta urinib ko‘ring.",
            reply_markup=user_menu()
        )
        await callback.message.edit_reply_markup()  # Remove buttons
        await callback.answer("🗑 To'lov bekor qilindi.")


# shop order accept
@dp.callback_query(lambda call: call.data.startswith("ac_"))
async def approve_order(call: CallbackQuery):
    _, product_id, user_id = call.data.split("_")
    product = Product.objects.filter(id=product_id).first()
    user = CustomUser.objects.filter(id=user_id).first()

    if not product or not user:
        await call.message.answer("❌ Maxsulot yoki foydalanuvchi topilmadi.")
        return

    order = Order.objects.filter(product=product, user=user, status="Pending").first()
    if not order:
        await call.message.answer("❌ Buyurtma topilmadi yoki allaqachon ko'rib chiqilgan.",show_alert=True)
        return

    # Update status to Accepted
    order.status = "Accepted"
    order.save()

    await call.message.edit_text("✅ Buyurtma qabul qilindi.")

    # Notify the buyer
    await bot.send_message(
        chat_id=user.chat_id,
        text=f"✅ Sizning {product.name} bo‘yicha buyurtmangiz tasdiqlandi!\n"
             f"Iltimos, markazga borib maxsulotni olib keting.",
        reply_markup=user_menu()
    )

# shop order cancel
@dp.callback_query(lambda call: call.data.startswith("can_"))
async def reject_order(call: CallbackQuery):
    _, product_id, user_id = call.data.split("_")
    product = Product.objects.filter(id=product_id).first()
    user = CustomUser.objects.filter(id=user_id).first()

    if not product or not user:
        await call.message.answer("❌ Maxsulot yoki foydalanuvchi topilmadi.")
        return

    order = Order.objects.filter(product=product, user=user, status="Pending").first()
    if not order:
        await call.message.answer("❌ Buyurtma topilmadi yoki allaqachon ko'rib chiqilgan.",show_alert=True)
        return

    # Refund and delete the order
    user.balance += product.price
    user.save()
    order.delete()

    await call.message.edit_text("❌ Buyurtma rad etildi.")

    # Notify the buyer
    await bot.send_message(
        chat_id=user.chat_id,
        text=f"❌ Afsuski, sizning {product.name} bo‘yicha buyurtmangiz rad etildi.\n"
             f"{product.price} tanga balansingizga qaytarildi.",
        reply_markup=user_menu()
    )



# Step 1: Boshlanish
@dp.message(lambda msg: msg.text == "⚙️ Materiallar yuklash")
async def materiallar(message: Message, state: FSMContext):
    await message.answer(
        text="Avval materiallar categoryasini tanlang:",
        reply_markup=materials_category()
    )
    await state.set_state(Materials_State.category)


# Step 2: Kategoriya tanlash
@dp.message(Materials_State.category)
async def category(message: Message, state: FSMContext):
    if message.text == "🔙 Ortga":
        await message.answer(
            text="Admin bo'limiga qaytdingiz.",
            reply_markup=admin()
        )
        await state.clear()
        return

    try:
        MaterialsCategories.objects.get(category=message.text)
    except MaterialsCategories.DoesNotExist:
        await message.answer("❌ Bunday kategoriya mavjud emas. Qayta tanlang.")
        return

    await state.update_data(category=message.text)

    await message.answer(
        text="Endi file yoki video, audio ni yuboring 👇",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="🔙 Ortga")]],
            resize_keyboard=True
        )
    )

    await state.set_state(Materials_State.file)


# Step 3: Fayl qabul qilish va validatsiya
@dp.message(Materials_State.file)
async def file_handler(message: Message, state: FSMContext):
    if message.text == "🔙 Ortga":
        await message.answer(
            text="Admin bo'limiga qaytdingiz.",
            reply_markup=admin()
        )
        await state.clear()
        return

    if not (message.document or message.video or message.audio or message.photo):
        await message.answer("❌ Faqat video, audio yoki fayl yuboring. Rasm va matn qabul qilinmaydi.")
        return

    data = await state.get_data()
    category_name = data.get("category")

    try:
        category = MaterialsCategories.objects.get(category=category_name)
    except ObjectDoesNotExist:
        await message.answer("❌ Kategoriya topilmadi. Qaytadan urinib ko'ring.")
        return

    expected_type = category.type
    file_type = None
    file_id = None

    if message.video:
        file_type = "Video"
        file_id = message.video.file_id
    elif message.audio:
        file_type = "Audio"
        file_id = message.audio.file_id
    elif message.document:
        file_type = "Document"
        file_id = message.document.file_id
    elif message.photo:
        file_type = "Image"
        file_id = message.photo[-1].file_id

    if file_type != expected_type:
        await message.answer(f"❌ Bu kategoriya faqat '{expected_type}' fayllarni qabul qiladi.")
        return

    # Fayl to'g'ri — vaqtincha saqlaymiz
    await state.update_data(file_id=file_id)

    await message.answer("📌 Endi material uchun sarlavha (title) yuboring:", reply_markup=ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Ortga")]], resize_keyboard=True
    ))
    await state.set_state(Materials_State.title)


# Step 4: Title kiritish
@dp.message(Materials_State.title)
async def material_title_handler(message: Message, state: FSMContext):
    if message.text == "🔙 Ortga":
        await message.answer(
            text="Admin bo'limiga qaytdingiz.",
            reply_markup=admin()
        )
        await state.clear()
        return

    title = message.text.strip()
    data = await state.get_data()

    category_name = data.get("category")
    file_id = data.get("file_id")

    try:
        category = MaterialsCategories.objects.get(category=category_name)
    except MaterialsCategories.DoesNotExist:
        await message.answer("❌ Kategoriya mavjud emas.")
        await state.clear()
        return

    # DB ga yozish
    Materials.objects.create(
        title=title,
        choice=category,
        type="Telegram",
        telegram_id=file_id,
    )

    await message.answer("✅ Material sarlavhasi bilan birga muvaffaqiyatli saqlandi.", reply_markup=admin())
    await state.clear()


@dp.message(lambda msg: msg.text == "📒 Qo'shimcha Video yuklash")
async def example_materials_handler(message: Message, state: FSMContext):
    await message.answer(
        text="Qo'shimcha videolarni yuboring 👇",
        reply_markup=back()
    )
    await state.set_state(CourseMaterials_State.video)


@dp.message(CourseMaterials_State.video)
async def example_materials_video_handler(message: Message, state: FSMContext):
    if message.text == "🔙 Ortga":
        await message.answer("Admin bo'limiga qaytdingiz.",reply_markup=admin())
        await state.clear()
        return
    if not (message.video):
        await message.answer("❌ Faqat video yuboring. Rasm va matn qabul qilinmaydi.")
        return

    file_id = None
    if message.video:
        file_id = message.video.file_id
        await state.update_data(file_id=file_id)

    await message.answer(text="Endi video nomini yuboring 👇",reply_markup=back())
    await state.set_state(CourseMaterials_State.name)


@dp.message(CourseMaterials_State.name)
async def example_materials_name_handler(message: Message, state: FSMContext):
    if message.text == "🔙 Ortga":
        await message.answer("Endi video nomini yuboring 👇",reply_markup=admin())
        await state.set_state(CourseMaterials_State.video)
        return

    if message.text:
        name = message.text.strip()
        await state.update_data(name=name)

    await message.answer("Endi video mazmunini yuboring 👇",reply_markup=back())
    await state.set_state(CourseMaterials_State.description)


@dp.message(CourseMaterials_State.description)
async def example_materials_description_handler(message: Message, state: FSMContext):
    if message.text == "🔙 Ortga":
        await message.answer("Endi video mazmunini yuboring 👇", reply_markup=admin())
        await state.set_state(CourseMaterials_State.description)
        return

    if message.text:
        description = message.text.strip()

        data = await state.get_data()
        name = data.get("name")
        description = message.text.strip()
        file_id = data.get("file_id")
        example = ThemeExamples.objects.create(
            name=name,
            description=description,
            video=file_id,
            link=None
        )

        if message:
            await message.answer("📒 Qo'shimcha Video yuklash yakunlandi.",reply_markup=admin())
    await state.clear()

