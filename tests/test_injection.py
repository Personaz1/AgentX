#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Тесты для модуля внедрения кода (Injection)
"""

import os
import sys
import unittest
from unittest.mock import MagicMock, patch, ANY
import platform
import ctypes

# Добавляем корневую директорию проекта в путь импорта
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Импортируем тестируемый модуль и его компоненты
# Делаем это внутри блока try/except на случай запуска не на Windows
try:
    from agent_modules.injection.process_hollowing import (
        hollow_process,
        get_image_base_address,
        unmap_view,
        virtual_alloc,
        write_memory,
        modify_thread_context,
        resume_thread,
        # Импортируем структуры и константы, если они нужны для моков
        STARTUPINFO, PROCESS_INFORMATION, CONTEXT, PROCESS_BASIC_INFORMATION, PEB,
        CREATE_SUSPENDED, PAGE_EXECUTE_READWRITE, MEM_COMMIT, MEM_RESERVE
    )
    # Определяем базовые типы wintypes для моков
    from ctypes.wintypes import HANDLE, DWORD, LPBYTE, LPWSTR, WORD, ULONG, PVOID
    IS_WINDOWS = True
except (ImportError, AttributeError):
    # Если запуск не на Windows, модуль может не импортироваться полностью
    # Создаем заглушки для тестов
    hollow_process = MagicMock(return_value=False)
    get_image_base_address = MagicMock(return_value=None)
    unmap_view = MagicMock(return_value=False)
    virtual_alloc = MagicMock(return_value=None)
    write_memory = MagicMock(return_value=False)
    modify_thread_context = MagicMock(return_value=False)
    resume_thread = MagicMock(return_value=False)
    # Заглушки для типов
    HANDLE = MagicMock
    DWORD = MagicMock
    STARTUPINFO = MagicMock
    PROCESS_INFORMATION = MagicMock
    CONTEXT = MagicMock
    IS_WINDOWS = False

@unittest.skipUnless(IS_WINDOWS, "Тесты Process Hollowing требуют Windows API")
class TestProcessHollowing(unittest.TestCase):
    """Тесты для модуля Process Hollowing"""

    def setUp(self):
        """Настройка перед каждым тестом"""
        self.target_path = "C:\\Windows\\System32\\notepad.exe"
        self.payload = b"\x90\x90\xC3" # Простой шеллкод (NOP, NOP, RET)
        self.h_process = HANDLE(1234) # Фиктивный хендл процесса
        self.h_thread = HANDLE(5678)  # Фиктивный хендл потока
        self.pid = 1111
        self.tid = 2222
        self.image_base = 0x400000
        self.payload_address = 0x500000
        
        # Создаем базовые моки для структур
        self.mock_startup_info = STARTUPINFO()
        self.mock_process_info = PROCESS_INFORMATION()
        self.mock_process_info.hProcess = self.h_process
        self.mock_process_info.hThread = self.h_thread
        self.mock_process_info.dwProcessId = self.pid
        self.mock_process_info.dwThreadId = self.tid
        
        self.mock_context = CONTEXT()
        # Устанавливаем фиктивные значения для полей контекста, если необходимо
        if hasattr(self.mock_context, 'Rcx'):
            self.mock_context.Rcx = 0x7FFFFFFF # Пример
        if hasattr(self.mock_context, 'Eax'):
             self.mock_context.Eax = 0x7FFFFFFF # Пример

    # --- Тесты для вспомогательных функций --- 

    @patch('agent_modules.injection.process_hollowing.ctypes.WinDLL')
    def test_get_image_base_address_success(self, mock_windll):
        """Тест успешного получения базового адреса (с заглушкой чтения PEB)"""
        mock_ntdll = MagicMock()
        mock_windll.return_value = mock_ntdll
        mock_ntdll.NtQueryInformationProcess.return_value = 0 # STATUS_SUCCESS
        
        # Мокаем byref и sizeof для PROCESS_BASIC_INFORMATION
        with patch('agent_modules.injection.process_hollowing.ctypes.byref') as mock_byref, \
             patch('agent_modules.injection.process_hollowing.ctypes.sizeof') as mock_sizeof:
            # Имитируем, что NtQueryInformationProcess заполняет структуру
            def query_effect(*args):
                # args[2] это byref(pbi)
                # Здесь мы могли бы изменить мок pbi, но пока это не нужно,
                # так как реальное чтение PEB - заглушка.
                # Главное, что функция возвращает 0.
                return 0
            mock_ntdll.NtQueryInformationProcess.side_effect = query_effect
            
            # Ожидаем получить адрес-заглушку 0x400000
            base_addr = get_image_base_address(self.h_process)
            self.assertEqual(base_addr, 0x400000)
            mock_ntdll.NtQueryInformationProcess.assert_called_once()

    # TODO: Добавить тесты для ошибок get_image_base_address

    @patch('agent_modules.injection.process_hollowing.ctypes.WinDLL')
    def test_unmap_view_success(self, mock_windll):
        """Тест успешного вызова NtUnmapViewOfSection"""
        mock_ntdll = MagicMock()
        mock_windll.return_value = mock_ntdll
        mock_ntdll.NtUnmapViewOfSection.return_value = 0 # STATUS_SUCCESS
        
        self.assertTrue(unmap_view(self.h_process, self.image_base))
        mock_ntdll.NtUnmapViewOfSection.assert_called_once_with(self.h_process, self.image_base)

    # TODO: Добавить тесты для ошибок unmap_view

    @patch('agent_modules.injection.process_hollowing.ctypes.WinDLL')
    def test_virtual_alloc_success(self, mock_windll):
        """Тест успешного выделения памяти VirtualAllocEx"""
        mock_kernel32 = MagicMock()
        mock_windll.return_value = mock_kernel32
        mock_kernel32.VirtualAllocEx.return_value = self.payload_address # Успешно выделено
        
        addr = virtual_alloc(self.h_process, self.image_base, len(self.payload))
        self.assertEqual(addr, self.payload_address)
        mock_kernel32.VirtualAllocEx.assert_called_once()

    # TODO: Добавить тесты для ошибок virtual_alloc (включая попытку по другому адресу)

    @patch('agent_modules.injection.process_hollowing.ctypes.WinDLL')
    def test_write_memory_success(self, mock_windll):
        """Тест успешной записи памяти WriteProcessMemory"""
        mock_kernel32 = MagicMock()
        mock_windll.return_value = mock_kernel32
        mock_kernel32.WriteProcessMemory.return_value = True # Успешно
        
        # Мокаем byref для bytes_written
        with patch('agent_modules.injection.process_hollowing.ctypes.byref') as mock_byref:
             # Имитируем запись правильного кол-ва байт
             def write_effect(*args):
                 # args[4] это byref(bytes_written)
                 # Здесь нужно изменить значение мока bytes_written.value
                 # Это сложно, т.к. bytes_written создается внутри функции.
                 # Проще проверить, что WriteProcessMemory вернула True.
                 return True
             mock_kernel32.WriteProcessMemory.side_effect = write_effect
             # Для полной проверки можно пропатчить DWORD и его .value
             with patch('agent_modules.injection.process_hollowing.DWORD') as mock_dword:
                  mock_dword_inst = MagicMock()
                  mock_dword_inst.value = len(self.payload)
                  mock_dword.return_value = mock_dword_inst
                  self.assertTrue(write_memory(self.h_process, self.payload_address, self.payload))
                  
        mock_kernel32.WriteProcessMemory.assert_called_once()

    # TODO: Добавить тесты для ошибок write_memory

    @patch('agent_modules.injection.process_hollowing.ctypes.WinDLL')
    def test_modify_thread_context_success(self, mock_windll):
        """Тест успешного изменения контекста потока"""
        mock_kernel32 = MagicMock()
        mock_windll.return_value = mock_kernel32
        mock_kernel32.GetThreadContext.return_value = True # Успех
        mock_kernel32.SetThreadContext.return_value = True # Успех
        
        with patch('agent_modules.injection.process_hollowing.ctypes.byref') as mock_byref, \
             patch('agent_modules.injection.process_hollowing.CONTEXT') as mock_context_cls:
             mock_context_inst = self.mock_context # Используем наш преднастроенный мок
             mock_context_cls.return_value = mock_context_inst
             
             self.assertTrue(modify_thread_context(self.h_thread, self.payload_address))
             
             # Проверяем, что точка входа была изменена
             if platform.machine().endswith('64'):
                 self.assertEqual(mock_context_inst.Rcx, self.payload_address)
             else:
                 self.assertEqual(mock_context_inst.Eax, self.payload_address)
                 
             mock_kernel32.GetThreadContext.assert_called_once()
             mock_kernel32.SetThreadContext.assert_called_once()
             
    # TODO: Добавить тесты для ошибок modify_thread_context

    @patch('agent_modules.injection.process_hollowing.ctypes.WinDLL')
    def test_resume_thread_success(self, mock_windll):
        """Тест успешного возобновления потока"""
        mock_kernel32 = MagicMock()
        mock_windll.return_value = mock_kernel32
        mock_kernel32.ResumeThread.return_value = 1 # Успех (вернул > -1)
        
        self.assertTrue(resume_thread(self.h_thread))
        mock_kernel32.ResumeThread.assert_called_once_with(self.h_thread)

    # TODO: Добавить тесты для ошибок resume_thread

    # --- Тесты для основной функции hollow_process --- 
    
    @patch('agent_modules.injection.process_hollowing.resume_thread')
    @patch('agent_modules.injection.process_hollowing.modify_thread_context')
    @patch('agent_modules.injection.process_hollowing.write_memory')
    @patch('agent_modules.injection.process_hollowing.virtual_alloc')
    @patch('agent_modules.injection.process_hollowing.unmap_view')
    @patch('agent_modules.injection.process_hollowing.get_image_base_address')
    @patch('agent_modules.injection.process_hollowing.ctypes.WinDLL')
    @patch('agent_modules.injection.process_hollowing.ctypes.byref')
    @patch('agent_modules.injection.process_hollowing.ctypes.sizeof')
    def test_hollow_process_success(self, mock_sizeof, mock_byref, mock_windll, 
                                  mock_get_base, mock_unmap, mock_alloc, mock_write, 
                                  mock_modify_context, mock_resume):
        """Тест успешного выполнения hollow_process"""
        # Настраиваем мок для CreateProcessW
        mock_kernel32 = MagicMock()
        mock_windll.return_value = mock_kernel32
        mock_kernel32.CreateProcessW.return_value = True # Успешное создание
        # Настраиваем мок byref для PROCESS_INFORMATION
        def byref_effect(arg):
            if isinstance(arg, PROCESS_INFORMATION):
                arg.hProcess = self.h_process
                arg.hThread = self.h_thread
                arg.dwProcessId = self.pid
                arg.dwThreadId = self.tid
            return MagicMock()
        mock_byref.side_effect = byref_effect
        mock_sizeof.return_value = 100 # Размер STARTUPINFO
        mock_kernel32.CloseHandle.return_value = True

        # Настраиваем успешный возврат для всех шагов
        mock_get_base.return_value = self.image_base
        mock_unmap.return_value = True
        mock_alloc.return_value = self.payload_address
        mock_write.return_value = True
        mock_modify_context.return_value = True
        mock_resume.return_value = True
        
        self.assertTrue(hollow_process(self.target_path, self.payload))
        
        # Проверяем вызовы
        mock_kernel32.CreateProcessW.assert_called_once()
        mock_get_base.assert_called_once_with(self.h_process)
        mock_unmap.assert_called_once_with(self.h_process, self.image_base)
        mock_alloc.assert_called_once_with(self.h_process, self.image_base, len(self.payload))
        mock_write.assert_called_once_with(self.h_process, self.payload_address, self.payload)
        mock_modify_context.assert_called_once_with(self.h_thread, self.payload_address)
        mock_resume.assert_called_once_with(self.h_thread)
        self.assertEqual(mock_kernel32.CloseHandle.call_count, 2) # Закрыли поток и процесс

    # TODO: Добавить тесты для различных ошибок в hollow_process
    # TODO: Добавить тесты для non-Windows

if __name__ == "__main__":
    # Пропускаем запуск тестов напрямую, если не Windows
    if IS_WINDOWS:
        unittest.main()
    else:
        print("Тесты Process Hollowing требуют Windows API и пропускаются на этой платформе.") 