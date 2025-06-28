from unittest.mock import call

from icecream import ic

from dispatcher import dp
from aiogram.types import Message, BufferedInputFile, CallbackQuery
from aiogram.fsm.context import FSMContext
from tg_bot.ai import GptFunctions
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
        text = f"*{theme_schreiben}* mavzusidagi schreiben uchun uz matningizni yuboring 👇"
        await state.set_state(Theme_State.schreiben)
        await call.message.answer(text, parse_mode="Markdown")
    else:
        await call.message.answer("Ushbu mavzu uchun schreiben topshirig'i topilmadi.")




@dp.message(Theme_State.schreiben)
async def user_lang_handler(message: Message, state: FSMContext):
    data = await state.get_data()
    theme_id = Theme.objects.first().schreiben  # Ehtimol bu dynamic bo'lishi kerak
    user_answer = message.text
    full_prompt = f"Mavzu: {theme_id} va Javob : {user_answer}"

    intent_result = await gpt.prompt_to_json(str(message.from_user.id), full_prompt)
    ic(intent_result)

    # Foydalanuvchiga chiroyli matnli natijani jo‘natish
    response_text = format_schreiben_result(intent_result)
    await message.answer(text=response_text, parse_mode="Markdown")

    await state.clear()
