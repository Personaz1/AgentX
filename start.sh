#!/bin/bash
# NeuroRAT C2 Server Startup Script

# Определение цветов для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====== Запуск NeuroRAT с MCP и Gemini ======${NC}"

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

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 не установлен!${NC}"
    echo "Пожалуйста, установите Python 3"
    exit 1
fi

echo -e "${YELLOW}Проверка зависимостей...${NC}"
pip install -q google-generativeai uvicorn fastapi pydantic python-dotenv

# Останавливаем предыдущие Docker контейнеры
echo -e "${YELLOW}Останавливаем предыдущие контейнеры...${NC}"
docker-compose down

# Запускаем контейнеры
echo -e "${YELLOW}Запускаем Docker контейнеры...${NC}"
docker-compose up --build -d

# Проверяем, успешно ли запустились контейнеры
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Docker контейнеры успешно запущены!${NC}"
else
    echo -e "${RED}Ошибка при запуске Docker контейнеров!${NC}"
    exit 1
fi

# Проверяем наличие ключа API для Gemini
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}API ключ для Gemini не найден в .env. Пожалуйста, введите ключ (или оставьте пустым для пропуска):${NC}"
    read gemini_key
else
    echo -e "${GREEN}Используем API ключ Gemini из .env файла${NC}"
    gemini_key=$GEMINI_API_KEY
fi

# Запускаем MCP сервер
echo -e "${YELLOW}Запускаем MCP сервер...${NC}"
if [ -z "$gemini_key" ]; then
    # Без API ключа
    python3 start_mcp.py --skip-docker --host 0.0.0.0 --port 8089
else
    # С API ключом
    python3 start_mcp.py --skip-docker --host 0.0.0.0 --port 8089 --gemini-key "$gemini_key"
fi

echo -e "${BLUE}====== Завершение работы ======${NC}"
exit 0 