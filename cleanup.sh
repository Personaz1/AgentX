#!/bin/bash
# Скрипт для очистки проекта NeuroRAT от устаревших файлов и компонентов

# Определение цветов для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====== ОЧИСТКА ПРОЕКТА NEURORAT ======${NC}"
echo -e "${YELLOW}Этот скрипт удалит устаревшие файлы и компоненты${NC}"
echo -e "${RED}ВНИМАНИЕ: Перед запуском убедитесь, что у вас есть резервная копия!${NC}"
echo ""

# Запрос подтверждения
read -p "Вы уверены, что хотите продолжить? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Операция отменена.${NC}"
    exit 1
fi

# Переходим в корневую директорию проекта
cd "$(dirname "$0")"

echo -e "${YELLOW}1. Удаление устаревших директорий и файлов...${NC}"

# Список устаревших директорий
OLD_DIRS=("frontend")

for dir in "${OLD_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${YELLOW}Удаляем директорию: ${dir}${NC}"
        rm -rf "$dir"
        echo -e "${GREEN}Директория ${dir} удалена${NC}"
    else
        echo -e "${BLUE}Директория ${dir} не найдена, пропускаем${NC}"
    fi
done

# Удаление устаревших скриптов запуска
echo -e "${YELLOW}Удаляем устаревшие скрипты запуска...${NC}"
find . -maxdepth 1 -type f -name "start_*.sh" -delete
find . -maxdepth 1 -type f -name "launcher*.sh" -delete
find . -maxdepth 1 -type f -name "run*.sh" -not -name "start.sh" -delete

# Удаление временных файлов
echo -e "${YELLOW}Удаляем временные файлы...${NC}"
find . -type f -name "*_old.*" -delete
find . -type f -name "*.bak" -delete
find . -type f -name "*.tmp" -delete

echo -e "${YELLOW}2. Удаление кэшей сборки...${NC}"

# Удаление кэшей Python
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name ".pytest_cache" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Удаление кэшей Node.js
find . -name "node_modules" -type d -prune -exec rm -rf {} +

# Удаление временных логов
echo -e "${YELLOW}3. Очистка устаревших логов...${NC}"
find . -type f -name "*.log.old" -delete

echo -e "${YELLOW}4. Проверка структуры проекта...${NC}"

# Проверка наличия необходимых директорий
REQUIRED_DIRS=("admin-panel-new" "agent_modules")
MISSING_DIRS=0

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        echo -e "${RED}ВНИМАНИЕ: Директория ${dir} не найдена!${NC}"
        MISSING_DIRS=$((MISSING_DIRS+1))
    else
        echo -e "${GREEN}Директория ${dir} найдена${NC}"
    fi
done

if [ $MISSING_DIRS -gt 0 ]; then
    echo -e "${RED}ВНИМАНИЕ: Некоторые необходимые директории отсутствуют!${NC}"
else
    echo -e "${GREEN}Все необходимые директории присутствуют${NC}"
fi

# Проверка и настройка основного скрипта запуска
if [ ! -f "start.sh" ]; then
    echo -e "${RED}ВНИМАНИЕ: Основной скрипт запуска start.sh не найден!${NC}"
else
    echo -e "${GREEN}Настройка прав доступа для start.sh${NC}"
    chmod +x start.sh
fi

echo -e "${BLUE}====== ОЧИСТКА ЗАВЕРШЕНА ======${NC}"
echo -e "${GREEN}Проект очищен от устаревших файлов и компонентов${NC}"
echo -e "${YELLOW}Для запуска проекта используйте: ./start.sh${NC}"
exit 0 