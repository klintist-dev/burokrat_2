"""
Инлайн-клавиатуры для бота
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_main_inline_keyboard() -> InlineKeyboardMarkup:
    """
    Главная инлайн-клавиатура с основными функциями (адаптировано для мобильных)
    Каждая кнопка на отдельной строке для лучшей читаемости
    """
    builder = InlineKeyboardBuilder()

    # Первая строка: поиск ИНН
    builder.row(
        InlineKeyboardButton(
            text="🔍 Поиск ИНН",
            callback_data="menu_find_inn"
        ),
        width=1
    )

    # Вторая строка: выписка ФНС
    builder.row(
        InlineKeyboardButton(
            text="📄 Выписка ФНС",
            callback_data="menu_extract"
        ),
        width=1
    )

    # Третья строка: госзакупки
    builder.row(
        InlineKeyboardButton(
            text="🏛 Госзакупки",
            callback_data="menu_goszakupki"
        ),
        width=1
    )

    # Четвёртая строка: GigaChat и документы (вместе)
    builder.row(
        InlineKeyboardButton(
            text="💬 GigaChat",
            callback_data="menu_ask"
        ),
        InlineKeyboardButton(
            text="✍️ Документ",
            callback_data="menu_doc"
        ),
        width=2
    )

    # Пятая строка: помощь
    builder.row(
        InlineKeyboardButton(
            text="❓ Помощь",
            callback_data="menu_help"
        ),
        width=1
    )

    return builder.as_markup()


def get_cancel_inline_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура с кнопкой отмены"""
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
    Клавиатура с типами документов (адаптировано для мобильных)
    """
    builder = InlineKeyboardBuilder()

    # Два ряда по две кнопки
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

    # Кнопка назад на всю ширину
    builder.row(
        InlineKeyboardButton(text="◀️ Назад", callback_data="menu_back"),
        width=1
    )

    return builder.as_markup()


def get_pagination_keyboard(current_page: int, total_pages: int, data_type: str) -> InlineKeyboardMarkup:
    """
    Создаёт клавиатуру для пагинации

    Args:
        current_page: текущая страница
        total_pages: всего страниц
        data_type: тип данных (goszakupki, extract_history и т.д.)
    """
    builder = InlineKeyboardBuilder()

    # Кнопки навигации
    buttons = []

    # Кнопка "Назад" (если не первая страница)
    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"{data_type}_page_{current_page - 1}"
            )
        )

    # Информационная кнопка с номером страницы
    buttons.append(
        InlineKeyboardButton(
            text=f"📄 {current_page}/{total_pages}",
            callback_data="noop"
        )
    )

    # Кнопка "Вперёд" (если не последняя страница)
    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="Вперёд ▶️",
                callback_data=f"{data_type}_page_{current_page + 1}"
            )
        )

    # Добавляем кнопки в ряд (3 кнопки или меньше)
    builder.row(*buttons, width=len(buttons))

    # Кнопка "В главное меню"
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_back"),
        width=1
    )

    return builder.as_markup()


def get_noop_keyboard() -> InlineKeyboardMarkup:
    """Заглушка для неактивных кнопок"""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="◀️ Вернуться в меню",
        callback_data="menu_back"
    )
    return builder.as_markup()


def get_simple_pagination_keyboard(current_page: int, total_pages: int, data_type: str) -> InlineKeyboardMarkup:
    """
    Упрощённая клавиатура для пагинации (только вперёд/назад)

    Args:
        current_page: текущая страница
        total_pages: всего страниц
        data_type: тип данных
    """
    builder = InlineKeyboardBuilder()

    # Если есть предыдущая страница
    if current_page > 1:
        builder.button(
            text="◀️ Предыдущая",
            callback_data=f"{data_type}_page_{current_page - 1}"
        )

    # Если есть следующая страница
    if current_page < total_pages:
        builder.button(
            text="Следующая ▶️",
            callback_data=f"{data_type}_page_{current_page + 1}"
        )

    # Выравниваем кнопки в ряд
    if len(builder.buttons) > 0:
        builder.adjust(len(builder.buttons))

    # Кнопка "В главное меню"
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_back"),
        width=1
    )

    return builder.as_markup()


def get_results_navigation_keyboard(current_page: int, total_pages: int, data_type: str) -> InlineKeyboardMarkup:
    """
    Клавиатура для навигации по результатам поиска

    Args:
        current_page: текущая страница
        total_pages: всего страниц
        data_type: тип данных
    """
    builder = InlineKeyboardBuilder()

    # Верхний ряд: навигация по страницам
    nav_buttons = []

    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="◀️",
                callback_data=f"{data_type}_page_{current_page - 1}"
            )
        )

    nav_buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="noop"
        )
    )

    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="▶️",
                callback_data=f"{data_type}_page_{current_page + 1}"
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons, width=len(nav_buttons))

    # Нижний ряд: действия
    builder.row(
        InlineKeyboardButton(text="🏠 Меню", callback_data="menu_back"),
        InlineKeyboardButton(text="🔄 Новый поиск", callback_data="menu_goszakupki"),
        width=2
    )

    return builder.as_markup()