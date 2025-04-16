#!/bin/bash
# NeuroRAT C2 Framework - Скрипт запуска сервера
# Автор: iamtomasanderson@gmail.com
# GitHub: https://github.com/Personaz1

# Определение цветов для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====== Запуск NeuroRAT C2 Framework ======${NC}"

# Переходим в корневую директорию проекта
cd "$(dirname "$0")"

# Проверка, запущен ли уже сервер
if pgrep -f "python3 server.py" > /dev/null; then
    echo -e "${YELLOW}Сервер уже запущен. Останавливаем...${NC}"
    pkill -f "python3 server.py"
    sleep 2
fi

# Активация виртуального окружения
if [ -d "venv" ]; then
    echo -e "${GREEN}Активация виртуального окружения...${NC}"
    source venv/bin/activate
else
    echo -e "${RED}Виртуальное окружение не найдено. Запустите сначала ./deploy.sh${NC}"
    exit 1
fi

# Проверка наличия файла .env
if [ ! -f ".env" ]; then
    echo -e "${RED}Файл .env не найден. Запустите сначала ./deploy.sh${NC}"
    exit 1
fi

# Загрузка .env файла
echo -e "${GREEN}Загрузка конфигурации из .env...${NC}"
source .env

# Запуск мониторинга логов в отдельном экране
if command -v screen &> /dev/null; then
    # Если screen установлен, запускаем отдельные сессии для сервера и логов
    echo -e "${GREEN}Запуск сервера в screen...${NC}"
    
    # Завершаем существующие сессии, если они есть
    screen -ls | grep "neurorat" | cut -d. -f1 | awk '{print $1}' | xargs -I{} screen -S {} -X quit > /dev/null 2>&1
    
    # Запускаем сервер в отдельной screen-сессии
    screen -dmS neurorat-server bash -c "source venv/bin/activate && python3 server.py; exec bash"
    
    # Запускаем монитор логов в отдельной screen-сессии
    screen -dmS neurorat-logs bash -c "tail -f logs/server.log; exec bash"
    
    echo -e "${YELLOW}Сервер запущен в screen-сессии 'neurorat-server'${NC}"
    echo -e "${YELLOW}Для подключения к серверу: ${GREEN}screen -r neurorat-server${NC}"
    echo -e "${YELLOW}Для просмотра логов: ${GREEN}screen -r neurorat-logs${NC}"
else
    # Если screen не установлен, запускаем сервер в фоновом режиме
    echo -e "${YELLOW}Запуск сервера в фоновом режиме...${NC}"
    mkdir -p logs
    nohup python3 server.py > logs/nohup.out 2>&1 &
    
    echo -e "${GREEN}Сервер запущен в фоновом режиме. PID: $!${NC}"
    echo -e "${YELLOW}Для просмотра логов: ${GREEN}tail -f logs/server.log${NC}"
fi

# Создание директории для логов, если её нет
if [ ! -d "logs" ]; then
    mkdir -p logs
    echo -e "${GREEN}Создана директория для логов${NC}"
fi

# Вывод информации о доступе
echo -e "${BLUE}Информация о доступе к C2 Framework:${NC}"
echo -e "${BLUE}=====================================${NC}"
echo -e "${YELLOW}Панель администратора доступна по адресу:${NC}"
echo -e "${GREEN}http://$(hostname -I | awk '{print $1}'):${SERVER_PORT:-8080}/admin${NC}"
echo -e "${YELLOW}Логин: ${GREEN}${ADMIN_USERNAME:-admin}${NC}"
echo -e "${YELLOW}Пароль: ${GREEN}${ADMIN_PASSWORD:-admin}${NC}"
echo -e "${BLUE}=====================================${NC}"

echo -e "${BLUE}====== NeuroRAT C2 Framework запущен ======${NC}"
exit 0 