"""
Простой HTTP-сервер для VK Mini App
Запускается отдельно от Telegram-бота
"""

import json
import asyncio
import logging
from aiohttp import web
from bot.parsers.gos_zakupki_parser import GosZakupkiParser

from aiohttp import web
from aiohttp.web import middleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаём экземпляр парсера
parser = GosZakupkiParser()


@middleware
async def cors_middleware(request, handler):
    """CORS middleware для работы с VK Mini App"""
    # Обрабатываем preflight запросы
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',  # В продакшене замени на конкретный домен
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-User-ID',
            'Access-Control-Allow-Credentials': 'true',
        }
        return web.Response(status=200, headers=headers)

    # Обрабатываем обычные запросы
    response = await handler(request)

    # Добавляем CORS заголовки к ответу
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Credentials'] = 'true'

    return response


# Добавь middleware при создании приложения
app = web.Application(middlewares=[cors_middleware])

async def handle_search(request):
    """
    Обработчик поиска контрактов по ИНН
    POST /api/search
    {"inn": "472100471235"}
    """
    try:
        # Получаем данные из запроса
        data = await request.json()
        inn = data.get('inn', '').strip()

        if not inn:
            return web.json_response({'error': 'ИНН не указан'}, status=400)

        logger.info(f"🔍 Поиск контрактов для ИНН: {inn}")

        # Запускаем парсинг (он может быть долгим)
        result = await asyncio.to_thread(parser.search_by_supplier_inn, inn)

        if not result.get('success'):
            return web.json_response({
                'success': False,
                'error': result.get('error', 'Ошибка при поиске')
            })

        # Форматируем контракты
        contracts = []
        for c in result.get('contracts', []):
            contracts.append({
                'number': c.get('number', ''),
                'status': c.get('status', ''),
                'price': c.get('price', ''),
                'customer': c.get('customer', ''),
                'object': c.get('object', ''),
                'url': c.get('url', ''),
                'publish_date': c.get('publish_date', ''),
                'update_date': c.get('update_date', '')
            })

        response_data = {
            'success': True,
            'contracts': contracts,
            'total': result.get('total', 0)
        }

        logger.info(f"✅ Найдено контрактов: {len(contracts)}")
        return web.json_response(response_data)

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return web.json_response({'success': False, 'error': str(e)}, status=500)


async def health_check(request):
    """Проверка работоспособности сервера"""
    return web.json_response({'status': 'ok', 'service': 'Burokrat HTTP API'})


# Создаём приложение
app = web.Application()
app.router.add_post('/api/search', handle_search)
app.router.add_get('/', health_check)


async def main():
    """Запуск сервера"""
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("🚀 HTTP-сервер запущен на порту 8080")
    logger.info("📡 Эндпоинт: POST /api/search")
    logger.info("🏥 Health check: GET /")

    # Держим сервер работающим
    await asyncio.Event().wait()


if __name__ == '__main__':
    asyncio.run(main())
