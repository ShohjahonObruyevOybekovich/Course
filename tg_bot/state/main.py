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


class MaterialState(StatesGroup):
    selecting_category = State()
    viewing_material_list = State()
    file = State()


class CourseMaterials_State(StatesGroup):
    video = State()
    file_id = State()
    name = State()
    description = State()
    select_course = State()


class ChatState(StatesGroup):
    waiting_user_reply = State()
    waiting_admin_reply = State()