/**
 * memory_hiding.h - Модуль защиты памяти от анализа
 *
 * Модуль обеспечивает функциональность для защиты важных областей памяти
 * от анализа путем их шифрования, обфускации, и обнаружения попыток
 * отладки/дампа памяти.
 */

#ifndef _MEMORY_HIDING_H_
#define _MEMORY_HIDING_H_

#include "../../core/neurozond.h"
#include <windows.h>
#include <stdint.h>
#include <stdbool.h>

// Максимальное количество скрытых регионов памяти
#define MEM_HIDING_MAX_REGIONS 32

// Типы событий для модуля защиты памяти
typedef enum {
    MEM_HIDING_EVENT_DEBUGGER_DETECTED,    // Обнаружен отладчик
    MEM_HIDING_EVENT_MEMORY_DUMPING,       // Обнаружена попытка дампа памяти
    MEM_HIDING_EVENT_INTEGRITY_VIOLATION,  // Нарушение целостности памяти
    MEM_HIDING_EVENT_HOOK_DETECTED,        // Обнаружен хук
    MEM_HIDING_EVENT_REGION_ACCESSED       // Доступ к защищенной области
} MEM_HIDING_EVENT_TYPE;

// Структура для события модуля защиты памяти
typedef struct {
    MEM_HIDING_EVENT_TYPE type;  // Тип события
    PVOID memoryAddress;         // Адрес памяти, связанный с событием
    SIZE_T memorySize;           // Размер области памяти
    DWORD accessType;            // Тип доступа (чтение/запись/исполнение)
    DWORD processId;             // ID процесса, вызвавшего событие
    DWORD threadId;              // ID потока, вызвавшего событие
} MEM_HIDING_EVENT;

// Тип функции обратного вызова для обработки событий
typedef void (*MemHidingEventCallback)(MEM_HIDING_EVENT* eventInfo);

// Флаги для защиты памяти
typedef enum {
    MEM_HIDING_FLAG_ENCRYPT     = 0x0001,  // Шифровать память
    MEM_HIDING_FLAG_OBFUSCATE   = 0x0002,  // Обфускация памяти
    MEM_HIDING_FLAG_TRAP_ACCESS = 0x0004,  // Ловушка для доступа
    MEM_HIDING_FLAG_INTEGRITY   = 0x0008,  // Проверка целостности
    MEM_HIDING_FLAG_PREVENT_DUMP = 0x0010, // Предотвращение дампа
    MEM_HIDING_FLAG_AUTO_RESTORE = 0x0020  // Автоматическое восстановление
} MEM_HIDING_FLAGS;

// Структура для конфигурации модуля
typedef struct {
    BOOL enableAntiDebug;              // Включить обнаружение отладчика
    BOOL enableAntiDump;               // Включить защиту от дампа памяти
    BOOL enableCodeIntegrityChecks;    // Включить проверку целостности кода
    BOOL encryptMemoryWhenIdle;        // Шифровать память в простое
    DWORD memoryCheckInterval;         // Интервал проверки памяти (мс)
    MemHidingEventCallback callback;   // Обработчик событий
} MEM_HIDING_CONFIG;

// Инициализация модуля защиты памяти
NEUROZOND_STATUS MemHiding_Initialize(const MEM_HIDING_CONFIG* config);

// Освобождение ресурсов модуля
void MemHiding_Cleanup(void);

// Регистрация области памяти для защиты
NEUROZOND_STATUS MemHiding_ProtectMemoryRegion(
    PVOID baseAddress,
    SIZE_T size,
    MEM_HIDING_FLAGS flags,
    PVOID encryptionKey,
    SIZE_T keySize
);

// Временное снятие защиты с области памяти для использования
NEUROZOND_STATUS MemHiding_UnprotectMemoryRegion(
    PVOID baseAddress,
    SIZE_T size
);

// Восстановление защиты области памяти
NEUROZOND_STATUS MemHiding_ReprotectMemoryRegion(
    PVOID baseAddress,
    SIZE_T size
);

// Проверка наличия отладчика
BOOL MemHiding_IsDebuggerPresent(void);

// Проверка на попытки дампа памяти
BOOL MemHiding_IsMemoryBeingDumped(void);

// Установка защиты от дампа памяти
NEUROZOND_STATUS MemHiding_PreventMemoryDump(void);

// Проверка и восстановление целостности кода
NEUROZOND_STATUS MemHiding_CheckCodeIntegrity(
    PVOID baseAddress,
    SIZE_T size,
    BOOL autoRestore
);

// Шифрование области памяти
NEUROZOND_STATUS MemHiding_EncryptMemory(
    PVOID address,
    SIZE_T size,
    PVOID key,
    SIZE_T keySize
);

// Дешифрование области памяти
NEUROZOND_STATUS MemHiding_DecryptMemory(
    PVOID address,
    SIZE_T size,
    PVOID key,
    SIZE_T keySize
);

// Обфускация области памяти
NEUROZOND_STATUS MemHiding_ObfuscateMemory(
    PVOID address,
    SIZE_T size
);

// Деобфускация области памяти
NEUROZOND_STATUS MemHiding_DeobfuscateMemory(
    PVOID address,
    SIZE_T size
);

// Начать мониторинг целостности памяти
NEUROZOND_STATUS MemHiding_StartIntegrityMonitoring(
    PVOID baseAddress,
    SIZE_T size,
    DWORD checkInterval
);

// Остановить мониторинг целостности памяти
NEUROZOND_STATUS MemHiding_StopIntegrityMonitoring(
    PVOID baseAddress,
    SIZE_T size
);

// Обнаружение перехватов в памяти
NEUROZOND_STATUS MemHiding_DetectHooks(
    PVOID baseAddress,
    SIZE_T size,
    BOOL removeIfFound
);

// Установка обработчика событий
NEUROZOND_STATUS MemHiding_SetEventCallback(
    MemHidingEventCallback callback
);

// Получение статуса модуля
NEUROZOND_STATUS MemHiding_GetStatus(void);

#endif // _MEMORY_HIDING_H_ 