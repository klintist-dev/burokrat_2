# bot/handlers/states/doc.py
"""Обработчик для создания документов"""

from aiogram.types import Message, FSInputFile

from bot.states import user_states
from bot.keyboards_inline import get_main_inline_keyboard
from bot.services.gigachat import gigachat_inn
from bot.services.statistics import stats
from bot.utils.docx_generator import DocxGenerator
import os
import logging

logger = logging.getLogger(__name__)


async def handle_doc(user_id: int, text: str, message: Message):
    """Обработка создания документов"""
    stats.log_command(user_id, "doc")

    wait_msg = await message.answer("📄 Составляю документ, это займёт несколько секунд...")

    try:
        # Получаем текст документа от GigaChat
        result_text = await gigachat_inn.create_document(text)

        # Создаем Word-документ
        title = text[:50] + ("..." if len(text) > 50 else "")
        filepath = DocxGenerator.create_document(title, result_text, user_id)

        # Отправляем файл
        document = FSInputFile(filepath)
        await message.answer_document(
            document,
            caption=(
                "✅ **Документ готов!**\n"
                f"📄 {title}\n"
                "📎 Файл в формате Word (.docx)"
            ),
            parse_mode="Markdown",
            reply_markup=get_main_inline_keyboard()
        )

        # Удаляем временный файл
        try:
            os.remove(filepath)
            logger.info(f"Документ удалён: {filepath}")
        except Exception as e:
            logger.warning(f"Не удалось удалить документ: {e}")

    except Exception as e:
        logger.error(f"Ошибка создания документа: {e}")
        await message.answer(
            f"❌ Ошибка при создании документа: {e}",
            reply_markup=get_main_inline_keyboard()
        )
    finally:
        await wait_msg.delete()
        # Очищаем состояние
        if user_id in user_states:
            del user_states[user_id]