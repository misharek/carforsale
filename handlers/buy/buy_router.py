from aiogram import Router, types
from aiogram.filters import Command

buy_router = Router()


@buy_router.message(Command("buy"))
async def handle_buy(message: types.Message):
    await message.answer("🛠️ Команда /buy: Реалізація пошуку та фільтрації буде тут.")
