# Обновление Docker контейнера для работы с Gemini API

Для интеграции с Google Gemini API в проекте NeuroRAT необходимо внести следующие изменения в Docker контейнер.

## 1. Обновление файлов

Следующие файлы необходимо скопировать в контейнер:

- `api_integration.py` - обновленная версия с поддержкой Gemini 2.0 Flash
- `test_gemini.py` - скрипт для тестирования интеграции с Gemini API
- `test_brain.py` - скрипт для тестирования автономного мозга с Gemini API
- `autonomous_brain.py` - обновленная версия с поддержкой API

## 2. Обновление .env файла

Необходимо добавить в файл `.env` следующие переменные окружения:

```
# Путь к учетным данным Google API
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/service_account.json

# Настройки для Gemini API 
GEMINI_API_KEY
GEMINI_MODEL
```

Значения ключей и модели должны быть указаны в реальном .env файле.

## 3. Обновление Dockerfile

Добавьте следующие строки в Dockerfile для установки необходимых зависимостей:

```dockerfile
# Установка дополнительных зависимостей для Gemini API
RUN pip install --no-cache-dir python-dotenv requests
```

## 4. Создание каталога для учетных данных

```bash
mkdir -p credentials
```

## 5. Пересборка и запуск контейнера

```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## 6. Проверка интеграции

После запуска контейнера выполните:

```bash
docker exec -it neurorat-server bash
python test_gemini.py --prompt "Проверка работы Gemini API" --stream
```

## 7. Тестирование автономного мозга

```bash
docker exec -it neurorat-server bash
python test_brain.py --scenario data_collection --verbose
```

## Протоколирование

Для отладки интеграции с Gemini API и работы автономного мозга логи сохраняются в:

- `api_integration.log` - логи интеграции с API
- `llm_processor.log` - логи обработки запросов LLM
- `autonomous_brain.log` - логи автономного мозга

## Дополнительные файлы документации

- `gemini_integration_guide.md` - руководство по использованию Gemini API в проекте

## Безопасность

При использовании API ключей необходимо убедиться, что они не попадают в Git репозиторий. Все API ключи в `.env` файле должны быть защищены и не публиковаться в публичных репозиториях.

Для защиты API ключей рекомендуется использовать секреты Docker или переменные окружения, предоставляемые средой выполнения, вместо хранения их в файле. 