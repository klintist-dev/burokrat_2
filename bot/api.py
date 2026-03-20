"""
HTTP API для VK Mini App
Использует существующие парсеры из gos_zakupki_parser.py и nalog_parser.py
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
import logging

# Импортируем твои парсеры
from bot.parsers.gos_zakupki_parser import GosZakupkiParser
from bot.parsers.nalog_parser import (
    find_inn_by_name,
    find_inn_by_name_with_region,
    find_name_by_inn,
    get_egrul_extract,
    check_inn_valid
)

logger = logging.getLogger(__name__)

app = FastAPI(title="БюрократЪ API", description="API для парсинга ФНС и госзакупок")

# Разрешаем запросы из VK Mini Apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для теста, позже ограничим доменами VK
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаём экземпляр парсера госзакупок один раз при старте
gos_parser = GosZakupkiParser()


# ========== МОДЕЛИ ДАННЫХ ==========

class SearchRequest(BaseModel):
    inn: str


class ContractResponse(BaseModel):
    number: str
    status: str
    price: str
    customer: str
    object: str
    url: str
    publish_date: Optional[str] = None
    update_date: Optional[str] None


class SearchResponse(BaseModel):
    success: bool
    contracts: List[ContractResponse] = []
    total: int = 0
    error: Optional[str] = None


class InnSearchRequest(BaseModel):
    name: str
    region: Optional[str] = None


class InnSearchResponse(BaseModel):
    success: bool
    result: Optional[str] = None
    error: Optional[str] = None


class EgrulResponse(BaseModel):
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class ContractDetailsResponse(BaseModel):
    success: bool
    details: Optional[dict] = None
    error: Optional[str] = None


# ========== ЭНДПОИНТЫ ==========

@app.get("/")
async def root():
    return {"status": "ok", "service": "Burokrat API", "version": "1.0"}


@app.post("/api/search", response_model=SearchResponse)
async def search_contracts(request: SearchRequest):
    """
    Поиск контрактов по ИНН поставщика
    """
    try:
        logger.info(f"🔍 Поиск контрактов для ИНН: {request.inn}")

        # Вызываем существующую функцию парсера госзакупок
        result = gos_parser.search_by_supplier_inn(request.inn)

        if not result.get('success'):
            return SearchResponse(
                success=False,
                error=result.get('error', 'Ошибка при поиске')
            )

        # Преобразуем контракты в нужный формат
        contracts = []
        for c in result.get('contracts', []):
            contracts.append(ContractResponse(
                number=c.get('number', ''),
                status=c.get('status', ''),
                price=c.get('price', ''),
                customer=c.get('customer', ''),
                object=c.get('object', ''),
                url=c.get('url', ''),
                publish_date=c.get('publish_date', ''),
                update_date=c.get('update_date', '')
            ))

        return SearchResponse(
            success=True,
            contracts=contracts,
            total=result.get('total', 0)
        )

    except Exception as e:
        logger.error(f"❌ Ошибка при поиске: {e}")
        return SearchResponse(success=False, error=str(e))


@app.post("/api/contract/details", response_model=ContractDetailsResponse)
async def get_contract_details(request: dict):
    """
    Получение детальной информации о контракте (документы, вкладки)
    Ожидает: {"url": "https://zakupki.gov.ru/..."}
    """
    try:
        contract_url = request.get('url')
        if not contract_url:
            return ContractDetailsResponse(success=False, error="URL не указан")

        logger.info(f"🔍 Получение деталей контракта: {contract_url}")

        details = gos_parser.get_contract_details(contract_url)

        if not details.get('success'):
            return ContractDetailsResponse(
                success=False,
                error=details.get('error', 'Ошибка при получении деталей')
            )

        return ContractDetailsResponse(success=True, details=details)

    except Exception as e:
        logger.error(f"❌ Ошибка при получении деталей: {e}")
        return ContractDetailsResponse(success=False, error=str(e))


@app.post("/api/find_inn", response_model=InnSearchResponse)
async def find_inn(request: InnSearchRequest):
    """
    Поиск ИНН по названию организации
    """
    try:
        logger.info(f"🔍 Поиск ИНН для: {request.name}")

        if request.region:
            result = await find_inn_by_name_with_region(request.name, request.region)
        else:
            result = await find_inn_by_name(request.name)

        return InnSearchResponse(success=True, result=result)

    except Exception as e:
        logger.error(f"❌ Ошибка при поиске ИНН: {e}")
        return InnSearchResponse(success=False, error=str(e))


@app.post("/api/find_by_inn", response_model=InnSearchResponse)
async def find_organization_by_inn(request: SearchRequest):
    """
    Поиск организации по ИНН
    """
    try:
        logger.info(f"🔍 Поиск организации по ИНН: {request.inn}")

        result = await find_name_by_inn(request.inn)

        return InnSearchResponse(success=True, result=result)

    except Exception as e:
        logger.error(f"❌ Ошибка при поиске: {e}")
        return InnSearchResponse(success=False, error=str(e))


@app.post("/api/egrul", response_model=EgrulResponse)
async def get_egrul(request: SearchRequest):
    """
    Получение выписки из ЕГРЮЛ по ИНН
    """
    try:
        logger.info(f"📄 Получение выписки для ИНН: {request.inn}")

        result = await get_egrul_extract(request.inn)

        if isinstance(result, dict) and result.get('error'):
            return EgrulResponse(success=False, error=result['error'])

        return EgrulResponse(success=True, data=result)

    except Exception as e:
        logger.error(f"❌ Ошибка при получении выписки: {e}")
        return EgrulResponse(success=False, error=str(e))


@app.post("/api/check_inn")
async def check_inn(request: SearchRequest):
    """
    Проверка ИНН на действительность
    """
    try:
        logger.info(f"🔍 Проверка ИНН: {request.inn}")

        result = await check_inn_valid(request.inn)

        return {"success": True, "result": result}

    except Exception as e:
        logger.error(f"❌ Ошибка при проверке ИНН: {e}")
        return {"success": False, "error": str(e)}


# Для запуска напрямую
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)