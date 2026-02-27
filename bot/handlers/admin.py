# bot/handlers/admin.py
from aiogram.types import Message
from aiogram.filters import Command
from bot.config_reader import get_config
from bot.services.statistics import stats


async def cmd_stats(message: Message):
    """Команда /stats - показывает статистику (только для админа)"""
    config = get_config()

    # Проверяем, что это админ
    if message.from_user.id != config.admin_id:
        await message.answer("❌ Эта команда только для администратора")
        return

    stats_text = stats.get_stats_text()
    await message.answer(stats_text, parse_mode="Markdown")