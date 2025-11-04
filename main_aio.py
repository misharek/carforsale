import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.client.default import DefaultBotProperties


BOT_TOKEN = "8117385329:AAFwTXqVa8Y6VTfoZs64wgwxIiG6xhowfF8"

default_properties = DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)

bot = Bot(token=BOT_TOKEN, default=default_properties)
dp = Dispatcher()


HELP_TEXT = (
    "CarForSaleBot — це ваш особистий інструмент для швидкої та зручної купівлі та продажу автомобілів у Telegram.\n\n"
    "**Що ви можете робити з CarForSaleBot:**\n\n"
    "/sell - Легко продати своє авто: Розмістіть оголошення за кілька хвилин, додайте фото та детальний опис.\n\n"
    "/buy - Знайти авто мрії: Переглядайте тисячі оголошень, фільтруйте за маркою, моделлю, ціною та іншими параметрами."
)

ABOUT_US_TEXT = """
⭐️ Проєкт: CarForSaleBot (Купівля/Продаж Авто)

🤝 Мета проєкту (Навчальна):
Цей Telegram-бот розроблений командою студентів [ІПЗ-11] в рамках курсового проєкту з дисципліни "[Основи програмної інженарії]".

Основна мета розробки - демонстрація практичних навичок у сфері:
- Розробки чат-ботів (Python, Telegram API).
- Реалізації багатоетапного збору даних.

💻 Технічна реалізація
- Платформа: Telegram
- Мова програмування: Python
- Бібліотека: aiogram (Асинхронна)

👥 Команда розробників:
- Головний розробник: [Ремез Михайло]
- Backend-розробник: [Кадик Владислав]

💡 Функціонал бота
CarForSaleBot призначений для автоматизації процесу розміщення оголошень про продаж авто (/sell) та пошуку автомобілів (/buy). Це прототип функціональної торгової платформи.

---
Дякуємо, що тестуєте наш проєкт! Ваш відгук важливий для успішного захисту.
"""


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    # Використовуємо await для асинхронної відправки повідомлення
    await message.answer(
        f"👋 Привіт, **{message.from_user.first_name}**!\n"
        "Ласкаво просимо до CarForSaleBot."
    )


@dp.message(Command("help"))
async def handle_help(message: types.Message):
    await message.answer(text=HELP_TEXT)


@dp.message(Command("about us"))
async def handle_aboutus(message: types.Message):
    await message.answer(
        text=ABOUT_US_TEXT, parse_mode=ParseMode.MARKDOWN
    )  # ParseMode додано для тексту з Markdown


@dp.message(Command("sell"))
async def handle_sell(message: types.Message):
    await message.answer("🛠️ Команда /sell: Реалізація діалогу продажу буде тут.")


@dp.message(Command("buy"))
async def handle_buy(message: types.Message):
    await message.answer("🛠️ Команда /buy: Реалізація пошуку та фільтрації буде тут.")


@dp.message()
async def handle_unknown_commands(message: types.Message):
    error_message = "❌ **Невірна команда.** Будь ласка, використайте команду: /help."
    await message.answer(text=error_message)


async def main():

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
