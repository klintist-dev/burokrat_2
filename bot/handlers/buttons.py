from aiogram.types import Message, FSInputFile
from aiogram.utils.formatting import Text as FText, Bold, Italic
from bot.services.gigachat import gigachat_inn
# from bot.keyboards import main_keyboard

from bot.states import user_states, user_data
from bot.keyboards_inline import get_main_inline_keyboard, get_cancel_inline_keyboard
from bot.parsers import find_inn_by_name, find_inn_by_name_with_region, get_egrul_extract
import os
from bot.services.statistics import stats

from bot.utils.docx_generator import DocxGenerator

from bot.utils.text_matcher import TextMatcher
import json
import time
from bot.parsers import find_inn_by_name_structured

EXIT_COMMANDS = ["выход", "exit", "стоп", "stop", "меню", "menu", "завершить", "назад"]


# ⚠️ Локальные хранилища УДАЛЕНЫ - используем импортированные user_states и user_data


def format_search_results(result: dict, original_query: str) -> str:
    """
    Красиво форматирует результаты поиска
    """
    total = result.get('total', 0)
    ranked = result.get('ranked', [])

    # Заголовок
    output = f"📊 **Найдено организаций: {total}**\n"
    if result.get('region'):
        region_display = "вся Россия" if result['region'] is None else f"код {result['region']}"
        output += f"📍 Регион: {region_display}\n"
    output += "\n"

    if ranked:
        # Первая организация (наилучшее совпадение)
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

        # Остальные результаты
        if len(ranked) > 1:
            output += "📋 **Другие организации:**\n\n"
            for i, org in enumerate(ranked[1:10], 2):  # со 2 по 10
                relevance = int(org.get('relevance', 0) * 100)
                output += f"{i}. **{org['name'][:100]}**\n"
                output += f"   ИНН: `{org['inn']}`\n"
                if org.get('ogrn'):
                    output += f"   ОГРН: {org['ogrn']}\n"
                output += f"   📊 Релевантность: {relevance}%\n\n"

            if len(ranked) > 10:
                output += f"... и ещё {len(ranked) - 10} организаций\n\n"
    else:
        output += "❌ **Организации не найдены**\n\n"

    # Подсказка
    output += "---\n"
    output += "💡 **Совет:** Если нужная организация не найдена, попробуйте:\n"
    output += "• Уточнить название (без кавычек)\n"
    output += "• Указать другой регион\n"
    output += "• Использовать поиск по ИНН"

    return output


async def handle_inn_by_name(message: Message):
    """Обработчик кнопки '🔍 Найти ИНН по названию'"""
    user_id = message.from_user.id
    user_states[user_id] = "name_step1"

    content = FText(
        Bold("🔍 Поиск ИНН по названию"), "\n\n",
        "Введите **название организации** (ЮЛ, ИП или физического лица):\n\n",
        Italic("Например: ООО Ромашка, ИП Иванов, Яндекс, Сбербанк")
    )
    await message.answer(**content.as_kwargs())


async def handle_extract_by_inn(message: Message):
    """Обработчик кнопки '📄 Выписка из ЕГРЮЛ (официально)'"""
    user_id = message.from_user.id
    user_states[user_id] = "extract"

    await message.answer(
        "📄 <b>Получение выписки из ЕГРЮЛ</b>\n\n"
        "Введите <b>ИНН организации</b>, и я пришлю ссылку на официальную выписку с сайта "
        '<a href="https://egrul.nalog.ru">ФНС России</a>.\n\n'
        "<i>Например: 4707013298, 7707083893</i>\n\n"
        "<i>Выписка придёт в формате PDF по ссылке</i>",
        parse_mode="HTML"
    )


async def handle_ask(message: Message):
    """Обработчик кнопки '💬 Задать вопрос GigaChat'"""
    user_id = message.from_user.id
    user_states[user_id] = "ask"

    content = FText(
        Bold("💬 Задать вопрос GigaChat"), "\n\n",
        "Задайте любой вопрос. Я постараюсь помочь.\n\n",
        Italic("Например: Что такое ОКВЭД? Как составить договор? Что такое ИНН?")
    )
    await message.answer(**content.as_kwargs())


async def handle_doc(message: Message):
    """Обработчик кнопки '✍️ Составить документ'"""
    user_id = message.from_user.id
    user_states[user_id] = "doc"

    content = FText(
        Bold("✍️ Составить документ"), "\n\n",
        "Опишите, какой документ вам нужен, и я помогу его составить.\n\n",
        Italic("Например: заявление на отпуск, претензия в магазин, договор аренды, жалоба в налоговую")
    )
    await message.answer(**content.as_kwargs())


async def handle_help(message: Message):
    """Обработчик кнопки '❓ Помощь'"""
    user_id = message.from_user.id
    stats.log_command(user_id, "help")

    await message.answer(
        "❓ <b>Помощь</b>\n\n"
        "Я умею:\n"
        "🔍 <b>Найти ИНН по названию</b> (с учётом региона)\n"
        "📄 <b>Получить ссылку на выписку из ЕГРЮЛ</b> (официальный PDF)\n"
        "💬 <b>Отвечать на вопросы</b> (GigaChat)\n"
        "✍️ <b>Составлять документы</b> (GigaChat)\n\n"
        "📌 <b>Ссылки:</b>\n"
        '• <a href="https://www.nalog.ru">ФНС России</a>\n'
        '• <a href="https://egrul.nalog.ru">Поиск по ЕГРЮЛ</a>\n\n'
        "Просто выберите нужную кнопку и следуйте инструкциям.",
        parse_mode="HTML"
    )


async def handle_user_input(message: Message):
    """
    Обрабатывает любой текст, который вводит пользователь
    """
    user_id = message.from_user.id
    text = message.text.strip()

    # Логируем пользователя
    username = message.from_user.username
    first_name = message.from_user.first_name
    stats.log_user(user_id, username, first_name)

    print(f"📨 Получен текст: '{text}' от пользователя {user_id}")
    print(f"🔍 Состояние до обработки: {user_states.get(user_id)}")
    print(f"📦 Сохранённые данные: {user_data.get(user_id)}")

    if user_id not in user_states:
        await message.answer(
            "Сначала выберите действие, нажав на кнопку под сообщением.",
            reply_markup=get_main_inline_keyboard()
        )
        return

    search_type = user_states[user_id]

    ###########################################################################
    # ПОИСК ИНН ПО НАЗВАНИЮ (2 ШАГА)
    ###########################################################################

    if search_type == "name_step1":
        stats.log_command(user_id, "inn_search_start")
        user_data[user_id] = {"company_name": text}
        user_states[user_id] = "name_step2"

        await message.answer(
            "📍 <b>Укажите код региона</b>\n\n"
            "Введите <b>код региона</b> (2 цифры) для уточнения поиска:\n\n"
            "<i>Например: 47 для Ленинградской области\n"
            "77 для Москвы\n"
            "78 для Санкт-Петербурга</i>\n\n"
            "<i>Или отправьте прочерк «-», если регион не важен</i>",
            parse_mode="HTML"
        )

    elif search_type == "name_step2":
        stats.log_command(user_id, "inn_search_complete")

        saved_data = user_data.get(user_id, {})
        company_name = saved_data.get("company_name", "")

        if not company_name:
            await message.answer(
                "❌ Что-то пошло не так. Начните поиск заново.",
                reply_markup=get_main_inline_keyboard()
            )
            if user_id in user_states:
                del user_states[user_id]
            if user_id in user_data:
                del user_data[user_id]
            return

        region_code = text if text not in ['-', 'любой', 'пропустить', 'нет'] else None
        region_text = region_code if region_code else "вся Россия"

        wait_msg = await message.answer(f"🔍 Ищу организацию '{company_name}' в регионе {region_text}...")
        result = await find_inn_by_name_structured(company_name, region_code)
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

        if user_id in user_states:
            del user_states[user_id]
        if user_id in user_data:
            del user_data[user_id]

    ###########################################################################
    # ПОЛУЧЕНИЕ ВЫПИСКИ ПО ИНН (1 ШАГ)
    ###########################################################################

    elif search_type == "extract":
        stats.log_command(user_id, "extract")

        if not text.isdigit() or len(text) not in (10, 12):
            await message.answer(
                "❌ ИНН должен содержать 10 или 12 цифр.\nПопробуйте ещё раз:",
                reply_markup=get_cancel_inline_keyboard()
            )
            return

        wait_msg = await message.answer(
            "📄 <b>Запрашиваю выписку...</b>\n"
            "<i>Обычно это занимает 10-20 секунд</i>",
            parse_mode="HTML"
        )

        result = await get_egrul_extract(text)
        await wait_msg.delete()

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
                    "✅ <b>Выписка получена!</b>\n"
                    f"📄 {result['org_name'][:200]}...\n"
                    '<i>Источник: </i><a href="https://egrul.nalog.ru">ФНС России</a>'
                ),
                parse_mode="HTML",
                reply_markup=get_main_inline_keyboard()
            )

            try:
                os.remove(result['filepath'])
                print(f"🗑️ Файл удалён: {result['filepath']}")
            except Exception as e:
                print(f"⚠️ Не удалось удалить файл: {e}")

        if user_id in user_states:
            del user_states[user_id]

    ###########################################################################
    # ОБЩИЕ ВОПРОСЫ GIGACHAT (1 ШАГ)
    ###########################################################################

    elif search_type == "ask":
        stats.log_command(user_id, "ask")

        if text.lower() in EXIT_COMMANDS:
            if user_id in user_states:
                del user_states[user_id]
            await message.answer(
                "✅ Вы вышли из режима вопросов. Выберите действие на клавиатуре.",
                reply_markup=get_main_inline_keyboard()
            )
            return

        wait_msg = await message.answer("🤔 GigaChat думает над ответом...")
        result = await gigachat_inn.ask_question(user_id, text)
        await wait_msg.delete()

        full_response = f"{result}\n\n---\n💡 **Как продолжить:**\n• Чтобы задать ещё вопрос, просто напишите его\n• Чтобы выйти из режима, напишите **«выход»** или **«стоп»**\n• Или выберите действие на клавиатуре ниже"
        await message.answer(
            full_response,
            parse_mode=None,
            reply_markup=get_main_inline_keyboard()
        )
        # НЕ удаляем состояние, чтобы диалог продолжался

    ###########################################################################
    # СОСТАВЛЕНИЕ ДОКУМЕНТОВ (1 ШАГ)
    ###########################################################################

    elif search_type == "doc":
        stats.log_command(user_id, "doc")
        wait_msg = await message.answer("📄 Составляю документ, это займёт несколько секунд...")

        result_text = await gigachat_inn.create_document(text)
        await wait_msg.delete()

        try:
            title = text[:50] + ("..." if len(text) > 50 else "")
            filepath = DocxGenerator.create_document(title, result_text, user_id)
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

            try:
                os.remove(filepath)
                print(f"🗑️ Документ удалён: {filepath}")
            except Exception as e:
                print(f"⚠️ Не удалось удалить документ: {e}")

        except Exception as e:
            print(f"❌ Ошибка создания документа: {e}")
            full_response = f"{result_text}\n\n---\n✅ **Документ готов!**\n\n👉 Чтобы составить ещё один документ, нажмите кнопку **«✍️ Составить документ»**"
            await message.answer(
                full_response,
                parse_mode=None,
                reply_markup=get_main_inline_keyboard()
            )

        if user_id in user_states:
            del user_states[user_id]