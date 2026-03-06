# bot/handlers/start.py

from aiogram.types import Message
from aiogram.filters import Command
from aiogram import Router  # ← ДОБАВЬ ЭТУ СТРОКУ
from aiogram.utils.formatting import Text, Bold, Italic
from bot.keyboards import main_keyboard

# Создаём роутер (ДОБАВЬ ЭТО!)
router = Router()

@router.message(Command("start"))  # ← ИЗМЕНИ ДЕКОРАТОР
async def cmd_start(message: Message):
    """Приветственное сообщение с кнопками"""
    # bot/handlers/start.py (добавь в начало функции cmd_start)
    print(f"📋 Используется клавиатура с кнопками: {[btn.text for row in main_keyboard.keyboard for btn in row]}")

    # 1. СОБИРАЕМ ИМЯ И ФАМИЛИЮ
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    # Если есть и имя, и фамилия
    if first_name and last_name:
        full_name = f"{first_name} {last_name}"
    # Если только имя
    elif first_name:
        full_name = first_name
    # Если ничего нет
    else:
        full_name = "пользователь"

    # 2. СОЗДАЁМ ТЕКСТ
    content = Text(
        Bold("👋 Добро пожаловать, "),
        Bold(full_name), "!\n\n",

        "Я ", Italic("БюрократЪ 2.0"), " — ваш информационный помощник.\n\n",

        Bold("📋 Что я умею:\n"),
        "• 🔍 Находить ИНН по названию организации (через парсинг)\n",
        "• 🏢 Находить название организации по ИНН (через парсинг)\n",
        "• 💬 Задать вопрос GigaChat\n",
        "• ✍️ Составить документ\n\n",

        "👇 Выберите действие на клавиатуре:"
    )

    # 4. ОТПРАВЛЯЕМ
    await message.answer(
        **content.as_kwargs(),
        reply_markup=main_keyboard
    )