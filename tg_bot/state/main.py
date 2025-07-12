from aiogram.fsm.state import State, StatesGroup


class User(StatesGroup):
    phone = State()
    full_name = State()
    user = State()
    browsing_courses = State()
    browsing_my_courses = State()
    payment = State()
    course = State()


class Theme_State(StatesGroup):
    schreiben=State()
    sprechen=State()


class Products_State(StatesGroup):
    products = State()

class Materials_State(StatesGroup):
    category = State()
    file = State()
    title = State()