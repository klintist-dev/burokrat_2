# bot/handlers/buttons.py
from aiogram.types import Message
from aiogram.utils.formatting import Text as FText, Bold, Italic
from bot.services.gigachat import gigachat_inn
from bot.keyboards import main_keyboard  # 👈 ИМПОРТИРУЕМ
from bot.parsers import find_inn_by_name, find_name_by_inn, get_egrul_extract

# Хранилище для временных данных (что ищет пользователь)
user_search_type = {}  # {user_id: "inn" или "name" или "ask" или "doc"}

async def handle_inn_by_name(message: Message):
    """Обработчик кнопки 'Узнать ИНН по названию'"""
    user_id = message.from_user.id
    user_search_type[user_id] = "name"  # Запоминаем, что пользователь ищет ИНН по названию

    content = FText(
        Bold("🔍 Поиск ИНН по названию"), "\n\n",
        "Введите название организации, и я найду её ИНН.\n\n",
        Italic("Например: ООО Ромашка")
    )
    await message.answer(**content.as_kwargs())

async def handle_name_by_inn(message: Message):
    """Обработчик кнопки 'Узнать название по ИНН'"""
    user_id = message.from_user.id
    user_search_type[user_id] = "inn"  # Запоминаем, что пользователь ищет название по ИНН

    content = FText(
        Bold("🏢 Поиск названия по ИНН"), "\n\n",
        "Введите ИНН организации, и я найду её название.\n\n",
        Italic("Например: 7707083893")
    )
    await message.answer(**content.as_kwargs())


async def handle_ask(message: Message):
    """Обработчик кнопки 'Задать вопрос GigaChat'"""
    user_id = message.from_user.id
    user_search_type[user_id] = "ask"

    content = FText(
        Bold("💬 Задать вопрос GigaChat"), "\n\n",
        "Задайте любой вопрос. Я постараюсь помочь.\n\n",
        Italic("Например: Что такое ОКВЭД? Как составить договор?")
    )
    await message.answer(**content.as_kwargs())


async def handle_doc(message: Message):
    """Обработчик кнопки 'Составить документ'"""
    user_id = message.from_user.id
    user_search_type[user_id] = "doc"

    content = FText(
        Bold("✍️ Составить документ"), "\n\n",
        "Опишите, какой документ вам нужен, и я помогу его составить.\n\n",
        Italic("Например: заявление на отпуск, претензия в магазин, договор аренды")
    )
    await message.answer(**content.as_kwargs())

async def handle_help(message: Message):
    """Обработчик кнопки 'Помощь' (если оставили)"""
    content = FText(
        Bold("❓ Помощь"), "\n\n",
        "Я умею:\n",
        "🔍 **Находить ИНН по названию** (через парсинг)\n",
        "🏢 **Находить название по ИНН** (через парсинг)\n",
        "💬 **Отвечать на вопросы** (GigaChat)\n",
        "✍️ **Составлять документы** (GigaChat)\n\n",
        "Просто выберите нужную кнопку и следуйте инструкциям."
    )
    await message.answer(**content.as_kwargs())


async def handle_user_input(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    print(f"📨 Получен текст: '{text}' от пользователя {user_id}")
    print(f"🔍 Состояние до обработки: {user_search_type.get(user_id)}")

    if user_id not in user_search_type:
        await message.answer(
            "Сначала выберите действие на клавиатуре.",
            reply_markup=main_keyboard  # 👈 ВОТ ТАК
        )
        return

    search_type = user_search_type[user_id]

    if search_type == "name":
        print("✅ ВЕТКА: name (парсинг ИНН по названию)")
        wait_msg = await message.answer("🔍 Ищу ИНН по названию...")
        result = await find_inn_by_name(text)
        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)

    elif search_type == "inn":
        print("✅ ВЕТКА: inn (парсинг названия по ИНН)")
        wait_msg = await message.answer("🔍 Ищу название по ИНН...")
        result = await find_name_by_inn(text)
        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)

    elif search_type == "ask":
        print("✅ ВЕТКА: ask (GigaChat вопрос)")
        wait_msg = await message.answer("🤔 GigaChat думает над ответом...")
        result = await gigachat_inn.ask_question(text)
        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)

    elif search_type == "doc":
        print("✅ ВЕТКА: doc (GigaChat документ)")
        wait_msg = await message.answer("📄 Составляю документ, это займёт несколько секунд...")
        result = await gigachat_inn.create_document(text)
        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)

    # После ответа сбрасываем состояние
    del user_search_type[user_id]