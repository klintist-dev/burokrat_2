"""
Flask API сервер для WebApp
"""

import logging
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
import time

# Добавляем путь к проекту для импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from bot.api.models import SearchResponse, Organization
from bot.parsers import find_inn_by_name_structured

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём Flask приложение
app = Flask(__name__)
CORS(app)  # Разрешаем запросы с других доменов

# Хранилище для кэша (чтобы не долбить ФНС каждую секунду)
search_cache = {}
CACHE_TTL = 300  # 5 минут

def run_async(coro):
    """
    Запускает асинхронную функцию в синхронном контексте Flask
    """
    try:
        # Пробуем получить существующий event loop
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # Если нет running loop - создаём новый
        return asyncio.run(coro)
    else:
        # Если loop уже запущен (например, в Jupyter) - используем другой подход
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, coro)
            return future.result()

@app.route('/api/search', methods=['POST', 'OPTIONS'])
def search():
    """
    Эндпоинт для поиска организаций
    Ожидает JSON: {"query": "название", "region": "код"}
    Возвращает: {"organizations": [...], "total": 10}
    """
    # Обработка OPTIONS запроса (для CORS)
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Получаем данные из запроса
        data = request.json
        query = data.get('query', '').strip()
        region = data.get('region', None)

        logger.info(f"🔍 API поиск: '{query}', регион: {region}")

        if not query:
            return jsonify({"error": "Пустой запрос"}), 400

        # Проверяем кэш
        cache_key = f"{query}_{region}"
        if cache_key in search_cache:
            cache_time, cache_result = search_cache[cache_key]
            if time.time() - cache_time < CACHE_TTL:
                logger.info(f"✅ Отдаём из кэша: {cache_key}")
                return jsonify(cache_result)

        # Выполняем поиск через парсер (асинхронно)
        result = run_async(find_inn_by_name_structured(query, region))

        if 'error' in result:
            return jsonify({"error": result['error']}), 404

        # Формируем ответ
        organizations = []
        for org_data in result.get('ranked', []):
            org = Organization(
                name=org_data.get('name', ''),
                inn=org_data.get('inn', ''),
                ogrn=org_data.get('ogrn', ''),
                address=org_data.get('address', ''),
                status=org_data.get('status', 'active'),
                relevance=org_data.get('relevance', 0)
            )
            organizations.append(org)

        response_data = {
            "query": query,
            "total": result.get('total', 0),
            "region": region,
            "organizations": [org.to_dict() for org in organizations[:10]]
        }

        # Сохраняем в кэш
        search_cache[cache_key] = (time.time(), response_data)

        return jsonify(response_data)

    except Exception as e:
        logger.error(f"❌ Ошибка в API: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/organization/<inn>', methods=['GET'])
def get_organization(inn):
    """
    Эндпоинт для получения детальной информации об организации по ИНН
    """
    try:
        logger.info(f"🔍 Запрос организации по ИНН: {inn}")

        # TODO: Реализовать получение детальной информации
        # Пока возвращаем заглушку

        mock_org = {
            "name": f"Организация с ИНН {inn}",
            "inn": inn,
            "ogrn": f"1{inn}",
            "address": "г. Москва, ул. Примерная, д. 1",
            "status": "active",
            "kpp": "770101001",
            "director": "Иванов И.И.",
            "okved": "70.10 - Деятельность головных офисов"
        }

        return jsonify(mock_org)

    except Exception as e:
        logger.error(f"❌ Ошибка получения организации: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/history/<int:user_id>', methods=['GET'])
def get_history(user_id):
    """
    Эндпоинт для получения истории поиска пользователя
    """
    try:
        # TODO: Подключить реальную БД для истории
        mock_history = [
            {"query": "ООО Ромашка", "timestamp": "2026-03-10T10:30:00"},
            {"query": "ИП Иванов", "timestamp": "2026-03-10T09:15:00"},
            {"query": "Яндекс", "timestamp": "2026-03-09T18:20:00"}
        ]

        return jsonify(mock_history)

    except Exception as e:
        logger.error(f"❌ Ошибка получения истории: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Проверка, что сервер работает"""
    return jsonify({"status": "ok", "service": "burokrat-api"})


def run_server(host='0.0.0.0', port=5000, debug=False):
    """Запускает Flask сервер"""
    logger.info(f"🚀 Запуск API сервера на {host}:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    run_server(debug=True)