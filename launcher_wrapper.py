#!/usr/bin/env python3
"""
Wrapper для запуска neurorat_launcher с правильной настройкой путей Python
"""

import os
import sys
import logging
import socket
import subprocess
import time

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('launcher_wrapper.log')
    ]
)

logger = logging.getLogger('launcher_wrapper')

def check_network_connectivity(host, port):
    """Проверка сетевого соединения с сервером"""
    logger.info(f"Проверка соединения с {host}:{port}...")
    
    # Проверка DNS-резолвинга
    try:
        logger.info(f"DNS lookup для {host}")
        host_ip = socket.gethostbyname(host)
        logger.info(f"IP-адрес для {host}: {host_ip}")
    except socket.gaierror:
        logger.error(f"Не удалось разрешить имя хоста {host}")
        host_ip = host  # Если резолвинг не удался, попробуем использовать имя как IP
    
    # Ping сервера
    try:
        logger.info(f"Пингуем хост {host}")
        ping_cmd = f"ping -c 3 {host}"
        ping_result = subprocess.run(ping_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"Результат пинга: {ping_result.returncode}")
        if ping_result.stdout:
            logger.info(f"Вывод пинга: {ping_result.stdout.decode('utf-8', errors='ignore')}")
    except Exception as e:
        logger.error(f"Ошибка при выполнении ping: {str(e)}")
    
    # Проверка TCP-соединения
    try:
        logger.info(f"Проверка TCP-соединения с {host}:{port}")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        result = s.connect_ex((host, port))
        s.close()
        
        if result == 0:
            logger.info(f"Соединение с {host}:{port} успешно установлено")
            return True
        else:
            logger.error(f"Не удалось подключиться к {host}:{port}, код ошибки: {result}")
            return False
    except Exception as e:
        logger.error(f"Ошибка при проверке TCP-соединения: {str(e)}")
        return False

def main():
    """Основная функция для запуска neurorat_launcher"""
    # Получаем абсолютный путь текущего скрипта
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Добавляем текущую директорию в начало sys.path
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
        logger.info(f"Добавлен путь в sys.path: {current_dir}")
    
    # Выводим текущее значение sys.path для отладки
    logger.info(f"sys.path: {sys.path}")
    
    # Отображаем текущую рабочую директорию и содержимое
    cwd = os.getcwd()
    logger.info(f"Текущая рабочая директория: {cwd}")
    try:
        files = os.listdir(cwd)
        logger.info(f"Содержимое текущей директории: {files}")
    except Exception as e:
        logger.error(f"Ошибка при получении содержимого директории: {str(e)}")
    
    # Проверяем сеть и соединение с сервером до запуска
    if '--server' in sys.argv and '--port' in sys.argv:
        server_index = sys.argv.index('--server') + 1
        port_index = sys.argv.index('--port') + 1
        
        if len(sys.argv) > server_index and len(sys.argv) > port_index:
            server = sys.argv[server_index]
            port = int(sys.argv[port_index])
            logger.info(f"Проверка соединения с сервером {server}:{port} перед запуском")
            
            # Максимум 3 попытки с интервалом в 5 секунд
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                logger.info(f"Попытка подключения {attempt} из {max_attempts}")
                if check_network_connectivity(server, port):
                    logger.info(f"Соединение с сервером {server}:{port} установлено успешно")
                    break
                elif attempt < max_attempts:
                    logger.info(f"Ожидание 5 секунд перед следующей попыткой...")
                    time.sleep(5)
    
    # Проверяем доступность модуля agent_protocol
    try:
        import agent_protocol
        logger.info(f"Модуль agent_protocol успешно импортирован из {agent_protocol.__file__}")
        print(f"Модуль agent_protocol успешно импортирован из {agent_protocol.__file__}", flush=True)
    except ImportError as e:
        logger.error(f"Не удалось импортировать agent_protocol: {str(e)}")
        print(f"ОШИБКА: Не удалось импортировать agent_protocol: {str(e)}", flush=True)
        sys.exit(1)
    
    # Проверяем доступность подмодулей
    try:
        from agent_protocol import agent
        logger.info(f"Модуль agent_protocol.agent успешно импортирован")
        print(f"Модуль agent_protocol.agent успешно импортирован", flush=True)
    except ImportError as e:
        logger.error(f"Не удалось импортировать agent_protocol.agent: {str(e)}")
        print(f"ОШИБКА: Не удалось импортировать agent_protocol.agent: {str(e)}", flush=True)
        sys.exit(1)
    
    try:
        from agent_protocol.shared import key_exchange
        logger.info(f"Модуль agent_protocol.shared.key_exchange успешно импортирован")
        print(f"Модуль agent_protocol.shared.key_exchange успешно импортирован", flush=True)
    except ImportError as e:
        logger.error(f"Не удалось импортировать agent_protocol.shared.key_exchange: {str(e)}")
        print(f"ОШИБКА: Не удалось импортировать agent_protocol.shared.key_exchange: {str(e)}", flush=True)
        sys.exit(1)
    
    # Импортируем neurorat_launcher
    try:
        import neurorat_launcher
        logger.info(f"Модуль neurorat_launcher успешно импортирован из {neurorat_launcher.__file__}")
        print(f"Модуль neurorat_launcher успешно импортирован из {neurorat_launcher.__file__}", flush=True)
    except ImportError as e:
        logger.error(f"Не удалось импортировать neurorat_launcher: {str(e)}")
        print(f"ОШИБКА: Не удалось импортировать neurorat_launcher: {str(e)}", flush=True)
        sys.exit(1)
    
    # Запускаем main из neurorat_launcher
    logger.info("Запуск neurorat_launcher.main()")
    print("Запуск neurorat_launcher.main()", flush=True)
    
    # Подменяем sys.stdout и sys.stderr для перехвата вывода
    import io
    from threading import Thread

    class LoggedOutput(io.StringIO):
        def __init__(self, logger, level, original):
            super().__init__()
            self.logger = logger
            self.level = level
            self.original = original

        def write(self, s):
            if s.strip():
                self.logger.log(self.level, s.strip())
            if self.original:
                self.original.write(s)

        def flush(self):
            if self.original:
                self.original.flush()

    # Сохраняем оригинальные stdout и stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr

    # Заменяем их на объекты, которые будут логировать вывод
    sys.stdout = LoggedOutput(logger, logging.INFO, original_stdout)
    sys.stderr = LoggedOutput(logger, logging.ERROR, original_stderr)

    try:
        neurorat_launcher.main()
    except Exception as e:
        logger.error(f"Ошибка при запуске neurorat_launcher.main(): {str(e)}")
        print(f"ОШИБКА: Ошибка при запуске neurorat_launcher.main(): {str(e)}", flush=True)
        sys.exit(1)
    finally:
        # Восстанавливаем оригинальные stdout и stderr
        sys.stdout = original_stdout
        sys.stderr = original_stderr

if __name__ == "__main__":
    main() 