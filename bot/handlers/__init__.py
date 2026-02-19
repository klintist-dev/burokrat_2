# bot/handlers/__init__.py
from aiogram import Router, F  # 👈 Импортируем F
from aiogram.filters import Command

from .start import cmd_start
from .buttons import handle_inn_by_name, handle_name_by_inn, handle_help

router = Router()

# Регистрируем команду /start
router.message.register(cmd_start, Command("start"))

# Регистрируем обработчики кнопок через F.text
router.message.register(handle_inn_by_name, F.text == "🔍 Узнать ИНН по названию")
router.message.register(handle_name_by_inn, F.text == "🏢 Узнать название по ИНН")
router.message.register(handle_help, F.text == "❓ Помощь")

print("🟢 Обработчики зарегистрированы!")