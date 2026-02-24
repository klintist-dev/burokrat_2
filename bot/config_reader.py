# bot/config_reader.py
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from functools import lru_cache


class BotConfig(BaseSettings):
    token: SecretStr  # Токен бота (секрет!)
    admin_id: int  # Твой Telegram ID
    bot_name: str = "БюрократЪ 2.0"  # Имя бота (можно поменять)
    debug: bool = False
    gigachat_api_key: SecretStr

    class Config:
        env_file = ".env"  # Где лежат секреты
        env_prefix = "BOT_"  # Все переменные начинаются с BOT_
        env_file_encoding = "utf-8"


@lru_cache
def get_config() -> BotConfig:
    """Возвращает конфиг (кэшируется)"""
    return BotConfig()