# bot/handlers/__init__.py
from aiogram import Router, F
from aiogram.filters import Command

from .start import cmd_start
from .buttons import (
    handle_inn_by_name,
    handle_extract_by_inn,
    handle_ask,
    handle_doc,
    handle_help,
    handle_user_input
)

from .admin import cmd_stats  # ⬅️ ДОБАВЬ ЭТУ СТРОКУ

router = Router()

# Команда /start
router.message.register(cmd_start, Command("start"))

# Команда /stats (только для админа)
router.message.register(cmd_stats, Command("stats"))  # ⬅️ ДОБАВЬ ЭТУ СТРОКУ

# Кнопки
router.message.register(handle_inn_by_name, F.text == "🔍 Найти ИНН по названию")
router.message.register(handle_extract_by_inn, F.text == "📄 Выписка из ЕГРЮЛ (https://egrul.nalog.ru)")
router.message.register(handle_ask, F.text == "💬 Задать вопрос GigaChat")
router.message.register(handle_doc, F.text == "✍️ Составить документ")
router.message.register(handle_help, F.text == "❓ Помощь")

# Обработчик любого текста (должен быть последним!)
router.message.register(handle_user_input)

print("🟢 Обработчики зарегистрированы!")