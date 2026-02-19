# bot/handlers/start.py
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.utils.formatting import Text, Bold, Italic


async def cmd_start(message: Message):
    """Приветственное сообщение с кнопками"""

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
        "• 🔍 Находить ИНН по названию организации\n",
        "• 🏢 Находить название организации по ИНН\n",
        "• ❓ Помогать с вопросами\n\n",

        "👇 Выберите действие на клавиатуре:"
    )

    # 3. СОЗДАЁМ КНОПКИ
    button_inn_by_name = KeyboardButton(text="🔍 Узнать ИНН по названию")
    button_name_by_inn = KeyboardButton(text="🏢 Узнать название по ИНН")
    button_help = KeyboardButton(text="❓ Помощь")

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [button_inn_by_name],
            [button_name_by_inn],
            [button_help]
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие..."
    )

    # 4. ОТПРАВЛЯЕМ
    await message.answer(
        **content.as_kwargs(),
        reply_markup=keyboard
    )