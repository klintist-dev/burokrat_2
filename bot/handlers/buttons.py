# bot/handlers/buttons.py
from aiogram.types import Message, FSInputFile
from aiogram.utils.formatting import Text as FText, Bold, Italic
from bot.services.gigachat import gigachat_inn
from bot.keyboards import main_keyboard
from bot.parsers import find_inn_by_name, find_inn_by_name_with_region, get_egrul_extract
import os

EXIT_COMMANDS = ["выход", "exit", "стоп", "stop", "меню", "menu", "завершить", "назад"]

# Хранилище для временных данных
user_search_type = {}
user_search_data = {}


async def handle_inn_by_name(message: Message):
    """Обработчик кнопки '🔍 Найти ИНН по названию'"""
    user_id = message.from_user.id
    user_search_type[user_id] = "name_step1"

    content = FText(
        Bold("🔍 Поиск ИНН по названию"), "\n\n",
        "Введите **название организации** (ЮЛ, ИП или физического лица):\n\n",
        Italic("Например: ООО Ромашка, ИП Иванов, Яндекс, Сбербанк")
    )
    await message.answer(**content.as_kwargs())


async def handle_extract_by_inn(message: Message):
    """Обработчик кнопки '📄 Выписка из ЕГРЮЛ (официально)'"""
    user_id = message.from_user.id
    user_search_type[user_id] = "extract"

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
    user_search_type[user_id] = "ask"

    content = FText(
        Bold("💬 Задать вопрос GigaChat"), "\n\n",
        "Задайте любой вопрос. Я постараюсь помочь.\n\n",
        Italic("Например: Что такое ОКВЭД? Как составить договор? Что такое ИНН?")
    )
    await message.answer(**content.as_kwargs())


async def handle_doc(message: Message):
    """Обработчик кнопки '✍️ Составить документ'"""
    user_id = message.from_user.id
    user_search_type[user_id] = "doc"

    content = FText(
        Bold("✍️ Составить документ"), "\n\n",
        "Опишите, какой документ вам нужен, и я помогу его составить.\n\n",
        Italic("Например: заявление на отпуск, претензия в магазин, договор аренды, жалоба в налоговую")
    )
    await message.answer(**content.as_kwargs())


async def handle_help(message: Message):
    """Обработчик кнопки '❓ Помощь'"""
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

    print(f"📨 Получен текст: '{text}' от пользователя {user_id}")
    print(f"🔍 Состояние до обработки: {user_search_type.get(user_id)}")
    print(f"📦 Сохранённые данные: {user_search_data.get(user_id)}")

    if user_id not in user_search_type:
        await message.answer(
            "Сначала выберите действие на клавиатуре.",
            reply_markup=main_keyboard
        )
        return

    search_type = user_search_type[user_id]

    ###########################################################################
    # ПОИСК ИНН ПО НАЗВАНИЮ (2 ШАГА)
    ###########################################################################

    if search_type == "name_step1":
        user_search_data[user_id] = {"company_name": text}
        user_search_type[user_id] = "name_step2"

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
        saved_data = user_search_data.get(user_id, {})
        company_name = saved_data.get("company_name", "")

        if not company_name:
            await message.answer("❌ Что-то пошло не так. Начните поиск заново.", reply_markup=main_keyboard)
            del user_search_type[user_id]
            if user_id in user_search_data:
                del user_search_data[user_id]
            return

        region_code = text if text not in ['-', 'любой', 'пропустить', 'нет'] else None
        region_text = region_code if region_code else "вся Россия"

        wait_msg = await message.answer(f"🔍 Ищу организацию '{company_name}' в регионе {region_text}...")

        if region_code:
            result = await find_inn_by_name_with_region(company_name, region_code)
        else:
            result = await find_inn_by_name(company_name)

        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)

        del user_search_type[user_id]
        if user_id in user_search_data:
            del user_search_data[user_id]

    ###########################################################################
    # ПОЛУЧЕНИЕ ВЫПИСКИ ПО ИНН (1 ШАГ) - РАБОЧАЯ ВЕРСИЯ СО ССЫЛКОЙ
    ###########################################################################

    elif search_type == "extract":
        if not text.isdigit() or len(text) not in (10, 12):
            await message.answer(
                "❌ ИНН должен содержать 10 или 12 цифр.\nПопробуйте ещё раз:",
                reply_markup=main_keyboard
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
            await message.answer(f"❌ {result['error']}", reply_markup=main_keyboard)
        else:
            # Отправляем сообщение со ссылкой и инструкцией
            await message.answer(
                result['message'],
                parse_mode="Markdown",
                reply_markup=main_keyboard,
                disable_web_page_preview=True
            )

        del user_search_type[user_id]

    ###########################################################################
    # ОБЩИЕ ВОПРОСЫ GIGACHAT (1 ШАГ)
    ###########################################################################

    elif search_type == "ask":
        # Проверяем, не хочет ли пользователь выйти
        if text.lower() in EXIT_COMMANDS:
            del user_search_type[user_id]
            await message.answer(
                "✅ Вы вышли из режима вопросов. Выберите действие на клавиатуре.",
                reply_markup=main_keyboard
            )
            return

        wait_msg = await message.answer("🤔 GigaChat думает над ответом...")
        result = await gigachat_inn.ask_question(user_id, text)
        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)
        # del user_search_type[user_id]  # оставляем закомментированным

    ###########################################################################
    # СОСТАВЛЕНИЕ ДОКУМЕНТОВ (1 ШАГ)
    ###########################################################################

    elif search_type == "doc":
        wait_msg = await message.answer("📄 Составляю документ, это займёт несколько секунд...")
        result = await gigachat_inn.create_document(text)
        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)
        del user_search_type[user_id]

    else:
        print(f"❌ Неизвестный тип поиска: {search_type}")
        await message.answer("❌ Что-то пошло не так. Начните заново.", reply_markup=main_keyboard)
        del user_search_type[user_id]