"""
Модели данных для API
"""

from dataclasses import dataclass
from typing import List, Optional
import json


@dataclass
class Organization:
    """Модель организации для API"""
    name: str
    inn: str
    ogrn: Optional[str] = None
    address: Optional[str] = None
    status: str = "active"  # active, liquidated
    relevance: float = 0.0

    def to_dict(self):
        """Преобразует объект в словарь для JSON"""
        return {
            "name": self.name,
            "inn": self.inn,
            "ogrn": self.ogrn,
            "address": self.address,
            "status": self.status,
            "relevance": round(self.relevance * 100)  # в проценты
        }

    @classmethod
    def from_parser_result(cls, result: dict):
        """Создаёт объект из результата парсера"""
        return cls(
            name=result.get('name', 'Неизвестно'),
            inn=result.get('inn', ''),
            ogrn=result.get('ogrn', ''),
            address=result.get('address', ''),
            status=result.get('status', 'active'),
            relevance=result.get('relevance', 0)
        )


@dataclass
class SearchResponse:
    """Ответ на поисковый запрос"""
    query: str
    total: int
    organizations: List[Organization]
    region: Optional[str] = None

    def to_dict(self):
        """Преобразует объект в словарь для JSON"""
        return {
            "query": self.query,
            "total": self.total,
            "region": self.region,
            "organizations": [org.to_dict() for org in self.organizations[:10]]  # топ-10
        }