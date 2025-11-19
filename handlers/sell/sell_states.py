from aiogram.fsm.state import State, StatesGroup


class SellCarFSM(StatesGroup):
    """Стани для багатоетапного процесу розміщення оголошення."""
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

class SellerFSM(StatesGroup):
    """Стани для одноразового налаштування продавця."""
    enter_phone = State()

# -------------------------------------------------------------------
class BuyFSM(StatesGroup):
    """Стани для багатоетапного налаштування пошуку."""
    choosing_filters = State()
    
    entering_brand = State()    
    entering_price_min = State() 
    entering_price_max = State() 
    entering_year_min = State()  
    entering_year_max = State()