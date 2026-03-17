#!/usr/bin/env python3
"""
Тест для поиска документов в контракте
"""

import sys
import os
import json
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))

from bot.parsers.gos_zakupki_parser import GosZakupkiParser
from bs4 import BeautifulSoup
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def debug_documents():
    """Подробный анализ поиска документов"""

    print("\n" + "=" * 60)
    print("📎 АНАЛИЗ ПОИСКА ДОКУМЕНТОВ")
    print("=" * 60 + "\n")

    parser = GosZakupkiParser()
    reestr = "3470704054126000003"
    url = f"https://zakupki.gov.ru/epz/contract/contractCard/common-info.html?reestrNumber={reestr}"

    # 1. Получаем страницу
    print(f"📄 Загружаем страницу контракта {reestr}...")
    response = parser._make_request('GET', url)
    soup = BeautifulSoup(response.text, 'lxml')

    # 2. Ищем все возможные ссылки на документы
    print("\n🔍 Поиск ссылок на файлы:")

    # Селектор 1: через filestore
    links1 = soup.select('a[href*="/44fz/filestore/"]')
    print(f"\n1. a[href*='/44fz/filestore/']: {len(links1)}")
    for i, link in enumerate(links1[:5], 1):
        print(f"   {i}. {link.get('title', link.text.strip())[:100]}")
        print(f"      URL: {link.get('href', '')[:80]}")

    # Селектор 2: через download
    links2 = soup.select('a[href*="download"]')
    print(f"\n2. a[href*='download']: {len(links2)}")
    for i, link in enumerate(links2[:5], 1):
        print(f"   {i}. {link.get('title', link.text.strip())[:100]}")

    # Селектор 3: внутри .attachment
    links3 = soup.select('.attachment a[href]')
    print(f"\n3. .attachment a[href]: {len(links3)}")
    for i, link in enumerate(links3[:5], 1):
        print(f"   {i}. {link.get('title', link.text.strip())[:100]}")

    # Селектор 4: все ссылки с расширениями файлов
    import re
    file_pattern = re.compile(r'\.(pdf|rar|zip|doc|docx|xls|xlsx|xml)$', re.I)
    all_links = soup.find_all('a', href=True)
    file_links = [link for link in all_links if file_pattern.search(link['href'])]
    print(f"\n4. Ссылки с расширениями файлов: {len(file_links)}")
    for i, link in enumerate(file_links[:5], 1):
        print(f"   {i}. {link.get('title', link.text.strip())[:100]}")
        print(f"      {link['href'][:80]}")

    # 3. Сохраняем HTML для ручного анализа
    html_file = f'tests/goszakupki/contract_{reestr}_debug.html'
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(response.text)
    print(f"\n💾 HTML сохранён в {html_file}")

    # 4. Пробуем найти блок с документами вручную
    print("\n🔎 Ищем блок 'Вложения' или 'Прикрепленные файлы':")
    for elem in soup.find_all(['div', 'section', 'h2', 'h3']):
        text = elem.get_text(strip=True)
        if any(word in text.lower() for word in ['вложен', 'прикреп', 'документ', 'attachment']):
            print(f"\n  Найден блок: '{text}'")
            # Покажи немного контекста
            parent = elem.find_parent('div', class_=True)
            if parent:
                print(f"  Класс родителя: {parent.get('class', [])}")
                # Найди ссылки внутри
                links = parent.find_all('a', href=True)
                if links:
                    print(f"  Ссылок внутри: {len(links)}")
                    for link in links[:3]:
                        print(f"    → {link.get('title', link.text.strip())[:100]}")


def test_documents_tab_direct():
    """Тестируем получение документов напрямую с вкладки 'Вложения'"""

    print("\n" + "=" * 60)
    print("📎 ТЕСТ: Прямое получение документов с вкладки 'Вложения'")
    print("=" * 60 + "\n")

    parser = GosZakupkiParser()
    reestr = "3470704054126000003"

    # URL вкладки с документами
    doc_url = f"https://zakupki.gov.ru/epz/contract/contractCard/document-info.html?reestrNumber={reestr}"

    print(f"📄 Загружаем: {doc_url}\n")

    response = parser._make_request('GET', doc_url)
    soup = BeautifulSoup(response.text, 'lxml')

    # Ищем документы
    file_links = soup.select('a[href*="/44fz/filestore/"]')

    print(f"🔍 Найдено ссылок на файлы: {len(file_links)}")

    for i, link in enumerate(file_links[:5], 1):
        print(f"\n{i}. {link.get('title', link.text.strip())}")
        print(f"   URL: {link.get('href', '')[:100]}")

        # Определяем тип
        href = link.get('href', '').lower()
        if '.pdf' in href:
            print(f"   Тип: PDF")
        elif '.rar' in href:
            print(f"   Тип: RAR")
        elif '.xml' in href:
            print(f"   Тип: XML")
        elif '.html' in href:
            print(f"   Тип: HTML")


def test_get_contract_details():
    """Тестируем метод get_contract_details"""

    print("\n" + "=" * 60)
    print("🔬 ТЕСТ: get_contract_details")
    print("=" * 60 + "\n")

    parser = GosZakupkiParser()
    reestr = "3470704054126000003"
    contract_url = f"https://zakupki.gov.ru/epz/contract/contractCard/common-info.html?reestrNumber={reestr}"

    details = parser.get_contract_details(contract_url)

    if details.get('success'):
        print(f"✅ Успех!")
        print(f"📌 Номер: {details.get('number')}")
        print(f"📌 Статус: {details.get('status')}")
        print(f"💰 Цена: {details.get('price')}")

        if details.get('customer'):
            print(f"\n🏢 Заказчик: {details['customer'].get('name', '')[:100]}...")

        if details.get('dates'):
            print(f"\n📅 Даты:")
            print(f"   Заключение: {details['dates'].get('conclusion')}")
            print(f"   Исполнение: {details['dates'].get('execution')}")
            print(f"   Опубликован: {details['dates'].get('published')}")
            print(f"   Обновлён: {details['dates'].get('updated')}")

        print(f"\n📎 Документов: {len(details.get('documents', []))}")
        for i, doc in enumerate(details.get('documents', [])[:3], 1):
            print(f"   {i}. {doc.get('title', '')[:50]}...")
    else:
        print(f"❌ Ошибка: {details.get('error')}")


if __name__ == "__main__":
    # debug_documents()
    test_documents_tab_direct()
    test_get_contract_details()