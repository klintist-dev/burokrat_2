from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from aiogram.utils.formatting import Text, Bold, Italic
import os
import asyncio
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.keyboards_inline import (
    get_main_inline_keyboard,
    get_cancel_inline_keyboard,
    get_document_types_keyboard,
    get_back_inline_keyboard,
    get_pagination_keyboard,
    get_documents_keyboard,
    get_back_to_contracts_keyboard,
    get_contract_details_keyboard,
    get_export_keyboard,
    get_back_to_contract_details_keyboard
)

from bot.states import user_states, user_data
from bot.handlers.buttons import (
    send_goszakupki_page,
    format_contract_details,
    handle_contracts_search,
    process_search_type,
    new_search,
    back_to_main_menu
)

from aiogram.fsm.context import FSMContext

from bot.services.exports.export_service import ExportService
import os

import logging

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "menu_find_inn")
async def callback_find_inn(callback: CallbackQuery):
    """Поиск ИНН по названию"""
    await callback.answer()
    user_id = callback.from_user.id
    user_states[user_id] = "name_step1"

    content = Text(
        Bold("🔍 Поиск ИНН по названию"), "\n\n",
        "Введите **название организации** (ЮЛ, ИП или физического лица):\n\n",
        Italic("Например: ООО Ромашка, ИП Иванов, Яндекс, Сбербанк")
    )
    await callback.message.answer(**content.as_kwargs())


@router.callback_query(F.data == "menu_extract")
async def callback_extract(callback: CallbackQuery):
    """Выписка из ЕГРЮЛ"""
    await callback.answer()
    user_id = callback.from_user.id
    user_states[user_id] = "extract"

    await callback.message.answer(
        "📄 <b>Получение выписки из ЕГРЮЛ</b>\n\n"
        "Введите <b>ИНН организации</b>, и я пришлю ссылку на официальную выписку.\n\n"
        "<i>Например: 4707013298, 7707083893</i>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "menu_ask")
async def callback_ask(callback: CallbackQuery):
    """Вопрос GigaChat"""
    await callback.answer()
    user_id = callback.from_user.id
    user_states[user_id] = "ask"

    content = Text(
        Bold("💬 Задать вопрос GigaChat"), "\n\n",
        "Задайте любой вопрос. Я постараюсь помочь.\n\n",
        Italic("Например: Что такое ОКВЭД? Как составить договор?")
    )
    await callback.message.answer(**content.as_kwargs())


@router.callback_query(F.data == "menu_doc")
async def callback_doc(callback: CallbackQuery):
    """Составление документа"""
    await callback.answer()
    user_id = callback.from_user.id
    user_states[user_id] = "doc"

    content = Text(
        Bold("✍️ Составить документ"), "\n\n",
        "Опишите, какой документ вам нужен, и я помогу его составить.\n\n",
        Italic("Например: заявление на отпуск, претензия в магазин, договор аренды")
    )
    await callback.message.answer(**content.as_kwargs())


@router.callback_query(F.data == "menu_help")
async def callback_help(callback: CallbackQuery):
    """Помощь"""
    await callback.answer()

    await callback.message.answer(
        "❓ <b>Помощь</b>\n\n"
        "Я умею:\n"
        "🔍 <b>Найти ИНН по названию</b>\n"
        "📄 <b>Получить выписку из ЕГРЮЛ</b>\n"
        "🔍 <b>Поиск контрактов на Госзакупках</b> (поставщик или заказчик)\n"
        "💬 <b>Отвечать на вопросы</b> (GigaChat)\n"
        "✍️ <b>Составлять документы</b> (GigaChat)\n"
        "🏛 <b>Искать контракты в госзакупках</b>\n\n"
        "Выберите нужную кнопку в меню ниже.",
        parse_mode="HTML",
        reply_markup=get_main_inline_keyboard()
    )


# ==================== ОБРАБОТЧИКИ ДЛЯ ПОИСКА КОНТРАКТОВ ====================

@router.callback_query(F.data == "menu_goszakupki")
async def callback_goszakupki(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки '🏛 Поиск в госзакупках'"""
    user_id = callback.from_user.id
    print(f"🔧 Нажата кнопка menu_goszakupki для user_id={user_id}")
    await callback.answer()

    # Передаём user_id и callback.message
    await handle_contracts_search(callback.message, state, user_id)


@router.callback_query(F.data.in_(["search_supplier", "search_customer", "search_cancel"]))
async def search_type_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора типа поиска (Поставщик/Заказчик)"""
    await callback.answer()
    from bot.handlers.buttons import process_search_type
    await process_search_type(callback, state)


@router.callback_query(F.data == "new_search")
async def new_search_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки '🔍 Новый поиск'"""
    await callback.answer()
    from bot.handlers.buttons import new_search
    await new_search(callback, state)


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки '🏠 Главное меню'"""
    await callback.answer()
    from bot.handlers.buttons import back_to_main_menu
    await back_to_main_menu(callback, state)


# ==================== ОСТАЛЬНЫЕ ОБРАБОТЧИКИ (БЕЗ ИЗМЕНЕНИЙ) ====================

@router.callback_query(F.data.startswith("download_doc_"))
async def callback_download_document(callback: CallbackQuery):
    """Отправляет ссылку на документ (без скачивания)"""
    await callback.answer()

    parts = callback.data.split("_")
    contract_index = int(parts[2])
    doc_index = int(parts[3]) - 1

    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    current_contract = user_data_dict.get('current_contract', {})
    details = current_contract.get('details', {})
    documents = details.get('documents', [])

    if not documents or doc_index < 0 or doc_index >= len(documents):
        await callback.message.answer(
            "❌ Документ не найден",
            reply_markup=get_back_to_contracts_keyboard()
        )
        return

    doc = documents[doc_index]
    doc_url = doc.get('url')
    doc_title = doc.get('title', 'Документ')
    doc_type = doc.get('type', 'unknown')
    source_tab = doc.get('source_tab', '')

    if not doc_url:
        await callback.message.answer(
            "❌ Ссылка на документ отсутствует",
            reply_markup=get_back_to_contracts_keyboard()
        )
        return

    doc_icon = {
        'PDF': '📕',
        'RAR': '📦',
        'XML': '📄',
        'HTML': '🌐',
        'unknown': '📎'
    }.get(doc_type, '📎')

    text = (
        f"{doc_icon} <b>{doc_title}</b>\n\n"
        f"📂 Раздел: {source_tab}\n"
        f"📋 Тип: {doc_type}\n\n"
        f"🔗 <b>Ссылка для скачивания:</b>\n"
        f"<code>{doc_url}</code>\n\n"
        f"⚠️ <i>Ссылка действительна ограниченное время</i>"
    )

    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_back_to_contracts_keyboard(),
        disable_web_page_preview=True
    )


@router.callback_query(F.data == "back_to_contracts")
async def callback_back_to_contracts(callback: CallbackQuery):
    """Возврат к списку контрактов"""
    await callback.answer()

    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    page = user_data_dict.get('goszakupki_page', 1)

    if user_id in user_data and 'current_contract' in user_data[user_id]:
        del user_data[user_id]['current_contract']

    await send_goszakupki_page(callback.message, user_id)


@router.callback_query(F.data == "back_to_contract_details")
async def callback_back_to_details(callback: CallbackQuery):
    """Возврат к деталям контракта"""
    await callback.answer()

    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    current_contract = user_data_dict.get('current_contract', {})

    index = current_contract.get('index', 1)
    details = current_contract.get('details', {})

    if not details:
        await callback.message.answer(
            "❌ Данные устарели",
            reply_markup=get_main_inline_keyboard()
        )
        return

    text = format_contract_details(details, index)
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_documents_keyboard(details.get('documents', []), index, current_tab='all')
    )


@router.callback_query(F.data.startswith("goszakupki_page_"))
async def callback_goszakupki_page(callback: CallbackQuery):
    """Переключение страниц госзакупок"""
    await callback.answer()

    user_id = callback.from_user.id
    page = int(callback.data.split("_")[-1])
    logger.info(f"📄 Переключение на страницу {page}")

    if user_id not in user_data or 'goszakupki_results' not in user_data[user_id]:
        await callback.message.answer(
            "❌ Данные устарели. Начните поиск заново.",
            reply_markup=get_main_inline_keyboard()
        )
        return

    user_data[user_id]['goszakupki_page'] = page
    await send_goszakupki_page(callback.message, user_id)


@router.callback_query(F.data.startswith("contract_details_"))
async def callback_contract_details(callback: CallbackQuery):
    """Показывает детали контракта"""
    await callback.answer("🔍 Загружаю детали контракта...")

    user_id = callback.from_user.id
    contract_index = int(callback.data.split("_")[-1])

    logger.info(f"📄 Загрузка деталей контракта #{contract_index} для user_id={user_id}")

    user_data_dict = user_data.get(user_id, {})
    results = user_data_dict.get('goszakupki_results', {})
    contracts = results.get('contracts', [])

    if contract_index < 1 or contract_index > len(contracts):
        await callback.message.answer("❌ Контракт не найден")
        return

    contract = contracts[contract_index - 1]
    contract_url = contract.get('url')

    if not contract_url:
        await callback.message.answer("❌ Ссылка на контракт отсутствует")
        return

    wait_msg = await callback.message.answer(
        "⏳ Загружаю детали контракта...\n"
        "<i>Это может занять несколько секунд</i>",
        parse_mode="HTML"
    )

    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['pending_contract'] = {
        'url': contract_url,
        'index': contract_index
    }

    asyncio.create_task(
        process_contract_details(
            callback.message,
            user_id,
            wait_msg.message_id
        )
    )


@router.callback_query(F.data.startswith("tab_"))
async def callback_switch_tab(callback: CallbackQuery):
    """Переключение между вкладками документов"""
    await callback.answer()

    parts = callback.data.split("_")
    if len(parts) < 3:
        logger.error(f"Неправильный формат tab_ callback: {callback.data}")
        return

    contract_index = int(parts[1])
    tab_name = parts[2]

    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    current_contract = user_data_dict.get('current_contract', {})

    if not current_contract or 'details' not in current_contract:
        await callback.message.answer(
            "❌ Сначала загрузите детали контракта",
            reply_markup=get_back_to_contracts_keyboard()
        )
        return

    details = current_contract.get('details', {})

    docs_by_tab = details.get('documents_by_tab', {})
    tab_mapping = {
        'Вложения': 'attachments',
        'Исполнение': 'execution',
        'Платежи': 'payments'
    }

    tab_key = tab_mapping.get(tab_name)
    if tab_key and tab_key not in docs_by_tab:
        logger.warning(f"Вкладка {tab_name} не найдена в documents_by_tab")
        await callback.answer(f"Вкладка {tab_name} пуста", show_alert=False)
        return

    current_tab = current_contract.get('current_tab', 'all')

    if current_tab == tab_name:
        logger.debug(f"Вкладка {tab_name} уже активна, ничего не меняем")
        await callback.answer(f"Вы уже на вкладке {tab_name}", show_alert=False)
        return

    if user_id not in user_data:
        user_data[user_id] = {}
    if 'current_contract' not in user_data[user_id]:
        user_data[user_id]['current_contract'] = {}
    user_data[user_id]['current_contract']['current_tab'] = tab_name

    text = format_contract_details(details, contract_index, current_tab=tab_name)
    keyboard = get_documents_keyboard(
        details.get('documents', []),
        contract_index,
        current_tab=tab_name
    )

    try:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        logger.info(f"✅ Переключился на вкладку {tab_name} для контракта #{contract_index}")
    except Exception as e:
        if "message is not modified" in str(e):
            logger.info(f"⚠️ Сообщение не изменилось (уже на вкладке {tab_name})")
            await callback.answer(f"Вы уже на вкладке {tab_name}", show_alert=False)
        else:
            logger.error(f"❌ Ошибка при редактировании: {e}")
            await callback.message.answer(
                text,
                parse_mode="HTML",
                reply_markup=keyboard
            )


@router.callback_query(F.data.startswith("copy_link_"))
async def callback_copy_link(callback: CallbackQuery):
    """Копирует ссылку в буфер обмена (через сообщение)"""
    await callback.answer()

    link_part = callback.data.replace("copy_link_", "")

    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    current_contract = user_data_dict.get('current_contract', {})
    details = current_contract.get('details', {})

    await callback.message.answer(
        "📋 Скопируйте ссылку:\n\n"
        f"<code>{link_part}</code>",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "show_export_menu")
async def callback_show_export_menu(callback: CallbackQuery):
    """Показывает меню экспорта"""
    await callback.answer()

    await callback.message.answer(
        "📊 <b>Экспорт данных</b>\n\n"
        "Выберите формат для экспорта найденных контрактов:\n\n"
        "• <b>Excel</b> - с группировкой по годам\n"
        "• <b>CSV</b> - простой табличный формат\n"
        "• <b>TXT</b> - детальная информация\n"
        "• <b>Все форматы</b> - сразу все варианты",
        parse_mode="HTML",
        reply_markup=get_export_keyboard()
    )


@router.callback_query(F.data == "export_excel")
async def callback_export_excel(callback: CallbackQuery):
    """Экспорт в Excel"""
    await callback.answer("⏳ Формирую Excel файл...")

    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    results = user_data_dict.get('goszakupki_results', {})
    contracts = results.get('contracts', [])

    if not contracts:
        await callback.message.answer("❌ Нет контрактов для экспорта")
        return

    wait_msg = await callback.message.answer("📊 Создаю Excel файл...")

    try:
        export_service = ExportService(user_id)
        filepath = await export_service.export_contracts_to_excel(contracts)

        document = FSInputFile(filepath)
        await callback.message.answer_document(
            document,
            caption=f"✅ Экспортировано контрактов: {len(contracts)}\n"
                    f"📊 Формат: Excel\n"
                    f"📁 Сгруппировано по годам",
            reply_markup=get_main_inline_keyboard()
        )

        export_service.cleanup_old_files()

    except Exception as e:
        logger.error(f"❌ Ошибка Excel экспорта: {e}")
        await callback.message.answer(
            f"❌ Ошибка при создании файла: {str(e)[:200]}",
            reply_markup=get_main_inline_keyboard()
        )
    finally:
        try:
            os.remove(filepath)
        except:
            pass
        await wait_msg.delete()


@router.callback_query(F.data == "export_csv")
async def callback_export_csv(callback: CallbackQuery):
    """Экспорт в CSV"""
    await callback.answer("⏳ Формирую CSV файл...")

    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    results = user_data_dict.get('goszakupki_results', {})
    contracts = results.get('contracts', [])

    if not contracts:
        await callback.message.answer("❌ Нет контрактов для экспорта")
        return

    wait_msg = await callback.message.answer("📊 Создаю CSV файл...")

    try:
        export_service = ExportService(user_id)
        filepath = await export_service.export_contracts_to_csv(contracts)

        document = FSInputFile(filepath)
        await callback.message.answer_document(
            document,
            caption=f"✅ Экспортировано контрактов: {len(contracts)}\n"
                    f"📄 Формат: CSV",
            reply_markup=get_main_inline_keyboard()
        )

        export_service.cleanup_old_files()

    except Exception as e:
        logger.error(f"❌ Ошибка CSV экспорта: {e}")
        await callback.message.answer(
            f"❌ Ошибка при создании файла: {str(e)[:200]}",
            reply_markup=get_main_inline_keyboard()
        )
    finally:
        try:
            os.remove(filepath)
        except:
            pass
        await wait_msg.delete()


@router.callback_query(F.data == "export_all")
async def callback_export_all(callback: CallbackQuery):
    """Экспорт во все форматы сразу"""
    await callback.answer("⏳ Формирую все форматы...")

    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    results = user_data_dict.get('goszakupki_results', {})
    contracts = results.get('contracts', [])

    if not contracts:
        await callback.message.answer("❌ Нет контрактов для экспорта")
        return

    wait_msg = await callback.message.answer(
        "📊 Создаю файлы в разных форматах...\n"
        "<i>Это может занять несколько секунд</i>",
        parse_mode="HTML"
    )

    try:
        export_service = ExportService(user_id)

        excel_file = await export_service.export_contracts_to_excel(contracts)
        csv_file = await export_service.export_contracts_to_csv(contracts)

        await callback.message.answer_document(
            FSInputFile(excel_file),
            caption="📊 Excel формат (с группировкой по годам)"
        )

        await callback.message.answer_document(
            FSInputFile(csv_file),
            caption="📄 CSV формат (табличные данные)"
        )

        await callback.message.answer(
            "✅ Все файлы отправлены!",
            reply_markup=get_main_inline_keyboard()
        )

        export_service.cleanup_old_files()

    except Exception as e:
        logger.error(f"❌ Ошибка экспорта: {e}")
        await callback.message.answer(
            f"❌ Ошибка при создании файлов: {str(e)[:200]}",
            reply_markup=get_main_inline_keyboard()
        )
    finally:
        try:
            os.remove(excel_file)
            os.remove(csv_file)
        except:
            pass
        await wait_msg.delete()


@router.callback_query(F.data.startswith("export_contract_txt_"))
async def callback_export_contract_txt(callback: CallbackQuery):
    """Экспорт деталей конкретного контракта в TXT"""
    await callback.answer("⏳ Формирую файл...")

    contract_index = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id

    user_data_dict = user_data.get(user_id, {})
    current_contract = user_data_dict.get('current_contract', {})
    details = current_contract.get('details', {})

    if not details:
        await callback.message.answer("❌ Детали контракта не найдены")
        return

    wait_msg = await callback.message.answer("📑 Создаю текстовый файл с деталями...")

    try:
        export_service = ExportService(user_id)
        filepath = await export_service.export_contract_details_to_txt(details, contract_index)

        document = FSInputFile(filepath)
        await callback.message.answer_document(
            document,
            caption=f"✅ Детали контракта #{contract_index}",
            reply_markup=get_back_to_contract_details_keyboard()
        )

        export_service.cleanup_old_files()

    except Exception as e:
        logger.error(f"❌ Ошибка TXT экспорта: {e}")
        await callback.message.answer(
            f"❌ Ошибка: {str(e)[:200]}",
            reply_markup=get_back_to_contract_details_keyboard()
        )
    finally:
        try:
            os.remove(filepath)
        except:
            pass
        await wait_msg.delete()


@router.callback_query(F.data == "menu_back")
async def callback_menu_back(callback: CallbackQuery):
    """Возврат в главное меню"""
    await callback.answer()

    user_id = callback.from_user.id

    if user_id in user_states:
        del user_states[user_id]
    if user_id in user_data:
        keys_to_keep = ['statistics']
        user_data[user_id] = {k: user_data[user_id][k] for k in keys_to_keep if k in user_data[user_id]}

    content = Text(
        Bold("🏠 Главное меню"), "\n\n",
        "Выберите нужное действие:"
    )

    await callback.message.answer(
        **content.as_kwargs(),
        reply_markup=get_main_inline_keyboard()
    )


async def process_contract_details(message: Message, user_id: int, wait_msg_id: int):
    """Фоновая задача для получения деталей контракта"""
    import time
    start_time = time.time()

    loading_complete = asyncio.Event()
    progress_message = None

    try:
        async def progress_indicator():
            nonlocal progress_message
            await asyncio.sleep(5)
            if not loading_complete.is_set():
                try:
                    progress_message = await message.answer(
                        "⏳ Всё ещё загружаю детали контракта...\n"
                        "<i>Обычно это занимает 10-15 секунд</i>",
                        parse_mode="HTML"
                    )
                except:
                    pass

        asyncio.create_task(progress_indicator())

        logger.info(f"🔍 Начинаю загрузку деталей контракта для user_id={user_id}")

        user_data_dict = user_data.get(user_id, {})
        pending = user_data_dict.get('pending_contract', {})
        contract_url = pending.get('url')
        index = pending.get('index')

        if not contract_url:
            logger.error(f"❌ contract_url отсутствует для user_id={user_id}")
            await message.answer("❌ Ошибка: контракт не найден")
            return

        logger.info(f"📡 Загружаю детали с URL: {contract_url[:100]}...")
        from bot.parsers.gos_zakupki_parser import GosZakupkiParser
        parser = GosZakupkiParser()
        details = parser.get_contract_details(contract_url)

        load_time = time.time() - start_time
        logger.info(f"⏱ Детали загружены за {load_time:.2f} сек")

        loading_complete.set()

        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=wait_msg_id)
        except:
            pass

        if progress_message:
            try:
                await progress_message.delete()
            except:
                pass

        if not details.get('success'):
            logger.error(f"❌ Ошибка парсинга: {details.get('error')}")
            await message.answer(
                f"❌ Ошибка: {details.get('error', 'Неизвестная ошибка')}",
                reply_markup=get_back_to_contracts_keyboard()
            )
            return

        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['current_contract'] = {
            'index': index,
            'details': details,
            'url': contract_url,
            'current_tab': 'all'
        }

        if 'pending_contract' in user_data[user_id]:
            del user_data[user_id]['pending_contract']

        text = format_contract_details(details, index, current_tab='all')

        logger.info(f"✅ Детали контракта #{index} успешно загружены за {load_time:.2f} сек")

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_documents_keyboard(details.get('documents', []), index, current_tab='all')
        )

    except Exception as e:
        logger.error(f"❌ Ошибка в process_contract_details: {e}", exc_info=True)
        loading_complete.set()

        if progress_message:
            try:
                await progress_message.delete()
            except:
                pass

        await message.answer(
            f"❌ Произошла ошибка при загрузке деталей",
            reply_markup=get_back_to_contracts_keyboard()
        )