// Ждём загрузки страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log('WebApp загружен!');

    // Инициализация Telegram WebApp
    const tg = window.Telegram.WebApp;

    // Сообщаем Telegram, что мы готовы
    tg.ready();

    // Расширяем окно на весь экран
    tg.expand();

    // Получаем данные пользователя из Telegram
    const user = tg.initDataUnsafe?.user;
    console.log('Пользователь:', user);

    // Получаем элементы
    const searchInput = document.getElementById('searchInput');
    const searchBtn = document.getElementById('searchBtn');
    const resultsDiv = document.getElementById('results');
    const loadingDiv = document.getElementById('loading');
    const regionSelect = document.getElementById('regionSelect');
    const statusSelect = document.getElementById('statusSelect');

    // Базовый URL API (в разработке - localhost, в продакшене - сервер)
    const API_BASE_URL = 'http://localhost:8080';  // для локальной разработки
    // const API_BASE_URL = 'https://твой-сервер.com';  // для продакшена

    // Показываем приветствие
    resultsDiv.innerHTML = `
        <div style="text-align: center; color: var(--hint-color); padding: 40px 0;">
            🔍 Введите название организации для поиска
        </div>
    `;

    // Загружаем историю пользователя
    if (user?.id) {
        loadUserHistory(user.id);
    }

    // Обработчик кнопки поиска
    searchBtn.addEventListener('click', function() {
        const query = searchInput.value.trim();
        if (query) {
            performSearch(query);
        } else {
            tg.showAlert('Введите название или ИНН');
        }
    });

    // Поиск при нажатии Enter
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            const query = searchInput.value.trim();
            if (query) {
                performSearch(query);
            }
        }
    });

    // Функция поиска (реальная)
    async function performSearch(query) {
        console.log('Ищем:', query);

        // Показываем загрузку
        loadingDiv.classList.remove('hidden');
        resultsDiv.innerHTML = '';

        // Получаем выбранный регион
        const region = regionSelect.value || null;

        try {
            // Отправляем запрос к нашему API
            const response = await fetch(`${API_BASE_URL}/api/search`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query,
                    region: region
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            // Отображаем результаты
            displayResults(data.organizations);

            // Добавляем в историю (локально)
            addToHistory(query);

        } catch (error) {
            console.error('Ошибка поиска:', error);
            resultsDiv.innerHTML = `
                <div style="text-align: center; color: #ff6b6b; padding: 40px 0;">
                    ❌ Ошибка при поиске: ${error.message}
                </div>
            `;
        } finally {
            // Прячем загрузку
            loadingDiv.classList.add('hidden');
        }
    }

    // Функция отображения результатов
    function displayResults(organizations) {
        if (!organizations || organizations.length === 0) {
            resultsDiv.innerHTML = `
                <div style="text-align: center; color: var(--hint-color); padding: 40px 0;">
                    😕 Ничего не найдено
                </div>
            `;
            return;
        }

        resultsDiv.innerHTML = '';

        organizations.forEach(org => {
            const card = document.createElement('div');
            card.className = 'org-card';

            const statusClass = org.status === 'active' ? 'status-active' : 'status-liquidated';
            const statusText = org.status === 'active' ? 'Действующее' : 'Ликвидировано';

            card.innerHTML = `
                <div class="org-name">${escapeHtml(org.name)}</div>
                <div class="org-details">
                    <div class="org-detail">ИНН: <span>${org.inn}</span></div>
                    <div class="org-detail">ОГРН: <span>${org.ogrn || '—'}</span></div>
                    <div class="org-detail" style="grid-column: span 2;">
                        Адрес: <span>${escapeHtml(org.address || '—')}</span>
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="org-status ${statusClass}">${statusText}</span>
                    <span style="color: var(--hint-color); font-size: 14px;">
                        Релевантность: ${org.relevance}%
                    </span>
                </div>
            `;

            // Добавляем обработчик клика на карточку
            card.addEventListener('click', () => {
                showOrganizationDetails(org.inn);
            });

            resultsDiv.appendChild(card);
        });
    }

    // Функция для экранирования HTML (безопасность)
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Функция для показа деталей организации
    async function showOrganizationDetails(inn) {
        try {
            tg.showPopup({
                title: 'Загрузка...',
                message: 'Получаем информацию об организации',
                buttons: [{type: 'close'}]
            });

            // TODO: Запросить детали с сервера
            // const response = await fetch(`${API_BASE_URL}/api/organization/${inn}`);
            // const data = await response.json();

            // Пока показываем заглушку
            tg.showPopup({
                title: 'Информация об организации',
                message: `ИНН: ${inn}\nПолная информация будет доступна в следующей версии.`,
                buttons: [{type: 'close'}]
            });

        } catch (error) {
            console.error('Ошибка получения деталей:', error);
        }
    }

    // Функция загрузки истории пользователя
    async function loadUserHistory(userId) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/history/${userId}`);
            if (response.ok) {
                const history = await response.json();
                updateHistoryList(history);
            }
        } catch (error) {
            console.error('Ошибка загрузки истории:', error);
        }
    }

    // Функция обновления списка истории
    function updateHistoryList(historyItems) {
        const historyList = document.getElementById('historyList');
        historyList.innerHTML = '';

        historyItems.forEach(item => {
            const historyItem = document.createElement('p');
            historyItem.className = 'history-item';
            historyItem.textContent = item.query;

            historyItem.addEventListener('click', () => {
                searchInput.value = item.query;
                performSearch(item.query);
            });

            historyList.appendChild(historyItem);
        });
    }

    // Функция добавления в историю (локально)
    function addToHistory(query) {
        const historyList = document.getElementById('historyList');

        // Проверяем, есть ли уже такой запрос
        const existing = Array.from(historyList.children).find(
            item => item.textContent === query
        );

        if (existing) {
            existing.remove();
        }

        // Создаём элемент истории
        const historyItem = document.createElement('p');
        historyItem.className = 'history-item';
        historyItem.textContent = query;

        historyItem.addEventListener('click', () => {
            searchInput.value = query;
            performSearch(query);
        });

        // Добавляем в начало списка
        historyList.insertBefore(historyItem, historyList.firstChild);

        // Ограничиваем историю 10 элементами
        if (historyList.children.length > 10) {
            historyList.removeChild(historyList.lastChild);
        }
    }
});