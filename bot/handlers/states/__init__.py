# bot/handlers/states/__init__.py
"""Обработчики для различных состояний пользователя"""

from .name import handle_name_step1, handle_name_step2
from .extract import handle_extract
from .goszakupki import handle_goszakupki
from .ask import handle_ask
from .doc import handle_doc

__all__ = [
    'handle_name_step1',
    'handle_name_step2',
    'handle_extract',
    'handle_goszakupki',
    'handle_ask',
    'handle_doc'
]