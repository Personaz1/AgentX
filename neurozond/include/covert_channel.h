/**
 * @file covert_channel.h
 * @brief Header file for covert communication channels module
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-01
 */

#ifndef COVERT_CHANNEL_H
#define COVERT_CHANNEL_H

#include <stdint.h>
#include <stddef.h>

/**
 * @brief Types of covert channels
 */
typedef enum {
    CHANNEL_TYPE_DNS,    /**< DNS-based covert channel */
    CHANNEL_TYPE_HTTPS,  /**< HTTPS-based covert channel */
    CHANNEL_TYPE_ICMP,   /**< ICMP-based covert channel */
} CovertChannelType;

/**
 * @brief Encryption algorithms for channel data
 */
typedef enum {
    ENCRYPTION_NONE,     /**< No encryption */
    ENCRYPTION_XOR,      /**< Simple XOR encryption */
    ENCRYPTION_AES256,   /**< AES 256 encryption */
    ENCRYPTION_CHACHA20, /**< ChaCha20 encryption */
} EncryptionType;

/**
 * @brief Handle to covert channel context
 */
typedef struct CovertChannel* CovertChannelHandle;

/**
 * @brief Configuration structure for covert channel
 */
typedef struct {
    CovertChannelType channel_type;    /**< Type of covert channel to use */
    EncryptionType encryption_type;    /**< Type of encryption to use */
    char* server_address;              /**< Address of C1 server */
    uint16_t server_port;              /**< Port of C1 server, if applicable */
    uint8_t* encryption_key;           /**< Encryption key */
    size_t key_length;                 /**< Length of encryption key */
    unsigned int jitter_min_ms;        /**< Minimum delay between packets in ms */
    unsigned int jitter_max_ms;        /**< Maximum delay between packets in ms */
} CovertChannelConfig;

/**
 * @brief Initialize a covert channel with given configuration
 * 
 * @param config Pointer to configuration structure
 * @return CovertChannelHandle Handle to initialized channel or NULL on error
 */
CovertChannelHandle covert_channel_init(CovertChannelConfig* config);

/**
 * @brief Connect to C1 server using the covert channel
 * 
 * @param handle Handle to covert channel
 * @return int 0 on success, negative value on error
 */
int covert_channel_connect(CovertChannelHandle handle);

/**
 * @brief Send data through covert channel
 * 
 * @param handle Handle to covert channel
 * @param data Pointer to data buffer
 * @param data_len Length of data
 * @return int Number of bytes sent or negative value on error
 */
int covert_channel_send(CovertChannelHandle handle, const uint8_t* data, size_t data_len);

/**
 * @brief Receive data from covert channel
 * 
 * @param handle Handle to covert channel
 * @param buffer Pointer to buffer for received data
 * @param buffer_size Size of buffer
 * @return int Number of bytes received or negative value on error
 */
int covert_channel_receive(CovertChannelHandle handle, uint8_t* buffer, size_t buffer_size);

/**
 * @brief Set jitter values for transmission timing
 * 
 * @param handle Handle to covert channel
 * @param min_ms Minimum delay in ms
 * @param max_ms Maximum delay in ms
 * @return int 0 on success, negative value on error
 */
int covert_channel_set_jitter(CovertChannelHandle handle, unsigned int min_ms, unsigned int max_ms);

/**
 * @brief Close and clean up a covert channel
 * 
 * @param handle Handle to covert channel
 */
void covert_channel_cleanup(CovertChannelHandle handle);

/**
 * @brief Get last error message
 * 
 * @param handle Handle to covert channel
 * @return const char* Error message
 */
const char* covert_channel_get_error(CovertChannelHandle handle);

#endif /* COVERT_CHANNEL_H */
