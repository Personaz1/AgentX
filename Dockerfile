FROM python:3.9-slim

LABEL maintainer="Mr. Thomas Anderson <iamtomasanderson@gmail.com>"
LABEL description="NeuroRAT Swarm Intelligence Test Environment (FOR RESEARCH ONLY)"

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    procps \
    net-tools \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Создание директории для хранения API ключей и учетных данных
RUN mkdir -p /app/credentials

# Копирование файлов проекта
COPY . /app/

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Установка python-dotenv для работы с .env файлами
RUN pip install --no-cache-dir python-dotenv

# Создаем директорию static для FastAPI (исправление ошибки "Directory 'static' does not exist")
RUN mkdir -p /app/static

# По умолчанию запускаем API сервер
CMD ["python", "server_api.py"]

# Экспортируем порты
EXPOSE 8080 5000 8443 