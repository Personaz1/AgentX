#!/bin/bash
# NeuroRAT C2 Framework - Скрипт запуска сервера
# Автор: iamtomasanderson@gmail.com
# GitHub: https://github.com/Personaz1

# Определение цветов для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}====== Запуск NeuroRAT C2 Framework ======${NC}"

# Переходим в корневую директорию проекта
cd "$(dirname "$0")"

# Создаем необходимые директории, если их нет
mkdir -p logs

# Проверка, работает ли уже сервер
if screen -list | grep -q "neurorat-server"; then
    echo -e "${YELLOW}Сервер уже запущен. Останавливаем...${NC}"
    screen -S neurorat-server -X quit
    sleep 2
fi

# Активация виртуального окружения
if [ -d "venv" ]; then
    echo -e "${GREEN}Виртуальное окружение активировано${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}Виртуальное окружение не найдено. Создание...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    echo -e "${GREEN}Виртуальное окружение создано и активировано${NC}"
fi

# Проверка наличия .env файла
if [ -f ".env" ]; then
    echo -e "${GREEN}Найден .env файл, загружаем настройки...${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${YELLOW}Файл .env не найден. Используем стандартные настройки.${NC}"
fi

# Создание необходимых директорий, если их нет
echo -e "${BLUE}Проверка структуры директорий...${NC}"
mkdir -p logs assets/{mcp,docs,logs,scripts,config,models} core server builders

# Компиляция фронтенда
echo -e "${BLUE}Компиляция панели администратора...${NC}"

if [ ! -d "neurorat-ui/dist" ]; then
    echo -e "${YELLOW}Установка зависимостей...${NC}"
    cd neurorat-ui
    npm install
    echo -e "${GREEN}Сборка фронтенда...${NC}"
    npm run build
    cd ..
    echo -e "${GREEN}Фронтенд успешно собран!${NC}"
else
    # Проверим, нужна ли пересборка
    if [ -n "$(find neurorat-ui/src -newer neurorat-ui/dist -type f 2>/dev/null)" ]; then
        echo -e "${YELLOW}Обнаружены изменения в исходном коде. Пересборка фронтенда...${NC}"
        cd neurorat-ui
        npm run build
        cd ..
        echo -e "${GREEN}Фронтенд успешно пересобран!${NC}"
    else
        echo -e "${GREEN}Фронтенд актуален.${NC}"
    fi
fi

# Настройка nginx (если установлен)
if command -v nginx &> /dev/null; then
    echo -e "${BLUE}Настройка Nginx...${NC}"
    sudo cp nginx/neurorat /etc/nginx/sites-available/
    sudo ln -sf /etc/nginx/sites-available/neurorat /etc/nginx/sites-enabled/
    
    echo -e "${BLUE}Проверка конфигурации Nginx...${NC}"
    if sudo nginx -t; then
        sudo systemctl restart nginx
        echo -e "${GREEN}Nginx настроен и перезапущен!${NC}"
    else
        echo -e "${RED}Ошибка в конфигурации Nginx!${NC}"
    fi
else
    echo -e "${YELLOW}Nginx не установлен или не найден. Пропускаем настройку.${NC}"
fi

# Запуск сервера в screen
echo -e "${YELLOW}Останавливаем предыдущую сессию сервера...${NC}"

if screen -list | grep -q "neurorat-server"; then
    screen -S neurorat-server -X quit
    sleep 2
fi

echo -e "${YELLOW}Активация виртуального окружения...${NC}"
source venv/bin/activate 2>/dev/null || echo -e "${YELLOW}Виртуальное окружение не найдено, используем системный Python${NC}"

echo -e "${YELLOW}Загрузка конфигурации из .env...${NC}"
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs) 2>/dev/null
fi

echo -e "${YELLOW}Запуск сервера в screen...${NC}"
screen -dmS neurorat-server python server.py
echo -e "${GREEN}Сервер запущен в screen-сессии 'neurorat-server'${NC}"
echo -e "${CYAN}Для подключения к серверу: ${GREEN}screen -r neurorat-server${NC}"
echo -e "${CYAN}Для просмотра логов: ${GREEN}tail -f logs/server.log${NC}"

echo -e "${GREEN}Информация о доступе к C2 Framework:${NC}"
echo -e "========================================"
echo -e "${CYAN}Панель администратора доступна по адресу:${NC}"
echo -e "${GREEN}http://$(hostname -I | awk '{print $1}'):8080${NC}"
echo -e "${CYAN}Логин: ${GREEN}admin${NC}"
echo -e "${CYAN}Пароль: ${GREEN}admin${NC} (по умолчанию) или установленный вами"
echo -e "========================================"

echo -e "${YELLOW}Дополнительные команды:${NC}"
echo -e "${CYAN}Запуск фронтенда в режиме разработки: ${GREEN}cd neurorat-ui && npm run dev${NC}"
echo -e "${CYAN}Просмотр логов сервера: ${GREEN}tail -f logs/server.log${NC}"
echo -e "${PURPLE}====== NeuroRAT C2 Framework запущен ======${NC}"
exit 0 