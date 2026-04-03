# bot/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==================== REPLY KEYBOARD (Главное меню) ====================

# Кнопки с эмодзи и описанием
button_inn_by_name = KeyboardButton(text="🔍 Найти ИНН по названию")
button_extract = KeyboardButton(text="📄 Выписка из ЕГРЮЛ (https://egrul.nalog.ru)")
button_contracts = KeyboardButton(text="🔍 Поиск контрактов")  # ← НОВАЯ КНОПКА
button_ask = KeyboardButton(text="💬 Задать вопрос GigaChat")
button_doc = KeyboardButton(text="✍️ Составить документ")
button_help = KeyboardButton(text="❓ Помощь")

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [button_inn_by_name],
        [button_extract],
        [button_contracts],  # ← НОВАЯ КНОПКА
        [button_ask],
        [button_doc],
        [button_help]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие..."
)

# ==================== INLINE KEYBOARD (Выбор типа поиска) ====================

# Клавиатура выбора типа поиска (Поставщик / Заказчик)
search_type_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="📦 Поставщик", callback_data="search_supplier"),
        InlineKeyboardButton(text="🏛 Заказчик", callback_data="search_customer")
    ],
    [
        InlineKeyboardButton(text="❌ Отмена", callback_data="search_cancel")
    ]
])

# Клавиатура для повторного поиска (после завершения поиска)
repeat_search_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="🔍 Новый поиск", callback_data="new_search"),
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    ]
])