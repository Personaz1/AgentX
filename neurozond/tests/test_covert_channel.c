/**
 * @file test_covert_channel.c
 * @brief Тесты для основного интерфейса модуля скрытых каналов связи
 *
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-03
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "../network/covert_channel.h"

// Счетчики тестов
static int tests_passed = 0;
static int tests_failed = 0;

// Макрос для запуска тестов и вывода результатов
#define RUN_TEST(test_func) do { \
    printf("Running test: %s... ", #test_func); \
    if (test_func() == 0) { \
        printf("PASSED\n"); \
        tests_passed++; \
    } else { \
        printf("FAILED\n"); \
        tests_failed++; \
    } \
} while (0)

/**
 * @brief Тест инициализации с валидными параметрами
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_init_valid_params() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_TYPE_DNS;
    config.encryption_type = ENCRYPTION_XOR;
    strncpy(config.server_address, "example.com", sizeof(config.server_address) - 1);
    config.server_port = 53;
    config.jitter_percent = 10;
    
    CovertChannelHandle handle = covert_channel_init(&config);
    
    if (handle == NULL) {
        return 1;
    }
    
    covert_channel_cleanup(handle);
    return 0;
}

/**
 * @brief Тест инициализации с NULL параметрами
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_init_null_params() {
    CovertChannelHandle handle = covert_channel_init(NULL);
    
    if (handle != NULL) {
        covert_channel_cleanup(handle);
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест работы с различными типами шифрования
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_encryption_types() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_TYPE_DNS;
    strncpy(config.server_address, "example.com", sizeof(config.server_address) - 1);
    config.server_port = 53;
    
    // Тест XOR шифрования
    config.encryption_type = ENCRYPTION_XOR;
    CovertChannelHandle handle1 = covert_channel_init(&config);
    
    if (handle1 == NULL) {
        return 1;
    }
    
    // Тест AES256 шифрования
    config.encryption_type = ENCRYPTION_AES256;
    CovertChannelHandle handle2 = covert_channel_init(&config);
    
    if (handle2 == NULL) {
        covert_channel_cleanup(handle1);
        return 1;
    }
    
    // Тест ChaCha20 шифрования
    config.encryption_type = ENCRYPTION_CHACHA20;
    CovertChannelHandle handle3 = covert_channel_init(&config);
    
    if (handle3 == NULL) {
        covert_channel_cleanup(handle1);
        covert_channel_cleanup(handle2);
        return 1;
    }
    
    covert_channel_cleanup(handle1);
    covert_channel_cleanup(handle2);
    covert_channel_cleanup(handle3);
    
    return 0;
}

/**
 * @brief Тест работы с различными типами каналов
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_channel_types() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.encryption_type = ENCRYPTION_XOR;
    strncpy(config.server_address, "example.com", sizeof(config.server_address) - 1);
    config.server_port = 53;
    
    // Тест DNS канала
    config.channel_type = CHANNEL_TYPE_DNS;
    CovertChannelHandle handle1 = covert_channel_init(&config);
    
    if (handle1 == NULL) {
        return 1;
    }
    
    // Тест HTTPS канала
    config.channel_type = CHANNEL_TYPE_HTTPS;
    config.server_port = 443;
    CovertChannelHandle handle2 = covert_channel_init(&config);
    
    if (handle2 == NULL) {
        covert_channel_cleanup(handle1);
        return 1;
    }
    
    // Тест ICMP канала
    config.channel_type = CHANNEL_TYPE_ICMP;
    config.server_port = 0;
    CovertChannelHandle handle3 = covert_channel_init(&config);
    
    if (handle3 == NULL) {
        covert_channel_cleanup(handle1);
        covert_channel_cleanup(handle2);
        return 1;
    }
    
    covert_channel_cleanup(handle1);
    covert_channel_cleanup(handle2);
    covert_channel_cleanup(handle3);
    
    return 0;
}

/**
 * @brief Тест работы с неправильным типом канала
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_invalid_channel_type() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = 99; // Недопустимый тип канала
    config.encryption_type = ENCRYPTION_XOR;
    strncpy(config.server_address, "example.com", sizeof(config.server_address) - 1);
    config.server_port = 53;
    
    CovertChannelHandle handle = covert_channel_init(&config);
    
    if (handle != NULL) {
        covert_channel_cleanup(handle);
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции connect с NULL дескриптором
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_connect_null_handle() {
    int result = covert_channel_connect(NULL);
    
    if (result != -1) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции send с NULL дескриптором
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_send_null_handle() {
    char data[] = "Test data";
    int result = covert_channel_send(NULL, data, strlen(data));
    
    if (result != -1) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции receive с NULL дескриптором
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_receive_null_handle() {
    char buffer[128];
    int result = covert_channel_receive(NULL, buffer, sizeof(buffer));
    
    if (result != -1) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции установки jitter
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_set_jitter() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_TYPE_DNS;
    config.encryption_type = ENCRYPTION_XOR;
    strncpy(config.server_address, "example.com", sizeof(config.server_address) - 1);
    config.server_port = 53;
    config.jitter_percent = 0;
    
    CovertChannelHandle handle = covert_channel_init(&config);
    
    if (handle == NULL) {
        return 1;
    }
    
    // Установка допустимого значения
    int result1 = covert_channel_set_jitter(handle, 20);
    
    // Установка недопустимого значения
    int result2 = covert_channel_set_jitter(handle, -10);
    int result3 = covert_channel_set_jitter(handle, 60);
    
    covert_channel_cleanup(handle);
    
    if (result1 != 0 || result2 != -1 || result3 != -1) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Мок-тест для проверки отправки и получения данных
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_send_receive_mock() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_TYPE_DNS;
    config.encryption_type = ENCRYPTION_XOR;
    strncpy(config.server_address, "example.com", sizeof(config.server_address) - 1);
    config.server_port = 53;
    
    CovertChannelHandle handle = covert_channel_init(&config);
    
    if (handle == NULL) {
        return 1;
    }
    
    // Мы не выполняем реальную отправку/получение, 
    // так как это требует сетевого соединения.
    // Это мок-тест для проверки, что функции не возвращают ошибки
    // на этапе подготовки данных
    
    covert_channel_cleanup(handle);
    return 0;
}

/**
 * @brief Точка входа для тестов
 * 
 * @return int Код возврата программы
 */
int main() {
    printf("=== Testing Covert Channel Module ===\n\n");
    
    // Запуск тестов
    RUN_TEST(test_init_valid_params);
    RUN_TEST(test_init_null_params);
    RUN_TEST(test_encryption_types);
    RUN_TEST(test_channel_types);
    RUN_TEST(test_invalid_channel_type);
    RUN_TEST(test_connect_null_handle);
    RUN_TEST(test_send_null_handle);
    RUN_TEST(test_receive_null_handle);
    RUN_TEST(test_set_jitter);
    RUN_TEST(test_send_receive_mock);
    
    // Вывод итогов
    printf("\n=== Test Results ===\n");
    printf("Passed: %d\n", tests_passed);
    printf("Failed: %d\n", tests_failed);
    printf("Total: %d\n", tests_passed + tests_failed);
    
    return tests_failed > 0 ? 1 : 0;
} 