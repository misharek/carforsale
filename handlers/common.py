from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


from config import HELP_TEXT, ABOUT_US_TEXT

common_router = Router()

main_menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/sell"), KeyboardButton(text="/buy")],
        [KeyboardButton(text="/my_ads"), KeyboardButton(text="/help")],
    ],
    resize_keyboard=True,
    one_time_keyboard=False 
)
# ...
@common_router.message(CommandStart())
async def handle_start_command(message: types.Message):
    await message.answer(
        f"👋 Привіт, **{message.from_user.first_name}**!\n\nЛаскаво просимо до CarForSaleBot.",
        reply_markup=main_menu_kb
    )


@common_router.message(Command("help"))
async def handle_help(message: types.Message):
    await message.answer(text=HELP_TEXT)


@common_router.message(Command("about_us"))
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
    ~Command("my_ads"),
    ~Command("skip"),
)
async def handle_unknown_commands(message: types.Message):
    error_message = "❌ **Невірна команда.** Будь ласка, використайте команду: /help."
    await message.answer(text=error_message)