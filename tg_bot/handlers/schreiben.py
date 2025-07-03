from unittest.mock import call

from icecream import ic

from account.models import CustomUser
from dispatcher import dp
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext

from studentcourse.models import UserTasks
from tg_bot.ai import GptFunctions
from tg_bot.buttons.reply import user_menu
from tg_bot.state.main import Theme_State
from tg_bot.utils import format_schreiben_result
from theme.models import Theme


gpt = GptFunctions()

@dp.callback_query(lambda c: c.data.startswith("schreiben_"))
async def schreiben(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)

    try:
        theme_id = call.data.split("_")[1]
    except IndexError:
        return await call.message.answer("Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

    theme = Theme.objects.filter(id=theme_id).first()
    if not theme:
        return await call.message.answer("Mavzu topilmadi.")

    theme_schreiben = theme.schreiben

    if theme_schreiben:
        # ✅ Save theme_id in state
        await state.update_data(theme_id=theme_id)

        # Then set the state
        await state.set_state(Theme_State.schreiben)

        text = f"*{theme_schreiben}* mavzusidagi schreiben uchun uz matningizni yuboring 👇"
        await call.message.answer(text, parse_mode="Markdown")
    else:
        await call.message.answer("Ushbu mavzu uchun schreiben topshirig'i topilmadi.")


import asyncio  # ensure this is imported at the top
from tg_bot.buttons.inline import course_levels

@dp.message(Theme_State.schreiben)
async def user_lang_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    theme_id = data.get("theme_id")

    user = CustomUser.objects.filter(chat_id=message.from_user.id).first()

    if not theme_id:
        return await message.answer("⚠️ Mavzu aniqlanmadi. Iltimos, qaytadan urinib ko'ring.")

    theme = Theme.objects.filter(id=theme_id).first()
    if not theme:
        return await message.answer("❌ Mavzu topilmadi.")

    first_type = theme.course_type.first()
    if first_type:
        await message.answer(f"📘 Bu mavzuning darajasi: <b>{first_type.name}</b>", parse_mode="HTML")
    else:
        await message.answer("⚠️ Bu mavzuga bog'langan kurs darajasi topilmadi.")

    user_answer = message.text
    full_prompt = f"Mavzu: {theme.schreiben}\nJavob: {user_answer}\nKurs darajasi: {first_type.name if first_type else 'Nomaʼlum'}"

    # ⏳ Show loading animation
    loading_msg = await message.answer("✍️ Matningiz qabul qilindi. AI baholamoqda...")
    await asyncio.sleep(0.8)
    await loading_msg.edit_text("🧠 AI baholamoqda..")
    await asyncio.sleep(0.8)
    await loading_msg.edit_text("🧠 AI baholamoqda...")

    # 🎯 Get GPT response
    intent_result = await gpt.prompt_to_json(str(message.from_user.id), full_prompt)
    ic(intent_result)

    await loading_msg.edit_text("✅ AI bahosi tayyor!")

    # 📝 Format and send result
    response_text = format_schreiben_result(intent_result)

    ball = intent_result.get("gesamtpunktzahl")
    has_done = UserTasks.objects.filter(user=user, choice="Schreiben", theme=theme).exists()

    if ball is not None and not has_done:
        UserTasks.objects.create(
            user=user,
            theme=theme,
            choice="Schreiben",
            ball=ball,
        )
        user.balance += ball
        user.save()

        response_text += f"\n\n💸 <b>Vazifa uchun ball:</b> <code>{ball}</code>"
        response_text += f"\n📈 <b>Jami ballaringiz:</b> <code>{user.balance}</code>"

    await message.answer(
        text=response_text,
        reply_markup=course_levels(course_id=theme.course.all().first().id),
        parse_mode="HTML"
    )

    await state.clear()
