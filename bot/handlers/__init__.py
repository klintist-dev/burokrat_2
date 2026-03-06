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
from .analysis import cmd_analysis

from . import start, buttons, webapp


router = Router()

router.include_router(start.router)
router.include_router(webapp.router)

# Команда /start
router.message.register(cmd_start, Command("start"))

# Команда /stats (только для админа)
router.message.register(cmd_stats, Command("stats"))  # ⬅️ ДОБАВЬ ЭТУ СТРОКУ

# Команда /analysis
router.message.register(cmd_analysis, Command("analysis"))

# Кнопки
router.message.register(handle_inn_by_name, F.text == "🔍 Найти ИНН по названию")
router.message.register(handle_extract_by_inn, F.text == "📄 Выписка из ЕГРЮЛ (https://egrul.nalog.ru)")
router.message.register(handle_ask, F.text == "💬 Задать вопрос GigaChat")
router.message.register(handle_doc, F.text == "✍️ Составить документ")
router.message.register(handle_help, F.text == "❓ Помощь")
router.message.register(webapp.handle_webapp, F.text == "🌐 Умный поиск (Mini App)")

# Обработчик любого текста (должен быть последним!)
router.message.register(handle_user_input)

print("🟢 Обработчики зарегистрированы!")