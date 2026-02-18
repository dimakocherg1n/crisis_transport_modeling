// Конфигурация
const API_BASE_URL = window.location.origin.includes('localhost')
    ? 'http://localhost:8000/api'
    : '/api';

let currentTab = 'scenarios';
let simulationInterval = null;
let simulationProgress = 0;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    console.log("Страница загружена! API URL:", API_BASE_URL);

    // Инициализация слайдера интенсивности
    const intensitySlider = document.getElementById('crisisIntensity');
    const intensityValue = document.getElementById('intensityValue');

    if (intensitySlider) {
        intensitySlider.addEventListener('input', function() {
            intensityValue.textContent = this.value;
        });
    }

    // Загрузка начальных данных
    loadScenarios();
    loadSimulationsForAnalytics();

    // Проверка соединения с API
    checkAPIHealth();
});

// Проверка здоровья API
async function checkAPIHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        if (response.ok) {
            console.log('API подключен:', data.message);
            // Показываем статус в углу
            showStatusIndicator('online', 'API подключен');
        } else {
            showNotification('API не отвечает правильно', 'error');
            showStatusIndicator('offline', 'API недоступен');
        }
    } catch (error) {
        console.warn('API недоступен:', error.message);
        showStatusIndicator('offline', 'Режим оффлайн');

        // В демо-режиме загружаем демо-данные
        setTimeout(() => {
            loadDemoScenarios();
            loadDemoScenariosForSimulation();
        }, 500);
    }
}

// Показать индикатор статуса
function showStatusIndicator(status, message) {
    const statusDiv = document.createElement('div');
    statusDiv.id = 'apiStatus';
    statusDiv.style.position = 'fixed';
    statusDiv.style.bottom = '10px';
    statusDiv.style.right = '10px';
    statusDiv.style.padding = '5px 10px';
    statusDiv.style.borderRadius = '5px';
    statusDiv.style.fontSize = '0.8rem';
    statusDiv.style.zIndex = '1000';
    statusDiv.innerHTML = `<i class="fas fa-${status === 'online' ? 'check-circle' : 'exclamation-triangle'}"></i> ${message}`;

    if (status === 'online') {
        statusDiv.style.background = 'rgba(46, 204, 113, 0.2)';
        statusDiv.style.color = '#27ae60';
        statusDiv.style.border = '1px solid #27ae60';
    } else {
        statusDiv.style.background = 'rgba(231, 76, 60, 0.2)';
        statusDiv.style.color = '#c0392b';
        statusDiv.style.border = '1px solid #c0392b';
    }

    // Удаляем старый индикатор если есть
    const oldStatus = document.getElementById('apiStatus');
    if (oldStatus) oldStatus.remove();

    document.body.appendChild(statusDiv);
}

// Остальной код frontend/app.js оставляем, но меняем все fetch запросы
// с `${API_BASE_URL}/api/...` на `${API_BASE_URL}/...`
// Пример для loadScenarios:
async function loadScenarios() {
    const scenariosList = document.getElementById('scenariosList');
    if (!scenariosList) return;

    try {
        const response = await fetch(`${API_BASE_URL}/scenarios`);

        if (response.ok) {
            const scenarios = await response.json();
            renderScenariosList(scenarios);
            showStatusIndicator('online', 'Данные загружены');
        } else {
            throw new Error('API недоступен');
        }
    } catch (error) {
        console.warn('Не удалось загрузить сценарии:', error);
        loadDemoScenarios();
    }
}

// Для createScenario:
async function createScenario() {
    const name = document.getElementById('scenarioName').value;
    const type = document.getElementById('scenarioType').value;
    const severity = document.getElementById('severity').value;
    const description = document.getElementById('description').value;

    if (!name.trim()) {
        showNotification('Введите название сценария', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/scenarios`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: name,
                scenario_type: type,
                severity: parseInt(severity),
                description: description,
                affected_area: 100,
                transport_modes: "road,rail"
            })
        });

        if (response.ok) {
            const result = await response.json();
            showNotification('Сценарий создан успешно!', 'success');
            loadScenarios();
            resetScenarioForm();
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка сервера');
        }
    } catch (error) {
        console.error('Ошибка создания сценария:', error);
        showNotification(`Ошибка: ${error.message}`, 'error');
    }
}

// Для startSimulation:
async function startSimulation() {
    const scenarioId = document.getElementById('simScenario').value;
    const simName = document.getElementById('simName').value;
    const duration = parseInt(document.getElementById('duration').value);
    const numVehicles = parseInt(document.getElementById('numVehicles').value);
    const crisisIntensity = parseFloat(document.getElementById('crisisIntensity').value);

    if (!scenarioId) {
        showNotification('Выберите сценарий для симуляции', 'error');
        return;
    }

    try {
        showNotification('Запуск симуляции...', 'info');

        const response = await fetch(`${API_BASE_URL}/simulate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                scenario_id: parseInt(scenarioId),
                name: simName,
                duration_hours: duration,
                num_vehicles: numVehicles,
                num_hubs: 5,
                crisis_intensity: crisisIntensity
            })
        });

        if (response.ok) {
            const result = await response.json();

            // Начинаем отслеживать прогресс
            startSimulationProgress(result, duration);

            showNotification('Симуляция запущена успешно!', 'success');
        } else {
            const error = await response.json();
            throw new Error(error.detail || 'Ошибка запуска симуляции');
        }
    } catch (error) {
        console.error('Ошибка запуска симуляции:', error);
        showNotification(`Ошибка: ${error.message}`, 'error');
    }
}