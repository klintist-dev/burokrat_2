# bot/utils/message_utils.py
"""Вспомогательные функции для работы с сообщениями"""

from aiogram.types import Message, CallbackQuery


async def update_or_send_message(callback: CallbackQuery, text: str, reply_markup=None):
    """Универсальное обновление или отправка сообщения"""
    if callback.message.text:
        await callback.message.edit_text(text, reply_markup=reply_markup)
    else:
        await callback.message.answer(text, reply_markup=reply_markup)


def format_search_results(result: dict, original_query: str, max_results: int = 4) -> str:
    """
    Красиво форматирует результаты поиска
    (переносим сюда из buttons.py)
    """
    total = result.get('total', 0)
    ranked = result.get('ranked', [])

    output = f"📊 **Найдено организаций: {total}**\n"
    if result.get('region'):
        region_display = "вся Россия" if result['region'] is None else f"код {result['region']}"
        output += f"📍 Регион: {region_display}\n"
    output += "\n"

    if ranked:
        best = ranked[0]
        output += "✨ **Наилучшее совпадение:**\n\n"
        output += f"**{best['name'][:100]}**\n"
        output += f"└ ИНН: `{best['inn']}`\n"
        if best.get('ogrn'):
            output += f"└ ОГРН: {best['ogrn']}\n"
        if best.get('date'):
            output += f"└ Дата регистрации: {best['date']}\n"
        if best.get('status'):
            status_emoji = "✅" if best['status'] == "действующее" else "❌"
            output += f"└ Статус: {status_emoji} {best['status']}\n"

        relevance = int(best.get('relevance', 0) * 100)
        output += f"\n📊 **Релевантность: {relevance}%**\n\n"

        if len(ranked) > 1:
            output += "📋 **Другие организации:**\n\n"
            remaining = min(max_results - 1, len(ranked) - 1)

            for i, org in enumerate(ranked[1:remaining + 1], 2):
                relevance = int(org.get('relevance', 0) * 100)
                output += f"{i}. **{org['name'][:100]}**\n"
                output += f"   ИНН: `{org['inn']}`\n"
                if org.get('ogrn'):
                    output += f"   ОГРН: {org['ogrn']}\n"
                output += f"   📊 Релевантность: {relevance}%\n\n"

            if len(ranked) > max_results:
                output += f"... и ещё {len(ranked) - max_results} организаций\n\n"
    else:
        output += "❌ **Организации не найдены**\n\n"

    output += "---\n"
    output += "💡 **Совет:** Если нужная организация не найдена, попробуйте:\n"
    output += "• Уточнить название (без кавычек)\n"
    output += "• Указать другой регион\n"
    output += "• Использовать поиск по ИНН"

    return output