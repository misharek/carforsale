import asyncio
from datetime import datetime
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# Імпорт даних та функцій бази
# (Ці файли мають бути доступні у вашій структурі проєкту)
from database.cars_data import MODEL_DATABASE, BRAND_MAPPING, ALLOWED_COLORS, FUEL_TYPES
from database.user_manager import get_user, add_user 
from database.car_manager import find_car_ads, count_car_ads 

# Імпорти станів та клавіатур
from handlers.buy.buy_states import BuyCarFSM
from handlers.buy.buy_keyboards import get_filter_keyboard, get_input_control_keyboard

buy_router = Router()

MENU_TEXT = "🔍 **ПОШУК АВТОМОБІЛІВ**\n\nНалаштуйте фільтри:"

MAIN_MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/sell"), KeyboardButton(text="/buy")],
        [KeyboardButton(text="/my_ads"), KeyboardButton(text="/help")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# ==========================================
# 🛠 ДОПОМІЖНІ ФУНКЦІЇ (UTILS)
# ==========================================

def build_mongo_query(data: dict) -> dict:
    """Перетворює дані з FSM у запит MongoDB"""
    query = {}
    if data.get("brand"): query["brand"] = data["brand"]
    if data.get("model"): query["model"] = data["model"]
    if data.get("color"): query["color"] = data["color"]
    if data.get("fuel"): query["fuel"] = data["fuel"]

    if data.get("min_price") or data.get("max_price"):
        query["price"] = {}
        if data.get("min_price"): query["price"]["$gte"] = data["min_price"]
        if data.get("max_price"): query["price"]["$lte"] = data["max_price"]

    if data.get("min_year") or data.get("max_year"):
        query["year"] = {}
        if data.get("min_year"): query["year"]["$gte"] = data["min_year"]
        if data.get("max_year"): query["year"]["$lte"] = data["max_year"]

    if data.get("min_mileage") or data.get("max_mileage"):
        query["mileage"] = {}
        if data.get("min_mileage"): query["mileage"]["$gte"] = data["min_mileage"]
        if data.get("max_mileage"): query["mileage"]["$lte"] = data["max_mileage"]

    return query

def format_car_caption(car: dict) -> str:
    """Формує текст картки авто"""
    desc = car.get('description', 'Не вказано')
    desc_text = "" if desc == "Не вказано" else f"\n📝 _{desc}_"

    return (
        f"🚗 **{car['brand']} {car['model']}** ({car['year']})\n"
        f"💵 **${car['price']:,}**\n\n"
        f"🛣 Пробіг: {car['mileage']} тис. км\n"
        f"⛽ Паливо: {car['fuel']}\n"
        f"🎨 Колір: {car['color']}"
        f"{desc_text}"
    )

def get_pagination_keyboard(page_index: int, total: int, seller_id: int) -> InlineKeyboardMarkup:
    """Створює кнопки під карткою авто (Вперед/Назад)"""
    builder = InlineKeyboardBuilder()
    current_display = f"{page_index + 1} / {total}"
    
    builder.button(text="📞 Зв'язок з продавцем", callback_data=f"get_contact_{seller_id}")
    builder.button(text="⬅️", callback_data="prev_car")
    builder.button(text=current_display, callback_data="noop")
    builder.button(text="➡️", callback_data="next_car")
    builder.button(text="🔙 Змінити фільтри", callback_data="back_to_filters")
    
    builder.adjust(1, 3, 1)
    return builder.as_markup()

async def show_temp_error(message: types.Message, text: str):
    """Показує повідомлення про помилку, яке зникає через 4 секунди."""
    try: await message.delete()
    except: pass
    error_msg = await message.answer(text)
    await asyncio.sleep(4)
    try: await error_msg.delete()
    except: pass

async def refresh_menu(message: types.Message, state: FSMContext):
    """Оновлює меню фільтрів після завершення кроку FSM."""
    data = await state.get_data()
    menu_id = data.get("menu_message_id")
    prompt_id = data.get("reply_prompt_id")
    
    if prompt_id:
        try: await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_id)
        except: pass
        await state.update_data(reply_prompt_id=None)

    try: await message.delete()
    except: pass

    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_id,
            text=MENU_TEXT,
            reply_markup=get_filter_keyboard(data)
        )
    except:
        msg = await message.answer(MENU_TEXT, reply_markup=get_filter_keyboard(data))
        await state.update_data(menu_message_id=msg.message_id)
    
    await state.set_state(None)

async def show_filter_menu(message: types.Message, state: FSMContext):
    """Показує початкове меню фільтрів."""
    temp = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await temp.delete()
    msg = await message.answer(MENU_TEXT, reply_markup=get_filter_keyboard({}))
    await state.update_data(menu_message_id=msg.message_id)


# ==========================================
# 1. БАЗОВІ КОМАНДИ (/buy, /help)
# ==========================================

@buy_router.message(Command("buy"))
async def handle_buy_command(message: types.Message, state: FSMContext):
    try: await message.delete()
    except: pass
    data = await state.get_data()
    old_menu_id = data.get("main_menu_id")
    if old_menu_id:
        try: await message.bot.delete_message(chat_id=message.chat.id, message_id=old_menu_id)
        except: pass

    await state.clear()
    user = await get_user(message.from_user.id)
    
    if user:
        await show_filter_menu(message, state)
    else:
        reg_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚠️ Зареєструватися та почати", callback_data="register_buyer")]
        ])
        await message.answer(
            f"Вітаю, {message.from_user.first_name}!\nВи тут вперше. Натисніть кнопку для реєстрації.",
            reply_markup=reg_kb
        )

@buy_router.message(Command("help"))
async def handle_help_command(message: types.Message, state: FSMContext):
    try: await message.delete()
    except: pass
    help_text = (
        "🤖 **Допомога по боту**\n\n"
        "📌 **/buy** — Пошук автомобілів.\n"
        "📌 **/sell** — Продаж автомобіля.\n"
        "📌 **/my_ads** — Ваші оголошення."
    )
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu")]
    ])
    await message.answer(help_text, reply_markup=back_kb)

@buy_router.callback_query(F.data == "register_buyer")
async def register_buyer_handler(callback: CallbackQuery, state: FSMContext):
    user_data = callback.from_user
    new_user = {
        "telegram_id": user_data.id,
        "full_name": user_data.full_name,
        "username": f"@{user_data.username}" if user_data.username else None,
        "role": "buyer", 
        "registration_date": datetime.utcnow()
    }
    await add_user(new_user)
    await callback.answer("✅ Ви успішно зареєстровані!", show_alert=True)
    await callback.message.delete()
    await show_filter_menu(callback.message, state)


# ==========================================
# 2. ЛОГІКА ФІЛЬТРІВ (Ціна, Рік, Пробіг...)
# ==========================================

# --- ЦІНА (ОНОВЛЕНО) ---
@buy_router.callback_query(F.data == "filter_price")
async def start_price(callback: CallbackQuery, state: FSMContext):
    await callback.answer() 
    await callback.message.edit_text(
        "💲 Введіть мінімальну ціну ($), мінімум $1000:", reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_min_price)

@buy_router.message(BuyCarFSM.enter_min_price)
async def set_min_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await show_temp_error(message, "⚠️ Введіть ціну тільки цифрами.")
        return 
    
    price = int(message.text)
    if price < 1000:
        await show_temp_error(message, "⚠️ Мінімальна ціна має бути не менше $1000.")
        return 

    await state.update_data(min_price=price)
    try: await message.delete()
    except: pass

    data = await state.get_data()
    menu_id = data.get("menu_message_id")
    
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=menu_id,
        text=f"✅ Від: ${price:,}\n\n💲 Тепер введіть максимальну ціну ($):",
        reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_max_price)

@buy_router.message(BuyCarFSM.enter_max_price)
async def set_max_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await show_temp_error(message, "⚠️ Введіть ціну тільки цифрами.")
        return 
    
    max_price = int(message.text)
    
    data = await state.get_data()
    min_price = data.get("min_price", 0) 
    
    if min_price > 0 and max_price < min_price:
        await show_temp_error(message, f"⚠️ Максимальна ціна (${max_price:,}) не може бути меншою за мінімальну (${min_price:,}).")
        return
        
    await state.update_data(max_price=max_price)
    await refresh_menu(message, state)

# --- РІК (ОНОВЛЕНО) ---
@buy_router.callback_query(F.data == "filter_year")
async def start_year(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    current_year = datetime.now().year
    await callback.message.edit_text(
        f"📅 Введіть мінімальний рік (1900 - {current_year + 1}):", reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_min_year)

@buy_router.message(BuyCarFSM.enter_min_year)
async def set_min_year(message: types.Message, state: FSMContext):
    current_year = datetime.now().year
    
    if not message.text.isdigit() or len(message.text) != 4:
        await show_temp_error(message, "⚠️ Рік має складатися з 4 цифр.")
        return
    
    year = int(message.text)
    if not (1900 <= year <= current_year + 1): 
        await show_temp_error(message, f"⚠️ Рік має бути в діапазоні 1900 - {current_year + 1}.")
        return
        
    await state.update_data(min_year=year)
    try: await message.delete()
    except: pass
    
    data = await state.get_data()
    menu_id = data.get("menu_message_id")

    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=menu_id,
        text=f"✅ Від: {year}\n\n📅 Тепер введіть максимальний рік:",
        reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_max_year)

@buy_router.message(BuyCarFSM.enter_max_year)
async def set_max_year(message: types.Message, state: FSMContext):
    current_year = datetime.now().year
    
    if not message.text.isdigit() or len(message.text) != 4:
        await show_temp_error(message, "⚠️ Рік має складатися з 4 цифр.")
        return
        
    max_year = int(message.text)
    
    if not (1900 <= max_year <= current_year + 1): 
        await show_temp_error(message, f"⚠️ Рік має бути в діапазоні 1900 - {current_year + 1}.")
        return

    data = await state.get_data()
    min_year = data.get("min_year", 0) 
    
    if min_year > 0 and max_year < min_year:
        await show_temp_error(message, f"⚠️ Максимальний рік ({max_year}) не може бути меншим за мінімальний ({min_year}).")
        return

    await state.update_data(max_year=max_year)
    await refresh_menu(message, state)

# --- ПРОБІГ (ОНОВЛЕНО) ---
@buy_router.callback_query(F.data == "filter_mileage")
async def start_mileage(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "🛣️ Введіть мінімальний пробіг (тис. км), мінімум 0 тис. км:", reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_min_mileage)

@buy_router.message(BuyCarFSM.enter_min_mileage)
async def set_min_mileage(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await show_temp_error(message, "⚠️ Введіть пробіг цифрами.")
        return
        
    mileage = int(message.text)
    if mileage < 0:
        await show_temp_error(message, "⚠️ Пробіг не може бути від'ємним.")
        return
        
    await state.update_data(min_mileage=mileage)
    try: await message.delete()
    except: pass

    data = await state.get_data()
    menu_id = data.get("menu_message_id")
    await message.bot.edit_message_text(
        chat_id=message.chat.id, message_id=menu_id,
        text=f"✅ Від: {mileage} тис.км\n\n🛣️ Тепер введіть максимальний пробіг:",
        reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_max_mileage)

@buy_router.message(BuyCarFSM.enter_max_mileage)
async def set_max_mileage(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await show_temp_error(message, "⚠️ Введіть пробіг цифрами.")
        return
        
    max_mileage = int(message.text)
    
    data = await state.get_data()
    min_mileage = data.get("min_mileage", 0) 
    
    if min_mileage >= 0 and max_mileage < min_mileage:
        await show_temp_error(message, f"⚠️ Максимальний пробіг ({max_mileage}) не може бути меншим за мінімальний ({min_mileage}).")
        return
        
    await state.update_data(max_mileage=max_mileage)
    await refresh_menu(message, state)

# --- МАРКА І МОДЕЛЬ ---
@buy_router.callback_query(F.data == "filter_brand")
async def start_brand(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "🚗 Введіть марку авто (наприклад BMW):", reply_markup=get_input_control_keyboard(show_skip=False)
    )
    await state.set_state(BuyCarFSM.enter_brand)

@buy_router.message(BuyCarFSM.enter_brand)
async def set_brand(message: types.Message, state: FSMContext):
    raw_brand = message.text.strip().upper()
    if raw_brand in BRAND_MAPPING:
        correct_brand = BRAND_MAPPING[raw_brand]
        await state.update_data(brand=correct_brand)
        # При зміні марки скидаємо модель
        await state.update_data(model=None) 
        await refresh_menu(message, state)
    else:
        await show_temp_error(message, "⚠️ Така марка не знайдена. Спробуйте: Audi, BMW, Ford...")

@buy_router.callback_query(F.data == "filter_model")
async def start_model(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    brand = data.get("brand")
    if not brand:
        await callback.answer("⚠️ Спочатку оберіть Марку!", show_alert=True)
        return

    relevant_models = MODEL_DATABASE.get(brand, [])
    example_text = ", ".join(relevant_models[:3]) if relevant_models else "Будь-яка"
    
    await callback.message.edit_text(
        f"🚘 Введіть модель для {brand} (наприклад: {example_text}):",
        reply_markup=get_input_control_keyboard(show_skip=False)
    )
    await state.set_state(BuyCarFSM.enter_model)

@buy_router.message(BuyCarFSM.enter_model)
async def set_model(message: types.Message, state: FSMContext):
    data = await state.get_data()
    brand = data.get("brand")
    input_model = message.text.strip()
    
    found_model = None
    if brand in MODEL_DATABASE:
        for db_model in MODEL_DATABASE[brand]:
            if db_model.lower() == input_model.lower():
                found_model = db_model
                break
    
    if found_model:
        await state.update_data(model=found_model)
        await refresh_menu(message, state)
    else:
        available = ", ".join(MODEL_DATABASE.get(brand, [])[:3])
        await show_temp_error(message, f"⚠️ Модель '{input_model}' не знайдена.\nПриклади: {available}...")

# --- КОЛІР І ПАЛИВО ---
@buy_router.callback_query(F.data == "filter_color")
async def start_color(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    
    builder = ReplyKeyboardBuilder()
    for col in ALLOWED_COLORS: builder.button(text=col)
    builder.button(text="🔙 Скасувати")
    builder.adjust(2)
    
    prompt = await callback.message.answer(
        "🎨 Оберіть колір:", reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await state.update_data(reply_prompt_id=prompt.message_id)
    await state.set_state(BuyCarFSM.enter_color)

@buy_router.message(BuyCarFSM.enter_color)
async def set_color(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "🔙 Скасувати":
        await refresh_menu(message, state)
        return
    if text.capitalize() in ALLOWED_COLORS:
        await state.update_data(color=text.capitalize())
        await refresh_menu(message, state)
    else:
        await show_temp_error(message, "⚠️ Оберіть колір кнопкою 👇")

@buy_router.callback_query(F.data == "filter_fuel")
async def start_fuel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    
    builder = ReplyKeyboardBuilder()
    for f in FUEL_TYPES: builder.button(text=f)
    builder.button(text="🔙 Скасувати")
    builder.adjust(2)
    
    prompt = await callback.message.answer(
        "⛽ Оберіть тип палива:", reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await state.update_data(reply_prompt_id=prompt.message_id)
    await state.set_state(BuyCarFSM.enter_fuel)

@buy_router.message(BuyCarFSM.enter_fuel)
async def set_fuel(message: types.Message, state: FSMContext):
    text = message.text.strip()
    if text == "🔙 Скасувати":
        await refresh_menu(message, state)
        return
    if text.title() in FUEL_TYPES:
        await state.update_data(fuel=text.title())
        await refresh_menu(message, state)
    else:
        await show_temp_error(message, "⚠️ Оберіть паливо кнопкою 👇")


# ==========================================
# 3. КОНТРОЛЬ ВВОДУ (Пропустити / Скасувати / Очистити)
# ==========================================

@buy_router.callback_query(F.data == "skip_step")
async def skip_current_step(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    current_state = await state.get_state()
    
    if current_state == BuyCarFSM.enter_min_price:
        # Пропустити мінімальну ціну: переходимо до максимальної
        await callback.message.edit_text("💲 Введіть максимальну ціну ($):", reply_markup=get_input_control_keyboard(True))
        await state.set_state(BuyCarFSM.enter_max_price)
    elif current_state == BuyCarFSM.enter_max_price:
        # Пропустити максимальну ціну: повертаємось до меню
        await refresh_menu(callback.message, state)
    elif current_state == BuyCarFSM.enter_min_year:
        # Пропустити мінімальний рік: переходимо до максимального
        await callback.message.edit_text("📅 Введіть максимальний рік:", reply_markup=get_input_control_keyboard(True))
        await state.set_state(BuyCarFSM.enter_max_year)
    elif current_state == BuyCarFSM.enter_max_year:
        await refresh_menu(callback.message, state)
    elif current_state == BuyCarFSM.enter_min_mileage:
        # Пропустити мінімальний пробіг: переходимо до максимального
        await callback.message.edit_text("🛣️ Введіть максимальний пробіг:", reply_markup=get_input_control_keyboard(True))
        await state.set_state(BuyCarFSM.enter_max_mileage)
    elif current_state == BuyCarFSM.enter_max_mileage:
        await refresh_menu(callback.message, state)

@buy_router.callback_query(F.data == "cancel_input")
async def cancel_input(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await refresh_menu(callback.message, state)

@buy_router.callback_query(F.data == "clear_filters")
async def clear_filters(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Фільтри очищено ✅")
    data = await state.get_data()
    mid = data.get("menu_message_id")
    await state.clear()
    await state.update_data(menu_message_id=mid)
    try: await callback.message.edit_text(MENU_TEXT, reply_markup=get_filter_keyboard({}))
    except TelegramBadRequest: pass


# ==========================================
# 4. ПОШУК ТА ПАГІНАЦІЯ
# ==========================================

@buy_router.callback_query(F.data == "show_results")
async def show_res(callback: CallbackQuery, state: FSMContext):
    # 1. Одразу відповідаємо серверу
    await callback.answer()
    
    data = await state.get_data()
    query = build_mongo_query(data)
    
    # 2. Рахуємо кількість
    total_count = await count_car_ads(query)
    
    # 3. Якщо нічого не знайдено
    if total_count == 0:
        msg = await callback.message.answer(
            "😔 На жаль, нічого не знайдено.\n"
            "Спробуйте змінити параметри пошуку (наприклад, прибрати марку або розширити діапазон цін)."
        )
        
        await asyncio.sleep(8)
        
        try: await msg.delete()
        except: pass 
            
        return
        
    # 4. Якщо машини є - показуємо першу
    cars = await find_car_ads(query, limit=1, skip=0)
    car = cars[0]

    await state.update_data(current_page=0, total_results=total_count)
    
    # Видаляємо меню фільтрів
    try: await callback.message.delete()
    except: pass

    kb = get_pagination_keyboard(0, total_count, car.get('seller_id'))
    await callback.message.answer_photo(
        photo=car['photo'],
        caption=format_car_caption(car),
        reply_markup=kb
    )

@buy_router.callback_query(F.data.in_({"next_car", "prev_car"}))
async def paginate_cars(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_page = data.get("current_page", 0)
    total_results = data.get("total_results", 0)
    
    if callback.data == "next_car":
        new_page = current_page + 1
    else:
        new_page = current_page - 1

    if new_page < 0 or new_page >= total_results:
        await callback.answer("Це крайня сторінка")
        return

    await callback.answer()
    query = build_mongo_query(data)
    cars = await find_car_ads(query, limit=1, skip=new_page)
    
    if not cars:
        await callback.answer("Помилка завантаження.")
        return

    await state.update_data(current_page=new_page)
    car = cars[0]
    
    media = InputMediaPhoto(media=car['photo'], caption=format_car_caption(car))
    keyboard = get_pagination_keyboard(new_page, total_results, car.get('seller_id'))
    
    try:
        await callback.message.edit_media(media=media, reply_markup=keyboard)
    except Exception:
        # Якщо не вдалося змінити медіа, пробуємо змінити лише підпис/клавіатуру
        await callback.message.edit_caption(caption=format_car_caption(car), reply_markup=keyboard)


# ОНОВЛЕНА ФУНКЦІЯ ПОКАЗУ КОНТАКТІВ
@buy_router.callback_query(F.data.startswith("get_contact_"))
async def get_seller_contact(callback: CallbackQuery):
    seller_id = int(callback.data.split("_")[-1])
    
    seller = await get_user(seller_id)
    
    if not seller:
        await callback.answer("❌ Продавець не знайдений.", show_alert=True)
        return

    name = seller.get("full_name", "Невідомо")
    username = seller.get("username")
    phone = seller.get("phone_number", "Не вказано")

    username_text = f"{username}" if username else "Немає"

    text_response = (
        f"👤 **Продавець:** {name}\n"
        f"🔗 **Telegram:** {username_text}\n"
        f"📞 **Телефон:** {phone}"
    )
    
    await callback.answer(text_response, show_alert=True)

        
@buy_router.callback_query(F.data == "back_to_filters")
async def back_to_filters_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    
    data = await state.get_data()
    msg = await callback.message.answer(MENU_TEXT, reply_markup=get_filter_keyboard(data))
    await state.update_data(menu_message_id=msg.message_id)


@buy_router.callback_query(F.data == "main_menu")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    try: await callback.message.delete()
    except: pass
    
    menu_msg = await callback.message.answer("🏠 Головне меню:", reply_markup=MAIN_MENU_KB)
    await state.update_data(main_menu_id=menu_msg.message_id)