# БюрократЪ 2.0 — Полная документация для новичков

> 📚 **Для кого этот документ**: для студентов первого курса, которые только начинают изучать программирование и хотят понять, как работает Telegram-бот.

## 📋 Содержание

1. [Введение: что такое Telegram-бот?](#1-введение-что-такое-telegram-бот)
2. [Структура проекта](#2-структура-проекта)
3. [Файл `config_reader.py` — секреты и настройки](#3-файл-config_readerpy--секреты-и-настройки)
4. [Файл `keyboards.py` — кнопки для пользователя](#4-файл-keyboardspy--кнопки-для-пользователя)
5. [Папка `handlers/` — обработчики команд](#5-папка-handlers--обработчики-команд)
6. [Файл `start.py` — команда /start](#6-файл-startpy--команда-start)
7. [Файл `buttons.py` — логика всех кнопок](#7-файл-buttonspy--логика-всех-кнопок)
8. [Папка `parsers/` — парсинг сайтов](#8-папка-parsers--парсинг-сайтов)
9. [Файл `nalog_parser.py` — работа с сайтом ФНС (самое сложное!)](#9-файл-nalog_parserpy--работа-с-сайтом-фнс-самое-сложное)
10. [Папка `services/` — внешние сервисы](#10-папка-services--внешние-сервисы)
11. [Файл `gigachat.py` — работа с GigaChat](#11-файл-gigachatpy--работа-с-gigachat)
12. [Git: как мы сохраняли код](#12-git-как-мы-сохраняли-код)
13. [Railway: как бот попал в интернет](#13-railway-как-бот-попал-в-интернет)
14. [Словарь терминов для новичка](#14-словарь-терминов-для-новичка)

---

## 1. Введение: что такое Telegram-бот?

### 🤔 Простыми словами

Telegram-бот — это программа, которая живёт не на твоём компьютере, а где-то в интернете (на сервере). Ты пишешь ей сообщения, а она отвечает.

**Как это работает:**
1. Ты нажимаешь кнопку в боте → Telegram отправляет сигнал на сервер, где живёт бот
2. Сервер обрабатывает твоё сообщение (например, ищет ИНН на сайте ФНС)
3. Бот отправляет ответ обратно в Telegram

### 🧠 Аналогия для понимания

Представь, что бот — это твой друг, который сидит в библиотеке:
- Ты пишешь ему: "Найди книгу про Гарри Поттера" (это твой запрос)
- Друг идёт по библиотеке, ищет книгу (это обработка)
- Возвращается и говорит: "Вот она, на 3-й полке" (это ответ)

### ⚡ Почему бот не зависает (асинхронность)

В коде ты часто видишь слово `async` (асинхронно). Это значит, что бот может делать несколько дел одновременно.

Пример:
- Пока бот ждёт ответ от сайта ФНС (это может занять 10-20 секунд)
- Он уже отвечает другим пользователям
- Как только ответ пришёл — бот сразу возвращается к первому пользователю

Без асинхронности бот зависал бы на каждом запросе и не мог бы обслуживать несколько человек сразу.

---

## 2. Структура проекта

Вот как организованы файлы в твоём проекте:
burokrat_2/ # Корневая папка проекта
│
├── .env # СЕКРЕТНО! Токены бота (не в git!)
├── .env.example # Пример, как должен выглядеть .env
├── .gitignore # Какие файлы НЕ отправлять в GitHub
├── requirements.txt # Список библиотек, нужных боту
├── Procfile # Инструкция для Railway, как запускать
├── runtime.txt # Какая версия Python нужна
│
└── bot/ # Основная папка с кодом бота
│
├── init.py # Пустой файл, говорит Python: "это папка с кодом"
├── main.py # Запуск бота (точка входа)
├── config_reader.py # Читает токены из .env
├── keyboards.py # Кнопки для Telegram
│
├── handlers/ # Обработчики команд
│ ├── init.py
│ ├── start.py # Команда /start
│ └── buttons.py # Все остальные кнопки
│
├── parsers/ # Парсеры (достают данные с сайтов)
│ ├── init.py
│ └── nalog_parser.py # Работа с сайтом ФНС (ЕГРЮЛ)
│
└── services/ # Внешние сервисы
├── init.py
└── gigachat.py # Работа с GigaChat


### 🔍 Что означают папки:

| Папка | Что там лежит | Зачем |
|-------|---------------|-------|
| `handlers/` | Обработчики | Реагируют на команды пользователя |
| `parsers/` | Парсеры | "Парсят" (разбирают) сайты, чтобы достать информацию |
| `services/` | Сервисы | Работа с внешними API (GigaChat) |

---

## 3. Файл `config_reader.py` — секреты и настройки

Этот файл отвечает за чтение **токенов** и **настроек** из файла `.env`. Почему нельзя просто написать токен в коде? Потому что тогда любой, кто увидит код, сможет украсть твоего бота!

### 📝 Код с пояснениями

```python
# ⬇️ Pydantic — библиотека для работы с данными. SecretStr — тип "секретная строка"
from pydantic import SecretStr

# ⬇️ BaseSettings — читает настройки из .env автоматически
from pydantic_settings import BaseSettings

# ⬇️ lru_cache — запоминает результат функции, чтобы не читать .env каждый раз
from functools import lru_cache

class BotConfig(BaseSettings):
    """
    Класс с настройками бота.
    Когда создаётся объект этого класса, он сам читает переменные из .env
    """
    
    token: SecretStr  
    # ⬆️ Токен бота (секрет!). SecretStr значит, что при печати будет показывать '********'
    
    admin_id: int  
    # ⬆️ Твой Telegram ID (чтобы бот знал админа). Нужен для статистики
    
    bot_name: str = "БюрократЪ 2.0"  
    # ⬆️ Имя бота (можно поменять). Если не указано в .env, будет "БюрократЪ 2.0"
    
    debug: bool = False  
    # ⬆️ Режим отладки. Если True — будет печатать больше информации
    
    gigachat_api_key: SecretStr  
    # ⬆️ Ключ для GigaChat (тоже секрет!)

    class Config:
        """
        Внутренний класс с настройками самого конфига
        """
        env_file = ".env"  
        # ⬆️ Где лежат секреты (в файле .env в корне проекта)
        
        env_prefix = "BOT_"  
        # ⬆️ Все переменные начинаются с BOT_. 
        # Значит в .env должно быть BOT_TOKEN, BOT_ADMIN_ID и т.д.
        
        env_file_encoding = "utf-8"  
        # ⬆️ Кодировка файла (чтобы русские буквы читались)


@lru_cache  # ⬅️ Декоратор. Запоминает результат функции после первого вызова
def get_config() -> BotConfig:
    """
    Возвращает конфиг (объект с настройками).
    lru_cache гарантирует, что функция выполнится только 1 раз,
    а потом будет возвращать сохранённый результат.
    Это экономит время и ресурсы.
    """
    return BotConfig()  
    # ⬆️ Создаём объект класса BotConfig. 
    # При создании он сам прочитает .env и заполнит поля

🧠 Что здесь происходит простыми словами:

    class BotConfig(BaseSettings): — мы создаём "коробку" с настройками. В этой коробке будут лежать: токен, admin_id, ключ GigaChat и т.д.

    token: SecretStr — говорим: "в коробке есть отделение для токена, и оно секретное"

    env_prefix = "BOT_" — говорим: "когда будешь читать .env, ищи переменные, которые начинаются с BOT_"

    @lru_cache — "запомни результат, чтобы не читать файл каждый раз"

🔐 Почему токены нельзя хранить в коде?

Представь, что ты написал токен прямо в коде и выложил на GitHub. Любой может:

    Найти твоего бота

    Узнать токен

    Угнать бота (менять команды, отправлять спам)

Поэтому мы храним токены в .env, а сам .env — в .gitignore (чтобы не попадал в git).

4. Файл keyboards.py — кнопки для пользователя

Этот файл создаёт клавиатуру — те самые кнопки, которые видит пользователь внизу экрана.
📝 Код с пояснениями

# ⬇️ Импортируем типы для создания клавиатуры из библиотеки aiogram
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# ⬇️ Создаём каждую кнопку отдельно
# KeyboardButton — это одна кнопка
# В скобках пишем текст, который будет на кнопке
button_inn = KeyboardButton(text="🔍 Поиск ИНН")
# ⬆️ Кнопка для поиска ИНН по названию организации

button_extract = KeyboardButton(text="📄 Выписка ЕГРЮЛ")
# ⬆️ Кнопка для получения выписки из реестра

button_ask = KeyboardButton(text="💬 Вопрос")
# ⬆️ Кнопка для вопросов к GigaChat

button_doc = KeyboardButton(text="✍️ Документ")
# ⬆️ Кнопка для составления документов

button_help = KeyboardButton(text="❓ Помощь")
# ⬆️ Кнопка для справки

# ⬇️ Теперь собираем все кнопки в клавиатуру
# ReplyKeyboardMarkup — это целая клавиатура
# keyboard=[] — список рядов с кнопками
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [button_inn],          # ⬅️ Первый ряд: только кнопка Поиск ИНН
        [button_extract],      # ⬅️ Второй ряд: только Выписка
        [button_ask],          # ⬅️ Третий ряд: только Вопрос
        [button_doc],          # ⬅️ Четвёртый ряд: только Документ
        [button_help]          # ⬅️ Пятый ряд: только Помощь
    ],
    resize_keyboard=True,      
    # ⬆️ Уменьшить клавиатуру под размер экрана (чтобы не было огромных кнопок)
    
    input_field_placeholder="Выберите действие..."
    # ⬆️ Текст-подсказка в поле ввода (пока пользователь ничего не написал)
)
🧠 Что здесь происходит простыми словами:

    KeyboardButton — это как отдельная клавиша на пульте

    ReplyKeyboardMarkup — это весь пульт целиком (куда мы крепим кнопки)

    keyboard=[ [кнопка1], [кнопка2] ] — каждый внутренний список [ ] — это один ряд кнопок

📱 Как это выглядит у пользователя:

_____________________________
| 🔍 Поиск ИНН              |
| 📄 Выписка ЕГРЮЛ          |
| 💬 Вопрос                 |
| ✍️ Документ               |
| ❓ Помощь                  |
-----------------------------

🎨 Почему мы сделали кнопки вертикально?

На мобильных телефонах широкие кнопки в 2 ряда могут быть неудобны — пальцем трудно попасть. Вертикальное расположение (одна под другой) удобнее для тыканья пальцем.
5. Папка handlers/ — обработчики команд

В этой папке живут файлы, которые реагируют на действия пользователя.
Файл handlers/__init__.py

Этот файл связывает все обработчики воедино.

# ⬇️ Импортируем нужные классы из aiogram
from aiogram import Router, F
from aiogram.filters import Command

# ⬇️ Импортируем наши обработчики из других файлов
from .start import cmd_start                     # Обработчик /start
from .buttons import (
    handle_inn_by_name,      # Поиск ИНН
    handle_extract_by_inn,   # Выписка
    handle_ask,              # Вопрос GigaChat
    handle_doc,              # Составить документ
    handle_help,             # Помощь
    handle_user_input        # Любой другой текст
)

# ⬇️ Создаём "роутер" — объект, который будет направлять сообщения
# к нужным обработчикам
router = Router()

# ⬇️ Регистрируем обработчик для команды /start
# Когда пользователь пишет /start — вызывается cmd_start
router.message.register(cmd_start, Command("start"))

# ⬇️ Регистрируем обработчики для кнопок
# F.text == "текст" — значит, сработает, если текст сообщения совпадает с кнопкой
router.message.register(handle_inn_by_name, F.text == "🔍 Поиск ИНН")
router.message.register(handle_extract_by_inn, F.text == "📄 Выписка ЕГРЮЛ")
router.message.register(handle_ask, F.text == "💬 Вопрос")
router.message.register(handle_doc, F.text == "✍️ Документ")
router.message.register(handle_help, F.text == "❓ Помощь")

# ⬇️ Самый последний обработчик — для любого другого текста
# (должен быть последним, чтобы не перехватывать команды раньше)
router.message.register(handle_user_input)

print("🟢 Обработчики зарегистрированы!")
# ⬆️ Просто чтобы в консоли было видно, что всё загрузилось

🧠 Что такое роутер?

Представь, что бот — это большой офис, а роутер — это секретарь на ресепшене:

    Приходит сообщение "🔍 Поиск ИНН" → секретарь говорит: "Это к Ивану из отдела поиска" (handle_inn_by_name)

    Приходит сообщение "привет" (без кнопки) → секретарь говорит: "Я не знаю такого, это к стажёру" (handle_user_input)

Почему handle_user_input последний?

Потому что если поставить его первым, он будет перехватывать все сообщения, включая нажатия на кнопки. Нам нужно, чтобы сначала проверялись кнопки, а потом уже всё остальное.
6. Файл start.py — команда /start

Самый простой файл — просто приветствует пользователя.

from aiogram.types import Message
from aiogram.utils.formatting import Text, Bold
from bot.keyboards import main_keyboard  # Импортируем нашу клавиатуру

async def cmd_start(message: Message):
    """
    Обработчик команды /start
    message: объект сообщения от пользователя (содержит текст, id и т.д.)
    """
    
    # ⬇️ Берём имя пользователя (чтобы обратиться лично)
    user_name = message.from_user.first_name
    
    # ⬇️ Форматируем текст (Bold — жирный шрифт)
    content = Text(
        Bold(f"Привет, {user_name}!"), "\n\n",
        "Я БюрократЪ 2.0 — твой помощник в работе с документами.\n\n",
        "Я умею:\n",
        "🔍 Находить ИНН по названию организации\n",
        "📄 Давать ссылки на выписки из ЕГРЮЛ\n",
        "💬 Отвечать на вопросы через GigaChat\n",
        "✍️ Составлять документы\n\n",
        "Выбери действие на клавиатуре ниже 👇"
    )
    
    # ⬇️ Отправляем сообщение
    # **content.as_kwargs() — превращает форматированный текст в аргументы
    # reply_markup=main_keyboard — прикрепляем нашу клавиатуру
    await message.answer(**content.as_kwargs(), reply_markup=main_keyboard)

from aiogram.types import Message
from aiogram.utils.formatting import Text, Bold
from bot.keyboards import main_keyboard  # Импортируем нашу клавиатуру

async def cmd_start(message: Message):
    """
    Обработчик команды /start
    message: объект сообщения от пользователя (содержит текст, id и т.д.)
    """
    
    # ⬇️ Берём имя пользователя (чтобы обратиться лично)
    user_name = message.from_user.first_name
    
    # ⬇️ Форматируем текст (Bold — жирный шрифт)
    content = Text(
        Bold(f"Привет, {user_name}!"), "\n\n",
        "Я БюрократЪ 2.0 — твой помощник в работе с документами.\n\n",
        "Я умею:\n",
        "🔍 Находить ИНН по названию организации\n",
        "📄 Давать ссылки на выписки из ЕГРЮЛ\n",
        "💬 Отвечать на вопросы через GigaChat\n",
        "✍️ Составлять документы\n\n",
        "Выбери действие на клавиатуре ниже 👇"
    )
    
    # ⬇️ Отправляем сообщение
    # **content.as_kwargs() — превращает форматированный текст в аргументы
    # reply_markup=main_keyboard — прикрепляем нашу клавиатуру
    await message.answer(**content.as_kwargs(), reply_markup=main_keyboard)

🧠 Что здесь важно:

    message.from_user.first_name — так бот узнаёт имя пользователя

    Text и Bold — делают текст красивым (жирным)

    reply_markup=main_keyboard — прикрепляет кнопки к сообщению

7. Файл buttons.py — логика всех кнопок (самый большой!)

Этот файл обрабатывает все действия, кроме /start.
Хранилище состояний

# ⬇️ Словари для хранения временных данных
# user_search_type[user_id] = "ask"  — означает, что пользователь сейчас в режиме "вопрос"
user_search_type = {}

# user_search_data[user_id] = {"company_name": "Ромашка"}  — сохраняем название для поиска
user_search_data = {}

Зачем это нужно? Бот должен помнить, что пользователь сейчас делает. Если он нажал "Поиск ИНН", мы переводим его в режим name_step1 и ждём, пока он введёт название.
Обработчик "Поиск ИНН"

async def handle_inn_by_name(message: Message):
    """Обработчик кнопки '🔍 Найти ИНН по названию'"""
    user_id = message.from_user.id
    # ⬇️ Переводим пользователя в режим "поиск, шаг 1"
    user_search_type[user_id] = "name_step1"

    content = FText(
        Bold("🔍 Поиск ИНН по названию"), "\n\n",
        "Введите **название организации**:\n\n",
        Italic("Например: ООО Ромашка, ИП Иванов, Яндекс")
    )
    await message.answer(**content.as_kwargs())

async def handle_inn_by_name(message: Message):
    """Обработчик кнопки '🔍 Найти ИНН по названию'"""
    user_id = message.from_user.id
    # ⬇️ Переводим пользователя в режим "поиск, шаг 1"
    user_search_type[user_id] = "name_step1"

    content = FText(
        Bold("🔍 Поиск ИНН по названию"), "\n\n",
        "Введите **название организации**:\n\n",
        Italic("Например: ООО Ромашка, ИП Иванов, Яндекс")
    )
    await message.answer(**content.as_kwargs())

Обработчик "Выписка ЕГРЮЛ"

async def handle_extract_by_inn(message: Message):
    """Обработчик кнопки '📄 Выписка из ЕГРЮЛ'"""
    user_id = message.from_user.id
    # ⬇️ Переводим в режим "выписка"
    user_search_type[user_id] = "extract"

    await message.answer(
        "📄 <b>Получение выписки из ЕГРЮЛ</b>\n\n"
        "Введите <b>ИНН организации</b>, и я пришлю выписку "
        '<a href="https://egrul.nalog.ru">с сайта ФНС</a>.\n\n'
        "<i>Например: 4707013298</i>",
        parse_mode="HTML"  # ⬅️ Разрешаем HTML-теги в тексте
    )

Самый важный — handle_user_input

Эта функция обрабатывает любой текст, который вводит пользователь.

async def handle_user_input(message: Message):
    """
    Обрабатывает любой текст, который вводит пользователь
    """
    user_id = message.from_user.id
    text = message.text.strip()

    # ⬇️ Если пользователь не нажал ни одной кнопки — просим выбрать действие
    if user_id not in user_search_type:
        await message.answer(
            "Сначала выберите действие на клавиатуре.",
            reply_markup=main_keyboard
        )
        return

    search_type = user_search_type[user_id]

    ###########################################################################
    # ПОИСК ИНН ПО НАЗВАНИЮ (2 ШАГА)
    ###########################################################################
    
    if search_type == "name_step1":
        # ⬇️ Шаг 1: пользователь ввёл название
        user_search_data[user_id] = {"company_name": text}
        user_search_type[user_id] = "name_step2"
        
        await message.answer(
            "📍 <b>Укажите код региона</b>\n\n"
            "Введите <b>код региона</b> (2 цифры):\n\n"
            "<i>Например: 47 для Ленобласти\n"
            "77 для Москвы\n"
            "78 для Питера</i>\n\n"
            "<i>Или отправьте «-», если регион не важен</i>",
            parse_mode="HTML"
        )

    elif search_type == "name_step2":
        # ⬇️ Шаг 2: пользователь ввёл регион
        saved_data = user_search_data.get(user_id, {})
        company_name = saved_data.get("company_name", "")
        
        # ⬇️ Определяем, искать по региону или по всей России
        region_code = text if text not in ['-', 'любой', 'пропустить', 'нет'] else None
        
        # ⬇️ Показываем "бот печатает"
        wait_msg = await message.answer(f"🔍 Ищу организацию '{company_name}'...")
        
        # ⬇️ Вызываем парсер (он есть в другом файле)
        if region_code:
            result = await find_inn_by_name_with_region(company_name, region_code)
        else:
            result = await find_inn_by_name(company_name)
        
        # ⬇️ Удаляем сообщение "печатает"
        await wait_msg.delete()
        
        # ⬇️ Отправляем результат
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)
        
        # ⬇️ Удаляем состояние (пользователь вышел из режима)
        del user_search_type[user_id]
        if user_id in user_search_data:
            del user_search_data[user_id]

Обработчик "Вопрос" (с историей!)

elif search_type == "ask":
        # ⬇️ Проверяем, не хочет ли пользователь выйти
        if text.lower() in ["выход", "exit", "стоп", "stop", "меню", "menu"]:
            del user_search_type[user_id]
            await message.answer(
                "✅ Вы вышли из режима вопросов.",
                reply_markup=main_keyboard
            )
            return
            
        wait_msg = await message.answer("🤔 GigaChat думает над ответом...")
        
        # ⬇️ ВАЖНО: передаём user_id, чтобы GigaChat знал, чью историю брать
        result = await gigachat_inn.ask_question(user_id, text)
        
        await wait_msg.delete()
        await message.answer(result, parse_mode=None, reply_markup=main_keyboard)
        # ⬇️ НЕ удаляем состояние, чтобы можно было задавать несколько вопросов!
        # del user_search_type[user_id]  — закомментировано

Обработчик "Выписка" (после наших исправлений!)

    elif search_type == "extract":
        # ⬇️ Проверяем, что ввели 10 или 12 цифр
        if not text.isdigit() or len(text) not in (10, 12):
            await message.answer(
                "❌ ИНН должен содержать 10 или 12 цифр.\nПопробуйте ещё раз:",
                reply_markup=main_keyboard
            )
            return

        wait_msg = await message.answer(
            "📄 <b>Запрашиваю выписку...</b>\n"
            "<i>Обычно это занимает 10-20 секунд</i>",
            parse_mode="HTML"
        )

        # ⬇️ Вызываем нашу главную функцию!
        result = await get_egrul_extract(text)
        await wait_msg.delete()

        if 'error' in result:
            await message.answer(f"❌ {result['error']}", reply_markup=main_keyboard)
        else:
            # ⬇️ Отправляем файл пользователю
            document = FSInputFile(result['filepath'])
            await message.answer_document(
                document,
                caption=(
                    "✅ <b>Выписка получена!</b>\n"
                    f"📄 {result['org_name'][:200]}...\n"
                    '<i>Источник: </i><a href="https://egrul.nalog.ru">ФНС России</a>'
                ),
                parse_mode="HTML",
                reply_markup=main_keyboard
            )
            
            # ⬇️ Удаляем файл после отправки (чтобы не засорять диск)
            try:
                os.remove(result['filepath'])
            except:
                pass

        del user_search_type[user_id]

8. Файл nalog_parser.py — работа с сайтом ФНС (самое интересное!)

Этот файл — сердце бота. Именно здесь происходит вся магия получения выписок из ЕГРЮЛ.
📚 Что такое ЕГРЮЛ?

ЕГРЮЛ — Единый государственный реестр юридических лиц. Это база данных всех организаций в России. ФНС (налоговая) ведёт этот реестр и выдаёт выписки — официальные документы с информацией об организации.
🔍 Три режима работы парсера:

    find_inn_by_name — найти ИНН по названию организации

    find_name_by_inn — найти название по ИНН

    get_egrul_extract — получить выписку (PDF-файл) — самое сложное!

📥 Импорты

import aiohttp  # ⬅️ Библиотека для HTTP-запросов (как браузер, только в коде)
from bs4 import BeautifulSoup  # ⬅️ Парсит HTML (достаёт данные из страницы)
import re  # ⬅️ Регулярные выражения (поиск по шаблону, например, найти все цифры)
import asyncio  # ⬅️ Для асинхронности (чтобы бот не зависал в ожидании)
import time  # ⬅️ Для работы со временем (таймеры, паузы)
import os  # ⬅️ Для работы с файлами (сохранить PDF, удалить)

Функция find_inn_by_name — поиск ИНН по названию

async def find_inn_by_name(company_name: str) -> str:
    """
    Ищет ИНН организации по названию на сайте nalog.ru
    ⬆️ async — функция работает в фоне
    ⬆️ принимает название организации (строку)
    ⬆️ возвращает строку с результатом (ИНН или сообщение об ошибке)
    """
    
    base_url = "https://egrul.nalog.ru"  # ⬅️ Базовый адрес сайта ФНС
    
    # ⬇️ Заголовки HTTP-запроса (притворяемся браузером)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        # ⬆️ Говорим серверу: "я браузер Chrome на Windows"
        'Content-Type': 'application/x-www-form-urlencoded',
        # ⬆️ Тип данных, которые отправляем
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        # ⬆️ Говорим: "понимаю JSON и всё остальное"
        'X-Requested-With': 'XMLHttpRequest'
        # ⬆️ Говорим: "это AJAX-запрос" (как современный сайт)
    }

    try:
        # ⬇️ Создаём сессию (как браузер, который помнит куки)
        async with aiohttp.ClientSession() as session:
            
            # ===== ШАГ 1: Получаем куки =====
            print("🌐 Получаем куки...")
            async with session.get(f"{base_url}/index.html", headers=headers) as response:
                if response.status != 200:
                    return f"❌ Ошибка загрузки страницы: {response.status}"
                print("✅ Куки получены")
                # ⬆️ Куки — это как "пропуск" на сайт. Без них сайт не пустит дальше

            # ===== ШАГ 2: Отправляем поисковый запрос =====
            print(f"🔍 Ищем организацию '{company_name}'...")
            search_data = {
                'query': company_name,  # ⬅️ Название организации
                'page': '1',            # ⬅️ Первая страница результатов
                'search-type': 'ul'     # ⬅️ Ищем юрлица (не ИП)
            }

            async with session.post(f"{base_url}/", data=search_data, headers=headers) as response:
                if response.status != 200:
                    return f"❌ Ошибка поиска: {response.status}"

                search_result = await response.json()  # ⬅️ Ответ в формате JSON
                print(f"📦 Ответ на поиск: {search_result}")

                # ⬇️ Извлекаем ID запроса (нужен для получения результатов)
                request_id = None
                if isinstance(search_result, dict):
                    if 't' in search_result:
                        request_id = search_result['t']  # ⬅️ Вот он, ID!
                    elif 'id' in search_result:
                        request_id = search_result['id']

                if not request_id:
                    return "❌ Не удалось получить ID запроса"

                print(f"🆔 Получен ID запроса: {request_id[:50]}...")

                # ===== ШАГ 3: Получаем результаты =====
                print(f"📥 Запрашиваем результаты...")

                max_attempts = 10  # ⬅️ Максимум 10 попыток
                attempt = 0
                results = None
                wait_time = 1  # ⬅️ Начинаем ждать 1 секунду

                while attempt < max_attempts:
                    attempt += 1
                    print(f"⏳ Попытка {attempt}/{max_attempts} (ждём {wait_time} сек)...")

                    # ⬇️ Сайт ФНС требует timestamp (время в миллисекундах)
                    timestamp = int(time.time() * 1000)
                    results_url = f"{base_url}/search-result/{request_id}?r={timestamp}&_={timestamp}"

                    async with session.get(results_url, headers=headers) as resp:
                        if resp.status == 200:
                            data = await resp.json()

                            if 'status' in data and data['status'] == 'wait':
                                print(f"⏳ Сервер говорит 'wait', данные ещё готовятся...")
                                await asyncio.sleep(wait_time)  # ⬅️ Ждём
                                wait_time += 1  # ⬅️ Увеличиваем время ожидания
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

                # ===== ШАГ 4: Парсим результаты =====
                print(f"📦 Результаты получены")

                if 'rows' in results and len(results['rows']) > 0:
                    total_results = len(results['rows'])
                    print(f"📊 Всего найдено: {total_results}")

                    output = f"📋 **Найдено организаций: {total_results}**\n\n"

                    # ⬇️ Показываем не больше 10 результатов
                    max_show = min(10, total_results)
                    output += f"**Первые {max_show} результатов:**\n\n"

                    for i, row in enumerate(results['rows'][:max_show], 1):
                        org_info = []

                        # ⬇️ Название организации
                        if 'n' in row:
                            name = row['n']
                            if len(name) > 200:
                                name = name[:200] + "..."
                            org_info.append(f"**{i}. {name}**")

                        # ⬇️ ИНН
                        if 'i' in row:
                            org_info.append(f"ИНН: `{row['i']}`")

                        # ⬇️ ОГРН и дата
                        if 'o' in row:
                            org_info.append(f"ОГРН: {row['o']}")
                        if 'r' in row:
                            org_info.append(f"Дата: {row['r']}")

                        output += "\n".join(org_info) + "\n\n"

                    return output

                return "❌ Организации не найдены"

    except Exception as e:
        print(f"❌ Исключение: {e}")
        return f"❌ Ошибка при парсинге: {e}"

🧠 Что здесь происходит (простые слова):

    Притворяемся браузером — отправляем заголовки, чтобы сайт не понял, что мы бот

    Получаем куки — заходим на главную страницу, чтобы получить "пропуск"

    Ищем организацию — отправляем название, получаем ID запроса

    Ждём результаты — сайт ФНС готовит данные не мгновенно, нужно подождать

    Парсим JSON — разбираем ответ и показываем пользователю

9. Самая важная функция — get_egrul_extract (получение PDF)

Это функция, которую мы так долго отлаживали! Она делает 3 запроса к ФНС:

async def get_egrul_extract(inn: str) -> dict:
    """
    Получает выписку из ЕГРЮЛ по ИНН
    Возвращает словарь с путём к файлу или ошибкой
    """
    print(f"🔍 get_egrul_extract: начинаем поиск для ИНН {inn}")

    # ⬇️ Разные адреса на сайте ФНС
    base_url = "https://egrul.nalog.ru"
    search_url = f"{base_url}/"                     # Для поиска
    result_url = f"{base_url}/search-result/"       # Для результатов
    request_url = f"{base_url}/vyp-request/"        # Для активации выписки (ШАГ 5!)
    status_url = f"{base_url}/vyp-status/"          # Для проверки статуса (ШАГ 6!)
    download_base = f"{base_url}/vyp-download/"     # Для скачивания (ШАГ 8!)

    # ⬇️ Заголовки (притворяемся браузером Safari на Mac)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3 Safari/605.1.15',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    try:
        async with aiohttp.ClientSession() as session:
            # ===== ШАГ 1: Получаем куки =====
            print("🌐 Получаем куки...")
            async with session.get(f"{base_url}/index.html", headers=headers) as response:
                if response.status != 200:
                    return {'error': f'Ошибка загрузки страницы: {response.status}'}
                print("✅ Куки получены")

            # ===== ШАГ 2: Ищем организацию =====
            print(f"🔍 Ищем организацию с ИНН {inn}...")
            
            # ⬇️ Заголовки для AJAX-запросов
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

            # ===== ШАГ 3: Получаем результаты поиска =====
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

            # ===== ШАГ 4: Получаем код для скачивания =====
            print("🔍 Получаем код для скачивания...")

            t_value = None
            org_name = "Неизвестная организация"

            if isinstance(results, dict) and 'rows' in results and len(results['rows']) > 0:
                first_row = results['rows'][0]
                org_name = first_row.get('n', 'Неизвестная организация')

                if 't' in first_row:
                    t_value = first_row['t']
                    print(f"✅ Найден код в поле 't': длина {len(t_value)}")

                    if len(t_value) < 150:
                        print(f"⚠️ Короткий код ({len(t_value)}) - выписка возможно ещё не готова")

            if not t_value:
                return {'error': 'Не найден код для скачивания'}

            # ===== ШАГ 5: Активируем выписку через vyp-request (САМОЕ ВАЖНОЕ!) =====
            print("🔄 ШАГ 5: Активируем выписку через vyp-request...")
            request_activate_url = f"{request_url}{t_value}?r=&_={int(time.time()*1000)}"

            async with session.get(request_activate_url, headers=ajax_headers) as resp:
                if resp.status == 200:
                    print("✅ Запрос на активацию отправлен успешно")
                    try:
                        activate_data = await resp.json()
                        print(f"📊 Ответ на активацию: {activate_data}")
                        # ⬆️ Здесь приходит ДЛИННЫЙ код (160 символов)!
                    except:
                        print("⚠️ Не удалось распарсить ответ активации")
                else:
                    print(f"⚠️ Ошибка при активации: {resp.status}")

            # ===== ШАГ 6: Проверяем статус через vyp-status =====
            print("⏳ ШАГ 6: Проверяем статус выписки...")

            max_status_attempts = 15
            status_attempt = 0
            status_wait_time = 2
            ready = False

            while status_attempt < max_status_attempts and not ready:
                status_attempt += 1
                print(f"⏳ Проверка статуса {status_attempt}/{max_status_attempts} (ждём {status_wait_time} сек)...")

                timestamp = int(time.time() * 1000)
                check_status_url = f"{status_url}{t_value}?r={timestamp}&_={timestamp}"

                async with session.get(check_status_url, headers=ajax_headers) as resp:
                    if resp.status == 200:
                        try:
                            status_data = await resp.json()
                            print(f"📊 Статус: {status_data}")

                            if status_data.get('status') == 'ready':
                                print("✅ Выписка готова к скачиванию!")
                                ready = True
                                break
                            elif status_data.get('status') == 'wait':
                                print(f"⏳ Выписка ещё готовится...")
                                await asyncio.sleep(status_wait_time)
                                status_wait_time += 1
                                continue
                            else:
                                await asyncio.sleep(status_wait_time)
                                status_wait_time += 1
                                continue
                        except Exception as e:
                            print(f"❌ Ошибка парсинга статуса: {e}")
                            await asyncio.sleep(status_wait_time)
                            status_wait_time += 1
                            continue
                    else:
                        print(f"❌ Ошибка проверки статуса: {resp.status}")
                        await asyncio.sleep(status_wait_time)
                        status_wait_time += 1

            if not ready:
                return {'error': 'Превышено время ожидания готовности выписки'}

            # ===== ШАГ 7: Ждём немного перед скачиванием =====
            print("⏳ Ждём 2 секунды перед скачиванием...")
            await asyncio.sleep(2)

            # ===== ШАГ 8: Скачиваем файл =====
            download_link = f"{download_base}{t_value}"
            print(f"📥 ШАГ 8: Скачиваю файл: {download_link[:100]}...")

            # ⬇️ Заголовки для скачивания PDF
            download_headers = {
                'User-Agent': headers['User-Agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Referer': f"{base_url}/index.html",
                'Connection': 'keep-alive',
            }

            # ⬇️ Добавляем куки в заголовки
            all_cookies = session.cookie_jar.filter_cookies(f"{base_url}/index.html")
            cookie_parts = []
            for key, cookie in all_cookies.items():
                cookie_parts.append(f"{key}={cookie.value}")
            if cookie_parts:
                download_headers['Cookie'] = '; '.join(cookie_parts)
                print(f"🍪 Передаём куки: {len(cookie_parts)} шт.")

            async with session.get(download_link, headers=download_headers, allow_redirects=True) as file_response:
                print(f"📋 Статус ответа: {file_response.status}")

                if file_response.status == 200:
                    content = await file_response.read()
                    print(f"📊 Размер файла: {len(content)} байт")

                    # ⬇️ Проверяем, что это действительно PDF
                    if len(content) > 1000 and content[:4].startswith(b'%PDF'):
                        print("✅ Получен валидный PDF")

                        # ⬇️ Получаем имя файла из заголовков
                        content_disp = file_response.headers.get('content-disposition', '')
                        filename = "extract.pdf"
                        if 'filename=' in content_disp:
                            match = re.search(r'filename=([^;]+)', content_disp)
                            if match:
                                filename = match.group(1).strip('"')

                        # ⬇️ Создаём папку data, если её нет
                        if not os.path.exists('data'):
                            os.makedirs('data')
                            print("📁 Создана папка data")

                        filepath = f"data/{filename}"
                        with open(filepath, 'wb') as f:
                            f.write(content)

                        print(f"✅ Файл сохранён: {filepath}")
                        return {
                            'success': True,
                            'filename': filename,
                            'filepath': filepath,
                            'org_name': org_name
                        }
                    else:
                        print(f"❌ Файл не является PDF или слишком мал")
                        return {'error': 'Получен повреждённый файл'}
                else:
                    print(f"❌ Ошибка скачивания: {file_response.status}")
                    return {'error': f'Ошибка скачивания: {file_response.status}'}

    except Exception as e:
        print(f"❌ Исключение: {e}")
        import traceback
        traceback.print_exc()
        return {'error': f'Ошибка: {str(e)}'}

🎯 Почему эта функция такая сложная?

    Сайт ФНС защищается от ботов — нужно точно повторять поведение браузера

    Три запроса вместо одного:

        Первый (vyp-request) — активирует выписку

        Второй (vyp-status) — проверяет готовность

        Третий (vyp-download) — скачивает PDF

    Куки — без правильных кук сайт не отдаст файл

    Тайминги — нужно ждать, пока выписка сформируется

10. Файл gigachat.py — работа с GigaChat

Здесь всё проще — мы просто отправляем запросы в GigaChat и получаем ответы.
История сообщений (то, что мы добавили!)

class GigaChatInnAssistant:
    """Специалист по ИНН и документам"""

    def __init__(self):
        # ⬇️ Хранилище истории по каждому пользователю
        # Это словарь, где ключ — ID пользователя, а значение — список последних сообщений
        self.user_history = {}  # {user_id: [{"user": вопрос, "bot": ответ}, ...]}
        self.max_history = 20    # Сколько последних сообщений запоминать
        
        # ... остальной код инициализации ...

Метод ask_question с историей

async def ask_question(self, user_id: int, question: str) -> str:
    """Отвечает на общие вопросы с учётом истории диалога"""
    
    if not self.available:
        return "❌ GigaChat не настроен"

    # ⬇️ Получаем историю пользователя (если её нет, создаём пустой список)
    if user_id not in self.user_history:
        self.user_history[user_id] = []

    # ⬇️ Берём последние 20 сообщений из истории
    recent_history = self.user_history[user_id][-self.max_history:]

    # ⬇️ Формируем контекст из истории
    history_text = ""
    if recent_history:
        history_text = "Вот предыдущие сообщения из этого диалога. Учитывай их при ответе:\n\n"
        for msg in recent_history:
            history_text += f"Пользователь: {msg['user']}\n"
            history_text += f"Ты: {msg['bot']}\n"
        history_text += "\n---\n"

    # ⬇️ Формируем промпт (запрос к GigaChat)
    prompt = f"""{history_text}Текущий вопрос пользователя: {question}

ВАЖНО: Отвечай, учитывая предыдущие сообщения. Если вопрос неполный (например, 'население'), отвечай про то, о чём шла речь ранее.

Ответ напиши на русском языке."""

    try:
        # ⬇️ Отправляем запрос в GigaChat
        response = self.client.chat(prompt)
        answer = response.choices[0].message.content.strip()

        # ⬇️ Сохраняем этот диалог в историю
        self.user_history[user_id].append({
            "user": question,
            "bot": answer
        })

        # ⬇️ Обрезаем историю, если слишком длинная
        if len(self.user_history[user_id]) > self.max_history * 2:
            self.user_history[user_id] = self.user_history[user_id][-self.max_history:]

        return f"💬 **Ответ:**\n\n{answer}"
    except Exception as e:
        return f"❌ Ошибка: {e}"

11. Git — как мы сохраняли код
Основные команды (с пояснениями)

# Показать текущее состояние (какие файлы изменены)
git status

# Добавить файлы в коммит (подготовить к сохранению)
git add bot/parsers/nalog_parser.py

# Сохранить изменения (коммит) с описанием
git commit -m "Fix EGRUL extraction with full cycle"

# Отправить на GitHub
git push origin main

# Создать новую ветку
git checkout -b feature/fix-egrul-activation

# Посмотреть все ветки
git branch

# Переключиться на другую ветку
git checkout main

# Слить ветку в текущую
git merge feature/fix-egrul-activation

# Удалить ветку (после слияния)
git branch -d feature/fix-egrul-activation
git push origin --delete feature/fix-egrul-activation

🌿 Зачем нужны ветки?

Ветки — это как черновики:

    В main лежит чистовой вариант (для пользователей)

    В feature/... лежат эксперименты

    Когда всё готово — сливаем черновик в чистовой вариант

12. Railway — как бот попал в интернет
Что такое деплой?

Деплой — это когда твой бот переезжает с твоего компьютера в интернет и начинает работать 24/7.
Важные файлы для Railway

# Procfile — инструкция, как запускать
web: python -m bot.__main__

# runtime.txt — версия Python
python-3.12.0

# requirements.txt — все библиотеки
aiogram==3.17.0
aiohttp==3.11.11
beautifulsoup4==4.12.3
lxml==5.3.0
python-dotenv==1.0.1
gigachat==0.1.13

Переменные окружения (секреты)

В Railway есть раздел Variables, куда мы добавили:
KEY	VALUE
BOT_TOKEN	твой_токен
BOT_ADMIN_ID	твой_id
BOT_GIGACHAT_API_KEY	твой_ключ

Важно! Эти переменные не видны никому, кроме Railway и твоего бота.
13. Словарь терминов для новичка
Термин	Что значит простыми словами
Асинхронность	Бот может делать несколько дел одновременно. Пока ждёт ответ от ФНС, уже отвечает другим
API	Способ для программ общаться друг с другом. Как официант между кухней и клиентом
JSON	Формат данных, понятный всем языкам. Как таблица Excel, только в тексте
Куки (cookies)	"Пропуск" для сайта. Чтобы сайт не спрашивал каждый раз "ты кто?"
Сессия	Временное хранилище данных между запросами. Как разговор, который не прерывается
Парсинг	Разбор сайта, чтобы достать нужную информацию
Хедеры (headers)	Дополнительная информация в запросе (кто ты, какой браузер, какой язык)
User-Agent	Строка, которая говорит сайту: "я браузер Chrome, не бойся меня"
Git	Система контроля версий. Как "Сохранить как..." для программистов
Репозиторий	Хранилище кода (папка с историей изменений)
Ветка (branch)	Отдельная линия разработки. Как черновик
Коммит (commit)	Сохранение изменений с описанием
Пуш (push)	Отправка кода на GitHub
Пулл (pull)	Загрузка кода с GitHub
Деплой (deploy)	Запуск бота в интернете
Переменные окружения	Секретные данные, которые не хранятся в коде
Токен	Секретный ключ для доступа к боту или API
🎉 ЗАКЛЮЧЕНИЕ

Твой бот теперь умеет:

✅ Находить ИНН по названию организации
✅ Получать официальные выписки из ЕГРЮЛ (PDF)
✅ Отвечать на вопросы через GigaChat (с историей 20 сообщений)
✅ Составлять документы
✅ Работать 24/7 на Railway
✅ Хранить секреты в безопасности

Статистика — кто использует бота
🔍 Зачем нужна статистика?

Когда бот начинает работать, хочется знать:

    Сколько человек им пользуется?

    Какие функции самые популярные?

    Кто заходил сегодня?

Для этого мы добавили систему статистики.
📁 Файл statistics.py — хранение данных

# bot/services/statistics.py
import json  # ⬅️ Для работы с JSON-файлами
import os    # ⬅️ Для проверки существования файла
from datetime import datetime  # ⬅️ Для работы с датами
from collections import defaultdict  # ⬅️ Удобный словарь со значениями по умолчанию

STATS_FILE = "data/statistics.json"  # ⬅️ Где храним статистику

class Statistics:
    def __init__(self):
        # ⬅️ При создании объекта загружаем существующую статистику
        self.stats = self.load_stats()
    
    def load_stats(self):
        """Загружает статистику из файла"""
        if os.path.exists(STATS_FILE):
            try:
                with open(STATS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.create_empty_stats()
        return self.create_empty_stats()
    
    def create_empty_stats(self):
        """Создаёт пустую структуру статистики"""
        return {
            "users": {},  # ⬅️ Здесь хранятся данные о пользователях
            "commands": {},  # ⬅️ Счётчики команд
            "daily": {},  # ⬅️ Статистика по дням
            "total_users": 0,  # ⬅️ Всего пользователей
            "total_commands": 0  # ⬅️ Всего команд
        }
    
    def log_user(self, user_id: int, username: str = None, first_name: str = None):
        """Логирует пользователя (запоминает, что он заходил)"""
        today = datetime.now().strftime("%Y-%m-%d")  # ⬅️ Сегодняшняя дата
        user_id_str = str(user_id)
        
        if user_id_str not in self.stats["users"]:
            # ⬇️ Новый пользователь
            self.stats["users"][user_id_str] = {
                "first_seen": today,  # ⬅️ Когда первый раз зашёл
                "last_seen": today,   # ⬅️ Когда последний раз заходил
                "username": username,  # ⬅️ @username в Telegram
                "first_name": first_name  # ⬅️ Имя пользователя
            }
            self.stats["total_users"] += 1
        else:
            # ⬇️ Старый пользователь — обновляем дату последнего визита
            self.stats["users"][user_id_str]["last_seen"] = today
            if username:
                self.stats["users"][user_id_str]["username"] = username
            if first_name:
                self.stats["users"][user_id_str]["first_name"] = first_name
        
        self.save_stats()  # ⬅️ Сразу сохраняем в файл
    
    def log_command(self, user_id: int, command: str):
        """Логирует использование команды"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # ⬇️ Увеличиваем счётчик команды
        if command in self.stats["commands"]:
            self.stats["commands"][command] += 1
        else:
            self.stats["commands"][command] = 1
        
        # ⬇️ Логируем по дням
        if today not in self.stats["daily"]:
            self.stats["daily"][today] = {}
        
        if command in self.stats["daily"][today]:
            self.stats["daily"][today][command] += 1
        else:
            self.stats["daily"][today][command] = 1
        
        self.stats["total_commands"] += 1
        self.save_stats()
    
    def get_stats_text(self) -> str:
        """Возвращает красивый текст статистики для команды /stats"""
        text = "📊 **Статистика бота**\n\n"
        text += f"👥 **Всего пользователей:** {self.stats['total_users']}\n"
        text += f"📝 **Всего команд:** {self.stats['total_commands']}\n\n"
        
        text += "**Последние 10 пользователей:**\n"
        # ⬇️ Сортируем по last_seen (последние сверху)
        sorted_users = sorted(
            self.stats["users"].items(), 
            key=lambda x: x[1]["last_seen"], 
            reverse=True
        )[:10]
        
        for user_id, data in sorted_users:
            name = data.get("first_name") or data.get("username") or "Без имени"
            text += f"• {name} (ID: {user_id}) — последний раз: {data['last_seen']}\n"
        
        text += "\n**Популярные команды:**\n"
        sorted_commands = sorted(
            self.stats["commands"].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        for cmd, count in sorted_commands:
            # ⬇️ Преобразуем имена команд в читаемый вид
            cmd_names = {
                "ask": "💬 Вопросы",
                "doc": "✍️ Документы", 
                "extract": "📄 Выписки",
                "inn_search_start": "🔍 Поиск ИНН (начало)",
                "inn_search_complete": "🔍 Поиск ИНН (завершён)",
                "help": "❓ Помощь"
            }
            cmd_display = cmd_names.get(cmd, cmd)
            text += f"• {cmd_display}: {count} раз\n"
        
        return text

# ⬇️ Создаём глобальный объект статистики
# Он будет доступен во всём боте
stats = Statistics()

📊 Как это работает простыми словами:

    log_user — вызывается каждый раз, когда пользователь что-то пишет боту. Запоминает:

        Когда пользователь первый раз зашёл

        Когда заходил последний раз

        Его имя и username

    log_command — вызывается при каждом действии (нажатии кнопки). Считает:

        Сколько раз использовали каждую команду

        Статистику по дням

    get_stats_text — собирает красивый отчёт для админа

👑 Команда /stats (только для админа)

В файле admin.py мы создали специальную команду:

# bot/handlers/admin.py
from aiogram.types import Message
from aiogram.filters import Command
from bot.config_reader import get_config
from bot.services.statistics import stats

async def cmd_stats(message: Message):
    """Команда /stats - показывает статистику (только для админа)"""
    config = get_config()
    
    # ⬇️ Проверяем, что это админ (сверяем с admin_id из .env)
    if message.from_user.id != config.admin_id:
        await message.answer("❌ Эта команда только для администратора")
        return
    
    stats_text = stats.get_stats_text()
    await message.answer(stats_text, parse_mode="Markdown")

🧠 Почему это полезно?

    Понимаешь аудиторию — сколько людей реально пользуется ботом

    Видишь популярные функции — что нужно улучшать в первую очередь

    Отслеживаешь активность — когда пользователи заходят

    Можешь показать инвесторам (если вдруг) — "у моего бота 1000 пользователей!"

markdown

# БюрократЪ 2.0 — Миграция с Railway на собственный сервер

> 📚 **Для кого этот документ**: для тех, кто хочет понять, почему облачные платформы могут подводить, и как перенести бота на свой сервер.

## 📋 Содержание

1. [Почему мы ушли с Railway](#1-почему-мы-ушли-с-railway)
2. [Что мы сделали сегодня](#2-что-мы-сделали-сегодня)
3. [Подготовка сервера на Timeweb](#3-подготовка-сервера-на-timeweb)
4. [Установка и настройка прокси 3proxy](#4-установка-и-настройка-прокси-3proxy)
5. [Перенос бота на сервер](#5-перенос-бота-на-сервер)
6. [Настройка автозапуска через PM2](#6-настройка-автозапуска-через-pm2)
7. [Решение проблемы с PYTHONPATH](#7-решение-проблемы-с-pythonpath)
8. [Полезные команды](#8-полезные-команды)
9. [Заключение](#9-заключение)

---

## 1. Почему мы ушли с Railway

### 🚨 Проблема
Наш бот работал на Railway 24/7, но при попытке получить выписки из ЕГРЮЛ мы столкнулись с ошибкой:

❌ Ошибка: Connection timeout to host https://egrul.nalog.ru/index.html
text


### 🔍 Диагностика
Мы провели тщательное расследование:

1. **Локально бот работал** — значит, код правильный
2. **Сайт ФНС был доступен** — проверили через браузер
3. **Проблема на стороне Railway** — их серверы не могли достучаться до ФНС

### 🎯 Вывод
Серверы Railway находятся за границей, и сайт ФНС их **блокирует**. Решение — **собственный сервер с российским IP**.

---

## 2. Что мы сделали сегодня

### 📅 Хронология событий

| Время | Событие |
|-------|---------|
| 10:00 | Обнаружили, что Railway не работает с ФНС |
| 10:15 | Приняли решение арендовать сервер на Timeweb |
| 10:30 | Установили и настроили прокси 3proxy |
| 11:00 | Перенесли бота на сервер |
| 11:30 | Настроили автозапуск через PM2 |
| 11:45 | ✅ Бот работает стабильно |

---

## 3. Подготовка сервера на Timeweb

### 3.1. Аренда сервера

Мы выбрали **Timeweb** (timeweb.cloud) по нескольким причинам:
- 🇷🇺 **Российский хостинг** — сайт ФНС не блокирует
- 💰 **Дёшево** — от 209 руб/мес
- 🛠 **Удобная панель управления**

### 3.2. Первое подключение

```bash
ssh root@94.241.142.61

Важно! При первом подключении появляется предупреждение:
text

The authenticity of host '94.241.142.61' can't be established.

Нужно ввести yes — это нормально.
3.3. Очистка от мусора

В домашней папке оказались странные файлы:
text

Host:  User-Agent:  CONNECT  Proxy-Authorization:

Это результат случайного копирования команд. Удалили их:
bash

rm -f "Host:" "User-Agent:" "CONNECT" "Proxy-Authorization:" "Proxy-Connection:" "'s -tuln | grep 3128'"

4. Установка и настройка прокси 3proxy
4.1. Почему нужен прокси

Бот на сервере мог бы ходить на сайт ФНС напрямую, но мы решили настроить прокси для:

    🔒 Дополнительной безопасности

    🔄 Возможности масштабирования

    📊 Мониторинга трафика

4.2. Установка 3proxy
bash

# Скачиваем
wget https://github.com/3proxy/3proxy/archive/refs/tags/0.9.4.tar.gz

# Распаковываем
tar -xzf 0.9.4.tar.gz
cd 3proxy-0.9.4

# Компилируем и устанавливаем
make -f Makefile.Linux
make -f Makefile.Linux install

4.3. Настройка конфига

Создали файл /etc/3proxy/3proxy.cfg:
conf

nserver 8.8.8.8
nserver 8.8.4.4
log /var/log/3proxy/3proxy.log D
logformat "- +_L%t.%. %N.%p %E %U %C:%c %R:%r %O %I %h %T"
rotate 30
auth strong
users klint-dev:CL:813o8y8pN
allow * * * * *
proxy -p3128

Что здесь важно:

    users klint-dev:CL:813o8y8pN — логин и пароль для доступа

    proxy -p3128 — порт, на котором работает прокси

4.4. Запуск прокси
bash

# Создаём папку для логов
mkdir -p /var/log/3proxy

# Запускаем
/usr/bin/3proxy /etc/3proxy/3proxy.cfg &

# Проверяем, что работает
ps aux | grep 3proxy
ss -tuln | grep 3128

4.5. Открываем порт в фаерволе
bash

ufw allow 3128/tcp
ufw enable

5. Перенос бота на сервер
5.1. Создание архива (на локальном компьютере)

Важно! Секреты не должны попасть в архив:
bash

tar -czf burokrat_bot.tar.gz \
  --exclude=".git" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude="data/*.json" \
  --exclude=".env" \
  --exclude="venv" \
  bot/ requirements.txt Procfile runtime.txt .env.example

Объяснение параметров:

    --exclude=".env" — самое важное! Не включаем секреты

    --exclude=".git" — не тащим историю версий

    --exclude="__pycache__" — не тащим кэш Python

5.2. Загрузка на сервер
bash

scp burokrat_bot.tar.gz root@94.241.142.61:/root/

5.3. Распаковка на сервере
bash

# Создаём отдельную папку для бота
mkdir -p /opt/burokrat_bot
cp burokrat_bot.tar.gz /opt/burokrat_bot/
cd /opt/burokrat_bot

# Распаковываем
tar -xzf burokrat_bot.tar.gz

5.4. Настройка окружения
bash

# Создаём виртуальное окружение
python3 -m venv .venv

# Активируем
source .venv/bin/activate

# Устанавливаем зависимости
pip install -r requirements.txt

# Создаём файл с секретами
nano .env

В .env вставляем:
text

BOT_TOKEN=8343156591:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw
ADMIN_ID=628150594
GIGACHAT_API_KEY=твой_ключ

5.5. Пробный запуск
bash

python -m bot.__main__

Если всё правильно — бот запустится и будет отвечать в Telegram.
6. Настройка автозапуска через PM2
6.1. Почему PM2?

PM2 — это менеджер процессов, который:

    🔄 Перезапускает бота, если он упал

    🔁 Запускает бота после перезагрузки сервера

    📊 Показывает логи и статистику

6.2. Установка PM2
bash

apt update
apt install -y npm
npm install -g pm2

6.3. Запуск бота через PM2
bash

pm2 start bot/__main__.py \
  --name "burokrat_bot" \
  --interpreter python3 \
  --env PYTHONPATH=/opt/burokrat_bot

6.4. Настройка автозагрузки
bash

pm2 save
pm2 startup

7. Решение проблемы с PYTHONPATH
7.1. Проблема

При запуске через PM2 бот падал с ошибкой:
text

ModuleNotFoundError: No module named 'bot'

7.2. Причина

Python не мог найти модуль bot, потому что текущая директория не была добавлена в путь поиска.
7.3. Решение

Добавили переменную окружения PYTHONPATH:
bash

export PYTHONPATH=/opt/burokrat_bot:$PYTHONPATH

И запустили PM2 с правильным путём:
bash

pm2 delete burokrat_bot
pm2 start bot/__main__.py \
  --name "burokrat_bot" \
  --interpreter python3 \
  --env PYTHONPATH=/opt/burokrat_bot

После этого бот заработал стабильно.
8. Полезные команды
8.1. Для бота
Команда	Что делает
pm2 status	Показать состояние бота
pm2 logs burokrat_bot	Посмотреть логи
pm2 restart burokrat_bot	Перезапустить бота
pm2 stop burokrat_bot	Остановить бота
pm2 delete burokrat_bot	Удалить из PM2
8.2. Для прокси
Команда	Что делает
ps aux | grep 3proxy	Проверить, запущен ли прокси
ss -tuln | grep 3128	Проверить, слушает ли порт
tail -f /var/log/3proxy/3proxy.log	Смотреть логи прокси
pkill 3proxy	Остановить прокси
/usr/bin/3proxy /etc/3proxy/3proxy.cfg &	Запустить прокси
8.3. Для сервера
Команда	Что делает
ssh root@94.241.142.61	Подключиться к серверу
exit	Отключиться
apt update && apt upgrade	Обновить систему
ufw status	Проверить фаервол
9. Заключение
✅ Что мы сделали

    Диагностировали проблему — Railway блокирует доступ к ФНС

    Арендовали сервер на Timeweb с российским IP

    Настроили прокси 3proxy для дополнительной безопасности

    Перенесли бота на сервер

    Настроили автозапуск через PM2

    Решили проблему с PYTHONPATH

🎯 Итог

Теперь бот работает 24/7 на собственном сервере:

    🇷🇺 Российский IP — сайт ФНС не блокирует

    🔒 Свой прокси — полный контроль

    🔄 Автозапуск — не боится перезагрузок

    📊 Мониторинг через PM2

🏆 Что мы узнали

    Облачные платформы (Railway, Heroku) удобны, но не всегда подходят для работы с российскими госсайтами

    Собственный сервер — это не страшно, а очень полезно

    PM2 — отличный инструмент для управления процессами

    3proxy — простой и надёжный прокси-сервер

    Главное — не бояться ошибок, каждая из них учит новому

📊 Сравнение: Railway vs Timeweb
Параметр	Railway	Timeweb (собственный сервер)
Цена	$5/мес (или бесплатно)	209 руб/мес
Доступ к ФНС	❌ Блокирует	✅ Отлично работает
Свой прокси	❌ Нельзя	✅ Можно
Контроль	Ограниченный	Полный
Автозапуск	✅ Есть	✅ Есть (через PM2)
Логи	Через веб-интерфейс	Прямо в терминале
🔥 Заключительные слова

Сегодня мы прошли огромный путь:

    От разочарования в Railway

    До полного контроля над своим сервером

    От непонятных ошибок

    До стабильно работающего бота

Ты теперь умеешь:

    ✅ Арендовать и настраивать сервер

    ✅ Устанавливать и настраивать прокси

    ✅ Переносить приложения

    ✅ Настраивать автозапуск

    ✅ Читать логи и находить ошибки

Это уровень настоящего системного администратора! 🏆