#!/bin/bash
# Запуск NeuroRAT C2 Server с API интеграцией

# Цвета для вывода
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========== NeuroRAT C2 Server ===========${NC}"
echo -e "${YELLOW}Автоматический запуск системы...${NC}"

# Проверяем наличие Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker не установлен. Пожалуйста, установите Docker и Docker Compose.${NC}"
    exit 1
fi

# Проверяем наличие файлов API ключей
if [ ! -f .env ]; then
    echo -e "${YELLOW}Файл .env не найден, создаю из шаблона...${NC}"
    cp .env.example .env
    echo -e "${RED}⚠️  ВНИМАНИЕ: Не забудьте заполнить настоящие API ключи в файле .env!${NC}"
fi

# Создаем необходимые директории
mkdir -p uploads logs credentials

# Останавливаем существующие контейнеры
echo -e "${YELLOW}Останавливаем существующие контейнеры...${NC}"
docker-compose down

# Собираем и запускаем систему
echo -e "${YELLOW}Собираем и запускаем контейнеры...${NC}"
docker-compose build && docker-compose up -d

# Ждем, пока система запустится
echo -e "${YELLOW}Ожидание запуска системы...${NC}"
sleep 5

# Проверяем статус контейнеров
if docker ps | grep -q "neurorat-server"; then
    echo -e "${GREEN}✅ NeuroRAT C2 Server успешно запущен!${NC}"
    echo -e "${GREEN}✅ Веб-интерфейс доступен по адресу: http://localhost:8080${NC}"
    
    # Проверяем доступность API
    if curl -s http://localhost:8080 > /dev/null; then
        echo -e "${GREEN}✅ API сервер отвечает${NC}"
    else
        echo -e "${RED}❌ API сервер не отвечает, проверьте логи${NC}"
    fi
    
    # Выводим логи для отладки
    echo -e "${YELLOW}Последние логи:${NC}"
    docker logs neurorat-server --tail 10
else
    echo -e "${RED}❌ Произошла ошибка при запуске системы${NC}"
    echo -e "${YELLOW}Логи запуска:${NC}"
    docker logs neurorat-server
fi

echo -e "${YELLOW}=========================================${NC}"
echo -e "${GREEN}Для остановки системы выполните: docker-compose down${NC}"
echo -e "${GREEN}Для просмотра логов: docker logs -f neurorat-server${NC}" 