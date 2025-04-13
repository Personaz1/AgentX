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

# Копирование файлов проекта
COPY . /app/

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# По умолчанию запускаем тестовый скрипт роевого интеллекта
CMD ["python", "test_swarm_isolated.py"]

# Контейнер слушает порт для коммуникации роевого интеллекта
EXPOSE 8443 