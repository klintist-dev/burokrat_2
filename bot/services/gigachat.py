# bot/services/gigachat.py
import os
from gigachat import GigaChat
from dotenv import load_dotenv
from bot.config_reader import get_config

# Загружаем .env
load_dotenv()


class GigaChatInnAssistant:
    """Специалист только по ИНН и организациям"""

    def __init__(self):
        # Для хранения истории сообщений по каждому пользователю
        self.user_history = {}  # {user_id: [{"user": вопрос, "bot": ответ}, ...]}
        self.max_history = 20    # Сколько последних сообщений запоминать

        # Пробуем разные способы получить ключ
        config = get_config()

        try:
            self.api_key = config.gigachat_api_key.get_secret_value()
            print("🔑 Ключ получен из config")
        except:
            self.api_key = os.getenv("GIGACHAT_API_KEY") or os.getenv("BOT_GIGACHAT_API_KEY")
            print("🔑 Ключ получен из os.getenv")

        self.client = None
        self.available = False

        if self.api_key:
            try:
                self.client = GigaChat(
                    credentials=self.api_key,
                    verify_ssl_certs=False,
                    model="GigaChat",
                    temperature=0.1
                )
                self.available = True
                print("✅ GigaChat (поиск по ИНН) готов к работе!")
            except Exception as e:
                print(f"❌ Ошибка инициализации GigaChat: {e}")
        else:
            print("❌ Ключ GigaChat не найден!")

    async def find_inn_by_name(self, company_name: str) -> str:
        """Ищет ИНН по названию организации"""
        if not self.available:
            return "❌ GigaChat не настроен. Добавьте ключ в .env"

        prompt = f"""Ты — специалист по поиску ИНН организаций.
Найди ИНН организации с названием "{company_name}".
Отвечай ТОЛЬКО ИНН (10 или 12 цифр), без лишних слов.
Если не знаешь — напиши "Не найдено"."""

        try:
            response = self.client.chat(prompt)
            answer = response.choices[0].message.content.strip()

            if answer.isdigit() and len(answer) in (10, 12):
                return f"✅ ИНН организации **{company_name}**: `{answer}`"
            elif "Не найдено" in answer:
                return f"❌ Организация «{company_name}» не найдена"
            else:
                return f"❌ Не удалось найти ИНН. Попробуйте уточнить название."
        except Exception as e:
            return f"❌ Ошибка: {e}"

    async def find_name_by_inn(self, inn: str) -> str:
        """Ищет название организации по ИНН"""
        if not self.available:
            return "❌ GigaChat не настроен"

        if not (inn.isdigit() and len(inn) in (10, 12)):
            return "❌ ИНН должен содержать 10 или 12 цифр"

        prompt = f"""Ты — специалист по поиску организаций по ИНН.
Найди название организации с ИНН {inn}.
Отвечай ТОЛЬКО названием организации, без лишних слов.
Если не знаешь — напиши "Не найдено"."""

        try:
            response = self.client.chat(prompt)
            answer = response.choices[0].message.content.strip()

            if "Не найдено" in answer:
                return f"❌ Организация с ИНН {inn} не найдена"
            elif len(answer) > 3:
                return f"✅ Название:\n\n{answer}"
            else:
                return f"❌ Не удалось найти организацию"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    async def ask_question(self, user_id: int, question: str) -> str:
        """Отвечает на общие вопросы с учётом истории диалога"""
        if not self.available:
            return "❌ GigaChat не настроен"

        # Получаем историю пользователя
        if user_id not in self.user_history:
            self.user_history[user_id] = []

        # Берём последние 5 сообщений из истории
        recent_history = self.user_history[user_id][-self.max_history:]

        # Формируем промпт с учётом истории
        history_text = ""
        if recent_history:
            history_text = "Вот предыдущие сообщения из этого диалога. Учитывай их при ответе:\n\n"
            for msg in recent_history:
                history_text += f"Пользователь: {msg['user']}\n"
                history_text += f"Ты: {msg['bot']}\n"
            history_text += "\n---\n"

        prompt = f"""{history_text}Текущий вопрос пользователя: {question}

        ВАЖНО: Отвечай, учитывая предыдущие сообщения. Если вопрос неполный (например, 'население'), отвечай про то, о чём шла речь ранее (например, про Париж).

        Ответ напиши на русском языке."""

        try:
            response = self.client.chat(prompt)
            answer = response.choices[0].message.content.strip()

            # Сохраняем в историю
            self.user_history[user_id].append({
                "user": question,
                "bot": answer
            })

            # Сохраняем этот диалог в историю
            self.user_history[user_id].append({
                "user": question,
                "bot": answer
            })

            # Обрезаем историю, если слишком длинная
            if len(self.user_history[user_id]) > self.max_history * 2:
                self.user_history[user_id] = self.user_history[user_id][-self.max_history:]

            return f"💬 **Ответ:**\n\n{answer}"
        except Exception as e:
            return f"❌ Ошибка: {e}"

    async def create_document(self, description: str) -> str:
        """Составляет документ по описанию"""
        if not self.available:
            return "❌ GigaChat не настроен"

        prompt = f"""Ты — помощник по составлению документов. На основе описания составь готовый документ.

Описание: {description}

Составь документ в правильном формате, с нужными разделами, датами и подписями. 
Используй официально-деловой стиль."""

        try:
            response = self.client.chat(prompt)
            document = response.choices[0].message.content.strip()
            return f"✍️ **Готовый документ:**\n\n{document}"
        except Exception as e:
            return f"❌ Ошибка: {e}"


gigachat_inn = GigaChatInnAssistant()