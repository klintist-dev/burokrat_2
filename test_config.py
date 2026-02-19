# test_config.py
from bot.config_reader import get_config

config = get_config()
print(f"Токен: {config.token}")
print(f"Admin ID: {config.admin_id}")
print(f"Имя бота: {config.bot_name}")