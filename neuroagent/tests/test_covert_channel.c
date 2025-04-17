/**
 * @file test_covert_channel.c
 * @brief Тесты для модуля скрытых каналов связи
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-02
 */

#include "../include/covert_channel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/* Общая статистика тестов */
static int total_tests = 0;
static int passed_tests = 0;

/* Макрос для запуска тестовой функции и вывода результата */
#define RUN_TEST(test_function) \
    do { \
        printf("Running test: %s...\n", #test_function); \
        total_tests++; \
        if (test_function()) { \
            printf("[PASSED] %s\n", #test_function); \
            passed_tests++; \
        } else { \
            printf("[FAILED] %s\n", #test_function); \
        } \
    } while (0)

/* Мок-функции для каналов связи */
static int mock_init(struct CovertChannel* channel) {
    return 0;
}

static int mock_connect(struct CovertChannel* channel) {
    return 0;
}

static int mock_send(struct CovertChannel* channel, const uint8_t* data, size_t data_len) {
    return (int)data_len;
}

static int mock_receive(struct CovertChannel* channel, uint8_t* buffer, size_t buffer_size) {
    const char* test_data = "TEST_RESPONSE_DATA";
    size_t len = strlen(test_data);
    
    if (buffer_size < len) {
        return -1;
    }
    
    memcpy(buffer, test_data, len);
    return (int)len;
}

static void mock_cleanup(struct CovertChannel* channel) {
    // Do nothing for mock
}

/* Структура для мок-данных канала */
typedef struct {
    int initialized;
    int connected;
} MockChannelData;

/**
 * Тест: Успешная инициализация канала с корректными параметрами
 */
static int test_init_success() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_TYPE_DNS;
    config.encryption_type = ENCRYPTION_XOR;
    config.server_address = "test.example.com";
    config.server_port = 53;
    
    /* Временно подменяем функции DNS канала на мок */
    int (*orig_dns_init)(struct CovertChannel*) = dns_channel_init;
    dns_channel_init = mock_init;
    
    CovertChannelHandle handle = covert_channel_init(&config);
    
    /* Восстанавливаем оригинальные функции */
    dns_channel_init = orig_dns_init;
    
    if (!handle) {
        printf("Failed to initialize covert channel\n");
        return 0;
    }
    
    covert_channel_cleanup(handle);
    return 1;
}

/**
 * Тест: Инициализация с различными типами шифрования
 */
static int test_encryption_types() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_TYPE_DNS;
    config.server_address = "test.example.com";
    config.server_port = 53;
    
    /* Временно подменяем функции DNS канала на мок */
    int (*orig_dns_init)(struct CovertChannel*) = dns_channel_init;
    dns_channel_init = mock_init;
    
    /* Тестируем разные типы шифрования */
    EncryptionType types[] = {
        ENCRYPTION_NONE,
        ENCRYPTION_XOR,
        ENCRYPTION_AES256,
        ENCRYPTION_CHACHA20
    };
    
    int success = 1;
    for (size_t i = 0; i < sizeof(types) / sizeof(types[0]); i++) {
        config.encryption_type = types[i];
        
        CovertChannelHandle handle = covert_channel_init(&config);
        if (!handle) {
            printf("Failed to initialize with encryption type %d\n", types[i]);
            success = 0;
            continue;
        }
        
        covert_channel_cleanup(handle);
    }
    
    /* Восстанавливаем оригинальные функции */
    dns_channel_init = orig_dns_init;
    
    return success;
}

/**
 * Тест: Инициализация с различными типами каналов
 */
static int test_channel_types() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.encryption_type = ENCRYPTION_NONE;
    config.server_address = "test.example.com";
    
    /* Временно подменяем функции каналов на мок */
    int (*orig_dns_init)(struct CovertChannel*) = dns_channel_init;
    int (*orig_https_init)(struct CovertChannel*) = https_channel_init;
    int (*orig_icmp_init)(struct CovertChannel*) = icmp_channel_init;
    
    dns_channel_init = mock_init;
    https_channel_init = mock_init;
    icmp_channel_init = mock_init;
    
    /* Тестируем разные типы каналов */
    CovertChannelType types[] = {
        CHANNEL_TYPE_DNS,
        CHANNEL_TYPE_HTTPS,
        CHANNEL_TYPE_ICMP
    };
    
    uint16_t ports[] = {53, 443, 0};
    
    int success = 1;
    for (size_t i = 0; i < sizeof(types) / sizeof(types[0]); i++) {
        config.channel_type = types[i];
        config.server_port = ports[i];
        
        CovertChannelHandle handle = covert_channel_init(&config);
        if (!handle) {
            printf("Failed to initialize channel type %d\n", types[i]);
            success = 0;
            continue;
        }
        
        covert_channel_cleanup(handle);
    }
    
    /* Восстанавливаем оригинальные функции */
    dns_channel_init = orig_dns_init;
    https_channel_init = orig_https_init;
    icmp_channel_init = orig_icmp_init;
    
    return success;
}

/**
 * Тест: Инициализация с некорректными параметрами
 */
static int test_invalid_params() {
    /* Тест с NULL конфигурацией */
    CovertChannelHandle handle = covert_channel_init(NULL);
    if (handle != NULL) {
        printf("Expected NULL handle with NULL config\n");
        covert_channel_cleanup(handle);
        return 0;
    }
    
    /* Тест с NULL адресом сервера */
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    config.channel_type = CHANNEL_TYPE_DNS;
    config.server_address = NULL;
    
    handle = covert_channel_init(&config);
    if (handle != NULL) {
        printf("Expected NULL handle with NULL server address\n");
        covert_channel_cleanup(handle);
        return 0;
    }
    
    /* Тест с некорректным типом канала */
    config.server_address = "test.example.com";
    config.channel_type = 999; /* Некорректный тип */
    
    handle = covert_channel_init(&config);
    if (handle != NULL) {
        printf("Expected NULL handle with invalid channel type\n");
        covert_channel_cleanup(handle);
        return 0;
    }
    
    return 1;
}

/**
 * Тест: Обработка NULL handles
 */
static int test_null_handles() {
    /* Тест функций с NULL-хендлом */
    int result;
    uint8_t buffer[100];
    
    result = covert_channel_connect(NULL);
    if (result != -1) {
        printf("Expected -1 from connect with NULL handle, got %d\n", result);
        return 0;
    }
    
    result = covert_channel_send(NULL, buffer, sizeof(buffer));
    if (result != -1) {
        printf("Expected -1 from send with NULL handle, got %d\n", result);
        return 0;
    }
    
    result = covert_channel_receive(NULL, buffer, sizeof(buffer));
    if (result != -1) {
        printf("Expected -1 from receive with NULL handle, got %d\n", result);
        return 0;
    }
    
    result = covert_channel_set_jitter(NULL, 100, 200);
    if (result != -1) {
        printf("Expected -1 from set_jitter with NULL handle, got %d\n", result);
        return 0;
    }
    
    /* Проверка, что cleanup с NULL не вызывает сегфолт */
    covert_channel_cleanup(NULL);
    
    /* Проверка, что get_error с NULL возвращает сообщение об ошибке */
    const char* error = covert_channel_get_error(NULL);
    if (error == NULL || strcmp(error, "Invalid channel handle") != 0) {
        printf("Expected 'Invalid channel handle' from get_error with NULL handle\n");
        return 0;
    }
    
    return 1;
}

/**
 * Тест: Установка джиттера
 */
static int test_set_jitter() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_TYPE_DNS;
    config.encryption_type = ENCRYPTION_NONE;
    config.server_address = "test.example.com";
    
    /* Временно подменяем функции DNS канала на мок */
    int (*orig_dns_init)(struct CovertChannel*) = dns_channel_init;
    dns_channel_init = mock_init;
    
    CovertChannelHandle handle = covert_channel_init(&config);
    if (!handle) {
        printf("Failed to initialize channel\n");
        return 0;
    }
    
    /* Тест корректных значений джиттера */
    int result = covert_channel_set_jitter(handle, 100, 500);
    if (result != 0) {
        printf("Failed to set valid jitter values: %d\n", result);
        covert_channel_cleanup(handle);
        return 0;
    }
    
    /* Тест некорректных значений джиттера (min > max) */
    result = covert_channel_set_jitter(handle, 500, 100);
    if (result != -1) {
        printf("Expected -1 when setting jitter with min > max, got %d\n", result);
        covert_channel_cleanup(handle);
        return 0;
    }
    
    covert_channel_cleanup(handle);
    
    /* Восстанавливаем оригинальные функции */
    dns_channel_init = orig_dns_init;
    
    return 1;
}

/**
 * Тест: Мок отправка и получение данных через DNS канал
 */
static int test_dns_channel_send_receive() {
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_TYPE_DNS;
    config.encryption_type = ENCRYPTION_NONE;
    config.server_address = "test.example.com";
    config.server_port = 53;
    
    /* Подменяем функции DNS канала на мок */
    int (*orig_dns_init)(struct CovertChannel*) = dns_channel_init;
    int (*orig_dns_connect)(struct CovertChannel*) = dns_channel_connect;
    int (*orig_dns_send)(struct CovertChannel*, const uint8_t*, size_t) = dns_channel_send;
    int (*orig_dns_receive)(struct CovertChannel*, uint8_t*, size_t) = dns_channel_receive;
    void (*orig_dns_cleanup)(struct CovertChannel*) = dns_channel_cleanup;
    
    dns_channel_init = mock_init;
    dns_channel_connect = mock_connect;
    dns_channel_send = mock_send;
    dns_channel_receive = mock_receive;
    dns_channel_cleanup = mock_cleanup;
    
    CovertChannelHandle handle = covert_channel_init(&config);
    if (!handle) {
        printf("Failed to initialize DNS channel\n");
        return 0;
    }
    
    int result = covert_channel_connect(handle);
    if (result != 0) {
        printf("Failed to connect DNS channel: %d\n", result);
        covert_channel_cleanup(handle);
        return 0;
    }
    
    /* Тест отправки данных */
    const char* test_msg = "Test message";
    result = covert_channel_send(handle, (const uint8_t*)test_msg, strlen(test_msg));
    if (result < 0) {
        printf("Failed to send data: %d\n", result);
        covert_channel_cleanup(handle);
        return 0;
    }
    
    /* Тест получения данных */
    uint8_t recv_buffer[100] = {0};
    result = covert_channel_receive(handle, recv_buffer, sizeof(recv_buffer));
    if (result < 0) {
        printf("Failed to receive data: %d\n", result);
        covert_channel_cleanup(handle);
        return 0;
    }
    
    if (strcmp((char*)recv_buffer, "TEST_RESPONSE_DATA") != 0) {
        printf("Received incorrect data: %s\n", recv_buffer);
        covert_channel_cleanup(handle);
        return 0;
    }
    
    covert_channel_cleanup(handle);
    
    /* Восстанавливаем оригинальные функции */
    dns_channel_init = orig_dns_init;
    dns_channel_connect = orig_dns_connect;
    dns_channel_send = orig_dns_send;
    dns_channel_receive = orig_dns_receive;
    dns_channel_cleanup = orig_dns_cleanup;
    
    return 1;
}

/**
 * Главная функция запуска тестов
 */
int main(int argc, char** argv) {
    printf("=== Covert Channel Module Tests ===\n\n");
    
    /* Запуск тестов */
    RUN_TEST(test_init_success);
    RUN_TEST(test_encryption_types);
    RUN_TEST(test_channel_types);
    RUN_TEST(test_invalid_params);
    RUN_TEST(test_null_handles);
    RUN_TEST(test_set_jitter);
    RUN_TEST(test_dns_channel_send_receive);
    
    /* Вывод статистики */
    printf("\n=== Test Summary ===\n");
    printf("Total tests: %d\n", total_tests);
    printf("Passed: %d (%.1f%%)\n", passed_tests, (float)passed_tests / total_tests * 100);
    printf("Failed: %d (%.1f%%)\n", total_tests - passed_tests, 
           (float)(total_tests - passed_tests) / total_tests * 100);
    
    return (passed_tests == total_tests) ? 0 : 1;
} 