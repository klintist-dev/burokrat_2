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
    get_contract_details_keyboard
)

from bot.states import user_states, user_data
from bot.handlers.buttons import send_goszakupki_page, format_contract_details

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
        "💬 <b>Отвечать на вопросы</b> (GigaChat)\n"
        "✍️ <b>Составлять документы</b> (GigaChat)\n"
        "🏛 <b>Искать контракты в госзакупках</b>\n\n"
        "Выберите нужную кнопку в меню ниже.",
        parse_mode="HTML",
        reply_markup=get_main_inline_keyboard()
    )

@router.callback_query(F.data.startswith("contract_details_"))
async def callback_contract_details(callback: CallbackQuery):
    """Показывает детальную информацию о контракте"""

    # 1. СРАЗУ отвечаем на callback
    await callback.answer()

    # Получаем индекс контракта
    index = int(callback.data.split("_")[-1])

    # Получаем данные пользователя
    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    results = user_data_dict.get('goszakupki_results', {})
    contracts = results.get('contracts', [])

    if not contracts or index < 1 or index > len(contracts):
        await callback.message.answer("❌ Контракт не найден")
        return

    # Сохраняем индекс для следующего шага
    if user_id not in user_data:
        user_data[user_id] = {}
    user_data[user_id]['pending_contract'] = {
        'index': index,
        'url': contracts[index - 1].get('url')
    }

    # 2. Показываем "печатает..." через бота
    bot = callback.bot
    await bot.send_chat_action(chat_id=callback.message.chat.id, action="typing")

    # 3. Отправляем сообщение о начале загрузки
    wait_msg = await callback.message.answer(
        "🔍 <b>Загружаю детали контракта...</b>\n"
        "<i>Это может занять 10-20 секунд</i>",
        parse_mode="HTML"
    )

    # 4. Запускаем фоновую задачу
    asyncio.create_task(process_contract_details(callback.message, user_id, wait_msg.message_id))

@router.callback_query(F.data.startswith("download_doc_"))
async def callback_download_document(callback: CallbackQuery):
    """Отправляет ссылку на документ (без скачивания)"""
    await callback.answer()

    # Парсим callback_data: download_doc_1_2
    parts = callback.data.split("_")
    contract_index = int(parts[2])
    doc_index = int(parts[3]) - 1

    # Получаем данные пользователя
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

    # Иконка для типа файла
    doc_icon = {
        'PDF': '📕',
        'RAR': '📦',
        'XML': '📄',
        'HTML': '🌐',
        'unknown': '📎'
    }.get(doc_type, '📎')

    # Создаём красивое сообщение со ссылкой
    text = (
        f"{doc_icon} <b>{doc_title}</b>\n\n"
        f"📂 Раздел: {source_tab}\n"
        f"📋 Тип: {doc_type}\n\n"
        f"🔗 <b>Ссылка для скачивания:</b>\n"
        f"<code>{doc_url}</code>\n\n"
        f"⚠️ <i>Ссылка действительна ограниченное время</i>"
    )

    # Отправляем сообщение со ссылкой
    await callback.message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_back_to_contracts_keyboard(),
        disable_web_page_preview=True  # не показываем превью ссылки
    )
@router.callback_query(F.data == "back_to_contracts")
async def callback_back_to_contracts(callback: CallbackQuery):
    """Возврат к списку контрактов"""
    await callback.answer()

    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    page = user_data_dict.get('goszakupki_page', 1)

    # Удаляем данные о текущем контракте
    if user_id in user_data and 'current_contract' in user_data[user_id]:
        del user_data[user_id]['current_contract']

    # Отправляем текущую страницу заново
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
        reply_markup=get_documents_keyboard(details.get('documents', []), index)
    )


# В bot/handlers/callbacks.py должен быть этот код:

@router.callback_query(F.data == "menu_goszakupki")
async def callback_goszakupki(callback: CallbackQuery):
    """Поиск в госзакупках"""

    # 1. СРАЗУ отвечаем на callback
    await callback.answer()

    user_id = callback.from_user.id
    user_states[user_id] = "goszakupki"

    # 2. Отправляем сообщение с просьбой ввести ИНН
    content = Text(
        Bold("🏛 Поиск в госзакупках\n\n"),
        "Введите ИНН организации-поставщика\n",
        "Я покажу все контракты, где она выступает исполнителем.\n\n",
        Italic("Например: 472100471235, 7707083893"), "\n\n",
        "Для отмены нажмите кнопку ниже"
    )

    await callback.message.answer(
        **content.as_kwargs(),
        reply_markup=get_cancel_inline_keyboard()
    )


@router.callback_query(F.data.startswith("goszakupki_page_"))
async def callback_goszakupki_page(callback: CallbackQuery):
    """Переключение страниц госзакупок"""
    await callback.answer()

    user_id = callback.from_user.id

    # Извлекаем номер страницы
    page = int(callback.data.split("_")[-1])
    logger.info(f"📄 Переключение на страницу {page}")

    # Проверяем данные
    if user_id not in user_data or 'goszakupki_results' not in user_data[user_id]:
        await callback.message.answer(
            "❌ Данные устарели. Начните поиск заново.",
            reply_markup=get_main_inline_keyboard()
        )
        return

    # Обновляем страницу
    user_data[user_id]['goszakupki_page'] = page

    # Отправляем новую страницу
    from bot.handlers.buttons import send_goszakupki_page
    await send_goszakupki_page(callback.message, user_id)


@router.callback_query(F.data.startswith("tab_"))
async def callback_switch_tab(callback: CallbackQuery):
    """Переключение между вкладками документов"""
    await callback.answer()

    # Парсим callback_data: tab_1_Вложения
    parts = callback.data.split("_")
    contract_index = int(parts[1])
    tab_name = parts[2]

    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    current_contract = user_data_dict.get('current_contract', {})
    details = current_contract.get('details', {})

    if not details:
        await callback.message.answer(
            "❌ Данные устарели",
            reply_markup=get_main_inline_keyboard()
        )
        return

    # Обновляем текущую вкладку в user_data
    if user_id not in user_data:
        user_data[user_id] = {}
    if 'current_contract' not in user_data[user_id]:
        user_data[user_id]['current_contract'] = {}
    user_data[user_id]['current_contract']['current_tab'] = tab_name

    # Формируем текст с деталями
    text = format_contract_details(details, contract_index)

    # Отправляем обновлённую клавиатуру
    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=get_documents_keyboard(
            details.get('documents', []),
            contract_index,
            current_tab=tab_name
        )
    )


@router.callback_query(F.data.startswith("copy_link_"))
async def callback_copy_link(callback: CallbackQuery):
    """Копирует ссылку в буфер обмена (через сообщение)"""
    await callback.answer()

    # Получаем ссылку из callback_data (обрезанную)
    link_part = callback.data.replace("copy_link_", "")

    # Нужно восстановить полную ссылку из user_data
    user_id = callback.from_user.id
    user_data_dict = user_data.get(user_id, {})
    current_contract = user_data_dict.get('current_contract', {})
    details = current_contract.get('details', {})

    # Отправляем сообщение со ссылкой для копирования
    await callback.message.answer(
        "📋 Скопируйте ссылку:\n\n"
        f"<code>{link_part}</code>",
        parse_mode="HTML"
    )


async def process_contract_details(message: Message, user_id: int, wait_msg_id: int):
    """Фоновая задача для получения деталей контракта"""
    try:
        # Получаем данные
        user_data_dict = user_data.get(user_id, {})
        pending = user_data_dict.get('pending_contract', {})
        contract_url = pending.get('url')
        index = pending.get('index')

        if not contract_url:
            await message.answer("❌ Ошибка: контракт не найден")
            return

        # Получаем детали через парсер
        from bot.parsers.gos_zakupki_parser import GosZakupkiParser
        parser = GosZakupkiParser()
        details = parser.get_contract_details(contract_url)

        # Удаляем сообщение о загрузке
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=wait_msg_id)
        except:
            pass

        if not details.get('success'):
            await message.answer(
                f"❌ Ошибка: {details.get('error', 'Неизвестная ошибка')}",
                reply_markup=get_back_to_contracts_keyboard()
            )
            return

        # Сохраняем детали
        if user_id not in user_data:
            user_data[user_id] = {}
        user_data[user_id]['current_contract'] = {
            'index': index,
            'details': details,
            'url': contract_url,
            'current_tab': 'all'
        }

        # Очищаем pending
        if 'pending_contract' in user_data[user_id]:
            del user_data[user_id]['pending_contract']

        # Формируем сообщение
        text = format_contract_details(details, index)

        # Отправляем результат
        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_documents_keyboard(details.get('documents', []), index, current_tab='all')
        )

    except Exception as e:
        logger.error(f"Ошибка в process_contract_details: {e}")
        await message.answer(
            f"❌ Произошла ошибка при загрузке деталей",
            reply_markup=get_back_to_contracts_keyboard()
        )