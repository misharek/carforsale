from aiogram.fsm.state import State, StatesGroup

class BuyCarFSM(StatesGroup):

    enter_min_price = State()
    enter_max_price = State()
    
    enter_brand = State()
    enter_model = State()
    
    enter_min_year = State()
    enter_max_year = State()
    
    enter_min_mileage = State()
    enter_max_mileage = State()

    enter_color = State()
    enter_fuel = State() 