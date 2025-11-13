from aiogram.fsm.state import State, StatesGroup


class SellCarFSM(StatesGroup):
    enter_brand = State()
    enter_model = State()
    enter_year = State()
    enter_mileage = State()
    enter_color = State()
    enter_fuel_type = State()
    upload_photo = State()
    enter_description = State()
    enter_price = State()
    confirm_ad = State()
