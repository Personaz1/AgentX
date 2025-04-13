#!/bin/bash
# Запуск инструментов мониторинга для NeuroRAT

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========== NeuroRAT Монитор ===========${NC}"
echo -e "${YELLOW}Запуск инструментов мониторинга...${NC}"

# Определяем директорию со скриптом
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Функция для запуска мониторинга в терминале
run_terminal_monitor() {
    echo -e "${YELLOW}Запуск терминального интерфейса...${NC}"
    python3 brain_terminal.py
}

# Функция для запуска прокси-сервера
run_proxy_server() {
    echo -e "${YELLOW}Запуск API прокси-сервера на порту 8888...${NC}"
    python3 direct_proxy.py &
    PROXY_PID=$!
    echo -e "${GREEN}Прокси-сервер запущен с PID: $PROXY_PID${NC}"
    echo -e "${GREEN}Веб-интерфейс логов: http://localhost:8888/${NC}"
    echo -e "${GREEN}API прокси: http://localhost:8888/proxy/${NC}"
    echo $PROXY_PID > proxy.pid
}

# Функция для просмотра логов контейнеров
view_container_logs() {
    echo -e "${YELLOW}Просмотр логов контейнера neurorat-server...${NC}"
    echo -e "${YELLOW}Для выхода нажмите Ctrl+C${NC}"
    docker logs -f neurorat-server
}

# Функция для остановки прокси-сервера
stop_proxy_server() {
    if [ -f proxy.pid ]; then
        PID=$(cat proxy.pid)
        echo -e "${YELLOW}Остановка прокси-сервера (PID: $PID)...${NC}"
        kill $PID 2>/dev/null || true
        rm proxy.pid
        echo -e "${GREEN}Прокси-сервер остановлен${NC}"
    else
        echo -e "${RED}Файл PID не найден. Прокси-сервер не запущен?${NC}"
    fi
}

# Функция для запуска в Docker-контейнере
run_in_container() {
    echo -e "${YELLOW}Копирование скриптов в контейнер...${NC}"
    docker cp brain_terminal.py neurorat-server:/app/
    docker cp direct_proxy.py neurorat-server:/app/
    
    echo -e "${YELLOW}Запуск в контейнере...${NC}"
    docker exec -it neurorat-server bash -c "cd /app && python brain_terminal.py"
}

# Функция для открытия bash в контейнере
container_bash() {
    echo -e "${YELLOW}Открытие bash в контейнере...${NC}"
    docker exec -it neurorat-server /bin/bash
}

# Меню выбора
show_menu() {
    echo -e "\n${BLUE}Выберите действие:${NC}"
    echo -e "  ${GREEN}1)${NC} Запустить терминальный интерфейс"
    echo -e "  ${GREEN}2)${NC} Запустить API прокси-сервер с веб-интерфейсом"
    echo -e "  ${GREEN}3)${NC} Просмотр логов контейнера"
    echo -e "  ${GREEN}4)${NC} Остановить прокси-сервер"
    echo -e "  ${GREEN}5)${NC} Запустить терминальный интерфейс в контейнере"
    echo -e "  ${GREEN}6)${NC} Открыть bash в контейнере"
    echo -e "  ${GREEN}0)${NC} Выход"
    echo -ne "\n${BLUE}Ваш выбор:${NC} "
    read choice
    
    case $choice in
        1) run_terminal_monitor ;;
        2) run_proxy_server ;;
        3) view_container_logs ;;
        4) stop_proxy_server ;;
        5) run_in_container ;;
        6) container_bash ;;
        0) exit 0 ;;
        *) echo -e "${RED}Неверный выбор!${NC}" ;;
    esac
}

# Обработка аргументов командной строки
if [ $# -eq 0 ]; then
    # Интерактивный режим
    while true; do
        show_menu
    done
else
    # Режим с аргументами
    case $1 in
        "terminal") run_terminal_monitor ;;
        "proxy") run_proxy_server ;;
        "logs") view_container_logs ;;
        "stop-proxy") stop_proxy_server ;;
        "container") run_in_container ;;
        "bash") container_bash ;;
        *) 
            echo -e "${RED}Неизвестная команда: $1${NC}"
            echo -e "${YELLOW}Доступные команды: terminal, proxy, logs, stop-proxy, container, bash${NC}"
            exit 1
            ;;
    esac
fi 