# bot/handlers/states/ask.py
"""Обработчик для вопросов GigaChat"""

from aiogram.types import Message
from aiogram.utils.formatting import Text, Bold

from bot.states import user_states
from bot.keyboards_inline import get_main_inline_keyboard
from bot.services.gigachat import gigachat_inn
from bot.services.statistics import stats
from bot.constants import EXIT_COMMANDS
import logging

logger = logging.getLogger(__name__)


async def handle_ask(user_id: int, text: str, message: Message):
    """Обработка вопросов к GigaChat"""
    stats.log_command(user_id, "ask")

    # Проверка на выход из режима
    if text.lower() in EXIT_COMMANDS:
        if user_id in user_states:
            del user_states[user_id]
        await message.answer(
            "✅ Вы вышли из режима вопросов. Выберите действие на клавиатуре.",
            reply_markup=get_main_inline_keyboard()
        )
        return

    # Отправляем запрос к GigaChat
    wait_msg = await message.answer("🤔 GigaChat думает над ответом...")

    try:
        result = await gigachat_inn.ask_question(user_id, text)
    except Exception as e:
        logger.error(f"Ошибка GigaChat: {e}")
        result = "❌ Произошла ошибка при обращении к GigaChat"
    finally:
        await wait_msg.delete()

    # Формируем ответ с подсказкой
    full_response = (
        f"{result}\n\n"
        "---\n"
        "💡 **Как продолжить:**\n"
        "• Чтобы задать ещё вопрос, просто напишите его\n"
        "• Чтобы выйти из режима, напишите **«выход»** или **«стоп»**\n"
        "• Или выберите действие на клавиатуре ниже"
    )

    await message.answer(
        full_response,
        parse_mode="Markdown",
        reply_markup=get_main_inline_keyboard()
    )
    # НЕ удаляем состояние, чтобы диалог продолжался