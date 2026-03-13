"""
Парсер для сайта госзакупок zakupki.gov.ru
Исправленная версия для работы на сервере
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class GosZakupkiParser:
    """
    Парсер для поиска контрактов по ИНН поставщика
    """

    BASE_URL = "https://zakupki.gov.ru"
    SEARCH_URL = f"{BASE_URL}/epz/contract/search/results.html"

    def __init__(self):
        self.session = requests.Session()

        # Настройка повторных попыток при ошибках
        retry_strategy = Retry(
            total=2,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Заголовки как в браузере
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',  # Явно просим brotli
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # Пробуем импортировать brotli (необязательно, но желательно)
        try:
            import brotli
            self.brotli_available = True
        except ImportError:
            self.brotli_available = False
            logger.warning("⚠️ brotli не установлен. Установите: pip install brotli")

        # Прогреваем сессию
        self._warmup_session()

    def _warmup_session(self):
        """Прогрев сессии: получаем cookies как настоящий браузер"""
        try:
            logger.info("🌡 Прогрев сессии...")

            # 1. Заходим на главную (она редиректит на /epz/main/public/home.html)
            self._make_request('GET', self.BASE_URL)
            time.sleep(1)

            # 2. Заходим на страницу поиска
            self._make_request('GET', f"{self.BASE_URL}/epz/contract/search/search.html")
            time.sleep(1)

            logger.info("✅ Сессия прогрета")

        except Exception as e:
            logger.warning(f"⚠️ Ошибка прогрева сессии: {e}")

    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Выполняет запрос с поддержкой Brotli и повторными попытками
        """
        # Таймаут по умолчанию
        if 'timeout' not in kwargs:
            kwargs['timeout'] = 30

        response = self.session.request(method, url, **kwargs)

        # Разжимаем Brotli если нужно
        if response.headers.get('content-encoding') == 'br' and self.brotli_available:
            try:
                import brotli
                response._content = brotli.decompress(response.content)
                logger.debug("📦 Распакован Brotli")
            except Exception as e:
                logger.error(f"❌ Ошибка распаковки Brotli: {e}")

        response.encoding = 'utf-8'
        return response

    def _check_response(self, response: requests.Response) -> bool:
        """
        Проверяет, не вернулась ли капча или блокировка
        """
        if response.status_code != 200:
            logger.error(f"❌ HTTP {response.status_code}")
            return False

        # Проверяем наличие капчи (по ключевым словам)
        text_lower = response.text.lower()
        if 'captcha' in text_lower or 'капча' in text_lower:
            logger.error("🚫 Обнаружена капча! IP может быть заблокирован")
            return False

        if 'blocked' in text_lower or 'блокировк' in text_lower:
            logger.error("🚫 Доступ заблокирован")
            return False

        return True

    def search_by_supplier_inn(self, inn: str) -> Dict:
        """
        Поиск контрактов по ИНН поставщика с обходом всех страниц
        """
        try:
            logger.info(f"🔍 Поиск контрактов для ИНН поставщика {inn}")

            all_contracts = []
            page = 1
            total_pages = 1  # пока неизвестно

            while page <= total_pages:
                # Формируем параметры запроса для текущей страницы
                params = {
                    'morphology': 'on',
                    'fz44': 'on',
                    'contractStageList_0': 'on',
                    'contractStageList_1': 'on',
                    'contractStageList_2': 'on',
                    'contractStageList_3': 'on',
                    'contractStageList': '0,1,2,3',
                    'selectedContractDataChanges': 'ANY',
                    'budgetLevelsIdNameHidden': '{}',
                    'supplierTitle': inn,
                    'countryRegIdNameHidden': '{}',
                    'sortBy': 'UPDATE_DATE',
                    'pageNumber': str(page),
                    'sortDirection': 'false',
                    'recordsPerPage': '_10',
                    'showLotsInfoHidden': 'false'
                }

                # Добавляем задержку между запросами
                time.sleep(random.uniform(1.5, 2.5))

                # Выполняем запрос
                response = self._make_request('GET', self.SEARCH_URL, params=params)

                # Проверяем ответ
                if not self._check_response(response):
                    return {
                        'inn': inn,
                        'total': 0,
                        'contracts': [],
                        'success': False,
                        'error': 'Response blocked or captcha detected'
                    }

                # Парсим страницу
                contracts, total_on_page = self._parse_search_results(response.text)

                # Если на странице нет карточек, останавливаемся
                if not contracts:
                    logger.warning(f"⚠️ На странице {page} нет карточек, останавливаемся")
                    break

                all_contracts.extend(contracts)

                # На первой странице узнаём общее количество страниц
                if page == 1:
                    soup = BeautifulSoup(response.text, 'lxml')
                    total_results = self._parse_total_count(soup)
                    if total_results > 0:
                        total_pages = (total_results + 9) // 10
                        logger.info(f"📊 Всего результатов: {total_results}, страниц: {total_pages}")
                    else:
                        logger.warning("⚠️ Не удалось определить общее количество результатов")
                        break

                logger.info(f"📄 Страница {page}: найдено {len(contracts)} контрактов")
                page += 1

            result = {
                'inn': inn,
                'total': len(all_contracts),
                'contracts': all_contracts,
                'success': True
            }

            logger.info(f"✅ Всего собрано контрактов: {len(all_contracts)}")
            return result

        except Exception as e:
            logger.error(f"❌ Ошибка при поиске для ИНН {inn}: {e}")
            return {'error': str(e), 'inn': inn, 'success': False}

    def _parse_search_results(self, html: str) -> Tuple[List[Dict], int]:
        """
        Парсит страницу результатов поиска
        """
        soup = BeautifulSoup(html, 'lxml')
        contracts = []

        cards = soup.select('.search-registry-entry-block')

        for card in cards:
            try:
                contract = self._parse_contract_card(card)
                if contract:
                    contracts.append(contract)
            except Exception as e:
                logger.error(f"Ошибка при парсинге карточки: {e}")
                continue

        total = self._parse_total_count(soup)
        return contracts, total

    def _parse_contract_card(self, card) -> Optional[Dict]:
        """
        Парсит одну карточку контракта
        """
        try:
            # Номер контракта и ссылка
            number_elem = card.select_one('.registry-entry__header-mid__number a')
            if not number_elem:
                return None

            number = number_elem.text.strip()
            relative_url = number_elem.get('href', '')
            url = urljoin(self.BASE_URL, relative_url) if relative_url else ''

            # Статус
            status_elem = card.select_one('.registry-entry__header-mid__title')
            status = status_elem.text.strip() if status_elem else ''

            # Заказчик
            customer_elem = card.select_one('.registry-entry__body-href a')
            customer = customer_elem.text.strip() if customer_elem else ''

            # Цена
            price_elem = card.select_one('.price-block__value')
            price = price_elem.text.strip() if price_elem else ''

            # Даты
            dates = card.select('.data-block .row .data-block__value')
            publish_date = dates[0].text.strip() if len(dates) > 0 else ''
            update_date = dates[1].text.strip() if len(dates) > 1 else ''

            # Объект закупки
            object_elem = card.select_one('.lots-wrap-content__body--item .lots-wrap-content__body__val span')
            object_name = object_elem.text.strip() if object_elem else ''

            return {
                'number': number,
                'url': url,
                'status': status,
                'customer': customer,
                'price': price,
                'publish_date': publish_date,
                'update_date': update_date,
                'object': object_name[:200] if object_name else ''
            }

        except Exception as e:
            logger.error(f"Ошибка парсинга карточки: {e}")
            return None

    def _parse_total_count(self, soup) -> int:
        """
        Парсит общее количество найденных контрактов
        """
        try:
            total_elem = soup.select_one('.search-results__total')
            if total_elem:
                text = total_elem.text
                import re
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
            return 0
        except:
            return 0

    def get_contract_details(self, contract_url: str) -> Dict:
        """
        Получает детальную информацию о конкретном контракте
        (для будущего расширения)
        """
        # TODO: Реализовать позже, когда понадобится
        return {'url': contract_url}

    def _parse_pagination(self, soup) -> Tuple[int, int]:
        """
        Парсит информацию о пагинации
        """
        try:
            current_page = 1
            total_pages = 1

            paginator = soup.select('.paginator')
            if paginator:
                active_page = paginator[0].select('.page__link_active')
                if active_page:
                    current_page = int(active_page[0].text.strip())

                pages = paginator[0].select('.page a')
                if pages:
                    last_page = pages[-1].text.strip()
                    if last_page.isdigit():
                        total_pages = int(last_page)

            return current_page, total_pages
        except:
            return 1, 1
