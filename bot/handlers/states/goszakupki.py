# bot/handlers/states/goszakupki.py
"""Обработчик для поиска в госзакупках"""

from aiogram.types import Message
from aiogram.utils.formatting import Text, Bold, Italic

from bot.states import user_states, user_data
from bot.keyboards_inline import get_main_inline_keyboard, get_cancel_inline_keyboard, get_pagination_keyboard
from bot.services.statistics import stats
from bot.utils.validators import is_valid_inn
from bot.parsers.gos_zakupki_parser import GosZakupkiParser
from bot.constants import ITEMS_PER_PAGE
import logging

logger = logging.getLogger(__name__)


async def handle_goszakupki(user_id: int, text: str, message: Message):
    """Обработка поиска в госзакупках"""
    stats.log_command(user_id, "goszakupki")

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

    # Поиск контрактов
    wait_msg = await message.answer(
        "🏛 **Ищу контракты в госзакупках...**\n"
        "_Это может занять несколько секунд_",
        parse_mode="Markdown"
    )

    try:
        parser = GosZakupkiParser()
        result = parser.search_by_supplier_inn(text)
    except Exception as e:
        logger.error(f"Ошибка поиска в госзакупках: {e}")
        result = {'error': str(e)}
    finally:
        await wait_msg.delete()

    # Обработка ошибки
    if 'error' in result:
        await message.answer(
            f"❌ Ошибка при поиске: {result['error']}",
            reply_markup=get_main_inline_keyboard()
        )
        if user_id in user_states:
            del user_states[user_id]
        return

    # Успешный результат
    contracts = result.get('contracts', [])
    total_contracts = len(contracts)
    total_pages = (total_contracts + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE if total_contracts > 0 else 1

    logger.info(f"✅ Найдено контрактов: {total_contracts}, страниц: {total_pages}")

    # Сохраняем данные
    user_data[user_id] = {
        'goszakupki_results': result,
        'goszakupki_inn': text,
        'goszakupki_page': 1,
        'goszakupki_total_pages': total_pages
    }

    # Отправляем первую страницу
    await _send_goszakupki_page(message, user_id)

    # Очищаем состояние (данные остаются для пагинации)
    if user_id in user_states:
        del user_states[user_id]


async def _send_goszakupki_page(message: Message, user_id: int):
    """Отправляет страницу с контрактами госзакупок"""
    data = user_data.get(user_id, {})
    result = data.get('goszakupki_results', {})
    page = data.get('goszakupki_page', 1)
    total_pages = data.get('goszakupki_total_pages', 1)
    inn = data.get('goszakupki_inn', '')

    if not result:
        await message.answer(
            "❌ Данные не найдены. Начните поиск заново.",
            reply_markup=get_main_inline_keyboard()
        )
        return

    contracts = result.get('contracts', [])
    total = result.get('total', 0)

    # Вычисляем, какие контракты показывать на текущей странице
    start_idx = (page - 1) * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, len(contracts))
    current_contracts = contracts[start_idx:end_idx]

    # Формируем ответ
    response = f"🏛 **Контракты по ИНН {inn}**\n"
    response += f"📊 Всего найдено: {total}\n"
    response += f"📄 Страница {page} из {total_pages}\n\n"

    if current_contracts:
        for i, contract in enumerate(current_contracts, start_idx + 1):
            customer_short = contract['customer'][:100] + "..." if len(contract['customer']) > 100 else contract['customer']
            object_short = contract['object'][:100] + "..." if len(contract['object']) > 100 else contract['object']

            response += (
                f"**{i}. {contract['number']}**\n"
                f"📌 Статус: {contract['status']}\n"
                f"💰 Цена: {contract['price']}\n"
                f"🏢 Заказчик: {customer_short}\n"
                f"📅 Опубликован: {contract['publish_date']}\n"
                f"📝 {object_short}\n"
                f"🔗 [Ссылка]({contract['url']})\n\n"
            )
    else:
        response += "❌ Контракты не найдены"

    await message.answer(
        response,
        parse_mode="Markdown",
        reply_markup=get_pagination_keyboard(page, total_pages, "goszakupki")
    )