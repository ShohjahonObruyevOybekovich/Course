from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, FSInputFile
)
from django.db.models import Sum

from account.models import CustomUser
from dispatcher import dp, TOKEN
from shop.models import Product, Order
from tg_bot.buttons.inline import order_accept
from tg_bot.state.main import Products_State

bot = Bot(token=TOKEN)

PRODUCTS_PER_PAGE = 1  # show one product per page like a slide

@dp.message(lambda message: message.text == "🛒 Shop")
async def show_products_menu(message: Message, state: FSMContext):
    await state.set_state(Products_State.products)
    await show_products_page(message.chat.id, page=1)

def build_product_detail_markup(product_id: str, current_page: int, total_pages: int):
    buttons = []

    # Always show both navigation buttons
    nav = [
        InlineKeyboardButton(text="⬅️", callback_data=f"page_{current_page - 1}"),
        InlineKeyboardButton(text="➡️", callback_data=f"page_{current_page + 1}")
    ]
    buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="💳 Sotib olish", callback_data=f"buy_{product_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"page_{current_page}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def show_products_page(chat_id: int, page: int,call: CallbackQuery = None):
    all_products = Product.objects.all()
    total_products = all_products.count()
    total_pages = (total_products + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE

    if page < 1 or page > total_pages:
        if call:
            await call.answer("❌ Maxsulot mavjud emas!", show_alert=True)
        else:
            await bot.send_message(chat_id=chat_id, text="❌ Maxsulot mavjud emas!")
        return

    product = all_products[(page - 1):(page)][0]
    total_quantity = Order.objects.filter(product=product, status="Accepted").aggregate(total=Sum("quantity"))['total'] or 0
    remaining = product.quantity - total_quantity
    caption = (
        f"⭐️ <b>{product.name}</b>\n\n"
        f"{product.description}\n\n"
        f"📦 Qolgan: <b>{remaining}</b> / {product.quantity}\n"
        f"💰 Narxi: <b>{product.price} ball</b>\n"
    )
    keyboard = build_product_detail_markup(product_id=str(product.id), current_page=page, total_pages=total_pages)

    if product.photo:
        photo = FSInputFile(product.photo.file.path)
        await bot.send_photo(chat_id, photo=photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
    else:
        await bot.send_message(chat_id, text=caption, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(lambda call: call.data.startswith("page_"))
async def handle_page_navigation(call: CallbackQuery):
    await call.answer()
    page = int(call.data.split("_")[1])

    total_products = Product.objects.count()
    total_pages = (total_products + PRODUCTS_PER_PAGE - 1) // PRODUCTS_PER_PAGE

    if page < 1 or page > total_pages:
        await call.answer("❌ Mahsulot mavjud emas!", show_alert=True)
        return

    await call.message.delete()
    await show_products_page(call.message.chat.id, page,call=call)

@dp.callback_query(lambda call: call.data.startswith("buy_"))
async def buy_product(call: CallbackQuery):
    await call.message.delete()
    product_id = call.data.split("_")[1]
    product = Product.objects.filter(id=product_id).first()
    user = CustomUser.objects.filter(chat_id=call.from_user.id).first()

    if not product:
        await call.message.answer("❌ Maxsulot topilmadi.")
        return

    total_quantity = Order.objects.filter(product=product, status="Accepted").aggregate(total=Sum("quantity"))['total'] or 0
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

    admins = CustomUser.objects.filter(role="Admin", chat_id__isnull=False)

    for admin in admins:
        if not admin.chat_id:
            continue
        print(f"Admin: {admin.full_name}, chat_id: {admin.chat_id} ({type(admin.chat_id)})")

        caption = (
            f"👨‍🏫 Talaba <b>{user.full_name}</b>\n"
            f"📲 Nomeri <b>{user.phone}</b>\n"
            f"📝 <b>{product.name}</b>\n\n"
            f"💰 Narxi: <b>{product.price}</b> ball\n"
            f"📦 Qolgan: <b>{remaining}</b> / {product.quantity}\n"
            f"📝 Tavsif:\n{product.description}"
        )
        photo = FSInputFile(product.photo.file.path)
        await bot.send_photo(
            photo=photo,
            chat_id=admin.chat_id,
            caption=caption,
            reply_markup=order_accept(product, user),
            parse_mode="HTML"
        )