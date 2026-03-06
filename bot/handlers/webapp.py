# bot/handlers/webapp.py

from aiogram.types import Message, WebAppInfo
from aiogram import Router
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()


@router.message(lambda message: message.text == "🌐 Умный поиск (Mini App)")
async def handle_webapp(message: Message):
    """Открывает мини-приложение"""

    # Создаём инлайн-кнопку с WebApp
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🔍 Открыть умный поиск",
        web_app=WebAppInfo(url="https://bot-web.94.241.142.61.sslip.io")
    )

    await message.answer(
        "🎯 **Добро пожаловать в мини-приложение!**\n\n"
        "Здесь будет удобный поиск организаций с красивыми карточками.\n"
        "Пока это просто тест — нажимай кнопку и смотри, как открывается окно!",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )