#!/bin/bash
# NeuroRAT C2 Server Startup Script

# Определение цветов для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====== Запуск NeuroRAT C2 Framework ======${NC}"

# Загрузка .env файла, если он существует
if [ -f .env ]; then
    echo -e "${GREEN}Найден .env файл, загружаем настройки...${NC}"
    source .env
fi

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker не установлен!${NC}"
    echo "Пожалуйста, установите Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Проверка наличия docker-compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose не установлен!${NC}"
    echo "Пожалуйста, установите Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Останавливаем предыдущие Docker контейнеры
echo -e "${YELLOW}Останавливаем предыдущие контейнеры...${NC}"
docker-compose down

# Запускаем контейнеры
echo -e "${YELLOW}Запускаем Docker контейнеры...${NC}"
docker-compose up --build -d

# Проверяем, успешно ли запустились контейнеры
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Docker контейнеры успешно запущены!${NC}"
    echo -e "${BLUE}Web интерфейс доступен по адресу:${NC} http://localhost:8080"
else
    echo -e "${RED}Ошибка при запуске Docker контейнеров!${NC}"
    exit 1
fi

echo -e "${BLUE}====== Завершение работы ======${NC}"
exit 0 