# scripts/analyze_searches.py
import json
import glob
from collections import Counter
from datetime import datetime


def analyze_searches():
    """Анализирует сохранённые поисковые запросы"""
    files = glob.glob("data/search_*.json")

    if not files:
        print("❌ Нет файлов для анализа")
        return

    total_searches = len(files)
    total_orgs = 0
    exact_matches = 0
    regions = Counter()
    queries = []

    print(f"📊 Найдено {total_searches} поисковых запросов\n")
    print("=" * 50)

    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            total_orgs += data.get('total', 0)

            # Считаем точные совпадения
            if data.get('best_match') and data['best_match'].get('match_details', {}).get('exact'):
                exact_matches += 1

            # Собираем регионы
            region = data.get('region')
            regions[region if region else 'вся Россия'] += 1

            # Сохраняем запросы
            queries.append({
                'query': data.get('query', ''),
                'best_match': data.get('best_match', {}).get('name', 'Не найдено')
            })

        except Exception as e:
            print(f"Ошибка при чтении {file}: {e}")

    # Выводим статистику
    print(f"📈 **Общая статистика:**")
    print(f"   Всего поисков: {total_searches}")
    print(f"   Всего организаций найдено: {total_orgs}")
    print(f"   Точных совпадений: {exact_matches}")
    if total_searches > 0:
        print(f"   Процент точных совпадений: {exact_matches / total_searches * 100:.1f}%\n")

    print("📍 **Популярные регионы:**")
    for region, count in regions.most_common(5):
        print(f"   {region}: {count} запросов")

    print("\n🔍 **Примеры запросов:**")
    for q in queries[:5]:
        print(f"   • Запрос: '{q['query']}'")
        print(f"     → Найдено: {q['best_match'][:50]}...")
        print()


if __name__ == "__main__":
    analyze_searches()