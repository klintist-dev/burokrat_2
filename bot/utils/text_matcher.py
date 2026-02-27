# bot/utils/text_matcher.py
import re
from difflib import SequenceMatcher
from typing import List, Dict, Optional


class TextMatcher:
    """Класс для умного сравнения текста"""

    @staticmethod
    def normalize(text: str) -> str:
        """
        Нормализует текст для сравнения
        """
        if not text:
            return ""

        # Приводим к нижнему регистру
        text = text.lower()

        # Заменяем ё на е
        text = text.replace('ё', 'е')

        # Убираем кавычки и спецсимволы
        text = re.sub(r'["\'«»„“*.,!?;:()\[\]{}]', '', text)

        # Убираем лишние пробелы
        text = ' '.join(text.split())

        return text.strip()

    @staticmethod
    def calculate_relevance(query: str, name: str) -> float:
        """
        Рассчитывает релевантность названия запросу
        Возвращает число от 0 до 1
        """
        norm_query = TextMatcher.normalize(query)
        norm_name = TextMatcher.normalize(name)

        # Разбиваем на слова
        query_words = set(norm_query.split())
        name_words = set(norm_name.split())

        if not query_words:
            return 0.0

        # Считаем, сколько слов из запроса есть в названии
        matched_words = query_words.intersection(name_words)

        # Веса для разных типов совпадений
        score = 0.0

        # 1. Главное: процент совпавших слов (0-1)
        word_match_ratio = len(matched_words) / len(query_words)
        score += word_match_ratio * 0.7  # 70% веса

        # 2. Дополнительно: точное совпадение фразы
        if norm_query in norm_name:
            score += 0.2  # +20% если фраза целиком есть в названии

        # 3. Дополнительно: порядок слов
        # Проверяем, идут ли слова в том же порядке
        query_list = norm_query.split()
        name_list = norm_name.split()

        # Ищем последовательность слов из запроса в названии
        matches = 0
        for i in range(len(name_list) - len(query_list) + 1):
            if name_list[i:i + len(query_list)] == query_list:
                matches += 1

        if matches > 0:
            score += 0.1  # +10% за сохранение порядка

        return min(score, 1.0)  # Не больше 1

    @staticmethod
    def rank_candidates(query: str, candidates: List[Dict], threshold: float = 0.1) -> List[Dict]:
        """
        Ранжирует кандидатов по релевантности
        """
        print(f"\n🔍 РАНЖИРОВАНИЕ для запроса: '{query}'")

        norm_query = TextMatcher.normalize(query)
        print(f"   Нормализованный запрос: '{norm_query}'")

        ranked = []

        for candidate in candidates:
            name = candidate.get('name', '')

            # Рассчитываем релевантность
            relevance = TextMatcher.calculate_relevance(query, name)

            # Для отладки
            norm_name = TextMatcher.normalize(name)
            query_words = set(norm_query.split())
            name_words = set(norm_name.split())
            matched_words = query_words.intersection(name_words)

            print(f"\n   Кандидат {candidate.get('inn')}:")
            print(f"      релевантность: {relevance:.3f}")
            print(f"      совпало слов: {len(matched_words)}/{len(query_words)}")
            print(f"      слова: {sorted(matched_words)}")

            if relevance >= threshold:
                candidate_copy = candidate.copy()
                candidate_copy['relevance'] = relevance
                candidate_copy['similarity'] = int(relevance * 100)  # для совместимости
                candidate_copy['matched_words'] = list(matched_words)
                ranked.append(candidate_copy)

        # Сортируем по релевантности
        ranked.sort(key=lambda x: x['relevance'], reverse=True)

        print(f"\n🏆 ТОП РЕЗУЛЬТАТОВ:")
        for i, org in enumerate(ranked[:5], 1):
            print(f"   {i}. {org['relevance']:.1%} - {org['inn']}")

        return ranked