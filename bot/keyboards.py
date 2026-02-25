# bot/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Кнопки с эмодзи и описанием
button_inn_by_name = KeyboardButton(text="🔍 Найти ИНН по названию")
button_extract = KeyboardButton(text="📄 Выписка из ЕГРЮЛ (https://egrul.nalog.ru)")
button_ask = KeyboardButton(text="💬 Задать вопрос GigaChat")
button_doc = KeyboardButton(text="✍️ Составить документ")
button_help = KeyboardButton(text="❓ Помощь")

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [button_inn_by_name, button_extract],
        [button_ask, button_doc],
        [button_help]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие..."
)