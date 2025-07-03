from aiogram import Bot, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto, InlineKeyboardButton, \
    InlineKeyboardMarkup
from aiogram.utils.chat_action import logger
from datetime import datetime
from decouple import config
from icecream import ic

from account.models import CustomUser
from bot.tasks import TelegramBot
from channel.models import Channel
from course.models import Course
from dispatcher import dp, TOKEN
from studentcourse.models import StudentCourse
from tg_bot.buttons.inline import course_navigation_buttons, admin_accept, my_course_navigation_buttons, \
    get_theme_buttons, themes_attendance, start_btn, course_levels
from tg_bot.buttons.reply import phone_number_btn, results, admin, user_menu, back
from tg_bot.buttons.text import start_txt, natija_txt
from tg_bot.state.main import User, Products_State
from tg_bot.utils import format_phone_number, check_user_in_channel, send_theme_material
from theme.models import ThemeAttendance, Theme, ThemeExamples
from transaction.models import Transaction

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, \
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent, CallbackQuery

bot = TelegramBot()


@dp.message(lambda message: message.text == "🛒 Shop")
async def my_courses(message: Message, state: FSMContext):
    await state.set_state(Products_State.products)
    button = InlineKeyboardButton(
        text="Qidirish 🔍",  # Button text
        switch_inline_query_current_chat="product:"
        # This will be used to handle the button press
    )
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])

    await message.answer(text="🛍 Sovg'alar ro'yxati", reply_markup=inline_keyboard)


@dp.inline_query()
async def search_products(inline_query: InlineQuery):
    query = inline_query.query.strip()

    if not query.startswith("product:"):
        return  # Ignore irrelevant inline queries

    keyword = query.replace("product:", "").strip()

    if not keyword:
        await inline_query.answer([], cache_time=0)
        return  # Don't query with empty keyword

    products = Product.objects.filter(name__icontains=keyword)[:25]

    results = []
    for product in products:
        total_quantity = Order.objects.filter(
            product=product,
            status="Accepted"
        ).aggregate(total=Sum("quantity"))["total"] or 0
        remaining = product.quantity - total_quantity
        photo_url = product.photo.first().url if product.photo.exists() else "Rasm mavjud emas"

        results.append(
            InlineQueryResultArticle(
                id=f"product_{product.id}",
                title=product.name,
                input_message_content=InputTextMessageContent(
                    message_text=f"🛍 {product.name}\n💸 {product.price} tanga\nQolgan: {remaining}"
                ),
                description=f"Narxi: {product.price} • Qolgan: {remaining}"
            )
        )

    await inline_query.answer(results, cache_time=0, is_personal=True)


@dp.message(Products_State.products)
async def handle_customer_selection(message: Message, state: FSMContext):
    try:
        parts = message.text.split()
        product_id = int(parts[parts.index("ID:") + 1])
    except (ValueError, IndexError):
        await message.answer("❌ Maxsulot ID topilmadi yoki noto‘g‘ri format.")
        return

    product = Product.objects.filter(id=product_id).first()
    if not product:
        await message.answer("❌ Maxsulot topilmadi.")
        return

    total_quantity = Order.objects.filter(
        status="Accepted", product=product
    ).aggregate(total=Sum("quantity"))["total"] or 0
    remaining = product.quantity - total_quantity
    photo_url = product.photo.first().url if product.photo.exists() else None

    caption = (
        f"🛍 <b>{product.name}</b>\n\n"
        f"💰 Narxi: <b>{product.price}</b> tanga\n"
        f"📦 Qolgan: <b>{remaining}</b> / {product.quantity}\n"
        f"📝 Tavsif:\n{product.description}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📥 Buyurtma berish", callback_data=f"buy_{product.id}")
    ]])

    if photo_url:
        await message.answer_photo(photo=photo_url, caption=caption, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(caption, reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(lambda call: call.data.startswith("buy_"))
async def buy_callback(call: CallbackQuery):
    id = call.data.split("_")[1]
    product = Product.objects.filter(id=id).first()
    user = CustomUser.objects.filter(chat_id=call.from_user.id).first()

    if product.quantity <= 0:
        await call.message.answer(
            text="Maxsulot hozirda mavjud emas!",
            reply_markup=user_menu()
        )

    if user.balance < product.price:
        await call.message.answer(
            text="⁉️ Sizning hisobingda yetarli coinlar mavjud emas.",
            reply_markup=user_menu()
        )
    order = Order.objects.create(
        product=product,
        user=user,
        quantity=1,
        status="Pending",
    )
    if order:

        user.balance -= order.price
        user.save()

        await call.message.answer(
            text="Sizning xaridingiz markazimiz administratsiyasiga yuborildi,\n"
                 "tasdiqlanganidan so'ng markazimizga borib maxsulotni olishingiz mumkin",
            reply_markup=user_menu()
        )

        admins = CustomUser.objects.filter(role="Admin")
        for admin in admins:
            remaining = product.quantity - total_quantity

            # Get photo (if available)
            photo = product.photo.first()
            photo_url = photo.url if photo else None

            # Send reply

            order = Order.objects.filter(
                status="Accepted",
                product=product,
            ).aggregate(
                total_quantity=Sum("quantity"),
            )
            total_quantity = order["total_quantity"] or 0

            caption = (
                f"👨‍🎓 Talaba <b>{user.full_name}</b>"
                f"📲 Nomeri <b>{user.phone}</b>"
                f"🛍 <b>{product.name}</b>\n\n"
                f"💰 Narxi: <b>{product.price}</b> tanga\n"
                f"📦 Qolgan: <b>{remaining}</b> / {product.quantity}\n"
                f"📝 Tavsif:\n{product.description}"
            )

            bot.send_message(
                chat_id=admin.chat_id,
                text=caption,
                reply_markup=order_accept(product, user)
            )

    else:
        await call.message.answer(
            "Buyurtma berib bo'lmadi",
        )
