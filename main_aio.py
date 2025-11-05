import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command

from config import BOT_TOKEN, DEFAULT_BOT_PROPERTIES


from handlers.common import common_router, handle_unknown_commands
from handlers.sell.sell_router import sell_router
from handlers.buy.buy_router import buy_router


logging.basicConfig(level=logging.INFO)


async def main():
    bot = Bot(token=BOT_TOKEN, default=DEFAULT_BOT_PROPERTIES)
    dp = Dispatcher()

    dp.include_router(common_router)
    dp.include_router(sell_router)
    dp.include_router(buy_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user.")
