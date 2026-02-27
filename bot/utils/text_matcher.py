# bot/utils/text_matcher.py
import re
from difflib import SequenceMatcher
import json
from typing import List, Dict, Optional


class TextMatcher:
    """Класс для умного сравнения текста"""

    @staticmethod
    def normalize(text: str) -> str:
        """
        Нормализует текст (убирает лишнее, приводит к общему виду)
        """
        if not text:
            return ""

        # Приводим к нижнему регистру
        text = text.lower()

        # Убираем кавычки разных типов
        text = re.sub(r'["\'«»]', '', text)

        # Убираем лишние пробелы
        text = ' '.join(text.split())

        # Убираем организационно-правовые формы (ООО, ЗАО, ИП и т.д.)
        text = re.sub(
            r'\b(ооо|зао|оао|пао|ао|ип|ooo|oooо|оооо|общество|с ограниченной ответственностью|закрытое акционерное|открытое акционерное|публичное акционерное)\b',
            '', text, flags=re.IGNORECASE)

        # Убираем слова "компания", "фирма", "корпорация" и т.д.
        text = re.sub(r'\b(компания|фирма|корпорация|холдинг|группа|предприятие|организация)\b', '', text,
                      flags=re.IGNORECASE)

        return text.strip()

    @staticmethod
    def similarity(a: str, b: str) -> float:
        """
        Возвращает коэффициент похожести двух строк (0-1)
        """
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    @staticmethod
    def is_exact_match(query: str, name: str) -> bool:
        """
        Проверяет точное совпадение (с учётом нормализации)
        """
        norm_query = TextMatcher.normalize(query)
        norm_name = TextMatcher.normalize(name)
        return norm_query == norm_name

    @staticmethod
    def contains_all_words(query: str, name: str) -> bool:
        """
        Проверяет, содержит ли название все слова из запроса
        """
        query_words = set(TextMatcher.normalize(query).split())
        name_words = set(TextMatcher.normalize(name).split())

        # Если запрос пустой, считаем что содержит
        if not query_words:
            return True

        return query_words.issubset(name_words)

    @staticmethod
    def word_coverage(query: str, name: str) -> float:
        """
        Возвращает долю слов из запроса, которые есть в названии
        """
        query_words = set(TextMatcher.normalize(query).split())
        name_words = set(TextMatcher.normalize(name).split())

        if not query_words:
            return 1.0

        matched_words = query_words.intersection(name_words)
        return len(matched_words) / len(query_words)

    @staticmethod
    def get_best_match(query: str, candidates: List[Dict], threshold: float = 0.5) -> Optional[Dict]:
        """
        Находит лучшее совпадение среди кандидатов
        """
        if not candidates:
            return None

        best_match = None
        best_score = 0
        best_details = {}

        for candidate in candidates:
            name = candidate.get('name', '')

            # Считаем несколько метрик
            exact = 1.0 if TextMatcher.is_exact_match(query, name) else 0
            contains = 1.0 if TextMatcher.contains_all_words(query, name) else 0
            coverage = TextMatcher.word_coverage(query, name)
            similarity = TextMatcher.similarity(
                TextMatcher.normalize(query),
                TextMatcher.normalize(name)
            )

            # Комбинируем метрики с весами
            score = (exact * 1.0 +
                     contains * 0.5 +
                     coverage * 0.3 +
                     similarity * 0.2)

            # Бонус за короткое название (меньше шума)
            if len(name) < len(query) * 2:
                score += 0.1

            details = {
                'exact': exact > 0,
                'contains': contains > 0,
                'coverage': coverage,
                'similarity': similarity,
                'score': score
            }

            if score > best_score and similarity > threshold:
                best_score = score
                best_match = candidate.copy()
                best_match['match_details'] = details

        return best_match

    @staticmethod
    def rank_candidates(query: str, candidates: List[Dict], threshold: float = 0.3) -> List[Dict]:
        """
        Ранжирует всех кандидатов по степени совпадения
        """
        ranked = []

        for candidate in candidates:
            name = candidate.get('name', '')
            similarity = TextMatcher.similarity(
                TextMatcher.normalize(query),
                TextMatcher.normalize(name)
            )

            if similarity >= threshold:
                candidate_copy = candidate.copy()
                candidate_copy['similarity'] = similarity
                candidate_copy['exact'] = TextMatcher.is_exact_match(query, name)
                ranked.append(candidate_copy)

        # Сортируем по убыванию схожести
        ranked.sort(key=lambda x: (x.get('exact', False), x.get('similarity', 0)), reverse=True)
        return ranked