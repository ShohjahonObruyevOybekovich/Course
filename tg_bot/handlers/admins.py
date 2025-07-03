from aiogram import Bot, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, \
    InlineQuery, InlineQueryResultArticle, InputTextMessageContent, CallbackQuery
from asgiref.sync import sync_to_async
from icecream import ic

from account.models import CustomUser
from dispatcher import dp, TOKEN
from studentcourse.models import StudentCourse
from tg_bot.buttons.inline import start_btn
from tg_bot.buttons.reply import phone_number_btn, results, admin, user_menu
from tg_bot.buttons.text import start_txt, natija_txt
from tg_bot.state.main import User
from tg_bot.utils import format_phone_number
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
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard=[[button]])
    await message.answer("👤 Talabalarni tanlang yoki qidiring:",
                         reply_markup=inline_keyboard)


@dp.inline_query()
async def search_customers(inline_query: InlineQuery):
    query = inline_query.query.strip()
    user = CustomUser.objects.filter(role="User", full_name__icontains=query).all()

    results = []
    for installment in user:
        results.append(
            InlineQueryResultArticle(
                id=str(installment.chat_id),
                title=f"{installment.full_name} ({installment.phone})",
                input_message_content=InputTextMessageContent(
                    message_text=f"👤 Tanlangan talaba:\nID: {installment.chat_id} \n{installment.full_name} ({installment.phone})"
                ),
                description="Talaba haqida ma'lumotni ko'rish"
            )
        )

    await inline_query.answer(results, cache_time=0, is_personal=True)



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
