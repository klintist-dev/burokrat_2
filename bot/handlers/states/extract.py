# bot/handlers/states/extract.py
"""Обработчик для получения выписки из ЕГРЮЛ"""

from aiogram.types import Message, FSInputFile
from aiogram.utils.formatting import Text, Bold, Italic

from bot.states import user_states, user_data
from bot.keyboards_inline import get_main_inline_keyboard, get_cancel_inline_keyboard
from bot.parsers import get_egrul_extract
from bot.services.statistics import stats
from bot.utils.validators import is_valid_inn
import os
import logging

logger = logging.getLogger(__name__)


async def handle_extract(user_id: int, text: str, message: Message):
    """Обработка запроса выписки из ЕГРЮЛ"""
    stats.log_command(user_id, "extract")

    # Валидация ИНН
    if not is_valid_inn(text):
        content = Text(
            "❌ ", Bold("Некорректный ИНН"), "\n\n",
            "ИНН должен содержать 10 или 12 цифр.\n",
            "Попробуйте ещё раз:"
        )
        await message.answer(
            **content.as_kwargs(),
            reply_markup=get_cancel_inline_keyboard()
        )
        return

    # Запрос выписки
    wait_msg = await message.answer(
        "📄 **Запрашиваю выписку...**\n"
        "_Обычно это занимает 10-20 секунд_",
        parse_mode="Markdown"
    )

    try:
        result = await get_egrul_extract(text)
    except Exception as e:
        logger.error(f"Ошибка получения выписки: {e}")
        result = {'error': 'Ошибка при получении выписки'}
    finally:
        await wait_msg.delete()

    # Обработка результата
    if 'error' in result:
        await message.answer(
            f"❌ {result['error']}",
            reply_markup=get_main_inline_keyboard()
        )
    else:
        document = FSInputFile(result['filepath'])
        await message.answer_document(
            document,
            caption=(
                "✅ **Выписка получена!**\n"
                f"📄 {result['org_name'][:200]}...\n"
                '_Источник: <a href="https://egrul.nalog.ru">ФНС России</a>_'
            ),
            parse_mode="HTML",
            reply_markup=get_main_inline_keyboard()
        )

        # Удаляем временный файл
        try:
            os.remove(result['filepath'])
            logger.info(f"Файл удалён: {result['filepath']}")
        except Exception as e:
            logger.warning(f"Не удалось удалить файл: {e}")

    # Очищаем состояние
    if user_id in user_states:
        del user_states[user_id]