from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from decouple import config

from account.models import CustomUser
from dispatcher import dp
from tg_bot.buttons.inline import referral_buttons

TOKEN = config('BOT_USERNAME')
@dp.message(lambda msg: msg.text == "🔗 Referral yuborish")
async def referral(message: Message, state: FSMContext):
    user = CustomUser.objects.filter(chat_id=message.chat.id).first()

    if not user:
        await message.answer("❌ Siz hali ro'yxatdan o'tmagansiz. /start orqali boshlang.")
        return

    ref_link = f"https://t.me/{TOKEN}?start={user.referral_code}"
    referral_count = user.referrals.count()

    text = (
        f"📢 *Do'stlaringizni taklif qiling!*\n\n"
        f"👉 Sizning referral havolangiz:\n`{ref_link}`\n\n"
        f"👥 Siz orqali qo‘shilganlar soni: *{referral_count}* ta\n\n"
        f"📨 Quyidagi tugma orqali do‘stingizga jo‘nating!"
    )

    if referral_count > 0:
        text += f"\n🎁 Sizga {referral_count} / 10 foydalanuvchi qo‘shildi! Bonusga ega bo‘lish imkoningiz bor."
    else:
        text += f"\n🚀 {10 - referral_count} ta do‘stingizni taklif qiling va bonusga ega bo‘ling."

    await message.answer(text, parse_mode="Markdown", reply_markup=referral_buttons(ref_link))

