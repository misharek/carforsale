from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode


from config import HELP_TEXT, ABOUT_US_TEXT

common_router = Router()


@common_router.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer(
        f"👋 Привіт, **{message.from_user.first_name}**!\n"
        "Ласкаво просимо до CarForSaleBot."
    )


@common_router.message(Command("help"))
async def handle_help(message: types.Message):
    await message.answer(text=HELP_TEXT)


@common_router.message(Command("aboutus"))
async def handle_aboutus(message: types.Message):
    await message.answer(text=ABOUT_US_TEXT, parse_mode=ParseMode.MARKDOWN)


@common_router.message(
    F.text,
    F.text.startswith("/"),
    ~CommandStart(),
    ~Command("help"),
    ~Command("aboutus"),
    ~Command("sell"),
    ~Command("buy"),
)
async def handle_unknown_commands(message: types.Message):
    error_message = "❌ **Невірна команда.** Будь ласка, використайте команду: /help."
    await message.answer(text=error_message)
