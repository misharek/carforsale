import logging
import asyncio
import re
from aiogram import Router, F
from aiogram.types import (
    CallbackQuery,
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove,
)
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from database import user_manager
from database import car_manager
# Примітка: SellCarFSM та SellerFSM повинні бути визначені у sell_states.py
from .sell_states import SellCarFSM, SellerFSM 

sell_router = Router()

# ==========================================
# 🛠 ДОПОМІЖНІ ФУНКЦІЇ (UTILS)
# ==========================================

async def show_temp_message(message: Message, text: str, delay: int = 3):
    """Показує повідомлення про помилку/інфо, яке зникає через N секунд."""
    msg = await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(delay)
    try: await msg.delete()
    except: pass

def clean_and_validate_phone(text: str) -> tuple[str | None, bool]:
    """Очищає текст і перевіряє, чи схожий він на номер телефону."""
    # Залишаємо лише цифри
    cleaned_phone = "".join(filter(str.isdigit, text))
    
    # Мінімальна довжина 9 цифр для валідності (без коду країни)
    if len(cleaned_phone) < 9: 
        return None, False

    # Форматуємо для зберігання (додаємо '+' на початок)
    if not cleaned_phone.startswith("380") and len(cleaned_phone) == 10:
        # Приклад: якщо ввели 098... (10 цифр), додаємо +38
        formatted_phone = f"+38{cleaned_phone}"
    elif len(cleaned_phone) >= 10:
        # Для міжнародного формату або повного українського
        if not cleaned_phone.startswith("+"):
            formatted_phone = f"+{cleaned_phone.lstrip('0')}"
        else:
            formatted_phone = cleaned_phone
    else:
        # Якщо щось інше, залишаємо як є, але вважаємо валідним, якщо > 9 цифр
        formatted_phone = "+" + cleaned_phone
        
    return formatted_phone, True


# ==========================================
# 1. СТАРТ ПРОДАЖУ
# ==========================================
@sell_router.message(Command("sell"))
async def handle_sell_command(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass

    data = await state.get_data()
    old_menu_id = data.get("main_menu_id")
    if old_menu_id:
        try: await message.bot.delete_message(chat_id=message.chat.id, message_id=old_menu_id)
        except: pass
    
    user = await user_manager.get_user_by_id(message.from_user.id)
    if user is None:
        button_text = "⚠️ Зареєструватися та почати"
        message_text = "Вітаю! Ви тут вперше. Натисніть кнопку для реєстрації."
    else:
        button_text = "🚗 Розмістити нове оголошення"
        message_text = f"Раді бачити, {user.get('full_name')}! Продамо авто?"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data="sell_car")],
            [InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu")]
        ]
    )
    await message.answer(message_text, reply_markup=keyboard, parse_mode=None)


# ==========================================
# 2. РЕЄСТРАЦІЯ ТА ПЕРЕВІРКА
# ==========================================
@sell_router.callback_query(F.data == "sell_car")
async def handle_sell_car(callback: CallbackQuery, state: FSMContext):
    try:
        try: await callback.message.delete()
        except: pass

        user_data = callback.from_user
        user = await user_manager.get_or_create_user(
            telegram_id=user_data.id,
            full_name=user_data.full_name, # Виправлено: використовуємо full_name
            username=user_data.username,
        )

        alert_text = None
        if user["role"] == "buyer":
            await user_manager.set_user_role_seller(user_data.id, full_name=user_data.full_name)
            user["role"] = "seller"
            alert_text = "✅ Ви тепер зареєстровані як Продавець!"

        if user.get("phone_number") is None:
            if alert_text: await callback.answer(alert_text, show_alert=True)
            else: await callback.answer()

            await state.set_state(SellerFSM.enter_phone)
            
            contact_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)],
                    [KeyboardButton(text="❌ Скасувати")]
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            
            request_msg = await callback.message.answer(
                "❗️ **Потрібен Ваш контакт.**\n\n"
                "Щоб покупці могли з Вами зв'язатися, поділіться, будь ласка, номером телефону:",
                reply_markup=contact_kb
            )
            await state.update_data(phone_request_id=request_msg.message_id)
            await state.update_data(last_bot_msg_id=request_msg.message_id)
            return
            
        if alert_text: await callback.answer(alert_text, show_alert=True)
        else: await callback.answer()

        # Якщо телефон є, починаємо створення оголошення
        await state.set_state(SellCarFSM.enter_brand)
        
        cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Скасувати")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        msg = await callback.message.answer(
            "🚗 **Створення оголошення**\n\n"
            "**Крок 1/9: Введіть МАРКУ авто** (наприклад: BMW, Audi, Ford):",
            reply_markup=cancel_kb
        )
        await state.update_data(last_bot_msg_id=msg.message_id)

    except Exception as e:
        logging.error(f"Помилка sell_car: {e}", exc_info=True)
        await callback.message.answer("❌ Помилка бази даних.")
        await callback.answer()


# ==========================================
# 3. ОБРОБКА ТЕЛЕФОНУ (ВИПРАВЛЕНО)
# ==========================================

@sell_router.message(
    SellerFSM.enter_phone, 
    Command("start", "sell", "buy", "my_ads", "help")
)
async def block_commands_during_phone_input(message: Message, state: FSMContext):
    """
    НОВИЙ ОБРОБНИК: Блокує всі команди під час очікування номера телефону, 
    щоб вони не збивали FSM.
    """
    try: await message.delete()
    except: pass
    
    await show_temp_message(
        message, 
        "⚠️ **Зачекайте!** Бот очікує Ваш **номер телефону**.\n"
        "Скористайтеся кнопкою '📱 Поділитися контактом' або введіть номер вручну.", 
        delay=5
    )


@sell_router.message(SellerFSM.enter_phone, F.contact | F.text)
async def handle_phone_request(message: Message, state: FSMContext):
    """
    Обробляє введення номера телефону з кнопкою або вручну, 
    додано жорстку валідацію.
    """
    try: await message.delete()
    except: pass

    data = await state.get_data()
    request_msg_id = data.get("phone_request_id")
    
    phone_number = None
    valid = False

    if message.contact:
        # Ввід через кнопку "Поділитися контактом"
        phone_number = message.contact.phone_number
        valid = True
    
    elif message.text:
        text = message.text.strip()
        
        if text == "❌ Скасувати": 
            # Цей вихід буде оброблено у sell_fsm_router, але ми можемо додати логіку тут, якщо потрібно.
            # Наразі просто виходимо, щоб не обробляти це як номер.
            return 
        
        # Ручний ввід тексту
        phone_number, valid = clean_and_validate_phone(text)
            
    # --- ЛОГІКА ВАЛІДАЦІЇ ---
    if not valid:
        if request_msg_id:
            # Видаляємо попередній запит
            try: await message.bot.delete_message(chat_id=message.chat.id, message_id=request_msg_id)
            except: pass 
            
        # Надсилаємо нове повідомлення про помилку та повторний запит
        contact_kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)],
                [KeyboardButton(text="❌ Скасувати")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        )
        
        error_msg = await message.answer(
            "❌ **Некоректний формат.** Введіть номер (мінімум 9 цифр) або скористайтеся кнопкою 'Поділитися контактом'.",
            reply_markup=contact_kb
        )
        # Оновлюємо ID повідомлення з новим запитом
        await state.update_data(phone_request_id=error_msg.message_id)
        return # Залишаємося у SellerFSM.enter_phone

    # --- УСПІШНЕ ЗБЕРЕЖЕННЯ ---
    if request_msg_id:
        try: await message.bot.delete_message(chat_id=message.chat.id, message_id=request_msg_id)
        except: pass 
        await state.update_data(phone_request_id=None) 
    
    user_full_name = message.from_user.full_name
    await user_manager.update_user_phone(
        telegram_id=message.from_user.id, 
        phone_number=phone_number,
        full_name=user_full_name
    )
    
    temp_success = await message.answer(
        f"✅ Номер {phone_number} збережено!\nРеєстрацію завершено.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    await state.set_state(SellCarFSM.enter_brand)
    
    await asyncio.sleep(3)
    try: await temp_success.delete()
    except: pass

    cancel_kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Скасувати")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    
    msg = await message.answer(
        "🚗 **Створення оголошення**\n\n"
        "**Крок 1/9: Введіть МАРКУ авто** (наприклад: BMW, Audi, Ford):",
        reply_markup=cancel_kb
    )
    await state.update_data(last_bot_msg_id=msg.message_id)


# ==========================================
# 4. МОЇ ОГОЛОШЕННЯ (/my_ads)
# ==========================================
@sell_router.message(Command("my_ads"))
async def handle_my_ads_command(message: Message, state: FSMContext):
    try: await message.delete()
    except: pass

    data = await state.get_data()
    old_menu_id = data.get("main_menu_id")
    if old_menu_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=old_menu_id)
        except: pass
    
    await state.update_data(main_menu_id=None)

    seller_id = message.from_user.id
    # Примітка: Функція car_manager.find_car_ads має існувати
    ads = await car_manager.find_car_ads(query={"seller_id": seller_id}, limit=100) 
    
    if not ads:
        back_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Розмістити оголошення", callback_data="sell_car")],
                [InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu")]
            ]
        )
        msg = await message.answer("📂 У вас поки немає активних оголошень.", reply_markup=back_kb)
        await state.update_data(main_menu_id=msg.message_id)
        return

    response_text = "⭐️ **Ваші активні оголошення:** ⭐️\n\n"
    keyboard_buttons = []
    
    for i, ad in enumerate(ads, 1):
        ad_id = str(ad['_id'])
        response_text += f"*{i}. {ad['brand']} {ad['model']}* ({ad['year']}) — ${ad['price']}\n"
        delete_button = InlineKeyboardButton(
            text=f"❌ Видалити #{i}",
            callback_data=f"delete_ad_{ad_id}"
        )
        keyboard_buttons.append([delete_button])

    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Головне меню", callback_data="main_menu")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    msg = await message.answer(response_text, reply_markup=keyboard, parse_mode='Markdown')
    await state.update_data(main_menu_id=msg.message_id)


@sell_router.callback_query(F.data.startswith("delete_ad_"))
async def handle_delete_ad(callback: CallbackQuery):
    ad_id = callback.data.split("_")[-1]
    # Примітка: Функція car_manager.delete_car_ad має існувати
    success = await car_manager.delete_car_ad(ad_id)
    
    if success:
        await callback.answer("✅ Оголошення успішно видалено!", show_alert=True)
        await callback.message.edit_text("♻️ Список оновлюється...")
        await asyncio.sleep(1)
        try: await callback.message.delete()
        except: pass
    else:
        await callback.answer("❌ Помилка видалення.", show_alert=True)