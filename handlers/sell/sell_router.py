# handlers/sell/sell_router.py
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery

from database import user_manager

from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

sell_router = Router()


@sell_router.message(Command("sell"))
async def handle_sell_command(message: Message):

    user = await user_manager.get_user_by_id(message.from_user.id)

    if user is None:
        button_text = "⚠️ Зареєструватися та почати"
        message_text = (
            "Вітаю! Схоже, ви тут вперше.\n\n"
            "Для розміщення оголошень потрібна швидка реєстрація. "
            "Натисніть кнопку нижче, щоб продовжити."
        )
    else:
        button_text = "🚗 Розмістити нове оголошення"
        message_text = (
            f"Раді бачити вас знову, {user['full_name']}!\n\n"
            "Натисніть, щоб додати нове оголошення."
        )

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=button_text, callback_data="sell_car")]
        ]
    )

    await message.answer(message_text, reply_markup=keyboard)


@sell_router.callback_query(F.data == "sell_car")
async def handle_sell_car(callback: CallbackQuery):
    try:
        user_data = callback.from_user

        user = await user_manager.get_or_create_user(
            telegram_id=user_data.id,
            full_name=user_data.first_name,
            username=user_data.username,
        )

        if user["role"] == "buyer":
            await user_manager.set_user_role_seller(user_data.id)

            await callback.message.answer(
                "✅ **Реєстрацію завершено!**\n"
                "Ви зареєстровані як **Продавець**.\n\n"
                "Тепер давайте додамо ваше оголошення..."
            )
        else:
            await callback.message.answer(f"Починаємо процес додавання оголошення...")
        await callback.answer()

    except Exception as e:
        logging.error(f"Помилка в handle_sell_car: {e}", exc_info=True)
        await callback.message.answer(
            "❌ **Виникла помилка**\n\n"
            "Щось пішло не так під час з'єднання з базою даних. "
            "Спробуйте натиснути /start або /sell ще раз."
        )
        await callback.answer("Помилка! Див. повідомлення вище.", show_alert=True)
