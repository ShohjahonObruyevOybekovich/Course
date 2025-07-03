from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
)
from django.db.models import Sum

from account.models import CustomUser
from dispatcher import dp, TOKEN
from shop.models import Product, Order  # Replace with your actual app name
from tg_bot.state.main import Products_State

bot = Bot(token=TOKEN)


PRODUCTS_PER_PAGE = 5

def build_product_page(products, page: int, total_pages: int):
    buttons = []
    for product in products:
        buttons.append([
            InlineKeyboardButton(
                text=f"{product.name} ({product.price} tanga)",
                callback_data=f"product_{product.id}"
            )
        ])

    navigation = []
    if page > 1:
        navigation.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"page_{page - 1}"))
    if page < total_pages:
        navigation.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"page_{page + 1}"))
    if navigation:
        buttons.append(navigation)

    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(lambda message: message.text == "🛒 Shop")
async def show_products_menu(message: Message, state: FSMContext):
    await state.set_state(Products_State.products)
    await show_products_page(message.chat.id, page=1)

async def show_products_page(chat_id: int, page: int):
    all_products = Product.objects.all()
    total_products = all_products.count()
    total_pages = (total_products + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE

    start = (page - 1) * PRODUCTS_PER_PAGE
    end = start + PRODUCTS_PER_PAGE
    page_products = all_products[start:end]

    markup = build_product_page(page_products, page, total_pages)
    await bot.send_message(chat_id=chat_id, text="🏍 Sovg'alar ro'yxati:", reply_markup=markup)

@dp.callback_query(lambda call: call.data.startswith("page_"))
async def handle_page_navigation(call: CallbackQuery):
    page = int(call.data.split("_")[1])
    await call.message.delete()
    await show_products_page(call.message.chat.id, page)

@dp.callback_query(lambda call: call.data.startswith("product_"))
async def show_product_details(call: CallbackQuery):
    product_id = int(call.data.split("_")[1])
    product = Product.objects.filter(id=product_id).first()
    user = CustomUser.objects.filter(chat_id=call.from_user.id).first()

    if not product:
        await call.message.answer("❌ Maxsulot topilmadi.")
        return

    total_quantity = Order.objects.filter(product=product, status="Accepted").aggregate(total=Sum("quantity"))["total"] or 0
    remaining = product.quantity - total_quantity
    photo = product.photo.first()  # Assuming product.photo is a related_name manager

    caption = (
        f"⭐️ <b>{product.name}</b>\n\n"
        f"{product.description}\n\n"
        f"📦 Qolgan: <b>{remaining}</b> / {product.quantity}\n"
        f"💰 Narxi: <b>{product.price} so'm</b>\n"
        f"📅 <i>1 yillik foydalanish uchun</i>\n"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("✅ Tasdiqlangan", callback_data="noop")],
        [InlineKeyboardButton("📘 Darsni boshlash", callback_data=f"buy_{product.id}")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="page_1")]
    ])

    if photo:
        await call.message.answer_photo(photo=photo.url, caption=caption, reply_markup=keyboard, parse_mode="HTML")
    else:
        await call.message.answer(caption, reply_markup=keyboard, parse_mode="HTML")


@dp.callback_query(lambda call: call.data.startswith("buy_"))
async def buy_product(call: CallbackQuery):
    product_id = int(call.data.split("_")[1])
    product = Product.objects.filter(id=product_id).first()
    user = CustomUser.objects.filter(chat_id=call.from_user.id).first()

    if not product:
        await call.message.answer("❌ Maxsulot topilmadi.")
        return

    total_quantity = Order.objects.filter(product=product, status="Accepted").aggregate(total=Sum("quantity"))["total"] or 0
    remaining = product.quantity - total_quantity

    if remaining <= 0:
        await call.message.answer("❌ Maxsulot hozirda mavjud emas!")
        return

    if user.balance < product.price:
        await call.message.answer("⁉️ Hisobda yetarli mablag' mavjud emas.")
        return

    order = Order.objects.create(product=product, user=user, quantity=1, status="Pending")
    user.balance -= product.price
    user.save()

    await call.message.answer("✅ Buyurtma yuborildi. Tasdiqlanishini kuting.")

    admins = CustomUser.objects.filter(role="Admin")
    for admin in admins:
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
