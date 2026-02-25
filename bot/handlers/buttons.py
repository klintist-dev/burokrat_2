# bot/handlers/buttons.py
from aiogram.types import Message
from aiogram.utils.formatting import Text as FText, Bold, Italic
from bot.services.gigachat import gigachat_inn
from bot.keyboards import main_keyboard
from bot.parsers import find_inn_by_name, find_name_by_inn, find_inn_by_name_with_region

# Хранилище для временных данных (что ищет пользователь)
user_search_type = {}  # {user_id: "name_step1" или "name_step2" или "inn" или "ask" или "doc"}
user_search_data = {}  # {user_id: {"company_name": "..."}} для хранения названия


async def handle_inn_by_name(message: Message):
    """Обработчик кнопки '🔍 Узнать ИНН по названию'"""
    user_id = message.from_user.id
    user_search_type[user_id] = "name_step1"

    content = FText(
        Bold("🔍 Поиск ИНН по названию"), "\n\n",
        "Введите **название организации** (ЮЛ, ИП или физического лица):\n\n",
        Italic("Например: ООО Ромашка, ИП Иванов, Яндекс, Сбербанк")
    )
    await message.answer(**content.as_kwargs())


async def handle_name_by_inn(message: Message):
    """Обработчик кнопки '🏢 Узнать название по ИНН'"""
    user_id = message.from_user.id
    user_search_type[user_id] = "inn"

    content = FText(
        Bold("🏢 Поиск названия по ИНН"), "\n\n",
        "Введите **ИНН организации**, и я найду её название.\n\n",
        Italic("Например: 7707083893, 7728168971, 4707013298")
    )
    await message.answer(**content.as_kwargs())


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
    content = FText(
        Bold("❓ Помощь"), "\n\n",
        "Я умею:\n",
        "🔍 **Находить ИНН по названию** (можно указать регион)\n",
        "🏢 **Находить название по ИНН**\n",
        "💬 **Отвечать на вопросы** (GigaChat)\n",
        "✍️ **Составлять документы** (GigaChat)\n\n",
        "Просто выберите нужную кнопку и следуйте инструкциям."
    )
    await message.answer(**content.as_kwargs())


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
        # ШАГ 1: Пользователь ввёл название организации
        user_search_data[user_id] = {"company_name": text}
        user_search_type[user_id] = "name_step2"

        # Спрашиваем регион
        content = FText(
            Bold("📍 Укажите код региона"), "\n\n",
            "Введите **код региона** (2 цифры) для уточнения поиска:\n\n",
            Italic("Например: 47 для Ленинградской области\n"
                   "77 для Москвы\n"
                   "78 для Санкт-Петербурга\n\n"
                   "Или отправьте прочерк «-», если регион не важен")
        )
        await message.answer(**content.as_kwargs())

    elif search_type == "name_step2":
        # ШАГ 2: Пользователь ввёл код региона
        saved_data = user_search_data.get(user_id, {})
        company_name = saved_data.get("company_name", "")

        if not company_name:
            await message.answer("❌ Что-то пошло не так. Начните поиск заново.", reply_markup=main_keyboard)
            del user_search_type[user_id]
            if user_id in user_search_data:
                del user_search_data[user_id]
            return

        # Определяем, хочет ли пользователь указать регион
        region_code = text if text not in ['-', 'любой', 'пропустить', 'нет'] else None

        # Отправляем сообщение о начале поиска
        region_text = region_code if region_code else "вся Россия"
        wait_msg = await message.answer(f"🔍 Ищу организацию '{company_name}' в регионе {region_text}...")

        # 👇 ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ С РЕГИОНОМ!
        if region_code:
            result = await find_inn_by_name_with_region(company_name, region_code)
        else:
            result = await find_inn_by_name(company_name)

        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)

        # Очищаем данные
        del user_search_type[user_id]
        if user_id in user_search_data:
            del user_search_data[user_id]

    ###########################################################################
    # ПОИСК НАЗВАНИЯ ПО ИНН (1 ШАГ)
    ###########################################################################

    elif search_type == "inn":
        if not text.isdigit() or len(text) not in (10, 12):
            await message.answer(
                "❌ ИНН должен содержать 10 или 12 цифр.\nПопробуйте ещё раз:",
                reply_markup=main_keyboard
            )
            return

        wait_msg = await message.answer("🔍 Ищу название по ИНН...")
        result = await find_name_by_inn(text)
        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)
        del user_search_type[user_id]

    ###########################################################################
    # ОБЩИЕ ВОПРОСЫ GIGACHAT (1 ШАГ)
    ###########################################################################

    elif search_type == "ask":
        wait_msg = await message.answer("🤔 GigaChat думает над ответом...")
        result = await gigachat_inn.ask_question(text)
        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)
        del user_search_type[user_id]

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