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
    user_states[user_id] = "find_inn"

    content = Text(
        Bold("🔍 Поиск ИНН по названию\n\n"),
        "Введите название организации (например: ",
        Italic("ООО Ромашка"), ")\n\n",
        "Для отмены нажмите кнопку ниже"
    )

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    await callback.message.edit_text(
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

    content = Text(
        "✅ ",
        Bold("Действие отменено\n\n"),
        "Выберите действие в меню:"
    )

    await callback.message.edit_text(
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

    content = Text(
        "◀️ ",
        Bold("Главное меню\n\n"),
        "Выберите действие:"
    )

    await callback.message.edit_text(
        **content.as_kwargs(),
        reply_markup=get_main_inline_keyboard()
    )
    await callback.answer()