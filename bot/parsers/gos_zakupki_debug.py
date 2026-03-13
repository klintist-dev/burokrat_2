"""
Парсер госзакупок с подробным логированием для отладки
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlencode

logger = logging.getLogger(__name__)


class GosZakupkiDebugParser:
    """
    Парсер для поиска контрактов по ИНН поставщика с подробным логированием
    """

    BASE_URL = "https://zakupki.gov.ru"
    SEARCH_URL = f"{BASE_URL}/epz/contract/search/results.html"

    def __init__(self, debug: bool = True):
        self.session = requests.Session()
        self.debug = debug
        self.request_log = []

        # Точные заголовки Firefox из HAR-файла
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:147.0) Gecko/20100101 Firefox/147.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })

        # Куки как в браузере
        self.cookies = {
            'userRegionName': 'Ленинградская',
            'yandexRegionName': 'Ленинградская область',
            'doNotShowKladrPopUp': 'true',
            'detectedRegionId': '47000000000',
            '_ym_uid': '1768300417367406414',
            '_ym_d': '1768300417',
            '_ym_isad': '2',
        }
        self.session.cookies.update(self.cookies)

    def _log_request(self, method: str, url: str, params: Dict = None, response=None, error: str = None):
        """Логирует детали запроса"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'url': url,
            'params': params,
            'headers': dict(self.session.headers),
            'cookies': dict(self.session.cookies),
            'status': response.status_code if response else None,
            'response_length': len(response.text) if response and response.text else 0,
            'response_preview': response.text[:500] if response and response.text else None,
            'error': error
        }
        self.request_log.append(log_entry)

        # Выводим в консоль
        logger.info(f"🌐 {method} {url}")
        logger.info(f"📊 Параметры: {json.dumps(params, ensure_ascii=False, indent=2)}")
        logger.info(f"🔑 Куки: {dict(self.session.cookies)}")
        if response:
            logger.info(f"✅ Статус: {response.status_code}")
            logger.info(f"📦 Размер: {len(response.text)} байт")
            if 'captcha' in response.text.lower():
                logger.warning("⚠️ Обнаружена капча!")
        if error:
            logger.error(f"❌ Ошибка: {error}")
        logger.info("-" * 50)

    def _make_request(self, method: str, url: str, params: Dict = None, delay: int = 3):
        """Делает запрос с задержкой и логированием"""
        time.sleep(delay)

        try:
            response = self.session.request(method, url, params=params, timeout=30)
            self._log_request(method, url, params, response)
            return response
        except Exception as e:
            self._log_request(method, url, params, error=str(e))
            raise

    def search_by_supplier_inn(self, inn: str) -> Dict:
        """
        Поиск контрактов по ИНН поставщика с полным логированием
        """
        try:
            logger.info(f"🔍 Поиск контрактов для ИНН поставщика {inn}")

            # 1. Сначала заходим на главную
            logger.info("🌐 Шаг 1: Заходим на главную...")
            self._make_request('GET', 'https://zakupki.gov.ru', delay=2)

            # 2. Заходим на страницу поиска
            logger.info("🔍 Шаг 2: Заходим на страницу поиска...")
            self._make_request('GET', 'https://zakupki.gov.ru/epz/contract/search/search.html', delay=3)

            # 3. Выполняем поиск
            logger.info(f"🔎 Шаг 3: Выполняем поиск по ИНН {inn}...")
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
                'pageNumber': '1',
                'sortDirection': 'false',
                'recordsPerPage': '_10',
                'showLotsInfoHidden': 'false'
            }

            response = self._make_request('GET', self.SEARCH_URL, params=params, delay=3)

            # Сохраняем полный лог в файл
            with open(f'goszakupki_debug_{inn}.json', 'w', encoding='utf-8') as f:
                json.dump(self.request_log, f, ensure_ascii=False, indent=2)

            # Проверяем результат
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                cards = soup.select('.search-registry-entry-block')
                logger.info(f"✅ Найдено карточек на странице: {len(cards)}")

                # Сохраняем HTML для анализа
                with open(f'goszakupki_result_{inn}.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                logger.info(f"💾 HTML сохранён в goszakupki_result_{inn}.html")

                return {
                    'success': True,
                    'status_code': response.status_code,
                    'cards_count': len(cards),
                    'html_saved': True,
                    'log_saved': True
                }
            else:
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': 'Не удалось получить данные'
                }

        except Exception as e:
            logger.error(f"❌ Ошибка: {e}")
            return {
                'success': False,
                'error': str(e),
                'log_saved': True
            }

    def save_log(self, filename: str = 'goszakupki_debug_log.json'):
        """Сохраняет лог запросов в файл"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.request_log, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 Лог сохранён в {filename}")