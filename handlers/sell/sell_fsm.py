from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from .sell_states import SellCarFSM

fsm_router = Router()

def is_digit_filter(message: types.Message):
    return message.text.isdigit()

# ----------------------------------------------------
# КРОК 1: Ловимо МАРКУ -> питаємо МОДЕЛЬ
# ----------------------------------------------------
@fsm_router.message(SellCarFSM.enter_brand, F.text)
async def handle_brand(message: types.Message, state: FSMContext):
    # Робимо великими: "bmw" -> "BMW"
    clean_brand = message.text.strip().upper()
    
    await state.update_data(brand=clean_brand)
    # Переходимо до моделі
    await state.set_state(SellCarFSM.enter_model)
    
    await message.answer(
        f"✅ Марка: {clean_brand}\n\n"
        "**Крок 2/9: Введіть МОДЕЛЬ** (напр., X5, Passat, Focus):"
    )

# ----------------------------------------------------
# КРОК 2: Ловимо МОДЕЛЬ -> питаємо РІК
# ----------------------------------------------------
@fsm_router.message(SellCarFSM.enter_model, F.text)
async def handle_model(message: types.Message, state: FSMContext):
    # Робимо першу велику: "passat" -> "Passat"
    clean_model = message.text.strip().title()

    await state.update_data(model=clean_model)
    # Переходимо до року
    await state.set_state(SellCarFSM.enter_year)
    
    await message.answer(
        f"✅ Модель: {clean_model}\n\n"
        "**Крок 3/9: Введіть рік випуску** (напр., 2019):"
    )

# ----------------------------------------------------
# КРОК 3: Ловимо РІК -> далі без змін...
# ----------------------------------------------------
@fsm_router.message(SellCarFSM.enter_year, is_digit_filter)
async def handle_year(message: types.Message, state: FSMContext):
    await state.update_data(year=int(message.text))
    await state.set_state(SellCarFSM.enter_mileage)
    await message.answer(
        "✅ Рік прийнято.\n\n" "**Крок 4/9: Введіть пробіг (тис. км)**:"
    )


# ----------------------------------------------------
# КРОК 4: Ловимо ПРОБІГ -> питаємо КОЛІР
# ----------------------------------------------------
@fsm_router.message(SellCarFSM.enter_mileage, is_digit_filter)
async def handle_mileage(message: types.Message, state: FSMContext):
    await state.update_data(mileage=int(message.text))
    await state.set_state(SellCarFSM.enter_color)
    await message.answer("✅ Пробіг прийнято.\n\n" "**Крок 5/9: Введіть колір**:")


# ----------------------------------------------------
# КРОК 5: Ловимо КОЛІР -> питаємо ПАЛИВО (З кнопками)
# ----------------------------------------------------
@fsm_router.message(SellCarFSM.enter_color, F.text)
async def handle_color(message: types.Message, state: FSMContext):
    # Нормалізуємо колір (червоний -> Червоний)
    clean_color = message.text.strip().capitalize()
    await state.update_data(color=clean_color)

    # Створюємо кнопки для вибору палива
    fuel_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Бензин"), KeyboardButton(text="Дизель")],
            [KeyboardButton(text="Газ"), KeyboardButton(text="Електро")],
            [KeyboardButton(text="Гібрид")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await state.set_state(SellCarFSM.enter_fuel_type)
    await message.answer(
        "✅ Колір прийнято.\n\n" "**Крок 6/9: Оберіть тип палива:**",
        reply_markup=fuel_kb,
    )


# ----------------------------------------------------
# КРОК 6: Ловимо ПАЛИВО -> питаємо ФОТО
# ----------------------------------------------------
@fsm_router.message(SellCarFSM.enter_fuel_type, F.text)
async def handle_fuel(message: types.Message, state: FSMContext):
    # Можна додати перевірку, чи текст є серед дозволених варіантів
    valid_fuels = ["Бензин", "Дизель", "Газ", "Електро", "Гібрид"]
    if message.text not in valid_fuels:
        await message.answer("Будь ласка, оберіть варіант із кнопок знизу 👇")
        return

    await state.update_data(fuel=message.text)
    await state.set_state(SellCarFSM.upload_photo)
    await message.answer(
        "✅ Паливо прийнято.\n\n"
        "**Крок 7/9: Завантажте фото авто** (одне головне фото):",
        reply_markup=ReplyKeyboardRemove(),  # Ховаємо кнопки палива
    )


# ----------------------------------------------------
# КРОК 7: Ловимо ФОТО -> питаємо ОПИС
# ----------------------------------------------------
@fsm_router.message(SellCarFSM.upload_photo, F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)

    await state.set_state(SellCarFSM.enter_description)
    await message.answer(
        "✅ Фото завантажено.\n\n"
        "**Крок 8/9: Додайте опис.**\n"
        "Напишіть деталі (стан, комплектація) або надішліть '-', щоб пропустити."
    )


# ----------------------------------------------------
# КРОК 8: Ловимо ОПИС ->
# ----------------------------------------------------
@fsm_router.message(SellCarFSM.enter_description, F.text)
async def handle_description(message: types.Message, state: FSMContext):
    desc = message.text if message.text != "-" else "Немає"
    await state.update_data(description=desc)
    
    # Тепер ми не показуємо підсумок, а питаємо ЦІНУ
    await state.set_state(SellCarFSM.enter_price)
    await message.answer(
        "✅ Опис збережено.\n\n"
        "**Крок 9/9: Вкажіть ЦІНУ ($)**\n"
        "Введіть тільки цифри (наприклад: 15500):"
    )

    # Отримуємо ВСІ дані для попереднього перегляду
 # ----------------------------------------------------
# НОВИЙ КРОК 9: Ловимо ЦІНУ -> ФІНАЛ
# ----------------------------------------------------
@fsm_router.message(SellCarFSM.enter_price, is_digit_filter)
async def handle_price(message: types.Message, state: FSMContext):
    price = int(message.text)
    await state.update_data(price=price)
    
    # Ось тепер отримуємо всі дані і формуємо підсумок
    data = await state.get_data()
    
    summary = (
        f"🚗 **ПЕРЕВІРКА ОГОЛОШЕННЯ** 🚗\n\n"
        f"🔹 **Марка:** {data['brand']}\n"
        f"🔹 **Модель:** {data['model']}\n"
        f"🔹 **Рік:** {data['year']}\n"
        f"🔹 **Пробіг:** {data['mileage']} тис. км\n"
        f"🔹 **Колір:** {data['color']}\n"
        f"🔹 **Паливо:** {data['fuel']}\n"
        f"📝 **Опис:** {data['description']}\n\n"
        f"💰 **Ціна:** ${price}"  # <--- Додали ціну сюди
    )
    # Кнопки підтвердження
    confirm_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Опублікувати")],
            [KeyboardButton(text="❌ Скасувати")],
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    # Надсилаємо фото з підписом
    await message.answer_photo(
        photo=data["photo"], caption=summary, reply_markup=confirm_kb
    )
    await state.set_state(SellCarFSM.confirm_ad)


# ----------------------------------------------------
# КРОК 9: ОБРОБКА КНОПОК (ОПУБЛІКУВАТИ / СКАСУВАТИ)
# ----------------------------------------------------
@fsm_router.message(SellCarFSM.confirm_ad, F.text == "✅ Опублікувати")
async def publish_ad(message: types.Message, state: FSMContext):
    data = await state.get_data()

    # ТУТ БУДЕ КОД ЗБЕРЕЖЕННЯ В MONGODB
    # await db.add_car(data)

    await message.answer(
        "🎉 **Оголошення успішно опубліковано!**", reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()


@fsm_router.message(SellCarFSM.confirm_ad, F.text == "❌ Скасувати")
async def cancel_ad(message: types.Message, state: FSMContext):
    await message.answer(
        "Створення оголошення скасовано.", reply_markup=ReplyKeyboardRemove()
    )
    await state.clear()
