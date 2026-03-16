# bot/handlers/states/name.py
"""Обработчики для поиска ИНН по названию"""

from aiogram.types import Message
from aiogram.utils.formatting import Text, Bold, Italic

from bot.states import user_states, user_data
from bot.keyboards_inline import get_main_inline_keyboard, get_cancel_inline_keyboard
from bot.parsers import find_inn_by_name_structured
from bot.services.statistics import stats
from bot.utils.message_utils import format_search_results
from bot.constants import REGION_SKIP_COMMANDS
import logging

logger = logging.getLogger(__name__)


async def handle_name_step1(user_id: int, text: str, message: Message):
    """Шаг 1: сохраняем название организации"""
    stats.log_command(user_id, "inn_search_start")

    user_data[user_id] = {"company_name": text}
    user_states[user_id] = "name_step2"

    content = Text(
        "📍 ", Bold("Укажите код региона"), "\n\n",
        "Введите ", Bold("код региона"), " (2 цифры) для уточнения поиска:\n\n",
        Italic("Например: 47 для Ленинградской области\n"
               "77 для Москвы\n"
               "78 для Санкт-Петербурга\n\n"
               "Или отправьте прочерк «-», если регион не важен")
    )

    await message.answer(
        **content.as_kwargs(),
        reply_markup=get_cancel_inline_keyboard()
    )


async def handle_name_step2(user_id: int, text: str, message: Message):
    """Шаг 2: обрабатываем регион и выполняем поиск"""
    stats.log_command(user_id, "inn_search_complete")

    saved_data = user_data.get(user_id, {})
    company_name = saved_data.get("company_name", "")

    if not company_name:
        await message.answer(
            "❌ Что-то пошло не так. Начните поиск заново.",
            reply_markup=get_main_inline_keyboard()
        )
        _cleanup_user_state(user_id)
        return

    # Определяем регион
    region_code = None if text in REGION_SKIP_COMMANDS else text
    region_text = region_code if region_code else "вся Россия"

    # Поиск
    wait_msg = await message.answer(f"🔍 Ищу организацию '{company_name}' в регионе {region_text}...")

    try:
        result = await find_inn_by_name_structured(company_name, region_code)
    except Exception as e:
        logger.error(f"Ошибка поиска ИНН: {e}")
        result = {'error': 'Ошибка при поиске'}
    finally:
        await wait_msg.delete()

    if 'error' in result:
        await message.answer(
            f"❌ {result['error']}",
            reply_markup=get_main_inline_keyboard()
        )
    else:
        output = format_search_results(result, company_name)
        await message.answer(
            output,
            parse_mode="Markdown",
            reply_markup=get_main_inline_keyboard()
        )

    # Очищаем состояние
    _cleanup_user_state(user_id)


def _cleanup_user_state(user_id: int):
    """Очищает состояние пользователя"""
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_data:
        del user_data[user_id]