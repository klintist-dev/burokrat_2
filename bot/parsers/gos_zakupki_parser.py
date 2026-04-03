"""
Парсер для сайта госзакупок zakupki.gov.ru
Исправленная версия для работы на сервере
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
import random
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

logger = logging.getLogger(__name__)


class GosZakupkiParser:
    """
    Парсер для поиска контрактов по ИНН поставщика/заказчика и получения деталей контракта
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
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # Пробуем импортировать brotli
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

            # 1. Заходим на главную
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

        text_lower = response.text.lower()
        if 'captcha' in text_lower or 'капча' in text_lower:
            logger.error("🚫 Обнаружена капча! IP может быть заблокирован")
            return False

        if 'blocked' in text_lower or 'блокировк' in text_lower:
            logger.error("🚫 Доступ заблокирован")
            return False

        return True

    # ==================== ПОИСК ПО ПОСТАВЩИКУ ====================

    def search_by_supplier_inn(self, inn: str) -> Dict:
        """
        Поиск контрактов по ИНН поставщика с обходом всех страниц
        """
        try:
            logger.info(f"🔍 Поиск контрактов для ИНН поставщика {inn}")

            all_contracts = []
            page = 1
            total_pages = 1

            while page <= total_pages:
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

                time.sleep(random.uniform(1.5, 2.5))

                response = self._make_request('GET', self.SEARCH_URL, params=params)

                if not self._check_response(response):
                    return {
                        'inn': inn,
                        'total': 0,
                        'contracts': [],
                        'success': False,
                        'error': 'Response blocked or captcha detected'
                    }

                contracts, total_on_page = self._parse_search_results(response.text)

                if not contracts:
                    logger.warning(f"⚠️ На странице {page} нет карточек, останавливаемся")
                    break

                all_contracts.extend(contracts)

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

    # ==================== ПОИСК ПО ЗАКАЗЧИКУ ====================

    def search_customer_by_inn(self, inn: str) -> Dict:
        """
        Поиск заказчика по ИНН через модальное окно
        """
        try:
            logger.info(f"🔍 Поиск заказчика по ИНН: {inn}")

            # ШАГ 1: Открываем страницу выбора организации (как при нажатии кнопки "Выбрать")
            choose_url = f"{self.BASE_URL}/epz/organization/chooseOrganization/chooseOrganizationDialogModal.html"

            params = {
                'inputId': 'customer',
                'page': '1',
                'organizationType': 'ALL',
                'placeOfSearch': 'FZ_94',
                'withOutLaw': ''
            }

            # Получаем HTML с формой
            response = self._make_request('GET', choose_url, params=params)
            if not self._check_response(response):
                return {'error': 'Ошибка загрузки формы выбора', 'success': False}

            # Получаем CSRF токен из формы
            soup = BeautifulSoup(response.text, 'lxml')
            csrf_input = soup.find('input', {'name': '_csrf'})
            csrf_token = csrf_input.get('value', '') if csrf_input else ''

            # ШАГ 2: Отправляем поисковый запрос (как при вводе ИНН и нажатии "Найти")
            table_url = f"{self.BASE_URL}/epz/organization/chooseOrganization/chooseOrganizationTableModal.html"

            table_params = {
                'searchString': inn,
                'inputId': 'customer',
                'page': '1',
                'pageSize': '10',
                'organizationType': 'ALL',
                'placeOfSearch': 'FZ_94',
                'isBm25Search': 'true'
            }

            response = self._make_request('GET', table_url, params=table_params)

            if not self._check_response(response):
                return {'error': 'Ошибка поиска заказчика', 'success': False}

            soup = BeautifulSoup(response.text, 'lxml')

            # Ищем таблицу с результатами
            table = soup.find('table', class_='registry')
            if not table:
                return {'error': 'Организация не найдена', 'success': False}

            rows = table.find_all('tr')
            customers = []

            for row in rows[1:]:  # Пропускаем заголовок
                cols = row.find_all('td')
                if len(cols) >= 3:
                    # Извлекаем ID организации из radio button
                    radio = row.find('input', type='radio')
                    org_id = radio.get('value', '') if radio else ''

                    # Название (обычно в первой колонке, может быть ссылкой)
                    name_elem = cols[0].find('a')
                    name = name_elem.text.strip() if name_elem else cols[0].text.strip()

                    # ИНН (во второй колонке)
                    inn_value = cols[1].text.strip() if len(cols) > 1 else ''

                    # Адрес (в третьей колонке)
                    address = cols[2].text.strip() if len(cols) > 2 else ''

                    customers.append({
                        'id': org_id,
                        'name': name,
                        'inn': inn_value,
                        'address': address
                    })

            return {
                'inn': inn,
                'success': True,
                'total': len(customers),
                'customers': customers
            }

        except Exception as e:
            logger.error(f"❌ Ошибка поиска заказчика: {e}")
            return {'error': str(e), 'success': False}

    def search_contracts_by_customer_inn(self, inn: str) -> Dict:
        """
        Поиск контрактов по ИНН заказчика (с обходом всех страниц)
        """
        try:
            logger.info(f"🔍 Поиск контрактов для заказчика с ИНН {inn}")

            # Сначала находим ID организации заказчика
            customer_search = self.search_customer_by_inn(inn)
            if not customer_search.get('success') or not customer_search.get('customers'):
                return {
                    'inn': inn,
                    'total': 0,
                    'contracts': [],
                    'success': False,
                    'error': 'Заказчик не найден'
                }

            # Берем первого найденного заказчика
            customer = customer_search['customers'][0]
            customer_id = customer['id']
            customer_name = customer['name']

            logger.info(f"📋 Найден заказчик: {customer_name} (ID: {customer_id})")

            # Теперь ищем контракты по ID заказчика
            all_contracts = []
            page = 1
            total_pages = 1

            while page <= total_pages:
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
                    'customerIdOrg': customer_id,  # Ключевой параметр!
                    'countryRegIdNameHidden': '{}',
                    'sortBy': 'UPDATE_DATE',
                    'pageNumber': str(page),
                    'sortDirection': 'false',
                    'recordsPerPage': '_10',
                    'showLotsInfoHidden': 'false'
                }

                time.sleep(random.uniform(1.5, 2.5))

                response = self._make_request('GET', self.SEARCH_URL, params=params)

                if not self._check_response(response):
                    break

                contracts, total_on_page = self._parse_search_results(response.text)

                if not contracts:
                    logger.warning(f"⚠️ На странице {page} нет карточек, останавливаемся")
                    break

                all_contracts.extend(contracts)

                if page == 1:
                    soup = BeautifulSoup(response.text, 'lxml')
                    total_results = self._parse_total_count(soup)
                    if total_results > 0:
                        total_pages = (total_results + 9) // 10
                        logger.info(f"📊 Всего контрактов: {total_results}, страниц: {total_pages}")
                    else:
                        logger.warning("⚠️ Не удалось определить общее количество результатов")
                        break

                logger.info(f"📄 Страница {page}: найдено {len(contracts)} контрактов")
                page += 1

            return {
                'inn': inn,
                'customer_name': customer_name,
                'customer_id': customer_id,
                'total': len(all_contracts),
                'contracts': all_contracts,
                'success': True
            }

        except Exception as e:
            logger.error(f"❌ Ошибка поиска контрактов для заказчика: {e}")
            return {'error': str(e), 'success': False}

    # ==================== ОБЩИЕ МЕТОДЫ ====================

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

            dates = card.select('.data-block .row .data-block__value')
            publish_date = dates[0].text.strip() if len(dates) > 0 else ''
            update_date = dates[1].text.strip() if len(dates) > 1 else ''

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
                numbers = re.findall(r'\d+', text)
                if numbers:
                    return int(numbers[0])
            return 0
        except:
            return 0

    def get_contract_details(self, contract_url: str) -> Dict:
        """
        Получает детальную информацию о конкретном контракте
        со всех вкладок, где есть документы
        """
        try:
            logger.info(f"🔍 Получаем детали контракта: {contract_url}")

            # Получаем основную страницу
            response = self._make_request('GET', contract_url)

            if not self._check_response(response):
                return {'error': 'Не удалось загрузить страницу контракта', 'success': False}

            soup = BeautifulSoup(response.text, 'lxml')

            # Список вкладок с документами
            doc_tabs = [
                ('document-info.html', 'Вложения'),
                ('execution-info.html', 'Исполнение'),
                ('payment-info-and-target-of-order.html', 'Платежи')
            ]

            all_documents = []

            # Парсим каждую вкладку
            for tab_file, tab_name in doc_tabs:
                tab_url = contract_url.replace('common-info.html', tab_file)
                logger.info(f"📄 Загружаем вкладку '{tab_name}': {tab_url}")

                try:
                    tab_response = self._make_request('GET', tab_url)

                    # Если страница не найдена (404), просто пропускаем
                    if tab_response.status_code == 404:
                        logger.info(f"   Вкладка '{tab_name}' не существует (404)")
                        continue

                    if self._check_response(tab_response):
                        tab_soup = BeautifulSoup(tab_response.text, 'lxml')
                        tab_docs = self._extract_documents(tab_soup)

                        # Добавляем информацию об источнике
                        for doc in tab_docs:
                            doc['source_tab'] = tab_name

                        all_documents.extend(tab_docs)
                        logger.info(f"   Найдено документов в '{tab_name}': {len(tab_docs)}")
                except Exception as e:
                    logger.error(f"Ошибка при загрузке вкладки {tab_name}: {e}")
                    continue

            # Собираем все данные
            details = {
                'url': contract_url,
                'number': self._extract_contract_number(soup),
                'status': self._extract_contract_status(soup),
                'price': self._extract_contract_price(soup),
                'customer': self._extract_customer_info(soup),
                'supplier': self._extract_supplier_info(soup),
                'dates': self._extract_dates(soup),
                'documents': all_documents,
                'documents_by_tab': {
                    'attachments': [d for d in all_documents if d.get('source_tab') == 'Вложения'],
                    'execution': [d for d in all_documents if d.get('source_tab') == 'Исполнение'],
                    'payments': [d for d in all_documents if d.get('source_tab') == 'Платежи']
                },
                'success': True
            }

            logger.info(f"✅ Номер: {details['number']}")
            logger.info(f"✅ Статус: {details['status']}")
            logger.info(f"✅ Цена: {details['price']}")
            logger.info(f"✅ Всего документов: {len(all_documents)}")
            logger.info(f"   - Вложения: {len(details['documents_by_tab']['attachments'])}")
            logger.info(f"   - Исполнение: {len(details['documents_by_tab']['execution'])}")
            logger.info(f"   - Платежи: {len(details['documents_by_tab']['payments'])}")

            return details

        except Exception as e:
            logger.error(f"❌ Ошибка при получении деталей контракта: {e}")
            return {'error': str(e), 'success': False}

    def _extract_contract_number(self, soup) -> str:
        """Извлекает номер контракта"""
        try:
            elem = soup.select_one('.cardMainInfo__purchaseLink a')
            if elem:
                return elem.text.strip()

            elem = soup.select_one('a[href*="reestrNumber"]')
            if elem and 'Подписаться' not in elem.text:
                return elem.text.strip()

            return ''
        except Exception as e:
            logger.error(f"Ошибка извлечения номера: {e}")
            return ''

    def _extract_contract_status(self, soup) -> str:
        """Извлекает статус контракта"""
        try:
            elem = soup.select_one('.cardMainInfo__state')
            return elem.text.strip() if elem else ''
        except Exception as e:
            logger.error(f"Ошибка извлечения статуса: {e}")
            return ''

    def _extract_contract_price(self, soup) -> str:
        """Извлекает цену"""
        try:
            elem = soup.select_one('.cardMainInfo__content.cost')
            return elem.text.strip() if elem else ''
        except Exception as e:
            logger.error(f"Ошибка извлечения цены: {e}")
            return ''

    def _extract_customer_info(self, soup) -> Dict:
        """Информация о заказчике"""
        try:
            customer = {}
            elem = soup.select_one('.cardMainInfo__section .cardMainInfo__content a')
            if elem:
                customer['name'] = elem.text.strip()
                href = elem.get('href', '')
                if href:
                    customer['url'] = urljoin(self.BASE_URL, href)

                if 'organizationCode=' in href:
                    match = re.search(r'organizationCode=(\d+)', href)
                    if match:
                        customer['code'] = match.group(1)
            return customer
        except Exception as e:
            logger.error(f"Ошибка извлечения заказчика: {e}")
            return {}

    def _extract_supplier_info(self, soup) -> Dict:
        """Информация о поставщике (если есть)"""
        return {}

    def _extract_dates(self, soup) -> Dict:
        """Извлекает даты контракта"""
        try:
            dates = {}

            date_elements = soup.select('.date .cardMainInfo__section .cardMainInfo__content')

            if len(date_elements) >= 2:
                dates['conclusion'] = date_elements[0].text.strip()
                dates['execution'] = date_elements[1].text.strip()

            all_sections = soup.select('.cardMainInfo__section .cardMainInfo__content')
            if len(all_sections) >= 4:
                dates['published'] = all_sections[-2].text.strip()
                dates['updated'] = all_sections[-1].text.strip()

            return dates
        except Exception as e:
            logger.error(f"Ошибка извлечения дат: {e}")
            return {}

    def _extract_documents(self, soup) -> List[Dict]:
        """Извлекает ссылки на документы со страницы вложений"""
        documents = []

        try:
            file_links = soup.select('a[href*="/44fz/filestore/"]')

            for link in file_links:
                try:
                    doc = {}

                    href = link.get('href', '')
                    if href.startswith('/'):
                        doc['url'] = urljoin(self.BASE_URL, href)
                    else:
                        doc['url'] = href

                    doc['title'] = link.get('title', link.text.strip())

                    url_lower = doc['url'].lower()
                    title_lower = doc['title'].lower()

                    if '.pdf' in url_lower or '.pdf' in title_lower:
                        doc['type'] = 'PDF'
                    elif '.rar' in url_lower or '.rar' in title_lower:
                        doc['type'] = 'RAR'
                    elif '.xml' in url_lower or '.xml' in title_lower:
                        doc['type'] = 'XML'
                    elif '.doc' in url_lower or '.doc' in title_lower:
                        doc['type'] = 'DOC'
                    else:
                        doc['type'] = 'unknown'

                    size_match = re.search(r'\(([\d.,]+\s*[КМ]б)\)', link.get('title', ''))
                    if size_match:
                        doc['size'] = size_match.group(1)

                    documents.append(doc)

                except Exception as e:
                    logger.error(f"Ошибка парсинга документа: {e}")
                    continue

        except Exception as e:
            logger.error(f"Ошибка в _extract_documents: {e}")

        return documents

    def download_contract_document(self, doc_url: str, filename: str = None) -> Optional[str]:
        """
        Скачивает документ контракта
        """
        try:
            response = self._make_request('GET', doc_url)

            if response.status_code != 200:
                logger.error(f"Ошибка скачивания: {response.status_code}")
                return None

            os.makedirs('data/goszakupki', exist_ok=True)

            if not filename:
                import hashlib
                url_hash = hashlib.md5(doc_url.encode()).hexdigest()[:8]

                ext = '.bin'
                if '.pdf' in doc_url.lower():
                    ext = '.pdf'
                elif '.rar' in doc_url.lower():
                    ext = '.rar'
                elif '.xml' in doc_url.lower():
                    ext = '.xml'
                elif '.html' in doc_url.lower():
                    ext = '.html'

                filename = f"contract_{url_hash}{ext}"

            filepath = f"data/goszakupki/{filename}"

            with open(filepath, 'wb') as f:
                f.write(response.content)

            logger.info(f"✅ Документ сохранён: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Ошибка скачивания документа: {e}")
            return None


# Тестовая функция
def test_documents_tab():
    """Тестируем получение документов с отдельной вкладки"""

    print("\n" + "=" * 60)
    print("📎 ТЕСТ: Получение документов с вкладки 'Вложения'")
    print("=" * 60 + "\n")

    parser = GosZakupkiParser()
    reestr = "3470704054126000003"

    doc_url = f"https://zakupki.gov.ru/epz/contract/contractCard/document-info.html?reestrNumber={reestr}"

    print(f"📄 Загружаем: {doc_url}\n")

    response = parser._make_request('GET', doc_url)
    soup = BeautifulSoup(response.text, 'lxml')

    file_links = soup.select('a[href*="/44fz/filestore/"]')

    print(f"🔍 Найдено ссылок на файлы: {len(file_links)}")

    for i, link in enumerate(file_links[:5], 1):
        print(f"\n{i}. {link.get('title', link.text.strip())}")
        print(f"   URL: {link.get('href', '')[:100]}")

        href = link.get('href', '').lower()
        if '.pdf' in href:
            print(f"   Тип: PDF")
        elif '.rar' in href:
            print(f"   Тип: RAR")
        elif '.xml' in href:
            print(f"   Тип: XML")


if __name__ == "__main__":
    test_documents_tab()