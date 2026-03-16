# bot/utils/validators.py
'''Функции для валидации'''

def is_valid_inn(inn: str) -> bool:
    '''Проверяет, вляется ли строка валидным ИНН'''
    return inn.isdigit() and len(inn) in (10, 12)

def is_skip_region(text: str) -> bool:
    '''Проверяет, нужно ли пропустить выбор региона'''
    return text in ['-', 'любой', 'пропустить', 'нет']