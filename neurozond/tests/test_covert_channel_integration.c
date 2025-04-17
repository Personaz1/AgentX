/**
 * @file test_covert_channel_integration.c
 * @brief Тесты для проверки интеграции модуля скрытых каналов связи
 * @author iamtomasanderson@gmail.com (https://github.com/Personaz1/)
 * @date 2023-09-05
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "../network/covert_channel.h"

// Макрос для запуска теста и вывода результата
#define RUN_TEST(test_func) \
    do { \
        printf("Running test: %s\n", #test_func); \
        if (test_func() == 0) { \
            printf("[PASS] %s\n\n", #test_func); \
            tests_passed++; \
        } else { \
            printf("[FAIL] %s\n\n", #test_func); \
            tests_failed++; \
        } \
        total_tests++; \
    } while (0)

// Тест инициализации каналов различных типов
static int test_init_all_channel_types() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    // Базовые параметры для всех конфигураций
    config.server_address = "127.0.0.1";
    config.server_port = 8080;
    config.encryption_key = (unsigned char*)"TestKey12345";
    config.encryption_key_len = 12;
    config.jitter_min = 10;
    config.jitter_max = 50;
    
    // Тест канала DNS
    config.channel_type = CHANNEL_DNS;
    config.encryption = ENCRYPTION_XOR;
    CovertChannelHandle dns_handle = covert_channel_init(&config);
    if (!dns_handle) {
        printf("Failed to initialize DNS channel\n");
        return 1;
    }
    covert_channel_cleanup(dns_handle);
    
    // Тест канала HTTPS
    config.channel_type = CHANNEL_HTTPS;
    config.encryption = ENCRYPTION_AES256;
    CovertChannelHandle https_handle = covert_channel_init(&config);
    if (!https_handle) {
        printf("Failed to initialize HTTPS channel\n");
        return 1;
    }
    covert_channel_cleanup(https_handle);
    
    // Тест канала ICMP
    config.channel_type = CHANNEL_ICMP;
    config.encryption = ENCRYPTION_CHACHA20;
    CovertChannelHandle icmp_handle = covert_channel_init(&config);
    if (!icmp_handle) {
        printf("Failed to initialize ICMP channel\n");
        return 1;
    }
    covert_channel_cleanup(icmp_handle);
    
    return 0;
}

// Тест настройки параметров джиттера
static int test_set_jitter_parameters() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.server_address = "127.0.0.1";
    config.server_port = 8080;
    config.channel_type = CHANNEL_DNS;
    config.encryption = ENCRYPTION_NONE;
    config.encryption_key = (unsigned char*)"TestKey12345";
    config.encryption_key_len = 12;
    
    CovertChannelHandle handle = covert_channel_init(&config);
    if (!handle) {
        printf("Failed to initialize channel\n");
        return 1;
    }
    
    // Проверка корректных значений
    int result = covert_channel_set_jitter(handle, 100, 200);
    if (result != 0) {
        printf("Failed to set valid jitter parameters\n");
        covert_channel_cleanup(handle);
        return 1;
    }
    
    // Проверка некорректных значений (min > max)
    result = covert_channel_set_jitter(handle, 300, 200);
    if (result == 0) {
        printf("Set invalid jitter parameters (min > max) should have failed\n");
        covert_channel_cleanup(handle);
        return 1;
    }
    
    covert_channel_cleanup(handle);
    return 0;
}

// Тест проверки соединения
static int test_is_connected() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.server_address = "127.0.0.1";
    config.server_port = 8080;
    config.channel_type = CHANNEL_DNS;
    config.encryption = ENCRYPTION_NONE;
    
    CovertChannelHandle handle = covert_channel_init(&config);
    if (!handle) {
        printf("Failed to initialize channel\n");
        return 1;
    }
    
    // Соединение пока не установлено
    int connected = covert_channel_is_connected(handle);
    if (connected != 0) {
        printf("Channel should not be connected initially\n");
        covert_channel_cleanup(handle);
        return 1;
    }
    
    // Это симуляция, реальное соединение не устанавливается
    covert_channel_cleanup(handle);
    return 0;
}

// Тест работы с NULL хендлером
static int test_null_handle() {
    // Проверка функций с NULL хендлером
    int result = covert_channel_connect(NULL);
    if (result != -1) {
        printf("covert_channel_connect with NULL handle should return -1\n");
        return 1;
    }
    
    result = covert_channel_send(NULL, (unsigned char*)"test", 4);
    if (result != -1) {
        printf("covert_channel_send with NULL handle should return -1\n");
        return 1;
    }
    
    unsigned char buffer[128];
    result = covert_channel_receive(NULL, buffer, sizeof(buffer));
    if (result != -1) {
        printf("covert_channel_receive with NULL handle should return -1\n");
        return 1;
    }
    
    result = covert_channel_is_connected(NULL);
    if (result != -1) {
        printf("covert_channel_is_connected with NULL handle should return -1\n");
        return 1;
    }
    
    result = covert_channel_set_jitter(NULL, 10, 20);
    if (result != -1) {
        printf("covert_channel_set_jitter with NULL handle should return -1\n");
        return 1;
    }
    
    // Это не должно вызывать сбоев
    covert_channel_cleanup(NULL);
    
    return 0;
}

// Тест некорректной конфигурации
static int test_invalid_config() {
    // NULL конфигурация
    CovertChannelHandle handle = covert_channel_init(NULL);
    if (handle != NULL) {
        printf("covert_channel_init with NULL config should return NULL\n");
        covert_channel_cleanup(handle);
        return 1;
    }
    
    // Конфигурация без адреса сервера
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    config.channel_type = CHANNEL_DNS;
    config.server_address = NULL;
    
    handle = covert_channel_init(&config);
    if (handle != NULL) {
        printf("covert_channel_init with NULL server_address should return NULL\n");
        covert_channel_cleanup(handle);
        return 1;
    }
    
    // Конфигурация с некорректным типом канала
    config.server_address = "127.0.0.1";
    config.channel_type = 999; // Некорректный тип
    
    handle = covert_channel_init(&config);
    if (handle != NULL) {
        printf("covert_channel_init with invalid channel type should return NULL\n");
        covert_channel_cleanup(handle);
        return 1;
    }
    
    return 0;
}

// Тест работы с некорректными параметрами
static int test_invalid_params() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.server_address = "127.0.0.1";
    config.server_port = 8080;
    config.channel_type = CHANNEL_DNS;
    config.encryption = ENCRYPTION_NONE;
    
    CovertChannelHandle handle = covert_channel_init(&config);
    if (!handle) {
        printf("Failed to initialize channel\n");
        return 1;
    }
    
    // Отправка с NULL данными
    int result = covert_channel_send(handle, NULL, 10);
    if (result != -1) {
        printf("covert_channel_send with NULL data should return -1\n");
        covert_channel_cleanup(handle);
        return 1;
    }
    
    // Отправка с нулевой длиной
    result = covert_channel_send(handle, (unsigned char*)"test", 0);
    if (result != -1) {
        printf("covert_channel_send with zero length should return -1\n");
        covert_channel_cleanup(handle);
        return 1;
    }
    
    // Получение в NULL буфер
    result = covert_channel_receive(handle, NULL, 10);
    if (result != -1) {
        printf("covert_channel_receive with NULL buffer should return -1\n");
        covert_channel_cleanup(handle);
        return 1;
    }
    
    // Получение с нулевым размером буфера
    unsigned char buffer[128];
    result = covert_channel_receive(handle, buffer, 0);
    if (result != -1) {
        printf("covert_channel_receive with zero buffer size should return -1\n");
        covert_channel_cleanup(handle);
        return 1;
    }
    
    covert_channel_cleanup(handle);
    return 0;
}

int main() {
    int total_tests = 0;
    int tests_passed = 0;
    int tests_failed = 0;
    
    printf("==== Running Covert Channel Integration Tests ====\n\n");
    
    RUN_TEST(test_init_all_channel_types);
    RUN_TEST(test_set_jitter_parameters);
    RUN_TEST(test_is_connected);
    RUN_TEST(test_null_handle);
    RUN_TEST(test_invalid_config);
    RUN_TEST(test_invalid_params);
    
    printf("==== Test Summary ====\n");
    printf("Total tests: %d\n", total_tests);
    printf("Passed: %d\n", tests_passed);
    printf("Failed: %d\n", tests_failed);
    
    return tests_failed > 0 ? 1 : 0;
} 