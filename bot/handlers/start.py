from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.formatting import Text, Bold, Italic

from bot.keyboards_inline import get_main_inline_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Приветственное сообщение с инлайн-кнопками"""

    # Собираем имя пользователя
    first_name = message.from_user.first_name or ""
    last_name = message.from_user.last_name or ""

    if first_name and last_name:
        full_name = f"{first_name} {last_name}"
    elif first_name:
        full_name = first_name
    else:
        full_name = "пользователь"

    # Создаём форматированный текст
    content = Text(
        Bold("👋 Добро пожаловать, "),
        Bold(full_name), "!\n\n",
        "Я ", Italic("БюрократЪ 2.0"), " — ваш информационный помощник.\n\n",
        Bold("📋 Что я умею:\n"),
        "• 🔍 Находить ИНН по названию организации\n",
        "• 📄 Получать выписки из ЕГРЮЛ\n",
        "• 💬 Отвечать на вопросы (GigaChat)\n",
        "• ✍️ Составлять документы\n\n",
        "👇 Выберите действие на клавиатуре ниже:"
    )

    await message.answer(
        **content.as_kwargs(),
        reply_markup=get_main_inline_keyboard()
    )