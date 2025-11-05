from aiogram import Router, types
from aiogram.filters import Command

sell_router = Router()


@sell_router.message(Command("sell"))
async def handle_sell(message: types.Message):
    await message.answer("🛠️ Команда /sell: Реалізація діалогу продажу буде тут.")
