from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime 
from database.car_manager import add_car_ad
from .sell_states import SellCarFSM
from database.cars_data import MODEL_DATABASE, BRAND_MAPPING, ALLOWED_COLORS, FUEL_TYPES

fsm_router = Router()


back_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🔙 Назад")]],
    resize_keyboard=True,
    one_time_keyboard=True
)

MAIN_MENU_RETURN_KB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/sell"), KeyboardButton(text="/buy")],
        [KeyboardButton(text="/myads"), KeyboardButton(text="/help")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False 
)


@fsm_router.message(F.text == "🔙 Назад")
async def go_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    
    if current_state == SellCarFSM.enter_model:
        await state.set_state(SellCarFSM.enter_brand)
        await message.answer("↪️ Повертаємось. Введіть МАРКУ авто:", reply_markup=ReplyKeyboardRemove())
    
    elif current_state == SellCarFSM.enter_year:
        await state.set_state(SellCarFSM.enter_model)
        await message.answer("↪️ Повертаємось. Введіть МОДЕЛЬ авто:", reply_markup=back_kb)
        
    elif current_state == SellCarFSM.enter_mileage:
        await state.set_state(SellCarFSM.enter_year)
        await message.answer("↪️ Повертаємось. Введіть рік випуску:", reply_markup=back_kb)
        
    elif current_state == SellCarFSM.enter_color:
        await state.set_state(SellCarFSM.enter_mileage)
        await message.answer("↪️ Повертаємось. Введіть пробіг (тис. км):", reply_markup=back_kb)
        
    elif current_state == SellCarFSM.enter_fuel_type:
        await state.set_state(SellCarFSM.enter_color)
        color_kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Чорний"), KeyboardButton(text="Білий")],
                [KeyboardButton(text="Сірий"), KeyboardButton(text="Синій")],
                [KeyboardButton(text="Червоний"), KeyboardButton(text="Зелений")],
                [KeyboardButton(text="Коричневий"), KeyboardButton(text="Інший")],
                [KeyboardButton(text="🔙 Назад")]
            ],
            resize_keyboard=True
        )
        await message.answer("↪️ Повертаємось. Оберіть колір:", reply_markup=color_kb)

    elif current_state == SellCarFSM.upload_photo:
        await state.set_state(SellCarFSM.enter_fuel_type)
        fuel_kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Бензин"), KeyboardButton(text="Дизель")],
                [KeyboardButton(text="Газ"), KeyboardButton(text="Електро")],
                [KeyboardButton(text="Гібрид")],
                [KeyboardButton(text="🔙 Назад")]
            ],
            resize_keyboard=True
        )
        await message.answer("↪️ Повертаємось. Оберіть тип палива:", reply_markup=fuel_kb)

    elif current_state == SellCarFSM.enter_description:
        await state.set_state(SellCarFSM.upload_photo)
        await message.answer("↪️ Повертаємось. Завантажте нове фото:", reply_markup=back_kb)

    elif current_state == SellCarFSM.enter_price:
        await state.set_state(SellCarFSM.enter_description)
        skip_kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="▶️ Пропустити")],
                [KeyboardButton(text="🔙 Назад")]
            ],
            resize_keyboard=True
        )
        await message.answer("↪️ Повертаємось. Введіть опис або пропустіть:", reply_markup=skip_kb)
        
    elif current_state == SellCarFSM.confirm_ad:
        await state.set_state(SellCarFSM.enter_price)
        await message.answer("↪️ Повертаємось. Введіть ціну ($):", reply_markup=back_kb)


@fsm_router.message(SellCarFSM.enter_brand, F.text, ~F.text.startswith('/'))
async def handle_brand(message: types.Message, state: FSMContext):
    clean_input = message.text.strip().upper()
    
    if clean_input not in BRAND_MAPPING:
        await message.answer(
            f"❌ Марка '{clean_input}' не знайдена. Будь ласка, введіть повну назву або відоме скорочення.", 
            reply_markup=back_kb
        )
        return
        
    canonical_brand = BRAND_MAPPING[clean_input]

    relevant_models = MODEL_DATABASE.get(canonical_brand, [])
    model_examples = ", ".join(relevant_models[:3])

    await state.update_data(brand=canonical_brand)
    await state.set_state(SellCarFSM.enter_model)
    
    await message.answer(
        f"✅ Марка: {canonical_brand}\n\n"
        f"**Крок 2/9: Введіть МОДЕЛЬ** (напр., {model_examples}):",
        reply_markup=back_kb
    )
@fsm_router.message(SellCarFSM.enter_model, F.text, ~F.text.startswith('/'))
async def handle_model(message: types.Message, state: FSMContext):
    data = await state.get_data()
    brand = data.get('brand') 
    clean_model = message.text.strip().title()

    allowed_models = MODEL_DATABASE.get(brand, []) 

    if clean_model not in allowed_models:
        suggestions = ", ".join(allowed_models[:5]) 
        
        await message.answer(
            f"❌ Модель '{clean_model}' не відповідає марці {brand}.\n"
            f"Введіть коректну назву. Наприклад: {suggestions}, ...",
            reply_markup=back_kb
        )
        return

    # Якщо валідація пройшла успішно
    await state.update_data(model=clean_model)
    await state.set_state(SellCarFSM.enter_year)
    
    await message.answer(
        f"✅ Модель: {clean_model}\n\n"
        "**Крок 3/9: Введіть рік випуску** (напр., 2019):",
        reply_markup=back_kb
    )

@fsm_router.message(SellCarFSM.enter_year, F.text, ~F.text.startswith('/'))
async def handle_year(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Будь ласка, введіть тільки цифри (наприклад: 2019).", reply_markup=back_kb)
        return
    
    year = int(message.text)
    if year < 1900 or year > 2025:
        await message.answer("⚠️ Введіть реальний рік випуску (1900-2025).", reply_markup=back_kb)
        return

    await state.update_data(year=year)
    await state.set_state(SellCarFSM.enter_mileage)
    
    await message.answer(
        f"✅ Рік: {year}\n\n" 
        "**Крок 4/9: Введіть пробіг (тис. км)**:",
        reply_markup=back_kb
    )

@fsm_router.message(SellCarFSM.enter_mileage, F.text, ~F.text.startswith('/'))
async def handle_mileage(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("⚠️ Введіть пробіг цілим числом (наприклад: 150).", reply_markup=back_kb)
        return

    await state.update_data(mileage=int(message.text))
    await state.set_state(SellCarFSM.enter_color)

    color_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Чорний"), KeyboardButton(text="Білий")],
            [KeyboardButton(text="Сірий"), KeyboardButton(text="Синій")],
            [KeyboardButton(text="Червоний"), KeyboardButton(text="Зелений")],
            [KeyboardButton(text="Коричневий"), KeyboardButton(text="Інший")],
            [KeyboardButton(text="🔙 Назад")] 
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Оберіть колір 👇"
    )

    await message.answer(
        f"✅ Пробіг: {message.text} тис. км\n\n" 
        "**Крок 5/9: Оберіть колір авто:**",
        reply_markup=color_kb
    )


@fsm_router.message(SellCarFSM.enter_color, F.text, ~F.text.startswith('/'))
async def handle_color(message: types.Message, state: FSMContext):
    selected_color = message.text.strip().capitalize()

    if selected_color not in ALLOWED_COLORS:
        await message.answer("⛔ Невідомий колір. Будь ласка, оберіть варіант із кнопок знизу 👇")
        return

    await state.update_data(color=selected_color)

    fuel_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Бензин"), KeyboardButton(text="Дизель")],
            [KeyboardButton(text="Газ"), KeyboardButton(text="Електро")],
            [KeyboardButton(text="Гібрид")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Оберіть тип палива 👇"
    )

    await state.set_state(SellCarFSM.enter_fuel_type)
    
    await message.answer(
        f"✅ Колір: {selected_color}\n\n"
        "**Крок 6/9: Оберіть тип палива:**",
        reply_markup=fuel_kb,
    )


@fsm_router.message(SellCarFSM.enter_fuel_type, F.text, ~F.text.startswith('/')) 
async def handle_fuel(message: types.Message, state: FSMContext):
    text = message.text.strip().title()
    valid_fuels = FUEL_TYPES
    
    if text not in valid_fuels:
        await message.answer("⚠️ Будь ласка, оберіть варіант із кнопок знизу 👇")
        return

    await state.update_data(fuel=text)
    await state.set_state(SellCarFSM.upload_photo)
    
    await message.answer(
        f"✅ Паливо: {text}\n\n"
        "**Крок 7/9: Завантажте фото авто** (одне головне фото):",
        reply_markup=back_kb, 
    )


@fsm_router.message(SellCarFSM.upload_photo, F.photo)
async def handle_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)

    skip_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="▶️ Пропустити")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(SellCarFSM.enter_description)
    await message.answer(
        "✅ Фото завантажено.\n\n"
        "**Крок 8/9: Додайте опис.**\n"
        "Напишіть деталі (стан, комплектація) або натисніть кнопку нижче, якщо опис не потрібен.",
        reply_markup=skip_kb
    )


@fsm_router.message(SellCarFSM.enter_description, F.text, ~F.text.startswith('/')) 
async def handle_description(message: types.Message, state: FSMContext):
    if message.text == "▶️ Пропустити":
        desc = "Не вказано"
    else:
        desc = message.text.strip()
    
    await state.update_data(description=desc)
    
    await state.set_state(SellCarFSM.enter_price)
    
    await message.answer(
        "✅ Опис збережено.\n\n"
        "**Крок 9/9: Вкажіть ЦІНУ ($)**\n"
        "Введіть тільки цифри (наприклад: 15500):",
        reply_markup=back_kb
    )

@fsm_router.message(SellCarFSM.enter_price, F.text, ~F.text.startswith('/')) 
async def handle_price(message: types.Message, state: FSMContext):
    
    if not message.text.isdigit():
        await message.answer("⚠️ **Помилка!** Введіть ціну тільки цифрами, без пробілів та валюти.", reply_markup=back_kb)
        return

    price = int(message.text)
    if price < 100 or price > 10000000:
        await message.answer("⚠️ Вкажіть реальну ціну (від 100$ до 10 млн).", reply_markup=back_kb)
        return

    await state.update_data(price=price)
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
        f"💰 **Ціна:** ${price}"
    )

    confirm_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Опублікувати")],
            [KeyboardButton(text="❌ Скасувати")],
            [KeyboardButton(text="🔙 Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )

    await message.answer_photo(
        photo=data["photo"], caption=summary, reply_markup=confirm_kb
    )
    await state.set_state(SellCarFSM.confirm_ad)


@fsm_router.message(SellCarFSM.confirm_ad, F.text == "✅ Опублікувати")
async def publish_ad(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    data['seller_id'] = message.from_user.id
    data['published_at'] = datetime.utcnow()

    car_id = await add_car_ad(data) 

    await message.answer(
        "🎉 **Оголошення успішно опубліковано!**", 
        reply_markup=MAIN_MENU_RETURN_KB
    )
    await state.clear()

@fsm_router.message(SellCarFSM.confirm_ad, F.text == "❌ Скасувати")
async def cancel_ad(message: types.Message, state: FSMContext):
    await message.answer(
        "Створення оголошення скасовано.", 
        reply_markup=MAIN_MENU_RETURN_KB
    )
    await state.clear()