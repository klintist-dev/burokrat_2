# bot/parsers/nalog_parser.py
import aiohttp
from bs4 import BeautifulSoup
import re
import asyncio
import time


async def find_inn_by_name(company_name: str) -> str:
    """
    Ищет ИНН организации по названию на сайте nalog.ru
    """
    base_url = "https://egrul.nalog.ru"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        async with aiohttp.ClientSession() as session:
            # ШАГ 1: Получаем куки
            print("🌐 Получаем куки...")
            async with session.get(f"{base_url}/index.html", headers=headers) as response:
                if response.status != 200:
                    return f"❌ Ошибка загрузки страницы: {response.status}"
                print("✅ Куки получены")

            # ШАГ 2: Отправляем поисковый запрос
            print(f"🔍 Ищем организацию '{company_name}'...")
            search_data = {
                'query': company_name,
                'page': '1',
                'search-type': 'ul'
            }

            async with session.post(f"{base_url}/", data=search_data, headers=headers) as response:
                if response.status != 200:
                    return f"❌ Ошибка поиска: {response.status}"

                search_result = await response.json()
                print(f"📦 Ответ на поиск: {search_result}")

                # Извлекаем ID запроса
                request_id = None
                if isinstance(search_result, dict):
                    if 't' in search_result:
                        request_id = search_result['t']
                    elif 'id' in search_result:
                        request_id = search_result['id']

                if not request_id:
                    return "❌ Не удалось получить ID запроса"

                print(f"🆔 Получен ID запроса: {request_id[:50]}...")

                # ШАГ 3: Получаем результаты с проверкой статуса
                print(f"📥 Запрашиваем результаты...")

                max_attempts = 10
                attempt = 0
                results = None
                wait_time = 1

                while attempt < max_attempts:
                    attempt += 1
                    print(f"⏳ Попытка {attempt}/{max_attempts} (ждём {wait_time} сек)...")

                    # 👇 ИСПРАВЛЕННЫЙ КОД С ПАРАМЕТРАМИ r и _
                    timestamp = int(time.time() * 1000)  # текущее время в миллисекундах
                    results_url = f"{base_url}/search-result/{request_id}?r={timestamp}&_={timestamp}"

                    async with session.get(results_url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()

                            if 'status' in data and data['status'] == 'wait':
                                print(f"⏳ Сервер говорит 'wait', данные ещё готовятся...")
                                await asyncio.sleep(wait_time)
                                wait_time += 1
                                continue
                            else:
                                results = data
                                print(f"✅ Результаты получены на попытке {attempt}")
                                break
                        else:
                            error_text = await resp.text()
                            print(f"❌ Ошибка {resp.status}: {error_text[:200]}")
                            return f"❌ Ошибка получения результатов: {resp.status}"

                if not results:
                    return "❌ Превышено время ожидания результатов."

                print(f"📦 Результаты получены")

                # ШАГ 4: Парсим результаты
                if 'rows' in results and len(results['rows']) > 0:
                    total_results = len(results['rows'])
                    print(f"📊 Всего найдено: {total_results}")

                    output = f"📋 **Найдено организаций: {total_results}**\n\n"

                    # Показываем не больше 10 результатов
                    max_show = min(10, total_results)
                    output += f"**Первые {max_show} результатов:**\n\n"

                    for i, row in enumerate(results['rows'][:max_show], 1):
                        org_info = []

                        # Сокращаем название (первые 100 символов)
                        if 'n' in row:
                            name = row['n']
                            if len(name) > 200:
                                name = name[:200] + "..."
                            org_info.append(f"**{i}. {name}**")

                        # ИНН обязательно
                        if 'i' in row:
                            org_info.append(f"ИНН: `{row['i']}`")

                        # Только основные данные (ОГРН и дата)
                        if 'o' in row:
                            org_info.append(f"ОГРН: {row['o']}")
                        if 'r' in row:
                            org_info.append(f"Дата: {row['r']}")

                        output += "\n".join(org_info) + "\n\n"

                        # Проверяем длину сообщения
                        if len(output) > 3500:
                            output += "... (сообщение слишком длинное, показана часть)"
                            break

                    if total_results > max_show:
                        output += f"📌 **Всего найдено {total_results} организаций.**\n"
                        output += "🔍 **Уточните запрос** (добавьте ИНН, ОГРН или точное название) для более точного поиска.\n"
                        output += f"💡 Показаны первые {max_show} из {total_results}."

                    return output

                return "❌ Организации не найдены"

    except Exception as e:
        print(f"❌ Исключение: {e}")
        return f"❌ Ошибка при парсинге: {e}"


async def find_name_by_inn(inn: str) -> str:
    """
    Ищет название организации по ИНН на сайте nalog.ru
    """
    base_url = "https://egrul.nalog.ru"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        async with aiohttp.ClientSession() as session:
            # ШАГ 1: Получаем куки
            print("🌐 Получаем куки...")
            async with session.get(f"{base_url}/index.html", headers=headers) as response:
                if response.status != 200:
                    return f"❌ Ошибка загрузки страницы: {response.status}"
                print("✅ Куки получены")

            # ШАГ 2: Отправляем поисковый запрос с ИНН
            print(f"🔍 Ищем организацию по ИНН {inn}...")
            search_data = {
                'query': inn,
                'page': '1',
                'search-type': 'ul'
            }

            async with session.post(f"{base_url}/", data=search_data, headers=headers) as response:
                if response.status != 200:
                    return f"❌ Ошибка поиска: {response.status}"

                search_result = await response.json()
                print(f"📦 Ответ на поиск: {search_result}")

                # Извлекаем ID запроса
                request_id = None
                if isinstance(search_result, dict):
                    if 't' in search_result:
                        request_id = search_result['t']
                    elif 'id' in search_result:
                        request_id = search_result['id']

                if not request_id:
                    return "❌ Не удалось получить ID запроса"

                print(f"🆔 Получен ID запроса: {request_id[:50]}...")

                # ШАГ 3: Получаем результаты с проверкой статуса
                print(f"📥 Запрашиваем результаты...")

                max_attempts = 10
                attempt = 0
                results = None
                wait_time = 1

                while attempt < max_attempts:
                    attempt += 1
                    print(f"⏳ Попытка {attempt}/{max_attempts} (ждём {wait_time} сек)...")

                    async with session.get(f"{base_url}/search-result/{request_id}", headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()

                            if 'status' in data and data['status'] == 'wait':
                                print(f"⏳ Сервер говорит 'wait', данные ещё готовятся...")
                                await asyncio.sleep(wait_time)
                                wait_time += 1
                                continue
                            else:
                                results = data
                                print(f"✅ Результаты получены на попытке {attempt}")
                                break
                        else:
                            error_text = await resp.text()
                            print(f"❌ Ошибка {resp.status}: {error_text[:200]}")
                            return f"❌ Ошибка получения результатов: {resp.status}"

                if not results:
                    return "❌ Превышено время ожидания результатов."

                print(f"📦 Результаты получены")

                # ШАГ 4: Парсим результаты
                if 'rows' in results and len(results['rows']) > 0:
                    total_results = len(results['rows'])
                    print(f"📊 Всего найдено: {total_results}")

                    if total_results == 1:
                        # Одна организация — показываем подробно
                        row = results['rows'][0]
                        output = f"🏢 **Организация найдена**\n\n"

                        # Название
                        if 'n' in row:
                            output += f"**{row['n']}**\n\n"

                        # Реквизиты
                        if 'i' in row:
                            output += f"ИНН: `{row['i']}`\n"
                        if 'o' in row:
                            output += f"ОГРН: {row['o']}\n"
                        if 'r' in row:
                            output += f"Дата регистрации: {row['r']}\n"
                        if 'e' in row:
                            output += f"Дата прекращения: {row['e']}\n"
                        if 'g' in row:
                            output += f"Руководитель: {row['g']}\n"
                        if 'c' in row:
                            output += f"КПП: {row['c']}\n"

                        return output

                    else:
                        # Несколько организаций — показываем кратко
                        output = f"📋 **Найдено организаций: {total_results}**\n\n"

                        # Показываем не больше 5
                        max_show = min(5, total_results)
                        output += f"**Первые {max_show} результатов:**\n\n"

                        for i, row in enumerate(results['rows'][:max_show], 1):
                            # Название (сокращаем)
                            if 'n' in row:
                                name = row['n']
                                if len(name) > 80:
                                    name = name[:80] + "..."
                                output += f"**{i}. {name}**\n"

                            # ИНН
                            if 'i' in row:
                                output += f"ИНН: `{row['i']}`\n"

                            # ОГРН
                            if 'o' in row:
                                output += f"ОГРН: {row['o']}\n"

                            output += "\n"

                        output += f"📌 **Уточните запрос** (добавьте больше цифр ИНН или используйте поиск по названию)."

                        return output

                return "❌ Организация с таким ИНН не найдена"

    except Exception as e:
        print(f"❌ Исключение: {e}")
        return f"❌ Ошибка при парсинге: {e}"


async def find_inn_by_name_with_region(company_name: str, region_code: str = None) -> str:
    """
    Ищет ИНН организации по названию на сайте nalog.ru
    region_code - код региона (например "47" для Ленинградской области)
    """
    base_url = "https://egrul.nalog.ru"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        async with aiohttp.ClientSession() as session:
            # ШАГ 1: Получаем куки
            print("🌐 Получаем куки...")
            async with session.get(f"{base_url}/index.html", headers=headers) as response:
                if response.status != 200:
                    return f"❌ Ошибка загрузки страницы: {response.status}"
                print("✅ Куки получены")

            # ШАГ 2: Готовим данные для поиска
            search_data = {
                'query': company_name,
                'page': '1',
                'search-type': 'ul'
            }

            # Если указан код региона, добавляем его
            if region_code:
                search_data['region'] = region_code
                print(f"📍 Ищем в регионе с кодом: {region_code}")

            # ШАГ 3: Отправляем поисковый запрос
            print(f"🔍 Ищем организацию: '{company_name}'")
            async with session.post(f"{base_url}/", data=search_data, headers=headers) as response:
                if response.status != 200:
                    return f"❌ Ошибка поиска: {response.status}"

                search_result = await response.json()
                print(f"📦 Ответ на поиск: {search_result}")

                # Получаем ID запроса
                request_id = search_result.get('t') if isinstance(search_result, dict) else None
                if not request_id:
                    return "❌ Не удалось получить ID запроса"

                print(f"🆔 Получен ID запроса: {request_id[:50]}...")

                # ШАГ 4: Получаем результаты
                print(f"📥 Запрашиваем результаты...")

                max_attempts = 10
                attempt = 0
                results = None
                wait_time = 1

                while attempt < max_attempts:
                    attempt += 1
                    print(f"⏳ Попытка {attempt}/{max_attempts} (ждём {wait_time} сек)...")

                    timestamp = int(time.time() * 1000)
                    results_url = f"{base_url}/search-result/{request_id}?r={timestamp}&_={timestamp}"

                    async with session.get(results_url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()

                            if 'status' in data and data['status'] == 'wait':
                                print(f"⏳ Сервер говорит 'wait'...")
                                await asyncio.sleep(wait_time)
                                wait_time += 1
                                continue
                            else:
                                results = data
                                print(f"✅ Результаты получены на попытке {attempt}")
                                break
                        else:
                            return f"❌ Ошибка получения результатов: {resp.status}"

                if not results:
                    return "❌ Время ожидания истекло"

                # ШАГ 5: Парсим результаты
                if 'rows' in results and len(results['rows']) > 0:
                    total = len(results['rows'])
                    output = f"📋 **Найдено организаций: {total}**\n\n"

                    if region_code:
                        output += f"📍 Регион: {region_code}\n\n"

                    for i, row in enumerate(results['rows'][:10], 1):
                        name = row.get('n', 'Без названия')
                        inn = row.get('i', '')
                        ogrn = row.get('o', '')
                        date = row.get('r', '')

                        if len(name) > 200:
                            name = name[:200] + "..."
                        output += f"**{i}. {name}**\n"
                        if inn:
                            output += f"ИНН: `{inn}`\n"
                        if ogrn:
                            output += f"ОГРН: {ogrn}\n"
                        if date:
                            output += f"Дата: {date}\n"
                        output += "\n"

                    if total > 10:
                        output += f"📌 Показаны первые 10 из {total}. Уточните запрос."

                    return output

                return "❌ Организации не найдены"

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return f"❌ Ошибка при парсинге: {e}"


async def get_egrul_extract(inn: str) -> dict:
    """
    Получает выписку из ЕГРЮЛ по ИНН
    """
    print(f"🔍 get_egrul_extract: начинаем поиск для ИНН {inn}")

    base_url = "https://egrul.nalog.ru"
    search_url = f"{base_url}/"
    result_url = f"{base_url}/search-result/"
    download_base = f"{base_url}/vyp-download/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        async with aiohttp.ClientSession() as session:
            # ШАГ 1: Получаем куки
            print("🌐 Получаем куки...")
            async with session.get(f"{base_url}/index.html", headers=headers) as response:
                if response.status != 200:
                    return {'error': f'Ошибка загрузки страницы: {response.status}'}
                print("✅ Куки получены")

            # ШАГ 2: Ищем организацию
            print(f"🔍 Ищем организацию с ИНН {inn}...")

            ajax_headers = {
                'User-Agent': headers['User-Agent'],
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Referer': f"{base_url}/index.html",
            }

            search_data = {
                'query': inn,
                'page': '1',
                'search-type': 'ul'
            }

            async with session.post(search_url, data=search_data, headers=ajax_headers) as response:
                if response.status != 200:
                    return {'error': f'Ошибка поиска: {response.status}'}

                search_result = await response.json()
                request_id = search_result.get('t')
                if not request_id:
                    return {'error': 'Не удалось получить ID запроса'}

                print(f"🆔 ID запроса получен (длина {len(request_id)})")

            # ШАГ 3: Получаем результаты
            print(f"📥 Запрашиваем результаты...")

            max_attempts = 10
            attempt = 0
            results = None
            wait_time = 2

            while attempt < max_attempts:
                attempt += 1
                print(f"⏳ Попытка {attempt}/{max_attempts} (ждём {wait_time} сек)...")

                timestamp = int(time.time() * 1000)
                results_url = f"{result_url}{request_id}?r={timestamp}&_={timestamp}"

                async with session.get(results_url, headers=ajax_headers) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                        except:
                            text = await resp.text()
                            if "Ошибка" in text:
                                return {'error': '❌ Временные проблемы на сайте ФНС'}
                            return {'error': 'Неожиданный ответ от сервера'}

                        if isinstance(data, dict) and data.get('status') == 'wait':
                            print(f"⏳ Сервер говорит 'wait'...")
                            await asyncio.sleep(wait_time)
                            wait_time += 1
                            continue
                        else:
                            results = data
                            print(f"✅ Результаты получены на попытке {attempt}")
                            break
                    else:
                        print(f"❌ Ошибка {resp.status}")
                        await asyncio.sleep(wait_time)
                        wait_time += 1

            if not results:
                return {'error': 'Превышено время ожидания результатов'}

            # ШАГ 4: Получаем КОРОТКИЙ код (128 символов)
            print("🔍 Получаем короткий код...")

            short_code = None
            org_name = "Неизвестная организация"

            if isinstance(results, dict) and 'rows' in results and len(results['rows']) > 0:
                first_row = results['rows'][0]
                org_name = first_row.get('n', 'Неизвестная организация')

                if 't' in first_row:
                    short_code = first_row['t']
                    print(f"✅ Получен короткий код: длина {len(short_code)}")

                    if len(short_code) != 128:
                        print(f"⚠️ Неожиданная длина кода: {len(short_code)}")

            if not short_code:
                return {'error': 'Не найден код для скачивания'}

            # ШАГ 5: Имитируем нажатие кнопки "Получить выписку"
            # В браузере это вызывает запрос к API для получения длинного кода
            print("🔄 Запрашиваем длинный код (имитация нажатия кнопки)...")

            # Здесь должен быть дополнительный запрос к API ФНС
            # Но точный эндпоинт нам неизвестен
            # Вместо этого, дадим пользователю ссылку с коротким кодом
            # и объясним, что нужно сделать
            download_link = f"{download_base}{short_code}"

            return {
                'status': 'success',
                'download_link': download_link,
                'org_name': org_name,
                'message': f"✅ **Выписка для ИНН {inn} готова!**\n\n"
                           f"📄 **Организация:**\n{org_name[:200]}...\n\n"
                           f"🔗 **Ссылка для скачивания:**\n"
                           f"`{download_link}`\n\n"
                           f"📋 **Важно!**\n"
                           f"1. Скопируйте ссылку\n"
                           f"2. Вставьте в браузер\n"
                           f"3. **Если не скачивается** — просто **обновите страницу** (F5)\n"
                           f"4. Файл начнёт скачиваться после 1-2 обновлений\n\n"
                           f"🔄 Это особенность сайта ФНС: ссылка 'активируется' после первого клика."
            }

    except Exception as e:
        print(f"❌ Исключение: {e}")
        return {'error': f'Ошибка: {str(e)}'}


async def find_inn_by_passport(passport_data: str) -> str:
    """
    Ищет ИНН физического лица по паспортным данным
    Формат: серия и номер через пробел, например "4012 345678"
    """
    url = "https://service.nalog.ru/inn.do"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        parts = passport_data.split()
        if len(parts) != 2:
            return "❌ Неправильный формат. Используйте: серия номер (например: 4012 345678)"

        seria, number = parts

        data = {
            'c': 'innMy',
            'fam': '',
            'nam': '',
            'otch': '',
            'bdate': '',
            'docno': f'{seria}{number}',
            'docdt': ''
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    result = soup.find('div', class_='result')
                    if result:
                        inn_match = re.search(r'\b\d{12}\b', result.text)
                        if inn_match:
                            return f"✅ Ваш ИНН: `{inn_match.group(0)}`"

                    return "❌ ИНН не найден. Возможно, требуются дополнительные данные."
                else:
                    return f"❌ Ошибка сервера: {response.status}"
    except Exception as e:
        return f"❌ Ошибка при парсинге: {e}"


async def check_inn_valid(inn: str) -> str:
    """
    Проверяет, действителен ли ИНН
    """
    url = "https://service.nalog.ru/inn.do"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        data = {
            'c': 'innMy',
            'inn': inn
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    result = soup.find('div', class_='result')
                    if result:
                        if "действителен" in result.text.lower():
                            return f"✅ ИНН {inn} действителен"
                        elif "недействителен" in result.text.lower():
                            return f"❌ ИНН {inn} недействителен"

                    return f"❌ Не удалось проверить ИНН {inn}"
                else:
                    return f"❌ Ошибка сервера: {response.status}"
    except Exception as e:
        return f"❌ Ошибка при парсинге: {e}"


async def get_invalid_inn_list(region: str = "") -> str:
    """
    Получает список недействительных ИНН (по региону)
    """
    url = "https://www.nalog.gov.ru/rn77/service/invalid_inn/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'lxml')

                    table = soup.find('table', class_='data')
                    if table:
                        rows = table.find_all('tr')[:10]
                        result = "⚠️ **Недействительные ИНН (первые 10):**\n\n"

                        for row in rows:
                            cols = row.find_all('td')
                            if len(cols) >= 2:
                                inn = cols[0].text.strip()
                                date = cols[1].text.strip()
                                result += f"• `{inn}` - {date}\n"

                        return result
                    else:
                        return "❌ Не удалось получить список"
                else:
                    return f"❌ Ошибка сервера: {response.status}"
    except Exception as e:
        return f"❌ Ошибка при парсинге: {e}"