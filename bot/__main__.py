# bot/__main__.py
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from bot.config_reader import get_config
from bot.handlers import router

async def main():
    # 1. Получаем настройки (токен, имя и т.д.)
    config = get_config()

    # 2. Создаём бота (подключаемся к Telegram)
    bot = Bot(
        token=config.token.get_secret_value(),  # Достаём токен из коробочки
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)  # Красивое форматирование
    )

    # 3. Создаём диспетчер (главный диспетчер, который раздаёт команды)
    dp = Dispatcher()
    dp.include_router(router)

    # 4. Запускаем
    print(f"🚀 {config.bot_name} запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Настройка логирования (чтобы видеть ошибки)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    asyncio.run(main())