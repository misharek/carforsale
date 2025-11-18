import logging
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
# Імпортуємо обидва класи FSM
from .sell_states import SellCarFSM, SellerFSM 

sell_router = Router()


@sell_router.message(Command("sell"))
async def handle_sell_command(message: Message):
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


@sell_router.callback_query(F.data == "sell_car")
async def handle_sell_car(callback: CallbackQuery, state: FSMContext):
    try:
        user_data = callback.from_user
        user = await user_manager.get_or_create_user(
            telegram_id=user_data.id,
            full_name=user_data.first_name,
            username=user_data.username,
        )

        # 1. Оновлення ролі
        if user["role"] == "buyer":
            await user_manager.set_user_role_seller(user_data.id)
            user["role"] = "seller"
            await callback.message.answer("✅ Ви тепер зареєстровані як Продавець!")

        # 2. КРИТИЧНА ПЕРЕВІРКА НОМЕРА ТЕЛЕФОНУ
        if user.get("phone_number") is None:
            await state.set_state(SellerFSM.enter_phone)
            
            contact_kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="📱 Поділитися контактом", request_contact=True)]
                ],
                resize_keyboard=True,
                one_time_keyboard=True,
            )
            await callback.message.answer(
                "❗️ **Потрібен Ваш контакт.**\n\n"
                "Щоб покупці могли з Вами зв'язатися, поділіться, будь ласка, номером телефону:",
                reply_markup=contact_kb
            )
            await callback.answer()
            return # Зупиняємо процес, чекаємо на телефон
            
        # 3. ПРОДОВЖЕННЯ ПРОЦЕСУ ПРОДАЖУ (Якщо телефон є)
        await state.set_state(SellCarFSM.enter_brand)
        await callback.message.answer(
            "🚗 **Створення оголошення**\n\n"
            "**Крок 1/9: Введіть МАРКУ авто** (наприклад: BMW, Audi, Ford):"
        )
        await callback.answer()

    except Exception as e:
        logging.error(f"Помилка sell_car: {e}", exc_info=True)
        await callback.message.answer("❌ Помилка бази даних.")
        await callback.answer()


@sell_router.message(SellerFSM.enter_phone, F.contact | F.text)
async def handle_phone_request(message: Message, state: FSMContext):
    
    # 1. Збір номера
    if message.contact:
        phone_number = message.contact.phone_number
        
    elif message.text:
        # ВИПРАВЛЕННЯ: беремо message.text, а не весь об'єкт
        phone_number = message.text.strip()
        
    else:
        await message.answer("Будь ласка, скористайтеся кнопкою 'Поділитися контактом' або введіть номер вручну.", 
                             reply_markup=ReplyKeyboardRemove())
        return
    
    # 2. Оновлення бази даних
    await user_manager.update_user_phone(message.from_user.id, phone_number)
    
    # 3. Очищення стану та продовження FSM
    await state.clear()
    
    await message.answer(
        f"✅ Номер {phone_number} збережено.\n"
        "Тепер можемо почати розміщення оголошення.",
        reply_markup=ReplyKeyboardRemove()
    )
    # Перенаправляємо на старт FSM для продажу
    await state.set_state(SellCarFSM.enter_brand)
    await message.answer(
        "🚗 **Створення оголошення**\n\n"
        "**Крок 1/9: Введіть МАРКУ авто** (наприклад: BMW, Audi, Ford):"
    )