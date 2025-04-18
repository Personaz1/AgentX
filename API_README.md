# NeuroRAT S1 API Documentation

## Обзор
NeuroRAT S1 - это API сервер для управления зондами в киберинфраструктуре. API предоставляет полный контроль над зондами, модулями и задачами, с возможностью интеграции с внешними системами.

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

### Зонды

#### `GET /api/zonds`
Получение списка зондов с возможностью фильтрации.

Параметры запроса:
- `status` - фильтр по статусу (active, inactive)
- `search` - поиск по тексту

#### `POST /api/zond/{zond_id}/command`
Отправка команды зонду.

```json
{
  "command": "whoami"
}
```

#### `POST /api/zond/{zond_id}/module/{module_id}`
Запуск модуля на зонде.

```json
{
  "params": {
    "duration": 60,
    "stealth": true
  }
}
```

### Зонды

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
- `agent_id` - ID зонда
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