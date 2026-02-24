# bot/parsers/__init__.py
from .nalog_parser import (
    find_inn_by_name,
    find_name_by_inn,
    get_egrul_extract,
    find_inn_by_passport,
    check_inn_valid,
    get_invalid_inn_list
)

__all__ = [
    'find_inn_by_name',
    'find_name_by_inn',
    'get_egrul_extract',
    'find_inn_by_passport',
    'check_inn_valid',
    'get_invalid_inn_list'
]