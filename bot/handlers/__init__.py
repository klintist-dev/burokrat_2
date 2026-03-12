from aiogram import Router, F  # добавь Router сюда
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
from .admin import cmd_stats
from .analysis import cmd_analysis
from . import start, buttons, callbacks  # добавь callbacks
# from . import webapp  # закомментировано

router = Router()

# Подключаем роутеры
router.include_router(start.router)
router.include_router(callbacks.router)  # добавь эту строку
# router.include_router(webapp.router)  # закомментировано

# Команда /start
router.message.register(cmd_start, Command("start"))

# Команда /stats (только для админа)
router.message.register(cmd_stats, Command("stats"))

# Команда /analysis
router.message.register(cmd_analysis, Command("analysis"))

# Кнопки
router.message.register(handle_inn_by_name, F.text == "🔍 Найти ИНН по названию")
router.message.register(handle_extract_by_inn, F.text == "📄 Выписка из ЕГРЮЛ (https://egrul.nalog.ru)")
router.message.register(handle_ask, F.text == "💬 Задать вопрос GigaChat")
router.message.register(handle_doc, F.text == "✍️ Составить документ")
router.message.register(handle_help, F.text == "❓ Помощь")

# Обработчик любого текста (должен быть последним!)
router.message.register(handle_user_input)

print("🟢 Обработчики зарегистрированы!")