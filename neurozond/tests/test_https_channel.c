/**
 * @file test_https_channel.c
 * @brief Tests for the HTTPS channel implementation
 * @author iamtomasanderson@gmail.com (https://github.com/Personaz1/)
 * @date 2023-09-02
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../include/covert_channel.h"
#include <assert.h>

#define TEST_SERVER "test.neuronet.local"
#define TEST_PORT 443
#define TEST_ENDPOINT "/api/v1"

#define RUN_TEST(name, test_func) \
    printf("Running test: %s... ", name); \
    if (test_func() == 0) { \
        printf("PASSED\n"); \
        tests_passed++; \
    } else { \
        printf("FAILED\n"); \
        tests_failed++; \
    }

// Mock functions for testing without actual network connections
extern CovertChannelHandle https_channel_init(const CovertChannelConfig* config);
extern int https_channel_connect(CovertChannelHandle handle);
extern int https_channel_send(CovertChannelHandle handle, const unsigned char* data, size_t data_len);
extern int https_channel_receive(CovertChannelHandle handle, unsigned char* buffer, size_t buffer_size);
extern void https_channel_cleanup(CovertChannelHandle handle);

// Test function declarations
int test_https_init();
int test_https_init_invalid_params();
int test_https_encryption_aes();
int test_https_encryption_chacha20();
int test_https_jitter_settings();
int test_https_null_handle();
int test_https_mock_send_receive();

int main() {
    int tests_passed = 0;
    int tests_failed = 0;
    
    printf("=== HTTPS Channel Tests ===\n");
    
    RUN_TEST("HTTPS Channel Initialization", test_https_init);
    RUN_TEST("HTTPS Channel Initialization with Invalid Parameters", test_https_init_invalid_params);
    RUN_TEST("HTTPS Channel with AES Encryption", test_https_encryption_aes);
    RUN_TEST("HTTPS Channel with ChaCha20 Encryption", test_https_encryption_chacha20);
    RUN_TEST("HTTPS Channel Jitter Settings", test_https_jitter_settings);
    RUN_TEST("HTTPS Channel Null Handle Handling", test_https_null_handle);
    RUN_TEST("HTTPS Channel Mock Send/Receive", test_https_mock_send_receive);
    
    printf("\nTest Summary: %d passed, %d failed\n", tests_passed, tests_failed);
    
    return tests_failed > 0 ? 1 : 0;
}

int test_https_init() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_HTTPS;
    config.server_address = TEST_SERVER;
    config.endpoint = TEST_ENDPOINT;
    config.encryption = ENC_NONE;
    config.jitter_ms = 100;
    
    CovertChannelHandle handle = https_channel_init(&config);
    if (!handle) {
        return 1; // Failed
    }
    
    https_channel_cleanup(handle);
    return 0; // Passed
}

int test_https_init_invalid_params() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    // Test with NULL server address
    config.channel_type = CHANNEL_HTTPS;
    config.server_address = NULL;
    config.endpoint = TEST_ENDPOINT;
    
    CovertChannelHandle handle = https_channel_init(&config);
    if (handle != NULL) {
        https_channel_cleanup(handle);
        return 1; // Failed
    }
    
    // Test with NULL config
    handle = https_channel_init(NULL);
    if (handle != NULL) {
        https_channel_cleanup(handle);
        return 1; // Failed
    }
    
    return 0; // Passed
}

int test_https_encryption_aes() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_HTTPS;
    config.server_address = TEST_SERVER;
    config.endpoint = TEST_ENDPOINT;
    config.encryption = ENC_AES256;
    
    // Set encryption key
    const char* key = "AES256ENCRYPTIONKEY0123456789ABCDEF";
    config.encryption_key = (unsigned char*)key;
    config.key_length = strlen(key);
    
    CovertChannelHandle handle = https_channel_init(&config);
    if (!handle) {
        return 1; // Failed
    }
    
    https_channel_cleanup(handle);
    return 0; // Passed
}

int test_https_encryption_chacha20() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_HTTPS;
    config.server_address = TEST_SERVER;
    config.endpoint = TEST_ENDPOINT;
    config.encryption = ENC_CHACHA20;
    
    // Set encryption key
    const char* key = "CHACHA20ENCRYPTIONKEY0123456789ABCDEF";
    config.encryption_key = (unsigned char*)key;
    config.key_length = strlen(key);
    
    CovertChannelHandle handle = https_channel_init(&config);
    if (!handle) {
        return 1; // Failed
    }
    
    https_channel_cleanup(handle);
    return 0; // Passed
}

int test_https_jitter_settings() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_HTTPS;
    config.server_address = TEST_SERVER;
    config.endpoint = TEST_ENDPOINT;
    config.jitter_ms = 500; // Set jitter to 500ms
    
    CovertChannelHandle handle = https_channel_init(&config);
    if (!handle) {
        return 1; // Failed
    }
    
    https_channel_cleanup(handle);
    return 0; // Passed
}

int test_https_null_handle() {
    // Test sending with NULL handle
    int result = https_channel_send(NULL, (const unsigned char*)"test", 4);
    if (result != -1) {
        return 1; // Failed
    }
    
    // Test receiving with NULL handle
    unsigned char buffer[128];
    result = https_channel_receive(NULL, buffer, sizeof(buffer));
    if (result != -1) {
        return 1; // Failed
    }
    
    // Test cleanup with NULL handle (should not crash)
    https_channel_cleanup(NULL);
    
    return 0; // Passed
}

int test_https_mock_send_receive() {
    // This test doesn't actually connect to the network
    // It just tests the API and basic functionality
    
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_HTTPS;
    config.server_address = TEST_SERVER;
    config.endpoint = TEST_ENDPOINT;
    config.encryption = ENC_XOR; // Simple encryption for testing
    
    // Set encryption key
    const char* key = "TESTKEY123";
    config.encryption_key = (unsigned char*)key;
    config.key_length = strlen(key);
    
    CovertChannelHandle handle = https_channel_init(&config);
    if (!handle) {
        return 1; // Failed
    }
    
    // We won't actually connect since that would require a real server
    // Just test the API contract
    
    // Send and receive would fail without a real connection, so we don't test return values
    const char* test_data = "Test message for HTTPS channel";
    https_channel_send(handle, (const unsigned char*)test_data, strlen(test_data));
    
    unsigned char buffer[128] = {0};
    https_channel_receive(handle, buffer, sizeof(buffer));
    
    https_channel_cleanup(handle);
    return 0; // Passed
} 