# bot/keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# Создаём кнопки
button_inn_by_name = KeyboardButton(text="🔍 Узнать ИНН по названию")
button_name_by_inn = KeyboardButton(text="🏢 Узнать название по ИНН")
button_ask = KeyboardButton(text="💬 Задать вопрос GigaChat")
button_doc = KeyboardButton(text="✍️ Составить документ")
button_help = KeyboardButton(text="❓ Помощь")

# Собираем клавиатуру
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [button_inn_by_name],
        [button_name_by_inn],
        [button_ask],
        [button_doc],
        [button_help]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие..."
)