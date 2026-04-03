from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Dict


def get_main_inline_keyboard():
    """Главная клавиатура с кнопками"""
    buttons = [
        # Первая строка: поиск ИНН
        [InlineKeyboardButton(text="🔍 Найти ИНН по названию", callback_data="menu_find_inn")],

        # Вторая строка: выписка ФНС
        [InlineKeyboardButton(text="📄 Выписка из ЕГРЮЛ", callback_data="menu_extract")],

        # Третья строка: госзакупки (под выпиской)
        [InlineKeyboardButton(text="🏛 Поиск в госзакупках", callback_data="menu_goszakupki")],

        # Четвёртая строка: GigaChat и документы вместе
        [
            InlineKeyboardButton(text="💬 GigaChat", callback_data="menu_ask"),
            InlineKeyboardButton(text="✍️ Документы", callback_data="menu_doc")
        ],

        # Пятая строка: помощь (в самом низу)
        [InlineKeyboardButton(text="❓ Помощь", callback_data="menu_help")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_cancel_inline_keyboard():
    """Клавиатура с кнопкой отмены"""
    buttons = [
        [InlineKeyboardButton(text="❌ Отмена", callback_data="menu_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_inline_keyboard():
    """Клавиатура с кнопкой назад"""
    buttons = [
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_document_types_keyboard():
    """Клавиатура выбора типа документа"""
    buttons = [
        [InlineKeyboardButton(text="📝 Заявление", callback_data="doc_application")],
        [InlineKeyboardButton(text="📄 Договор", callback_data="doc_contract")],
        [InlineKeyboardButton(text="📋 Доверенность", callback_data="doc_power")],
        [InlineKeyboardButton(text="✉️ Письмо", callback_data="doc_letter")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="menu_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pagination_keyboard(current_page: int, total_pages: int, prefix: str = "page"):
    """Клавиатура для пагинации"""
    buttons = []

    # Кнопка "Назад"
    if current_page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"{prefix}_page_{current_page - 1}"
            )
        )

    # Текущая страница
    buttons.append(
        InlineKeyboardButton(
            text=f"{current_page}/{total_pages}",
            callback_data="noop"
        )
    )

    # Кнопка "Вперед"
    if current_page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="Вперед ▶️",
                callback_data=f"{prefix}_page_{current_page + 1}"
            )
        )

    # Собираем кнопки в строку
    keyboard = [buttons]

    # Кнопка "В главное меню"
    keyboard.append([
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="menu_back")
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_contract_details_keyboard(contract_url: str, index: int):
    """Клавиатура для просмотра деталей контракта"""
    buttons = [
        [InlineKeyboardButton(
            text=f"📄 Подробнее о контракте",
            callback_data=f"contract_details_{index}"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_documents_keyboard(documents: List[Dict], contract_index: int, current_tab: str = "all"):
    """Упрощённая клавиатура с кнопками вкладок"""
    buttons = []

    if not documents:
        buttons.append([
            InlineKeyboardButton(
                text="📭 Нет документов",
                callback_data="noop"
            )
        ])
    else:
        # Группируем по вкладкам
        docs_by_tab = {}
        for doc in documents:
            tab = doc.get('source_tab', 'Другие')
            if tab not in docs_by_tab:
                docs_by_tab[tab] = []
            docs_by_tab[tab].append(doc)

        # Сортируем вкладки
        tab_order = ['Вложения', 'Исполнение', 'Платежи', 'Другие']
        tab_buttons = []

        for tab in tab_order:
            if tab in docs_by_tab and docs_by_tab[tab]:
                count = len(docs_by_tab[tab])
                tab_buttons.append(
                    InlineKeyboardButton(
                        text=f"📁 {tab} ({count})",
                        callback_data=f"tab_{contract_index}_{tab}"
                    )
                )

        # Добавляем кнопки вкладок по 2 в ряд
        for i in range(0, len(tab_buttons), 2):
            buttons.append(tab_buttons[i:i + 2])

    # Кнопка возврата к деталям
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад к деталям",
            callback_data="back_to_contract_details"
        )
    ])

    # 🔥 НОВАЯ КНОПКА: Главное меню
    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="menu_back"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_contracts_keyboard():
    """Простая клавиатура для возврата к списку"""
    buttons = [
        [InlineKeyboardButton(
            text="◀️ Назад к списку контрактов",
            callback_data="back_to_contracts"
        )],
        [InlineKeyboardButton(  # 🔥 Добавляем главное меню
            text="🏠 Главное меню",
            callback_data="menu_back"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_contract_details_keyboard():
    """Клавиатура для возврата к деталям контракта"""
    buttons = [
        [InlineKeyboardButton(
            text="◀️ Назад к деталям контракта",
            callback_data="back_to_contract_details"
        )],
        [InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="menu_back"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_document_link_keyboard(doc_url: str):
    """Клавиатура с кнопкой копирования ссылки"""
    buttons = [
        [InlineKeyboardButton(
            text="🔗 Открыть ссылку",
            url=doc_url
        )],
        [InlineKeyboardButton(
            text="📋 Копировать ссылку",
            callback_data=f"copy_link_{doc_url[:50]}"
        )],
        [InlineKeyboardButton(
            text="◀️ Назад к документам",
            callback_data="back_to_contract_details"
        )],
        [InlineKeyboardButton(  # 🔥 Добавить эту кнопку
            text="🏠 Главное меню",
            callback_data="menu_back"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_document_navigation_keyboard(contract_index: int, tab_name: str, total_docs: int):
    """Клавиатура для навигации по документам"""
    buttons = []

    # Кнопки для первых 5 документов
    row = []
    for i in range(1, min(6, total_docs + 1)):
        row.append(
            InlineKeyboardButton(
                text=str(i),
                callback_data=f"doc_{contract_index}_{tab_name}_{i}"
            )
        )
    if row:
        buttons.append(row)

    # Кнопки для следующих 5 (если есть)
    if total_docs > 5:
        row = []
        for i in range(6, min(11, total_docs + 1)):
            row.append(
                InlineKeyboardButton(
                    text=str(i),
                    callback_data=f"doc_{contract_index}_{tab_name}_{i}"
                )
            )
        if row:
            buttons.append(row)

    # Кнопки навигации
    buttons.append([
        InlineKeyboardButton(
            text="◀️ Назад к вкладкам",
            callback_data="back_to_tabs"
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="menu_back"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_to_tabs_keyboard(contract_index: int):
    """Клавиатура для возврата к вкладкам"""
    buttons = [
        [InlineKeyboardButton(
            text="◀️ Назад к списку вкладок",
            callback_data=f"back_to_tabs_{contract_index}"
        )],
        [InlineKeyboardButton(
            text="🏠 Главное меню",
            callback_data="menu_back"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_export_keyboard():
    """Клавиатура для выбора формата экспорта"""
    buttons = [
        [
            InlineKeyboardButton(text="📊 Excel", callback_data="export_excel"),
            InlineKeyboardButton(text="📄 CSV", callback_data="export_csv")
        ],
        [
            InlineKeyboardButton(text="📑 TXT (детали)", callback_data="export_txt"),
            InlineKeyboardButton(text="📋 Все форматы", callback_data="export_all")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_back")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_contract_export_keyboard(contract_index: int):
    """Клавиатура для экспорта конкретного контракта"""
    buttons = [
        [InlineKeyboardButton(
            text="📑 Экспорт деталей (TXT)",
            callback_data=f"export_contract_txt_{contract_index}"
        )],
        [InlineKeyboardButton(
            text="📊 Экспорт всех контрактов",
            callback_data="export_all_contracts"
        )],
        [InlineKeyboardButton(
            text="◀️ Назад к деталям",
            callback_data="back_to_contract_details"
        )]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def add_export_button_to_contracts_keyboard(keyboard: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    """Добавляет кнопку экспорта к существующей клавиатуре контрактов"""
    # Добавляем кнопку экспорта в конец
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="📊 Экспорт данных", callback_data="show_export_menu")
    ])
    return keyboard


# ==================== НОВЫЕ КЛАВИАТУРЫ ДЛЯ ПОИСКА КОНТРАКТОВ ====================

def get_search_type_keyboard():
    """Клавиатура выбора типа поиска (Поставщик / Заказчик)"""
    buttons = [
        [
            InlineKeyboardButton(text="📦 Поставщик", callback_data="search_supplier"),
            InlineKeyboardButton(text="🏛 Заказчик", callback_data="search_customer")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="search_cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_repeat_search_keyboard():
    """Клавиатура для повторного поиска (после завершения)"""
    buttons = [
        [
            InlineKeyboardButton(text="🔍 Новый поиск", callback_data="new_search"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


