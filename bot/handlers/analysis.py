# bot/handlers/analysis.py
from aiogram.types import Message
from aiogram.filters import Command
from bot.config_reader import get_config
import glob
import json
import os


async def cmd_analysis(message: Message):
    """Команда /analysis - показывает анализ поисковых запросов (только для админа)"""
    config = get_config()

    # Проверяем, что это админ
    if message.from_user.id != config.admin_id:
        await message.answer("❌ Эта команда только для администратора")
        return

    files = glob.glob("data/search_*.json")

    if not files:
        await message.answer("❌ Нет данных для анализа")
        return

    total = len(files)
    exact = 0

    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('best_match') and data['best_match'].get('match_details', {}).get('exact'):
                exact += 1
        except:
            pass

    response = (
        f"📊 **Анализ поисковых запросов**\n\n"
        f"📁 Всего запросов: {total}\n"
        f"✅ Точных совпадений: {exact}\n"
        f"📈 Точность: {exact / total * 100:.1f}%\n\n"
        f"Файлы сохранены в папке data/"
    )

    await message.answer(response, parse_mode="Markdown")