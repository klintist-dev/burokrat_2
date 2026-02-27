from .nalog_parser import (
    find_inn_by_name,
    find_name_by_inn,
    find_inn_by_name_with_region,  # 👈 НОВАЯ ФУНКЦИЯ
    get_egrul_extract,
    find_inn_by_passport,
    check_inn_valid,
    get_invalid_inn_list,
    find_inn_by_name_structured
)

__all__ = [
    'find_inn_by_name',
    'find_name_by_inn',
    'find_inn_by_name_with_region',  # 👈 ДОБАВЬ СЮДА
    'get_egrul_extract',
    'find_inn_by_passport',
    'check_inn_valid',
    'get_invalid_inn_list',
    'find_inn_by_name_structured'
]