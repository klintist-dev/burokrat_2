# bot/handlers/__init__.py
from aiogram import Router, F
from aiogram.filters import Command

from .start import cmd_start
from .buttons import (
    handle_inn_by_name,
    handle_name_by_inn,
    handle_ask,        # 👈 НОВОЕ
    handle_doc,        # 👈 НОВОЕ
    handle_help,
    handle_user_input
)

router = Router()

# Регистрируем команду /start
router.message.register(cmd_start, Command("start"))

# Регистрируем обработчики кнопок через F.text
router.message.register(handle_inn_by_name, F.text == "🔍 Узнать ИНН по названию")
router.message.register(handle_name_by_inn, F.text == "🏢 Узнать название по ИНН")
router.message.register(handle_ask, F.text == "💬 Задать вопрос GigaChat")      # 👈 НОВОЕ
router.message.register(handle_doc, F.text == "✍️ Составить документ")           # 👈 НОВОЕ
router.message.register(handle_help, F.text == "❓ Помощь")
router.message.register(handle_user_input)

print("🟢 Обработчики зарегистрированы!")