# NeuroZond C2 API Documentation

## Обзор
NeuroZond C2 - это API сервер для управления агентами NeuroZond в киберинфраструктуре. API предоставляет полный контроль над агентами, модулями и задачами, с возможностью интеграции с внешними системами.

## Базовый URL
```
http://your-server:8080
```

## Аутентификация
API использует сессионную аутентификацию и токены. Для доступа к защищенным эндпоинтам необходимо выполнить аутентификацию.

**POST /api/login**
```json
{
  "username": "admin",
  "password": "admin"
}
```

Ответ:
```json
{
  "status": "success",
  "token": "dummy_token"
}
```

## API Эндпоинты

### Общие

#### `GET /`
Получение базовой информации об API.

#### `GET /api/docs`
Получение списка доступных эндпоинтов API.

#### `GET /api/status`
Получение текущего статуса системы.

```json
{
  "status": "ok",
  "version": "2.0.0",
  "uptime": "3 hours 12 minutes",
  "connected_zonds": 1,
  "total_zonds": 2,
  "tasks_pending": 1,
  "tasks_total": 2
}
```

### Агенты

#### `GET /api/agents`
Получение списка агентов с возможностью фильтрации.

Параметры запроса:
- `status` - фильтр по статусу (active, inactive)
- `search` - поиск по тексту

#### `POST /api/agent/{agent_id}/command`
Отправка команды агенту.

```json
{
  "command": "whoami"
}
```

#### `POST /api/agent/{agent_id}/module/{module_id}`
Запуск модуля на агенте.

```json
{
  "params": {
    "duration": 60,
    "stealth": true
  }
}
```

### Зонды

#### `GET /api/zonds`
Получение списка зондов.

#### `GET /api/zonds/{zond_id}`
Получение информации о конкретном зонде.

#### `POST /api/zonds/{zond_id}/execute`
Выполнение команды на зонде.

```json
{
  "command": "scan_network"
}
```

### Задачи

#### `GET /api/tasks`
Получение списка задач.

#### `GET /api/tasks/{task_id}`
Получение информации о конкретной задаче.

### Файлы

#### `GET /api/files`
Получение списка файлов с возможностью поиска.

Параметры запроса:
- `search` - поиск по тексту (имя файла, агент, категория)

#### `POST /api/files/upload`
Загрузка файла. Используйте multipart/form-data.

Параметры формы:
- `file` - файл для загрузки
- `agent_id` - ID агента
- `category` - категория файла

#### `GET /api/files/download`
Скачивание файла.

Параметры запроса:
- `file_id` - ID файла

#### `POST /api/files/delete`
Удаление файлов.

```json
{
  "file_ids": ["file-1", "file-2"]
}
```

### Лут

#### `GET /api/loot`
Получение списка добытых данных.

Параметры запроса:
- `type` - фильтр по типу (card, wallet, etc.)
- `search` - поиск по тексту

### Метрики

#### `GET /api/metrics`
Получение метрик системы.

### Модули

#### `GET /api/modules`
Получение списка доступных модулей.

### LLM Интеграция

#### `POST /api/llm/query`
Отправка запроса в LLM для анализа и рекомендаций.

```json
{
  "query": "Проанализировать уязвимости системы",
  "context": {
    "agent_id": "agent-1",
    "system_info": "Windows 11, версия 22H2"
  }
}
```

#### `POST /api/agent/{agent_id}/autonomy`
Включение/выключение автономного режима для агента.

```json
{
  "enabled": true
}
```

## Интеграция с NeuroZond

API сервер интегрируется с ядром NeuroZond для полного контроля над агентами и выполнения сложных операций. Основные модули NeuroZond:

- **crypto** - Криптографический модуль
- **core** - Ядро системы
- **command** - Модуль выполнения команд
- **network** - Сетевые операции
- **injection** - Внедрение в процессы
- **evasion** - Обход защитных механизмов
- **probes** - Сбор информации

## Примеры использования

### Получение статуса системы
```bash
curl -X GET http://localhost:8080/api/status
```

### Авторизация
```bash
curl -X POST http://localhost:8080/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

### Запуск модуля на агенте
```bash
curl -X POST http://localhost:8080/api/agent/agent-1/module/keylogger \
  -H "Content-Type: application/json" \
  -d '{"params": {"duration": 60}}'
```

### Получение списка агентов
```bash
curl -X GET http://localhost:8080/api/agents?status=active
```

## Особенности безопасности

- Все коммуникации должны осуществляться по защищенному каналу (HTTPS)
- API требует обязательной аутентификации
- Рекомендуется использовать сложные пароли и токены
- При высоких требованиях к безопасности рекомендуется дополнительная аутентификация через клиентские сертификаты 