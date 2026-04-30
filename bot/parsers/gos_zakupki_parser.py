"""
Парсер для сайта госзакупок zakupki.gov.ru
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class GosZakupkiParser:

    BASE_URL = "https://zakupki.gov.ru"
    SEARCH_URL = f"{BASE_URL}/epz/contract/search/results.html"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:149.0) Gecko/20100101 Firefox/149.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9",
            "Referer": "https://zakupki.gov.ru/",
            "Connection": "keep-alive"
        })
        self._warmup()

    # =========================
    # WARMUP (получение cookies)
    # =========================

    def _warmup(self):
        """Прогрев сессии — получаем cookies и csrf-токены"""
        try:
            urls = [
                "https://zakupki.gov.ru/",
                "https://zakupki.gov.ru/epz/contract/search/search.html"
            ]
            for u in urls:
                self.session.get(u, timeout=30)
                time.sleep(0.3)
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")

    # =========================
    # ПОИСК ПО ПОСТАВЩИКУ
    # =========================

    def search_by_supplier_inn(self, inn: str) -> Dict:
        """
        Поиск контрактов по ИНН поставщика
        """
        try:
            contracts = []
            page = 1
            total_pages = 1

            while page <= total_pages:
                params = {
                    "morphology": "on",
                    "fz44": "on",
                    "contractStageList_0": "on",
                    "contractStageList_1": "on",
                    "contractStageList_2": "on",
                    "contractStageList_3": "on",
                    "contractStageList": "0,1,2,3",
                    "supplierTitle": inn,
                    "selectedContractDataChanges": "ANY",
                    "budgetLevelsIdNameHidden": "{}",
                    "countryRegIdNameHidden": "{}",
                    "sortBy": "UPDATE_DATE",
                    "pageNumber": str(page),
                    "sortDirection": "false",
                    "recordsPerPage": "_10",
                    "showLotsInfoHidden": "false",
                }

                time.sleep(random.uniform(1, 1.5))

                r = self.session.get(self.SEARCH_URL, params=params, timeout=30)
                r.raise_for_status()

                page_contracts, total = self._parse_search_results(r.text)
                contracts.extend(page_contracts)

                if page == 1:
                    total_pages = max(1, (total + 9) // 10)

                page += 1

            return {
                "inn": inn,
                "total": len(contracts),
                "contracts": contracts,
                "success": True
            }

        except Exception as e:
            logger.error(f"Ошибка поиска по поставщику {inn}: {e}")
            return {"error": str(e), "success": False}

    # =========================
    # ПОИСК ПО ЗАКАЗЧИКУ
    # =========================

    def search_by_customer_inn(self, inn: str, page: int = 1, limit: int = 20) -> Dict:
        """
        Поиск контрактов по ИНН заказчика
        """
        try:
            # Полный цикл выбора организации
            org = self._select_organization(inn)
            if not org:
                return {"success": False, "error": f"Организация с ИНН {inn} не найдена"}

            # Формируем параметры поиска
            params = {
                "morphology": "on",
                "fz44": "on",
                "contractStageList_0": "on",
                "contractStageList_1": "on",
                "contractStageList_2": "on",
                "contractStageList_3": "on",
                "contractStageList": "0,1,2,3",
                "customerIdOrg": org["customer_id_org"],
                "selectedContractDataChanges": "ANY",
                "budgetLevelsIdNameHidden": "{}",
                "countryRegIdNameHidden": "{}",
                "sortBy": "UPDATE_DATE",
                "pageNumber": str(page),
                "sortDirection": "false",
                "recordsPerPage": f"_{limit}",
                "showLotsInfoHidden": "false",
            }

            time.sleep(0.5)

            r = self.session.get(self.SEARCH_URL, params=params, timeout=30)
            r.raise_for_status()

            contracts, total = self._parse_search_results(r.text)
            total_pages = (total + limit - 1) // limit if total > 0 else 0

            return {
                "inn": inn,
                "org": org,
                "total": total,
                "contracts": contracts,
                "current_page": page,
                "total_pages": total_pages,
                "limit": limit,
                "success": True
            }

        except Exception as e:
            logger.error(f"Ошибка поиска по заказчику {inn}: {e}")
            return {"error": str(e), "success": False}

    # =========================
    # ВЫБОР ОРГАНИЗАЦИИ (эмуляция)
    # =========================

    def _select_organization(self, inn: str) -> Optional[Dict]:
        """
        Полностью эмулирует выбор организации через модальное окно
        """
        try:
            # Шаг 1. Открываем страницу с модальным окном
            modal_url = "https://zakupki.gov.ru/epz/organization/chooseOrganization/chooseOrganizationDialogModal.html"
            modal_params = {
                'inputId': 'customer',
                'page': '1',
                'organizationType': 'ALL',
                'placeOfSearch': 'FZ_94'
            }
            self.session.get(modal_url, params=modal_params, timeout=30)
            time.sleep(0.5)

            # Шаг 2. Ищем организацию в модальном окне
            search_url = "https://zakupki.gov.ru/epz/organization/chooseOrganization/chooseOrganizationTableModal.html"
            search_params = {
                'searchString': inn,
                'inputId': 'customer',
                'page': '1',
                'pageSize': '10',
                'organizationType': 'ALL',
                'placeOfSearch': 'FZ_94'
            }

            r = self.session.get(search_url, params=search_params, timeout=30)
            soup = BeautifulSoup(r.text, 'lxml')

            # Находим организацию
            org_tag = soup.select_one(f'input[data-inn="{inn}"]')
            if not org_tag:
                logger.warning(f"Организация с ИНН {inn} не найдена")
                return None

            # Собираем ВСЕ data-атрибуты
            org_id = org_tag.get('data-id', '')
            org_name = org_tag.get('data-name', '')
            org_code = org_tag.get('data-code', '')
            org_fz94id = org_tag.get('data-fz94id', '')
            org_ogrn = org_tag.get('data-ogrn', '')
            org_kpp = org_tag.get('data-kpp', '')

            # Формируем customer_id_org в правильном формате (как в браузере)
            customer_id_org = f"{org_id}:{org_name}zZ{org_code}zZ{org_fz94id}zZzZ{inn}zZzZ{org_kpp}zZ{org_ogrn}"

            logger.info(f"Сформирован customer_id_org (первые 100 символов): {customer_id_org[:100]}...")

            # Шаг 3. Эмулируем выбор организации
            choose_url = "https://zakupki.gov.ru/epz/organization/chooseOrganization/chooseOrganizationAjaxDialog.html"
            choose_params = {
                'id': org_id,
                'inputId': 'customer',
                'organizationType': 'ALL'
            }

            self.session.get(choose_url, params=choose_params, timeout=30)
            time.sleep(0.5)

            return {
                "id": org_id,
                "name": org_name,
                "code": org_code,
                "fz94id": org_fz94id,
                "ogrn": org_ogrn,
                "kpp": org_kpp,
                "customer_id_org": customer_id_org
            }

        except Exception as e:
            logger.error(f"Ошибка выбора организации: {e}")
            return None

    # =========================
    # ПАРСИНГ HTML
    # =========================

    def _parse_search_results(self, html: str) -> Tuple[List[Dict], int]:
        """
        Парсит страницу результатов поиска
        """
        soup = BeautifulSoup(html, "lxml")

        contracts = []
        for card in soup.select(".search-registry-entry-block"):
            c = self._parse_contract_card(card)
            if c:
                contracts.append(c)

        total = self._parse_total_count(soup)
        return contracts, total

    def _parse_contract_card(self, card) -> Optional[Dict]:
        """
        Парсит одну карточку контракта
        """
        try:
            number_elem = card.select_one('.registry-entry__header-mid__number a')
            if not number_elem:
                return None

            number = number_elem.text.strip()
            relative_url = number_elem.get('href', '')
            url = urljoin(self.BASE_URL, relative_url) if relative_url else ''

            status_elem = card.select_one('.registry-entry__header-mid__title')
            status = status_elem.text.strip() if status_elem else ''

            customer_elem = card.select_one('.registry-entry__body-href a')
            customer = customer_elem.text.strip() if customer_elem else ''

            price_elem = card.select_one('.price-block__value')
            price = price_elem.text.strip() if price_elem else ''

            # ========== НОВЫЕ ПОЛЯ ==========
            # Дата публикации и обновления
            dates = card.select('.data-block .row .data-block__value')
            publish_date = dates[0].text.strip() if len(dates) > 0 else ''
            update_date = dates[1].text.strip() if len(dates) > 1 else ''

            # Объект закупки
            object_elem = card.select_one('.lots-wrap-content__body--item .lots-wrap-content__body__val span')
            object_name = object_elem.text.strip() if object_elem else ''
            # ===============================

            return {
                'number': number,
                'url': url,
                'status': status,
                'customer': customer,
                'price': price,
                'publish_date': publish_date,
                'update_date': update_date,
                'object': object_name[:200] if object_name else ''  # ограничим длину
            }

        except Exception as e:
            logger.error(f"Ошибка парсинга карточки: {e}")
            return None

    def _parse_total_count(self, soup) -> int:
        """
        Парсит общее количество найденных контрактов
        """
        try:
            total_elem = soup.select_one(".search-results__total")
            if not total_elem:
                return 0
            numbers = re.findall(r"\d+", total_elem.text)
            return int(numbers[0]) if numbers else 0
        except Exception:
            return 0

    def get_contract_details(self, contract_url: str) -> Dict:
        """
        Получает детальную информацию о контракте
        """
        # TODO: реализовать при необходимости
        return {"url": contract_url}


# =========================
# ОТДЕЛЬНАЯ ФУНКЦИЯ ДЛЯ API
# =========================

def search_contracts_by_customer_inn(inn: str, page: int = 1, limit: int = 20) -> Dict:
    """
    Отдельная функция для вызова из API
    """
    parser = GosZakupkiParser()
    return parser.search_by_customer_inn(inn, page, limit)


# =========================
# ТЕСТ
# =========================

if __name__ == "__main__":
    p = GosZakupkiParser()

    print("\n=== ПОСТАВЩИК ===")
    result = p.search_by_supplier_inn("7707083893")
    print(f"Найдено контрактов: {result['total']}")

    print("\n=== ЗАКАЗЧИК ===")
    inn = "4707023419"
    result = p.search_by_customer_inn(inn, page=1, limit=10)

    if result.get("success"):
        print(f"Организация: {result['org']['name']}")
        print(f"Всего контрактов: {result['total']}")
        print(f"Страница: {result['current_page']} из {result['total_pages']}")
        print(f"Контракты на этой странице: {len(result['contracts'])}")
        for c in result['contracts'][:3]:
            print(f"  - {c['number']}: {c['price']}")
    else:
        print(f"Ошибка: {result.get('error')}")