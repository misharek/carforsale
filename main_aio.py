import asyncio
import logging
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN, DEFAULT_BOT_PROPERTIES

# Імпортуємо роутери з папки 'handlers'
from handlers.common import common_router
from handlers.sell.sell_router import sell_router
from handlers.buy.buy_router import buy_router


logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=BOT_TOKEN, default=DEFAULT_BOT_PROPERTIES)
    dp = Dispatcher()

    # Підключаємо роутери до головного диспетчера
    dp.include_router(common_router)
    dp.include_router(sell_router)
    dp.include_router(buy_router)

    # --- ТУТ БІЛЬШЕ НЕМАЄ ЖОДНИХ ФУНКЦІЙ ---

    # Запуск бота
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
