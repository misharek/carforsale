from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

buy_router = Router()

@buy_router.message(Command("buy"))
async def handle_buy_command(message: types.Message, state: FSMContext): 
    
    # Визначення Inline-клавіатури для фільтрів:
    search_kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                # КНОПКА 1: Марка
                InlineKeyboardButton(text="Марка 🚗", callback_data="filter_brand"),
                # КНОПКА 2: Ціна
                InlineKeyboardButton(text="Ціна 💰", callback_data="filter_price"),
            ],
            [
                # КНОПКА 3: Рік
                InlineKeyboardButton(text="Рік 📅", callback_data="filter_year")
            ]
        ]
    )
    
    await state.clear() 
    
    # ... (решта коду) ...
    
    await message.answer(
        "🔎 **ПОШУК АВТОМОБІЛІВ**\n\n"
        "Оберіть, як ви хочете шукати:",
        reply_markup=ReplyKeyboardRemove() 
    )
    
    # Надсилаємо саму клавіатуру
    await message.answer(
        "Використовуйте фільтри нижче:", 
        reply_markup=search_kb
    )