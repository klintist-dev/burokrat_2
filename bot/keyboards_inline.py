"""
Инлайн-клавиатуры для бота
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_main_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Главная инлайн-клавиатура с основными функциями
    """
    builder = InlineKeyboardBuilder()
    
    # Первый ряд: поиск и выписка
    builder.row(
        InlineKeyboardButton(
            text="🔍 Найти ИНН по названию", 
            callback_data="menu_find_inn"
        ),
        InlineKeyboardButton(
            text="📄 Выписка из ЕГРЮЛ", 
            callback_data="menu_extract"
        ),
        width=2
    )
    
    # Второй ряд: GigaChat и документы
    builder.row(
        InlineKeyboardButton(
            text="💬 Задать вопрос GigaChat", 
            callback_data="menu_ask"
        ),
        InlineKeyboardButton(
            text="✍️ Составить документ", 
            callback_data="menu_doc"
        ),
        width=2
    )
    
    # Третий ряд: помощь
    builder.row(
        InlineKeyboardButton(
            text="❓ Помощь", 
            callback_data="menu_help"
        ),
        width=1
    )
    
    return builder.as_markup()

def get_cancel_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой отмены
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="❌ Отмена", 
        callback_data="menu_cancel"
    )
    return builder.as_markup()

def get_back_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с кнопкой назад
    """
    builder = InlineKeyboardBuilder()
    builder.button(
        text="◀️ Назад в меню", 
        callback_data="menu_back"
    )
    return builder.as_markup()

def get_confirm_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с подтверждением
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data="confirm_yes"),
        InlineKeyboardButton(text="❌ Нет", callback_data="confirm_no"),
        width=2
    )
    return builder.as_markup()

def get_document_types_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура с типами документов
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📝 Заявление", callback_data="doc_application"),
        InlineKeyboardButton(text="📋 Договор", callback_data="doc_contract"),
        width=2
    )
    builder.row(
        InlineKeyboardButton(text="📄 Доверенность", callback_data="doc_power"),
        InlineKeyboardButton(text="✉️ Письмо", callback_data="doc_letter"),
        width=2
    )
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu_back"),
        width=1
    )
    return builder.as_markup()
