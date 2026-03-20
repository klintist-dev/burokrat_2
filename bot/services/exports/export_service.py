"""
Сервис для экспорта данных в различные форматы
"""
import csv
import os
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class ExportService:
    """Класс для экспорта данных"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.export_dir = f"data/exports/{user_id}"
        self._ensure_export_dir()
    
    def _ensure_export_dir(self):
        """Создаёт папку для экспорта, если её нет"""
        os.makedirs(self.export_dir, exist_ok=True)
    
    def _generate_filename(self, prefix: str, extension: str) -> str:
        """Генерирует имя файла с датой и временем"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{self.export_dir}/{prefix}_{timestamp}.{extension}"
    
    async def export_contracts_to_csv(self, contracts: List[Dict]) -> str:
        """
        Экспорт списка контрактов в CSV
        Возвращает путь к файлу
        """
        filename = self._generate_filename("contracts", "csv")
        
        headers = [
            'Номер контракта', 'Статус', 'Цена', 
            'Заказчик', 'ИНН заказчика', 'Поставщик', 'ИНН поставщика',
            'Дата заключения', 'Дата исполнения', 'Объект закупки', 'Ссылка'
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)
                
                for contract in contracts:
                    writer.writerow([
                        contract.get('number', ''),
                        contract.get('status', ''),
                        contract.get('price', ''),
                        contract.get('customer', {}).get('name', ''),
                        contract.get('customer', {}).get('inn', ''),
                        contract.get('supplier', {}).get('name', ''),
                        contract.get('supplier', {}).get('inn', ''),
                        contract.get('dates', {}).get('conclusion', ''),
                        contract.get('dates', {}).get('execution', ''),
                        contract.get('object', ''),
                        contract.get('url', '')
                    ])
            
            logger.info(f"✅ CSV экспорт создан: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Ошибка CSV экспорта: {e}")
            raise
    
    async def export_contracts_to_excel(self, contracts: List[Dict]) -> str:
        """
        Экспорт контрактов в Excel с группировкой по годам
        """
        filename = self._generate_filename("contracts", "xlsx")
        
        try:
            # Группируем контракты по годам
            contracts_by_year = {}
            for contract in contracts:
                # Получаем год из даты заключения
                date_str = contract.get('dates', {}).get('conclusion', '')
                year = 'Без даты'
                
                if date_str and '.' in date_str:
                    # Формат: ДД.ММ.ГГГГ
                    year = date_str.split('.')[-1]
                elif date_str and len(date_str) == 4:
                    year = date_str
                
                if year not in contracts_by_year:
                    contracts_by_year[year] = []
                contracts_by_year[year].append(contract)
            
            # Сортируем года
            sorted_years = sorted(contracts_by_year.keys(), reverse=True)
            
            # Создаём Excel файл
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                for year in sorted_years:
                    year_contracts = contracts_by_year[year]
                    
                    # Подготавливаем данные
                    data = []
                    for c in year_contracts:
                        # Обрезаем длинные названия
                        object_text = c.get('object', '')
                        if len(object_text) > 100:
                            object_text = object_text[:97] + "..."
                        
                        data.append({
                            'Номер': c.get('number', ''),
                            'Статус': c.get('status', ''),
                            'Цена (₽)': c.get('price', '').replace('₽', '').strip(),
                            'Заказчик': c.get('customer', {}).get('name', ''),
                            'ИНН заказчика': c.get('customer', {}).get('inn', ''),
                            'Дата заключения': c.get('dates', {}).get('conclusion', ''),
                            'Дата исполнения': c.get('dates', {}).get('execution', ''),
                            'Объект': object_text
                        })
                    
                    df = pd.DataFrame(data)
                    
                    # Название листа (макс 31 символ)
                    sheet_name = str(year)[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Автоподбор ширины колонок
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"✅ Excel экспорт создан: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Ошибка Excel экспорта: {e}")
            raise
    
    async def export_contract_details_to_txt(self, details: Dict, contract_index: int) -> str:
        """
        Экспорт деталей контракта в текстовый файл
        """
        filename = self._generate_filename(f"contract_{contract_index}", "txt")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write(f"ДЕТАЛИ КОНТРАКТА #{contract_index}\n")
                f.write("=" * 60 + "\n\n")
                
                # Основная информация
                f.write(f"Номер: {details.get('number', 'Не указан')}\n")
                f.write(f"Статус: {details.get('status', 'Не указан')}\n")
                f.write(f"Цена: {details.get('price', 'Не указана')}\n\n")
                
                # Заказчик
                customer = details.get('customer', {})
                f.write("ЗАКАЗЧИК:\n")
                f.write(f"  Название: {customer.get('name', 'Не указан')}\n")
                f.write(f"  ИНН: {customer.get('inn', 'Не указан')}\n\n")
                
                # Поставщик
                supplier = details.get('supplier', {})
                if supplier:
                    f.write("ПОСТАВЩИК:\n")
                    f.write(f"  Название: {supplier.get('name', 'Не указан')}\n")
                    f.write(f"  ИНН: {supplier.get('inn', 'Не указан')}\n\n")
                
                # Даты
                dates = details.get('dates', {})
                f.write("ДАТЫ:\n")
                f.write(f"  Заключение: {dates.get('conclusion', 'Не указана')}\n")
                f.write(f"  Исполнение до: {dates.get('execution', 'Не указана')}\n\n")
                
                # Документы
                docs_by_tab = details.get('documents_by_tab', {})
                total_docs = details.get('total_documents', 0)
                
                f.write(f"ДОКУМЕНТЫ (всего: {total_docs}):\n")
                f.write("-" * 40 + "\n")
                
                for tab_name, docs in docs_by_tab.items():
                    if docs:
                        tab_display = {
                            'attachments': 'ВЛОЖЕНИЯ',
                            'execution': 'ИСПОЛНЕНИЕ',
                            'payments': 'ПЛАТЕЖИ'
                        }.get(tab_name, tab_name.upper())
                        
                        f.write(f"\n[{tab_display}] - {len(docs)} документов:\n")
                        for i, doc in enumerate(docs[:10], 1):
                            title = doc.get('title', 'Без названия')
                            doc_type = doc.get('type', 'unknown')
                            f.write(f"  {i}. {title} ({doc_type})\n")
                        
                        if len(docs) > 10:
                            f.write(f"  ... и ещё {len(docs) - 10} документов\n")
                
                f.write("\n" + "=" * 60 + "\n")
                f.write(f"Сформировано: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n")
            
            logger.info(f"✅ TXT экспорт создан: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"❌ Ошибка TXT экспорта: {e}")
            raise
    
    def cleanup_old_files(self, hours: int = 24):
        """Удаляет файлы старше N часов"""
        try:
            current_time = datetime.now().timestamp()
            for filename in os.listdir(self.export_dir):
                filepath = os.path.join(self.export_dir, filename)
                if os.path.isfile(filepath):
                    file_time = os.path.getmtime(filepath)
                    if current_time - file_time > hours * 3600:
                        os.remove(filepath)
                        logger.info(f"🗑 Удалён старый файл: {filename}")
        except Exception as e:
            logger.error(f"❌ Ошибка очистки: {e}")