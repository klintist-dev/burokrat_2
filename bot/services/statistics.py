# bot/services/statistics.py
import json
import os
from datetime import datetime
from collections import defaultdict

STATS_FILE = "data/statistics.json"


class Statistics:
    def __init__(self):
        self.stats = self.load_stats()

    def load_stats(self):
        """Загружает статистику из файла"""
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.create_empty_stats()
        return self.create_empty_stats()

    def create_empty_stats(self):
        """Создаёт пустую структуру статистики"""
        return {
            "users": {},
            # {user_id: {"first_seen": "дата", "last_seen": "дата", "username": "...", "first_name": "..."}}
            "commands": {},  # {command_name: count}
            "daily": {},  # {date: {command: count}}
            "total_users": 0,
            "total_commands": 0
        }

    def save_stats(self):
        """Сохраняет статистику в файл"""
        # Создаём папку data если её нет
        os.makedirs("data", exist_ok=True)

        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)

    def log_user(self, user_id: int, username: str = None, first_name: str = None):
        """Логирует пользователя"""
        today = datetime.now().strftime("%Y-%m-%d")
        user_id_str = str(user_id)

        if user_id_str not in self.stats["users"]:
            # Новый пользователь
            self.stats["users"][user_id_str] = {
                "first_seen": today,
                "last_seen": today,
                "username": username,
                "first_name": first_name
            }
            self.stats["total_users"] += 1
        else:
            # Существующий пользователь
            self.stats["users"][user_id_str]["last_seen"] = today
            if username:
                self.stats["users"][user_id_str]["username"] = username
            if first_name:
                self.stats["users"][user_id_str]["first_name"] = first_name

        self.save_stats()

    def log_command(self, user_id: int, command: str):
        """Логирует использование команды"""
        today = datetime.now().strftime("%Y-%m-%d")

        # Увеличиваем счётчик команды
        if command in self.stats["commands"]:
            self.stats["commands"][command] += 1
        else:
            self.stats["commands"][command] = 1

        # Логируем по дням
        if today not in self.stats["daily"]:
            self.stats["daily"][today] = {}

        if command in self.stats["daily"][today]:
            self.stats["daily"][today][command] += 1
        else:
            self.stats["daily"][today][command] = 1

        self.stats["total_commands"] += 1
        self.save_stats()

    def get_stats_text(self) -> str:
        """Возвращает красивый текст статистики"""
        text = "📊 **Статистика бота**\n\n"
        text += f"👥 **Всего пользователей:** {self.stats['total_users']}\n"
        text += f"📝 **Всего команд:** {self.stats['total_commands']}\n\n"

        text += "**Последние 10 пользователей:**\n"
        # Сортируем по last_seen (последние сверху)
        sorted_users = sorted(
            self.stats["users"].items(),
            key=lambda x: x[1]["last_seen"],
            reverse=True
        )[:10]

        for user_id, data in sorted_users:
            name = data.get("first_name") or data.get("username") or "Без имени"
            text += f"• {name} (ID: {user_id}) — последний раз: {data['last_seen']}\n"

        text += "\n**Популярные команды:**\n"
        sorted_commands = sorted(
            self.stats["commands"].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        for cmd, count in sorted_commands:
            # Преобразуем имена команд в читаемый вид
            cmd_names = {
                "ask": "💬 Вопросы",
                "doc": "✍️ Документы",
                "extract": "📄 Выписки",
                "inn_search": "🔍 Поиск ИНН",
                "help": "❓ Помощь"
            }
            cmd_display = cmd_names.get(cmd, cmd)
            text += f"• {cmd_display}: {count} раз\n"

        return text


# Создаём глобальный объект статистики
stats = Statistics()