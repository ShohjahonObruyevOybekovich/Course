from aiogram.fsm.state import State, StatesGroup


class User(StatesGroup):
    phone = State()
    full_name = State()
    user = State()
    browsing_courses = State()
    browsing_my_courses = State()
    payment = State()
    course = State()