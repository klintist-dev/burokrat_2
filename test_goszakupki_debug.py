#!/usr/bin/env python3
"""
Тестовый скрипт для отладки госзакупок
"""

import logging
import sys
import json
from bot.parsers.gos_zakupki_debug import GosZakupkiDebugParser

# Настраиваем подробное логирование
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('goszakupki_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def main():
    """Основная функция тестирования"""
    
    # ИНН для теста
    inn = "472100471235"
    
    print("=" * 60)
    print(f"🔍 ТЕСТИРОВАНИЕ ГОСЗАКУПОК ДЛЯ ИНН: {inn}")
    print("=" * 60)
    
    # Создаём парсер
    parser = GosZakupkiDebugParser(debug=True)
    
    # Выполняем поиск
    result = parser.search_by_supplier_inn(inn)
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТ:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print("=" * 60)
    
    # Сохраняем лог
    parser.save_log('goszakupki_debug_log.json')
    
    print("\n✅ Тест завершён!")
    print("📁 Созданы файлы:")
    print("   - goszakupki_debug.log (лог выполнения)")
    print("   - goszakupki_debug_log.json (детальный лог запросов)")
    print(f"   - goszakupki_result_{inn}.html (HTML страницы, если успешно)")

if __name__ == "__main__":
    main()
