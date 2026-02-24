# bot/parsers/nalog_parser.py
import aiohttp
from bs4 import BeautifulSoup
import re
import asyncio


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

                    output = f"📋 **Найдено организаций: {total_results}**\n\n"

                    # Показываем не больше 10 результатов
                    max_show = min(10, total_results)
                    output += f"**Первые {max_show} результатов:**\n\n"

                    for i, row in enumerate(results['rows'][:max_show], 1):
                        org_info = []

                        # Сокращаем название (первые 100 символов)
                        if 'n' in row:
                            name = row['n']
                            if len(name) > 100:
                                name = name[:100] + "..."
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


async def get_egrul_extract(inn: str) -> dict:
    """
    Получает выписку из ЕГРЮЛ по ИНН
    Возвращает словарь с путём к файлу или ошибкой
    """
    url = "https://egrul.nalog.ru/index.html"
    download_base = "https://egrul.nalog.ru/vyp-download/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Ищем организацию
            search_data = {
                'query': inn,
                'page': '1',
                'search-type': 'ul'
            }

            async with session.post(url, data=search_data, headers=headers) as response:
                if response.status != 200:
                    return {'error': f'Ошибка поиска: {response.status}'}

                html = await response.text()
                soup = BeautifulSoup(html, 'lxml')

                # 2. Ищем кнопку с data-t
                extract_button = soup.find('button', string='Получить выписку')
                if not extract_button:
                    extract_button = soup.find('button', class_='op-excerpt')

                if not extract_button:
                    return {'error': 'Кнопка получения выписки не найдена'}

                t_value = extract_button.get('data-t')
                if not t_value:
                    return {'error': 'Не найден код выписки (data-t)'}

                # 3. Скачиваем файл по прямой ссылке
                download_url = f"{download_base}{t_value}"

                async with session.get(download_url, headers=headers) as file_response:
                    if file_response.status != 200:
                        return {'error': f'Ошибка скачивания: {file_response.status}'}

                    # 4. Сохраняем файл
                    content_disp = file_response.headers.get('content-disposition', '')
                    filename = "extract.pdf"

                    if 'filename=' in content_disp:
                        match = re.search(r'filename=([^;]+)', content_disp)
                        if match:
                            filename = match.group(1).strip('"')
                    else:
                        filename = f"extract_{inn}.pdf"

                    filepath = f"data/{filename}"

                    with open(filepath, 'wb') as f:
                        f.write(await file_response.read())

                    return {
                        'success': True,
                        'filename': filename,
                        'filepath': filepath
                    }

    except Exception as e:
        return {'error': f'Ошибка: {e}'}


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