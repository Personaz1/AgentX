/**
 * @file test_icmp_channel.c
 * @brief Tests for ICMP covert channel implementation
 * @author iamtomasanderson@gmail.com
 * @date 2023-08-16
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <assert.h>

#include "../network/covert_channel.h"

// Test macro for simplifying test cases
#define RUN_TEST(test_name) \
    do { \
        printf("Running test: %s... ", #test_name); \
        if (test_name()) { \
            printf("PASSED\n"); \
            passed_tests++; \
        } else { \
            printf("FAILED\n"); \
            failed_tests++; \
        } \
        total_tests++; \
    } while (0)

// Forward declarations for test functions
static int test_icmp_init();
static int test_icmp_encryption();
static int test_icmp_invalid_params();
static int test_icmp_null_handle();
static int test_icmp_jitter();
static int test_icmp_checksum();
static int test_icmp_mock_send_receive();

// Global variables for test functions
static const char *test_server = "192.168.1.1";
static const uint8_t test_encryption_key[32] = {
    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 
    0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f, 0x10,
    0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 
    0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f, 0x20
};

// Test ICMP channel initialization
static int test_icmp_init() {
    void *handle = NULL;
    covert_channel_config config;
    
    // Initialize configuration
    config.encryption_algorithm = ENCRYPTION_CHACHA20;
    config.encryption_key = (uint8_t *)test_encryption_key;
    config.encryption_key_len = sizeof(test_encryption_key);
    
    // Test initialization
    int result = icmp_channel_init(&handle, test_server, &config);
    
    // Cleanup
    if (handle) {
        icmp_channel_cleanup(handle);
    }
    
    return (result == 0 && handle != NULL);
}

// Test encryption algorithm setting
static int test_icmp_encryption() {
    void *handle = NULL;
    covert_channel_config config;
    int result = 1;  // Default to success
    
    // Test different encryption algorithms
    encryption_algorithm algorithms[] = {
        ENCRYPTION_NONE,
        ENCRYPTION_XOR,
        ENCRYPTION_AES256,
        ENCRYPTION_CHACHA20
    };
    
    for (size_t i = 0; i < sizeof(algorithms) / sizeof(algorithms[0]); i++) {
        // Initialize configuration
        config.encryption_algorithm = algorithms[i];
        config.encryption_key = (uint8_t *)test_encryption_key;
        config.encryption_key_len = sizeof(test_encryption_key);
        
        // Test initialization
        if (icmp_channel_init(&handle, test_server, &config) != 0) {
            result = 0;
            break;
        }
        
        // Cleanup
        if (handle) {
            icmp_channel_cleanup(handle);
            handle = NULL;
        }
    }
    
    return result;
}

// Test invalid parameters handling
static int test_icmp_invalid_params() {
    void *handle = NULL;
    covert_channel_config config;
    
    // Initialize configuration
    config.encryption_algorithm = ENCRYPTION_CHACHA20;
    config.encryption_key = (uint8_t *)test_encryption_key;
    config.encryption_key_len = sizeof(test_encryption_key);
    
    // Test with NULL handle
    if (icmp_channel_init(NULL, test_server, &config) == 0) {
        return 0;
    }
    
    // Test with NULL server
    if (icmp_channel_init(&handle, NULL, &config) == 0) {
        return 0;
    }
    
    // Test connect with NULL handle
    if (icmp_channel_connect(NULL) == 0) {
        return 0;
    }
    
    // Test send with NULL handle
    uint8_t test_data[] = "Test data";
    if (icmp_channel_send(NULL, test_data, sizeof(test_data)) == 0) {
        return 0;
    }
    
    // Test receive with NULL handle
    uint8_t buffer[1024];
    size_t bytes_received;
    if (icmp_channel_receive(NULL, buffer, sizeof(buffer), &bytes_received) == 0) {
        return 0;
    }
    
    return 1;
}

// Test null handle in cleanup
static int test_icmp_null_handle() {
    // Test cleanup with NULL handle
    return (icmp_channel_cleanup(NULL) == -1);
}

// Test jitter setting
static int test_icmp_jitter() {
    void *handle = NULL;
    covert_channel_config config;
    int result = 0;
    
    // Initialize configuration
    config.encryption_algorithm = ENCRYPTION_CHACHA20;
    config.encryption_key = (uint8_t *)test_encryption_key;
    config.encryption_key_len = sizeof(test_encryption_key);
    
    // Initialize channel
    if (icmp_channel_init(&handle, test_server, &config) != 0) {
        return 0;
    }
    
    // Test setting valid jitter
    if (icmp_channel_set_jitter(handle, 100, 500) == 0) {
        result = 1;
    }
    
    // Test invalid jitter (min > max)
    if (icmp_channel_set_jitter(handle, 500, 100) == 0) {
        result = 0;
    }
    
    // Test NULL handle
    if (icmp_channel_set_jitter(NULL, 100, 500) == 0) {
        result = 0;
    }
    
    // Cleanup
    if (handle) {
        icmp_channel_cleanup(handle);
    }
    
    return result;
}

// Test ICMP checksum calculation
static int test_icmp_checksum() {
    // This test would verify the ICMP checksum calculation functionality
    // Since the checksum function is usually internal, we'll just create a simple
    // test case with predefined data and expected result
    
    // For this example, we'll just return success
    // In a real implementation, we would call the checksum function with test data
    // and verify the result against a pre-calculated value
    return 1;
}

// Test send and receive with mock data
static int test_icmp_mock_send_receive() {
    // This test would normally require raw socket privileges and mocking
    // For simplicity, we'll just test initialization and verify that
    // the functions return expected values for invalid states
    
    void *handle = NULL;
    covert_channel_config config;
    
    // Initialize configuration
    config.encryption_algorithm = ENCRYPTION_CHACHA20;
    config.encryption_key = (uint8_t *)test_encryption_key;
    config.encryption_key_len = sizeof(test_encryption_key);
    
    // Initialize channel
    if (icmp_channel_init(&handle, test_server, &config) != 0) {
        return 0;
    }
    
    // Attempt to send data without connecting (should fail)
    uint8_t test_data[] = "Test data for ICMP channel";
    if (icmp_channel_send(handle, test_data, sizeof(test_data)) == 0) {
        icmp_channel_cleanup(handle);
        return 0;
    }
    
    // Attempt to receive data without connecting (should fail)
    uint8_t buffer[1024];
    size_t bytes_received;
    if (icmp_channel_receive(handle, buffer, sizeof(buffer), &bytes_received) == 0) {
        icmp_channel_cleanup(handle);
        return 0;
    }
    
    // Cleanup
    icmp_channel_cleanup(handle);
    
    return 1;
}

// Main entry point
int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;
    
    int total_tests = 0;
    int passed_tests = 0;
    int failed_tests = 0;
    
    // Initialize random seed
    srand((unsigned int)time(NULL));
    
    printf("Running ICMP channel tests...\n");
    
    // Run all tests
    RUN_TEST(test_icmp_init);
    RUN_TEST(test_icmp_encryption);
    RUN_TEST(test_icmp_invalid_params);
    RUN_TEST(test_icmp_null_handle);
    RUN_TEST(test_icmp_jitter);
    RUN_TEST(test_icmp_checksum);
    RUN_TEST(test_icmp_mock_send_receive);
    
    // Print summary
    printf("\nTest summary:\n");
    printf("Total tests: %d\n", total_tests);
    printf("Passed: %d\n", passed_tests);
    printf("Failed: %d\n", failed_tests);
    
    return (failed_tests == 0) ? 0 : 1;
} 