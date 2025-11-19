from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

# --- Допоміжна функція для красивого тексту діапазонів ---
def format_range(data: dict, min_key: str, max_key: str, label: str, prefix: str = "", suffix: str = ""):
    """
    Формує текст кнопки. Наприклад: "✅ Рік: 2010-2015" або "✅ Ціна: від 5000 $"
    """
    min_val = data.get(min_key)
    max_val = data.get(max_key)
    
    # Логіка формування тексту
    if min_val and max_val:
        value_text = f"{min_val}-{max_val}"
    elif min_val:
        value_text = f"від {min_val}"
    elif max_val:
        value_text = f"до {max_val}"
    else:
        return f"{prefix} {label}" # Якщо нічого не вибрано, просто назва

    return f"✅ {label}: {value_text} {suffix}"


def get_filter_keyboard(filters: dict) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # === РЯДОК 1: МАРКА | МОДЕЛЬ ===
    # 1. Марка
    brand = filters.get('brand')
    brand_text = f"✅ {brand}" if brand else "🚗 Марка"
    builder.button(text=brand_text, callback_data="filter_brand")
    
    # 2. Модель
    model = filters.get('model')
    model_text = f"✅ {model}" if model else "🚘 Модель"
    builder.button(text=model_text, callback_data="filter_model")

    # === РЯДОК 2: РІК | ПРОБІГ ===
    # 3. Рік
    year_text = format_range(filters, 'min_year', 'max_year', "Рік", "📅")
    builder.button(text=year_text, callback_data="filter_year")
    
    # 4. Пробіг
    mileage_text = format_range(filters, 'min_mileage', 'max_mileage', "Пробіг", "🛣️", "тис.км")
    builder.button(text=mileage_text, callback_data="filter_mileage")

    # === РЯДОК 3: КОЛІР | ПАЛИВО ===
    # 5. Колір
    color = filters.get('color')
    color_text = f"✅ {color}" if color else "🎨 Колір"
    builder.button(text=color_text, callback_data="filter_color")
    
    # 6. Паливо
    fuel = filters.get('fuel')
    fuel_text = f"✅ {fuel}" if fuel else "⛽ Паливо"
    builder.button(text=fuel_text, callback_data="filter_fuel")

    # === РЯДОК 4: ЦІНА (ВЕЛИКА КНОПКА) ===
    # 7. Ціна
    price_text = format_range(filters, 'min_price', 'max_price', "Ціна", "💲", "$")
    # Якщо ціна не обрана, робимо її більш помітною
    if "✅" not in price_text:
        price_text = "💲 Вказати ціну ($) 💲"
    builder.button(text=price_text, callback_data="filter_price")

    # === РЯДОК 5: ПОШУК ===
    # 8. Пошук
    builder.button(text="🔍 Показати результати", callback_data="show_results")
    
    # === РЯДОК 6: НИЖНІ КНОПКИ ===
    # 9. Очистити
    builder.button(text="❌ Очистити фільтри", callback_data="clear_filters")
    # 10. Меню
    builder.button(text="🔙 Головне меню", callback_data="main_menu")
    
    # === НАЛАШТУВАННЯ СІТКИ (GRID) ===
    # (2 кнопки, 2 кнопки, 2 кнопки, 1 кнопка, 1 кнопка, 2 кнопки)
    builder.adjust(2, 2, 2, 1, 1, 2)
    
    return builder.as_markup()


# Клавіатура для скасування або пропуску кроку (залишається такою ж)
def get_input_control_keyboard(show_skip: bool = False):
    builder = InlineKeyboardBuilder()
    if show_skip:
        builder.button(text="▶️ Пропустити", callback_data="skip_step")
    builder.button(text="🔙 Скасувати", callback_data="cancel_input")
    builder.adjust(1)
    return builder.as_markup()