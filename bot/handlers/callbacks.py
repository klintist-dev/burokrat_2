"""
Обработчики инлайн-кнопок (callback'ов)
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.formatting import Text, Bold, Italic

from bot.keyboards_inline import (
    get_main_inline_keyboard,
    get_cancel_inline_keyboard,
    get_document_types_keyboard,
    get_back_inline_keyboard
)

from bot.states import user_states, user_data

router = Router()


@router.callback_query(F.data == "menu_find_inn")
async def callback_find_inn(callback: CallbackQuery):
    """Поиск ИНН по названию"""
    user_id = callback.from_user.id
    user_states[user_id] = "name_step1"

    # Короткий и понятный текст
    content = Text(
        Bold("🔍 Поиск ИНН\n\n"),
        "Введите название организации\n",
        Italic("Пример: ООО Ромашка, ИП Иванов"), "\n\n",
        "Для отмены нажмите кнопку ниже"
    )

    # Проверяем, есть ли текст в сообщении
    if callback.message.text:
        await callback.message.edit_text(
            **content.as_kwargs(),
            reply_markup=get_cancel_inline_keyboard()
        )
    else:
        await callback.message.answer(
            **content.as_kwargs(),
            reply_markup=get_cancel_inline_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "menu_extract")
async def callback_extract(callback: CallbackQuery):
    """Выписка из ЕГРЮЛ"""
    user_id = callback.from_user.id
    user_states[user_id] = "extract"

    content = Text(
        Bold("📄 Выписка из ЕГРЮЛ\n\n"),
        "Введите ИНН организации (10 или 12 цифр)\n\n",
        "Для отмены нажмите кнопку ниже"
    )

    if callback.message.text:
        await callback.message.edit_text(
            **content.as_kwargs(),
            reply_markup=get_cancel_inline_keyboard()
        )
    else:
        await callback.message.answer(
            **content.as_kwargs(),
            reply_markup=get_cancel_inline_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "menu_ask")
async def callback_ask(callback: CallbackQuery):
    """Вопрос GigaChat"""
    user_id = callback.from_user.id
    user_states[user_id] = "ask"

    content = Text(
        Bold("💬 Задать вопрос GigaChat\n\n"),
        "Напишите ваш вопрос\n\n",
        "Для отмены нажмите кнопку ниже"
    )

    if callback.message.text:
        await callback.message.edit_text(
            **content.as_kwargs(),
            reply_markup=get_cancel_inline_keyboard()
        )
    else:
        await callback.message.answer(
            **content.as_kwargs(),
            reply_markup=get_cancel_inline_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "menu_doc")
async def callback_doc(callback: CallbackQuery):
    """Составление документа"""
    user_id = callback.from_user.id
    user_states[user_id] = "doc"

    content = Text(
        Bold("✍️ Составить документ\n\n"),
        "Выберите тип документа:"
    )

    if callback.message.text:
        await callback.message.edit_text(
            **content.as_kwargs(),
            reply_markup=get_document_types_keyboard()
        )
    else:
        await callback.message.answer(
            **content.as_kwargs(),
            reply_markup=get_document_types_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "menu_help")
async def callback_help(callback: CallbackQuery):
    """Помощь"""
    content = Text(
        Bold("❓ Помощь\n\n"),
        "Я умею:\n",
        "• 🔍 Находить ИНН по названию\n",
        "• 📄 Получать выписки из ЕГРЮЛ\n",
        "• 💬 Отвечать на вопросы (GigaChat)\n",
        "• ✍️ Составлять документы\n\n",
        "Выберите действие в меню ниже"
    )

    if callback.message.text:
        await callback.message.edit_text(
            **content.as_kwargs(),
            reply_markup=get_main_inline_keyboard()
        )
    else:
        await callback.message.answer(
            **content.as_kwargs(),
            reply_markup=get_main_inline_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "menu_cancel")
async def callback_cancel(callback: CallbackQuery):
    """Отмена действия"""
    user_id = callback.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_data:
        del user_data[user_id]

    content = Text(
        "✅ ",
        Bold("Действие отменено\n\n"),
        "Выберите действие в меню:"
    )

    if callback.message.text:
        await callback.message.edit_text(
            **content.as_kwargs(),
            reply_markup=get_main_inline_keyboard()
        )
    else:
        await callback.message.answer(
            **content.as_kwargs(),
            reply_markup=get_main_inline_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "menu_back")
async def callback_back(callback: CallbackQuery):
    """Назад в главное меню"""
    user_id = callback.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_data:
        del user_data[user_id]

    content = Text(
        "◀️ ",
        Bold("Главное меню\n\n"),
        "Выберите действие:"
    )

    if callback.message.text:
        await callback.message.edit_text(
            **content.as_kwargs(),
            reply_markup=get_main_inline_keyboard()
        )
    else:
        await callback.message.answer(
            **content.as_kwargs(),
            reply_markup=get_main_inline_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data.startswith("doc_"))
async def callback_doc_type(callback: CallbackQuery):
    """Выбор типа документа"""
    user_id = callback.from_user.id
    doc_type = callback.data.split("_")[1]  # application, contract, power, letter

    # Сохраняем тип документа
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]["doc_type"] = doc_type

    # Оставляем состояние doc для дальнейшего ввода
    user_states[user_id] = "doc"

    doc_names = {
        "application": "заявления",
        "contract": "договора",
        "power": "доверенности",
        "letter": "письма"
    }

    content = Text(
        Bold(f"✍️ Составление {doc_names.get(doc_type, 'документа')}\n\n"),
        "Опишите, какой документ вам нужен, и я помогу его составить.\n\n",
        Italic("Например: заявление на отпуск, претензия в магазин, договор аренды, жалоба в налоговую")
    )

    if callback.message.text:
        await callback.message.edit_text(
            **content.as_kwargs(),
            reply_markup=get_cancel_inline_keyboard()
        )
    else:
        await callback.message.answer(
            **content.as_kwargs(),
            reply_markup=get_cancel_inline_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "confirm_yes")
async def callback_confirm_yes(callback: CallbackQuery):
    """Подтверждение действия"""
    if callback.message.text:
        await callback.message.edit_text(
            "✅ Подтверждено",
            reply_markup=get_main_inline_keyboard()
        )
    else:
        await callback.message.answer(
            "✅ Подтверждено",
            reply_markup=get_main_inline_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "confirm_no")
async def callback_confirm_no(callback: CallbackQuery):
    """Отмена действия"""
    user_id = callback.from_user.id
    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_data:
        del user_data[user_id]

    if callback.message.text:
        await callback.message.edit_text(
            "❌ Отменено",
            reply_markup=get_main_inline_keyboard()
        )
    else:
        await callback.message.answer(
            "❌ Отменено",
            reply_markup=get_main_inline_keyboard()
        )
    await callback.answer()