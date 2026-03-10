#!/usr/bin/env python3
"""
Скрипт для запуска API сервера
"""

from bot.api.server import run_server

if __name__ == '__main__':
    # Запускаем API сервер на порту 8080 (свободный порт)
    run_server(host='0.0.0.0', port=8080, debug=True)