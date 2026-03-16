import logging
from bot.parsers.gos_zakupki_parser import GosZakupkiParser

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("🚀 Тестируем парсер госзакупок на СЕРВЕРЕ...")
    
    parser = GosZakupkiParser()
    inn = "472100471235"
    
    result = parser.search_by_supplier_inn(inn)
    
    print(f"\n{'='*60}")
    print(f"РЕЗУЛЬТАТ:")
    print(f"  Успех: {result.get('success')}")
    print(f"  ИНН: {result.get('inn')}")
    print(f"  Найдено контрактов: {result.get('total', 0)}")
    
    if result.get('error'):
        print(f"  Ошибка: {result.get('error')}")
    
    print(f"{'='*60}\n")
    
    if result.get('success') and result.get('contracts'):
        print(f"📋 Первые 3 контракта:")
        for i, contract in enumerate(result['contracts'][:3], 1):
            print(f"\n{i}. {contract['number']}")
            print(f"   Статус: {contract['status']}")
            print(f"   Цена: {contract['price']}")
            print(f"   Заказчик: {contract['customer'][:70]}...")

if __name__ == "__main__":
    main()
