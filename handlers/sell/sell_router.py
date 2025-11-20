import logging
import asyncio
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
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from database import user_manager
from database import car_manager
from .sell_states import SellCarFSM, SellerFSM 

sell_router = Router()

# --- Допоміжна функція для тимчасових повідомлень ---
async def show_temp_message(message: Message, text: str, delay: int = 3):
    msg = await message.answer(text, reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(delay)
    try: await msg.delete()
    except: pass

# ==========================================
# 1. СТАРТ ПРОДАЖУ
# ==========================================
@sell_router.message(Command("sell"))
async def handle_sell_command(message: Message):
    # Видаляємо повідомлення користувача /sell для чистоти
    try: await message.delete()
    except: pass

    user = await user_manager.get_user_by_id(message.from_user.id)
    if user is None:
        button_text = "⚠️ Зареєструватися та почати"
        message_text = "Вітаю! Ви тут вперше. Натисніть кнопку для реєстрації."
    else:
        button_text = "🚗 Розмістити нове оголошення"
        message_text = f"Раді бачити, {user['full_name']}! Продамо авто?"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data="sell_car")]
        ]
    )
    await message.answer(message_text, reply_markup=keyboard)


# ==========================================
# 2. РЕЄСТРАЦІЯ ТА ПЕРЕВІРКА
# ==========================================
@sell_router.callback_query(F.data == "sell_car")
async def handle_sell_car(callback: CallbackQuery, state: FSMContext):
    try:
        # Видаляємо попереднє меню з кнопкою
        try: await callback.message.delete()
        except: pass

        user_data = callback.from_user
        user = await user_manager.get_or_create_user(
            telegram_id=user_data.id,
            full_name=user_data.first_name,
            username=user_data.username,
        )

        alert_text = None

        # Логіка зміни ролі
        if user["role"] == "buyer":
            await user_manager.set_user_role_seller(user_data.id, full_name=user_data.full_name)
            user["role"] = "seller"
            alert_text = "✅ Ви тепер зареєстровані як Продавець!"

        # === ЛОГІКА ПЕРЕВІРКИ ТЕЛЕФОНУ ===
        if user.get("phone_number") is None:
            # Показуємо алерт, якщо він був
            if alert_text:
                await callback.answer(alert_text, show_alert=True)
            else:
                await callback.answer()

            await state.set_state(SellerFSM.enter_phone)
            
            contact_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)]
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            
            # 🔥 ЗБЕРІГАЄМО ПОВІДОМЛЕННЯ, ЩОБ ВИДАЛИТИ ЙОГО ПОТІМ
            request_msg = await callback.message.answer(
                "❗️ **Потрібен Ваш контакт.**\n\n"
                "Щоб покупці могли з Вами зв'язатися, поділіться, будь ласка, номером телефону:",
                reply_markup=contact_kb
            )
            # Записуємо ID цього повідомлення в пам'ять
            await state.update_data(phone_request_id=request_msg.message_id)
            return
            
        # === ЯКЩО ТЕЛЕФОН ВЖЕ Є ===
        if alert_text:
            await callback.answer(alert_text, show_alert=True)
        else:
            await callback.answer()

        await state.set_state(SellCarFSM.enter_brand)
        await callback.message.answer(
            "🚗 **Створення оголошення**\n\n"
            "**Крок 1/9: Введіть МАРКУ авто** (наприклад: BMW, Audi, Ford):",
            reply_markup=ReplyKeyboardRemove()
        )

    except Exception as e:
        logging.error(f"Помилка sell_car: {e}", exc_info=True)
        await callback.message.answer("❌ Помилка бази даних.")
        await callback.answer()


# ==========================================
# 3. ОБРОБКА ТЕЛЕФОНУ (Видалення старих повідомлень)
# ==========================================
@sell_router.message(SellerFSM.enter_phone, F.contact | F.text)
async def handle_phone_request(message: Message, state: FSMContext):
    # 1. Видаляємо повідомлення, яке надіслав користувач (контакт або текст)
    try: await message.delete()
    except: pass

    # 2. 🔥 ВИДАЛЯЄМО ПОВІДОМЛЕННЯ БОТА ("Потрібен контакт"), ЯКЕ БУЛО НА СКРІНШОТІ
    data = await state.get_data()
    request_msg_id = data.get("phone_request_id")
    if request_msg_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=request_msg_id)
        except:
            pass # Якщо вже видалено або помилка

    # Обробка номера
    if message.contact:
        phone_number = message.contact.phone_number
    elif message.text:
        phone_number = message.text.strip()
    else:
        await show_temp_message(message, "⚠️ Скористайтеся кнопкою або введіть номер.", delay=4)
        return

    # Оновлення в БД
    user_full_name = message.from_user.full_name
    await user_manager.update_user_phone(
        telegram_id=message.from_user.id, 
        phone_number=phone_number,
        full_name=user_full_name
    )
    
    # Очищаємо дані про ID повідомлення, але переходимо в наступний стан
    await state.update_data(phone_request_id=None) 
    
    # 3. Показуємо повідомлення про успіх, яке зникає через 3 секунди
    temp_success = await message.answer(
        f"✅ Номер {phone_number} збережено!\nРеєстрацію завершено.",
        reply_markup=ReplyKeyboardRemove()
    )
    
    # Перехід до кроку 1
    await state.set_state(SellCarFSM.enter_brand)
    
    # Чекаємо 3 сек, видаляємо успіх і показуємо питання про марку
    await asyncio.sleep(3)
    try: await temp_success.delete()
    except: pass

    await message.answer(
        "🚗 **Створення оголошення**\n\n"
        "**Крок 1/9: Введіть МАРКУ авто** (наприклад: BMW, Audi, Ford):"
    )


# ==========================================
# 4. МОЇ ОГОЛОШЕННЯ
# ==========================================
@sell_router.message(Command("myads"))
async def handle_my_ads(message: Message):
    try: await message.delete()
    except: pass

    seller_id = message.from_user.id
    ads = await car_manager.find_car_ads(query={"seller_id": seller_id}, limit=100) 
    
    if not ads:
        # Тимчасове повідомлення
        await show_temp_message(message, "У вас немає активних оголошень. Розмістіть перше!", delay=5)
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

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(response_text, reply_markup=keyboard, parse_mode='Markdown')


@sell_router.callback_query(F.data.startswith("delete_ad_"))
async def handle_delete_ad(callback: CallbackQuery):
    ad_id = callback.data.split("_")[-1]
    success = await car_manager.delete_car_ad(ad_id)
    
    if success:
        # Алерт по центру екрану
        await callback.answer("✅ Оголошення успішно видалено!", show_alert=True)
        # Очищаємо повідомлення зі списком
        await callback.message.edit_text("♻️ Список оновлюється...")
        await asyncio.sleep(1)
        try: await callback.message.delete()
        except: pass
    else:
        await callback.answer("❌ Помилка видалення.", show_alert=True)