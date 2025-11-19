import asyncio
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# 🔥 Імпортуємо дані для перевірки
from database.cars_data import MODEL_DATABASE, BRAND_MAPPING, ALLOWED_COLORS, FUEL_TYPES

# Імпорти з ваших файлів
from handlers.buy.buy_states import BuyCarFSM
from handlers.buy.buy_keyboards import get_filter_keyboard, get_input_control_keyboard

buy_router = Router()

# Текст меню
MENU_TEXT = "🔍 **ПОШУК АВТОМОБІЛІВ**\n\nНалаштуйте фільтри:"

# --- КЛАВІАТУРА ГОЛОВНОГО МЕНЮ ---
MAIN_MENU_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/sell"), KeyboardButton(text="/buy")],
        [KeyboardButton(text="/myads"), KeyboardButton(text="/help")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)


# --- ФУНКЦІЯ ПОКАЗУ ПОМИЛКИ (6 СЕКУНД) ---
async def show_temp_error(message: types.Message, text: str):
    """Показує помилку, чекає 6 секунд і видаляє її."""
    # 1. Видаляємо повідомлення користувача
    try: await message.delete()
    except: pass

    # 2. Надсилаємо помилку
    error_msg = await message.answer(text)
    
    # 3. Чекаємо 6 секунд (як ви просили) ⏱️
    await asyncio.sleep(6)
    
    # 4. Видаляємо помилку
    try: await error_msg.delete()
    except: pass


# --- ОНОВЛЕННЯ МЕНЮ ---
async def refresh_menu(message: types.Message, state: FSMContext):
    """Повертає користувача до меню фільтрів (Inline) і прибирає зайві повідомлення"""
    data = await state.get_data()
    menu_id = data.get("menu_message_id")
    prompt_id = data.get("reply_prompt_id")
    
    # Видаляємо промпт (якщо був)
    if prompt_id:
        try: await message.bot.delete_message(chat_id=message.chat.id, message_id=prompt_id)
        except: pass
        await state.update_data(reply_prompt_id=None)

    # Прибираємо Reply-клавіатуру знизу
    temp_msg = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await temp_msg.delete()

    # Видаляємо повідомлення користувача
    try: await message.delete()
    except: pass

    # Оновлюємо меню
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


# ==========================================
# 1. СТАРТ (/buy)
# ==========================================
@buy_router.message(Command("buy"))
async def handle_buy(message: types.Message, state: FSMContext):
    await state.clear()
    temp = await message.answer("...", reply_markup=ReplyKeyboardRemove())
    await temp.delete()
    
    msg = await message.answer(
        MENU_TEXT, 
        reply_markup=get_filter_keyboard({})
    )
    await state.update_data(menu_message_id=msg.message_id)


# ==========================================
# 2. ЦІНА
# ==========================================
@buy_router.callback_query(F.data == "filter_price")
async def start_price(callback: CallbackQuery, state: FSMContext):
    await callback.answer() 
    await callback.message.edit_text(
        "💲 Введіть мінімальну ціну ($):",
        reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_min_price)

@buy_router.message(BuyCarFSM.enter_min_price)
async def set_min_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await show_temp_error(message, "⚠️ Введіть ціну тільки цифрами.")
        return 
    await state.update_data(min_price=int(message.text))
    try: await message.delete()
    except: pass

    data = await state.get_data()
    menu_id = data.get("menu_message_id")
    
    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=menu_id,
        text=f"✅ Від: ${message.text}\n\n💲 Тепер введіть максимальну ціну ($):",
        reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_max_price)

@buy_router.message(BuyCarFSM.enter_max_price)
async def set_max_price(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await show_temp_error(message, "⚠️ Введіть ціну тільки цифрами.")
        return 
    await state.update_data(max_price=int(message.text))
    await refresh_menu(message, state)


# ==========================================
# 3. РІК
# ==========================================
@buy_router.callback_query(F.data == "filter_year")
async def start_year(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "📅 Введіть мінімальний рік (наприклад 2010):",
        reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_min_year)

@buy_router.message(BuyCarFSM.enter_min_year)
async def set_min_year(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or len(message.text) != 4:
        await show_temp_error(message, "⚠️ Рік має складатися з 4 цифр.")
        return
    await state.update_data(min_year=int(message.text))
    try: await message.delete()
    except: pass

    data = await state.get_data()
    menu_id = data.get("menu_message_id")

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=menu_id,
        text=f"✅ Від: {message.text}\n\n📅 Тепер введіть максимальний рік:",
        reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_max_year)

@buy_router.message(BuyCarFSM.enter_max_year)
async def set_max_year(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or len(message.text) != 4:
        await show_temp_error(message, "⚠️ Рік має складатися з 4 цифр.")
        return
    await state.update_data(max_year=int(message.text))
    await refresh_menu(message, state)


# ==========================================
# 4. ПРОБІГ
# ==========================================
@buy_router.callback_query(F.data == "filter_mileage")
async def start_mileage(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "🛣️ Введіть мінімальний пробіг (тис. км):",
        reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_min_mileage)

@buy_router.message(BuyCarFSM.enter_min_mileage)
async def set_min_mileage(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await show_temp_error(message, "⚠️ Введіть пробіг цифрами.")
        return
    await state.update_data(min_mileage=int(message.text))
    try: await message.delete()
    except: pass

    data = await state.get_data()
    menu_id = data.get("menu_message_id")

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=menu_id,
        text=f"✅ Від: {message.text} тис.км\n\n🛣️ Тепер введіть максимальний пробіг:",
        reply_markup=get_input_control_keyboard(show_skip=True)
    )
    await state.set_state(BuyCarFSM.enter_max_mileage)

@buy_router.message(BuyCarFSM.enter_max_mileage)
async def set_max_mileage(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await show_temp_error(message, "⚠️ Введіть пробіг цифрами.")
        return
    await state.update_data(max_mileage=int(message.text))
    await refresh_menu(message, state)


# ==========================================
# 5. МАРКА
# ==========================================
@buy_router.callback_query(F.data == "filter_brand")
async def start_brand(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "🚗 Введіть марку авто (наприклад BMW):",
        reply_markup=get_input_control_keyboard(show_skip=False)
    )
    await state.set_state(BuyCarFSM.enter_brand)

@buy_router.message(BuyCarFSM.enter_brand)
async def set_brand(message: types.Message, state: FSMContext):
    raw_brand = message.text.strip().upper()
    
    if raw_brand in BRAND_MAPPING:
        correct_brand = BRAND_MAPPING[raw_brand]
        await state.update_data(brand=correct_brand)
        await refresh_menu(message, state)
    else:
        await show_temp_error(
            message, 
            "⚠️ Така марка не знайдена. Спробуйте ввести офіційну назву (наприклад: Audi, BMW)."
        )


# ==========================================
# 6. МОДЕЛЬ
# ==========================================
@buy_router.callback_query(F.data == "filter_model")
async def start_model(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    brand = data.get("brand")
    if not brand:
        await callback.answer("⚠️ Спочатку оберіть Марку!", show_alert=True)
        return

    await callback.message.edit_text(
        f"🚘 Введіть модель для {brand} (наприклад X5):",
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
        await show_temp_error(
            message,
            f"⚠️ Модель '{input_model}' не знайдена для {brand}.\nСпробуйте: {available}..."
        )


# ==========================================
# 7. КОЛІР (Reply Buttons)
# ==========================================
@buy_router.callback_query(F.data == "filter_color")
async def start_color(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    
    builder = ReplyKeyboardBuilder()
    for col in ALLOWED_COLORS:
        builder.button(text=col)
    builder.button(text="🔙 Скасувати")
    builder.adjust(2)
    
    prompt_msg = await callback.message.answer(
        "🎨 Оберіть колір зі списку:", 
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await state.update_data(reply_prompt_id=prompt_msg.message_id)
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
        await show_temp_error(message, "⚠️ Оберіть колір, використовуючи кнопки нижче 👇")


# ==========================================
# 8. ПАЛИВО (Reply Buttons)
# ==========================================
@buy_router.callback_query(F.data == "filter_fuel")
async def start_fuel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    
    builder = ReplyKeyboardBuilder()
    for fuel in FUEL_TYPES:
        builder.button(text=fuel)
    builder.button(text="🔙 Скасувати")
    builder.adjust(2)
    
    prompt_msg = await callback.message.answer(
        "⛽ Оберіть тип палива:", 
        reply_markup=builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
    )
    await state.update_data(reply_prompt_id=prompt_msg.message_id)
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
        await show_temp_error(message, "⚠️ Оберіть паливо, використовуючи кнопки нижче 👇")


# ==========================================
# 9. УПРАВЛІННЯ
# ==========================================
@buy_router.callback_query(F.data == "skip_step")
async def skip_current_step(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    current_state = await state.get_state()
    
    if current_state == BuyCarFSM.enter_min_price:
        await callback.message.edit_text(
            "💲 Введіть максимальну ціну ($):",
            reply_markup=get_input_control_keyboard(show_skip=True)
        )
        await state.set_state(BuyCarFSM.enter_max_price)
    elif current_state == BuyCarFSM.enter_max_price:
        await refresh_menu(callback.message, state)
        
    elif current_state == BuyCarFSM.enter_min_year:
        await callback.message.edit_text(
            "📅 Введіть максимальний рік:",
            reply_markup=get_input_control_keyboard(show_skip=True)
        )
        await state.set_state(BuyCarFSM.enter_max_year)
    elif current_state == BuyCarFSM.enter_max_year:
        await refresh_menu(callback.message, state)
        
    elif current_state == BuyCarFSM.enter_min_mileage:
        await callback.message.edit_text(
            "🛣️ Введіть максимальний пробіг:",
            reply_markup=get_input_control_keyboard(show_skip=True)
        )
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
    
    try:
        await callback.message.edit_text(MENU_TEXT, reply_markup=get_filter_keyboard({}))
    except TelegramBadRequest:
        pass


# ==========================================
# 10. ПОКАЗ РЕЗУЛЬТАТІВ (Імітація)
# ==========================================
@buy_router.callback_query(F.data == "show_results")
async def show_res(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    
    # --- ІМІТАЦІЯ ---
    car_example = {
        "brand": "BMW", "model": "X5", "year": 2019, "price": 45000,
        "mileage": 68, "fuel": "Дизель",
        "desc": "Ідеальний стан, гаражне зберігання, перший власник."
    }
    
    car_card = (
        f"🚗 **{car_example['brand']} {car_example['model']}** ({car_example['year']})\n"
        f"💵 **${car_example['price']:,}**\n\n"
        f"🛣 Пробіг: {car_example['mileage']} тис. км\n"
        f"⛽ Паливо: {car_example['fuel']}\n\n"
        f"📝 _{car_example['desc']}_"
    )
    
    builder = InlineKeyboardBuilder()
    builder.button(text="📞 Зв'язатися з продавцем", callback_data="buy_contact")
    builder.button(text="⬅️", callback_data="prev_car")
    builder.button(text="1 / 10", callback_data="noop")
    builder.button(text="➡️", callback_data="next_car")
    builder.button(text="🔙 Змінити фільтри", callback_data="back_to_filters")
    builder.adjust(1, 3, 1)

    await callback.message.delete()
    await callback.message.answer(text=car_card, reply_markup=builder.as_markup())

@buy_router.callback_query(F.data == "back_to_filters")
async def back_to_filters_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    
    data = await state.get_data()
    msg = await callback.message.answer(
        MENU_TEXT, 
        reply_markup=get_filter_keyboard(data)
    )
    await state.update_data(menu_message_id=msg.message_id)

@buy_router.callback_query(F.data == "main_menu")
async def back_main(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        "🏠 Ви в головному меню. Оберіть дію:", 
        reply_markup=MAIN_MENU_KB
    )