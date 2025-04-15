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