/**
 * memory_hiding.c - Реализация модуля защиты памяти
 * 
 * Этот модуль предоставляет функциональность для защиты важных областей памяти
 * от анализа. Включает технологии шифрования, обфускации, обнаружения отладчиков
 * и защиты от дампа памяти.
 */

#include "memory_hiding.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <tlhelp32.h>
#include <winternl.h>

// Определения структур, необходимых для работы модуля
typedef struct _MEMORY_CONTEXT {
    void*   address;        // Адрес зашифрованной области
    SIZE_T  size;           // Размер области
    BYTE*   key;            // Ключ шифрования
    SIZE_T  keySize;        // Размер ключа
    DWORD   originalProtect; // Исходные права доступа
} MEMORY_CONTEXT, *PMEMORY_CONTEXT;

typedef struct _HIDDEN_REGION {
    void*   address;        // Адрес скрытого региона
    SIZE_T  size;           // Размер региона
    DWORD   originalProtect; // Исходные права доступа
    struct _HIDDEN_REGION* next; // Указатель на следующий элемент списка
} HIDDEN_REGION, *PHIDDEN_REGION;

// Глобальные переменные
static PHIDDEN_REGION g_hiddenRegions = NULL;
static MemHide_ScanDetectionCallback g_scanCallback = NULL;
static MemHide_InjectionCallback g_injectionCallback = NULL;
static BOOL g_initialized = FALSE;

// Функция генерации псевдослучайных чисел для ключей
static DWORD GenerateRandomValue(void) {
    static DWORD seed = 0;
    if (seed == 0) {
        seed = GetTickCount();
    }
    seed = seed * 1103515245 + 12345;
    return (seed >> 16) & 0x7FFF;
}

// Генерация случайного ключа
static BYTE* GenerateRandomKey(SIZE_T size) {
    BYTE* key = (BYTE*)malloc(size);
    if (key) {
        for (SIZE_T i = 0; i < size; i++) {
            key[i] = (BYTE)GenerateRandomValue();
        }
    }
    return key;
}

// Функция для XOR-шифрования блока памяти
static void XorMemory(BYTE* data, SIZE_T size, const BYTE* key, SIZE_T keySize) {
    for (SIZE_T i = 0; i < size; i++) {
        data[i] ^= key[i % keySize];
    }
}

// Операции работы со списком скрытых регионов
static BOOL AddHiddenRegion(void* address, SIZE_T size, DWORD protect) {
    PHIDDEN_REGION region = (PHIDDEN_REGION)malloc(sizeof(HIDDEN_REGION));
    if (!region) {
        return FALSE;
    }
    
    region->address = address;
    region->size = size;
    region->originalProtect = protect;
    region->next = g_hiddenRegions;
    g_hiddenRegions = region;
    
    return TRUE;
}

static PHIDDEN_REGION FindHiddenRegion(void* address) {
    PHIDDEN_REGION current = g_hiddenRegions;
    
    while (current) {
        if (current->address == address) {
            return current;
        }
        current = current->next;
    }
    
    return NULL;
}

static BOOL RemoveHiddenRegion(void* address) {
    PHIDDEN_REGION current = g_hiddenRegions;
    PHIDDEN_REGION prev = NULL;
    
    while (current) {
        if (current->address == address) {
            if (prev) {
                prev->next = current->next;
            } else {
                g_hiddenRegions = current->next;
            }
            free(current);
            return TRUE;
        }
        prev = current;
        current = current->next;
    }
    
    return FALSE;
}

// Устанавливает перехватчик исключений для защиты важных страниц памяти
static LONG WINAPI VectoredExceptionHandler(PEXCEPTION_POINTERS exceptionInfo) {
    // Проверка, что исключение связано с доступом к памяти
    if (exceptionInfo->ExceptionRecord->ExceptionCode == EXCEPTION_ACCESS_VIOLATION) {
        ULONG_PTR accessAddress = exceptionInfo->ExceptionRecord->ExceptionInformation[1];
        
        // Проверка всех скрытых регионов
        PHIDDEN_REGION current = g_hiddenRegions;
        while (current) {
            ULONG_PTR regionStart = (ULONG_PTR)current->address;
            ULONG_PTR regionEnd = regionStart + current->size;
            
            // Если адрес доступа внутри скрытого региона
            if (accessAddress >= regionStart && accessAddress < regionEnd) {
                // Если настроен callback для обнаружения сканирования
                if (g_scanCallback) {
                    DWORD currentProcessId = GetCurrentProcessId();
                    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
                    
                    if (hSnapshot != INVALID_HANDLE_VALUE) {
                        PROCESSENTRY32 pe32;
                        pe32.dwSize = sizeof(PROCESSENTRY32);
                        
                        if (Process32First(hSnapshot, &pe32)) {
                            do {
                                if (pe32.th32ProcessID != currentProcessId) {
                                    // Вызываем callback с ID процесса-сканера
                                    g_scanCallback(pe32.th32ProcessID);
                                    break;
                                }
                            } while (Process32Next(hSnapshot, &pe32));
                        }
                        CloseHandle(hSnapshot);
                    }
                }
                
                // Возвращаем EXCEPTION_CONTINUE_EXECUTION для игнорирования доступа
                return EXCEPTION_CONTINUE_EXECUTION;
            }
            
            current = current->next;
        }
    }
    
    // Для других исключений продолжаем обычную обработку
    return EXCEPTION_CONTINUE_SEARCH;
}

// Публичные функции модуля

BOOL MemHide_Initialize(void) {
    if (g_initialized) {
        return TRUE; // Уже инициализирован
    }
    
    // Регистрация обработчика исключений
    AddVectoredExceptionHandler(1, VectoredExceptionHandler);
    
    g_initialized = TRUE;
    return TRUE;
}

void MemHide_Cleanup(void) {
    if (!g_initialized) {
        return;
    }
    
    // Удаление всех скрытых регионов
    PHIDDEN_REGION current = g_hiddenRegions;
    while (current) {
        PHIDDEN_REGION next = current->next;
        
        // Восстановление оригинальной защиты
        DWORD oldProtect;
        VirtualProtect(current->address, current->size, current->originalProtect, &oldProtect);
        
        free(current);
        current = next;
    }
    
    g_hiddenRegions = NULL;
    g_scanCallback = NULL;
    g_injectionCallback = NULL;
    g_initialized = FALSE;
}

BOOL MemHide_EncryptMemory(void* address, SIZE_T size, const BYTE* key, SIZE_T keySize, void** context) {
    if (!address || size == 0 || !context) {
        return FALSE;
    }
    
    // Создание контекста для хранения информации о зашифрованной области
    PMEMORY_CONTEXT memContext = (PMEMORY_CONTEXT)malloc(sizeof(MEMORY_CONTEXT));
    if (!memContext) {
        return FALSE;
    }
    
    // Генерация ключа, если не указан
    BYTE* useKey = NULL;
    if (key && keySize > 0) {
        useKey = (BYTE*)malloc(keySize);
        if (!useKey) {
            free(memContext);
            return FALSE;
        }
        memcpy(useKey, key, keySize);
    } else {
        keySize = 16; // Размер ключа по умолчанию
        useKey = GenerateRandomKey(keySize);
        if (!useKey) {
            free(memContext);
            return FALSE;
        }
    }
    
    // Изменение прав доступа к памяти для записи
    DWORD oldProtect;
    if (!VirtualProtect(address, size, PAGE_READWRITE, &oldProtect)) {
        free(useKey);
        free(memContext);
        return FALSE;
    }
    
    // Шифрование данных
    XorMemory((BYTE*)address, size, useKey, keySize);
    
    // Восстановление исходных прав доступа
    DWORD tempProtect;
    VirtualProtect(address, size, oldProtect, &tempProtect);
    
    // Заполнение структуры контекста
    memContext->address = address;
    memContext->size = size;
    memContext->key = useKey;
    memContext->keySize = keySize;
    memContext->originalProtect = oldProtect;
    
    *context = memContext;
    return TRUE;
}

BOOL MemHide_DecryptMemory(void* context) {
    if (!context) {
        return FALSE;
    }
    
    PMEMORY_CONTEXT memContext = (PMEMORY_CONTEXT)context;
    
    // Изменение прав доступа к памяти для записи
    DWORD oldProtect;
    if (!VirtualProtect(memContext->address, memContext->size, PAGE_READWRITE, &oldProtect)) {
        return FALSE;
    }
    
    // Дешифрование данных (повторное применение XOR с тем же ключом)
    XorMemory((BYTE*)memContext->address, memContext->size, memContext->key, memContext->keySize);
    
    // Восстановление исходных прав доступа
    DWORD tempProtect;
    VirtualProtect(memContext->address, memContext->size, memContext->originalProtect, &tempProtect);
    
    // Освобождение ресурсов
    free(memContext->key);
    free(memContext);
    
    return TRUE;
}

BOOL MemHide_ObfuscateMemory(void* address, SIZE_T size, const BYTE* key, SIZE_T keySize) {
    if (!address || size == 0 || !key || keySize == 0) {
        return FALSE;
    }
    
    // Изменение прав доступа к памяти для записи
    DWORD oldProtect;
    if (!VirtualProtect(address, size, PAGE_READWRITE, &oldProtect)) {
        return FALSE;
    }
    
    // Обфускация данных с помощью XOR
    XorMemory((BYTE*)address, size, key, keySize);
    
    // Восстановление исходных прав доступа
    DWORD tempProtect;
    VirtualProtect(address, size, oldProtect, &tempProtect);
    
    return TRUE;
}

BOOL MemHide_IsDebuggerPresent(void) {
    // Простая проверка наличия отладчика
    if (IsDebuggerPresent()) {
        return TRUE;
    }
    
    // Проверка PEB на признаки отладки
    PPEB pPeb = (PPEB)__readgsqword(0x60);
    if (pPeb->BeingDebugged) {
        return TRUE;
    }
    
    // Проверка NtGlobalFlag
    DWORD ntGlobalFlag = *(DWORD*)((BYTE*)pPeb + 0x68);
    if (ntGlobalFlag & 0x70) { // FLG_HEAP_ENABLE_TAIL_CHECK | FLG_HEAP_ENABLE_FREE_CHECK | FLG_HEAP_VALIDATE_PARAMETERS
        return TRUE;
    }
    
    // Проверка наличия порта отладки
    BOOL isDebugPort = FALSE;
    NTSTATUS status;
    DWORD debugPort = 0;
    
    // Использование NtQueryInformationProcess для проверки порта отладки
    typedef NTSTATUS (WINAPI *TNtQueryInformationProcess)(
        HANDLE ProcessHandle,
        DWORD ProcessInformationClass,
        PVOID ProcessInformation,
        ULONG ProcessInformationLength,
        PULONG ReturnLength
    );
    
    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    if (hNtdll) {
        TNtQueryInformationProcess NtQueryInformationProcess = (TNtQueryInformationProcess)
            GetProcAddress(hNtdll, "NtQueryInformationProcess");
        
        if (NtQueryInformationProcess) {
            status = NtQueryInformationProcess(
                GetCurrentProcess(),
                7, // ProcessDebugPort
                &debugPort,
                sizeof(debugPort),
                NULL
            );
            
            if (NT_SUCCESS(status) && debugPort != 0) {
                isDebugPort = TRUE;
            }
        }
    }
    
    return isDebugPort;
}

BOOL MemHide_AntiDebug(BOOL terminateOnDetection) {
    if (MemHide_IsDebuggerPresent()) {
        if (terminateOnDetection) {
            // Аварийное завершение процесса
            TerminateProcess(GetCurrentProcess(), 0);
        }
        return FALSE;
    }
    
    return TRUE;
}

BOOL MemHide_HideMemoryRegion(void* address, SIZE_T size) {
    if (!address || size == 0) {
        return FALSE;
    }
    
    // Получаем текущие права доступа
    MEMORY_BASIC_INFORMATION mbi;
    if (VirtualQuery(address, &mbi, sizeof(mbi)) == 0) {
        return FALSE;
    }
    
    // Изменяем права доступа на PAGE_NOACCESS
    DWORD oldProtect;
    if (!VirtualProtect(address, size, PAGE_NOACCESS, &oldProtect)) {
        return FALSE;
    }
    
    // Добавляем регион в список скрытых
    if (!AddHiddenRegion(address, size, oldProtect)) {
        // Восстанавливаем оригинальные права доступа в случае ошибки
        VirtualProtect(address, size, oldProtect, &oldProtect);
        return FALSE;
    }
    
    return TRUE;
}

BOOL MemHide_RestoreMemoryRegion(void* address, SIZE_T size) {
    if (!address) {
        return FALSE;
    }
    
    // Находим регион в списке скрытых
    PHIDDEN_REGION region = FindHiddenRegion(address);
    if (!region) {
        return FALSE;
    }
    
    // Восстанавливаем оригинальные права доступа
    DWORD oldProtect;
    if (!VirtualProtect(address, region->size, region->originalProtect, &oldProtect)) {
        return FALSE;
    }
    
    // Удаляем регион из списка скрытых
    if (!RemoveHiddenRegion(address)) {
        return FALSE;
    }
    
    return TRUE;
}

BOOL MemHide_PreventMemoryDump(void) {
    // Установка флага для предотвращения создания дампа памяти процесса
    typedef NTSTATUS (WINAPI *TNtSetInformationProcess)(
        HANDLE ProcessHandle,
        DWORD ProcessInformationClass,
        PVOID ProcessInformation,
        ULONG ProcessInformationLength
    );
    
    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    if (!hNtdll) {
        return FALSE;
    }
    
    TNtSetInformationProcess NtSetInformationProcess = (TNtSetInformationProcess)
        GetProcAddress(hNtdll, "NtSetInformationProcess");
    
    if (!NtSetInformationProcess) {
        return FALSE;
    }
    
    // ProcessBreakOnTermination flag (0x1F)
    ULONG breakOnTermination = 1;
    NTSTATUS status = NtSetInformationProcess(
        GetCurrentProcess(),
        0x1D, // ProcessBreakOnTermination
        &breakOnTermination,
        sizeof(breakOnTermination)
    );
    
    if (!NT_SUCCESS(status)) {
        return FALSE;
    }
    
    // DisableProcessHeapGeneration flag
    DWORD heapFlags = 0x40000; // HEAP_CREATE_ENABLE_EXECUTE
    return HeapSetInformation(NULL, HeapCompatibilityInformation, &heapFlags, sizeof(heapFlags));
}

BOOL MemHide_DetectCodeInjection(MemHide_InjectionCallback callback) {
    if (!callback) {
        return FALSE;
    }
    
    g_injectionCallback = callback;
    
    // Здесь можно добавить более сложный механизм обнаружения инъекций,
    // например, периодическую проверку новых модулей или измененных регионов памяти
    
    return TRUE;
}

void* MemHide_CreateFalseSignatureRegion(SIZE_T size, const BYTE* falseSignature, SIZE_T signatureSize) {
    if (size == 0 || !falseSignature || signatureSize == 0) {
        return NULL;
    }
    
    // Выделяем память для ложной сигнатуры
    void* regionAddress = VirtualAlloc(NULL, size, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    if (!regionAddress) {
        return NULL;
    }
    
    // Заполняем память ложной сигнатурой
    for (SIZE_T offset = 0; offset < size; offset += signatureSize) {
        SIZE_T bytesToCopy = (offset + signatureSize <= size) ? signatureSize : (size - offset);
        memcpy((BYTE*)regionAddress + offset, falseSignature, bytesToCopy);
    }
    
    // Устанавливаем права доступа только для чтения
    DWORD oldProtect;
    if (!VirtualProtect(regionAddress, size, PAGE_READONLY, &oldProtect)) {
        VirtualFree(regionAddress, 0, MEM_RELEASE);
        return NULL;
    }
    
    return regionAddress;
}

BOOL MemHide_RemoveFalseSignatureRegion(void* address) {
    if (!address) {
        return FALSE;
    }
    
    return VirtualFree(address, 0, MEM_RELEASE);
}

BOOL MemHide_DetectMemoryScan(MemHide_ScanDetectionCallback callback) {
    if (!callback) {
        return FALSE;
    }
    
    g_scanCallback = callback;
    return TRUE;
}

BOOL MemHide_ProtectCriticalPages(void** addresses, SIZE_T count) {
    if (!addresses || count == 0) {
        return FALSE;
    }
    
    for (SIZE_T i = 0; i < count; i++) {
        if (addresses[i]) {
            // Получаем информацию о странице
            MEMORY_BASIC_INFORMATION mbi;
            if (VirtualQuery(addresses[i], &mbi, sizeof(mbi)) == 0) {
                continue;
            }
            
            // Скрываем страницу от сканирования
            if (!MemHide_HideMemoryRegion(addresses[i], mbi.RegionSize)) {
                // Если не удалось скрыть, пытаемся хотя бы зашифровать
                void* context;
                BYTE key[16] = {0x12, 0x34, 0x56, 0x78, 0x9A, 0xBC, 0xDE, 0xF0, 
                               0x0F, 0xED, 0xCB, 0xA9, 0x87, 0x65, 0x43, 0x21};
                if (!MemHide_EncryptMemory(addresses[i], mbi.RegionSize, key, sizeof(key), &context)) {
                    return FALSE;
                }
            }
        }
    }
    
    return TRUE;
} 