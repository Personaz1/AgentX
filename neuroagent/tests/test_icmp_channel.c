/**
 * @file test_icmp_channel.c
 * @brief Тесты для модуля ICMP канала связи
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

// Объявления внешних функций из модуля ICMP канала
extern int icmp_channel_init(const char *server_address, int encryption_type, void **channel_data);
extern int icmp_channel_connect(void *channel_data);
extern int icmp_channel_send(void *channel_data, const char *data, size_t data_len);
extern int icmp_channel_receive(void *channel_data, char *buffer, size_t buffer_size);
extern void icmp_channel_cleanup(void *channel_data);

/**
 * @brief Тест инициализации с валидными параметрами
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_icmp_init_valid_params() {
    void *channel_data = NULL;
    int result = icmp_channel_init("127.0.0.1", ENCRYPTION_XOR, &channel_data);
    
    if (result != 0 || channel_data == NULL) {
        if (channel_data != NULL) {
            icmp_channel_cleanup(channel_data);
        }
        return 1;
    }
    
    icmp_channel_cleanup(channel_data);
    return 0;
}

/**
 * @brief Тест инициализации с NULL параметрами
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_icmp_init_null_params() {
    void *channel_data = NULL;
    
    // Проверка с NULL адресом сервера
    int result1 = icmp_channel_init(NULL, ENCRYPTION_XOR, &channel_data);
    
    // Проверка с NULL указателем для channel_data
    int result2 = icmp_channel_init("127.0.0.1", ENCRYPTION_XOR, NULL);
    
    if (result1 != -1 || result2 != -1) {
        if (channel_data != NULL) {
            icmp_channel_cleanup(channel_data);
        }
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест работы с различными типами шифрования
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_icmp_encryption_types() {
    void *channel_data1 = NULL;
    void *channel_data2 = NULL;
    void *channel_data3 = NULL;
    
    // Тест XOR шифрования
    int result1 = icmp_channel_init("127.0.0.1", ENCRYPTION_XOR, &channel_data1);
    
    // Тест AES256 шифрования
    int result2 = icmp_channel_init("127.0.0.1", ENCRYPTION_AES256, &channel_data2);
    
    // Тест ChaCha20 шифрования
    int result3 = icmp_channel_init("127.0.0.1", ENCRYPTION_CHACHA20, &channel_data3);
    
    if (result1 != 0 || result2 != 0 || result3 != 0 || 
        channel_data1 == NULL || channel_data2 == NULL || channel_data3 == NULL) {
        if (channel_data1 != NULL) icmp_channel_cleanup(channel_data1);
        if (channel_data2 != NULL) icmp_channel_cleanup(channel_data2);
        if (channel_data3 != NULL) icmp_channel_cleanup(channel_data3);
        return 1;
    }
    
    icmp_channel_cleanup(channel_data1);
    icmp_channel_cleanup(channel_data2);
    icmp_channel_cleanup(channel_data3);
    
    return 0;
}

/**
 * @brief Тест функции connect с NULL дескриптором
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_icmp_connect_null_handle() {
    int result = icmp_channel_connect(NULL);
    
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
int test_icmp_send_null_handle() {
    char data[] = "Test data";
    int result = icmp_channel_send(NULL, data, strlen(data));
    
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
int test_icmp_receive_null_handle() {
    char buffer[128];
    int result = icmp_channel_receive(NULL, buffer, sizeof(buffer));
    
    if (result != -1) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции send с NULL данными
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_icmp_send_null_data() {
    void *channel_data = NULL;
    int init_result = icmp_channel_init("127.0.0.1", ENCRYPTION_XOR, &channel_data);
    
    if (init_result != 0 || channel_data == NULL) {
        if (channel_data != NULL) {
            icmp_channel_cleanup(channel_data);
        }
        return 1;
    }
    
    int result = icmp_channel_send(channel_data, NULL, 10);
    
    icmp_channel_cleanup(channel_data);
    
    if (result != -1) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест отправки и получения данных ICMP канала (мок-тест)
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_icmp_send_receive_mock() {
    void *channel_data = NULL;
    int init_result = icmp_channel_init("127.0.0.1", ENCRYPTION_XOR, &channel_data);
    
    if (init_result != 0 || channel_data == NULL) {
        if (channel_data != NULL) {
            icmp_channel_cleanup(channel_data);
        }
        return 1;
    }
    
    // Мы не выполняем реальное подключение и отправку/получение данных,
    // так как это требует сетевого соединения и прав администратора
    // для создания RAW сокетов
    
    icmp_channel_cleanup(channel_data);
    return 0;
}

/**
 * @brief Тест инициализации с неверным типом шифрования
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_icmp_invalid_encryption() {
    void *channel_data = NULL;
    int result = icmp_channel_init("127.0.0.1", 99, &channel_data); // 99 - недопустимый тип шифрования
    
    if (result != -1 || channel_data != NULL) {
        if (channel_data != NULL) {
            icmp_channel_cleanup(channel_data);
        }
        return 1;
    }
    
    return 0;
}

/**
 * @brief Точка входа для тестов
 * 
 * @return int Код возврата программы
 */
int main() {
    printf("=== Testing ICMP Channel Module ===\n\n");
    
    // Запуск тестов
    RUN_TEST(test_icmp_init_valid_params);
    RUN_TEST(test_icmp_init_null_params);
    RUN_TEST(test_icmp_encryption_types);
    RUN_TEST(test_icmp_connect_null_handle);
    RUN_TEST(test_icmp_send_null_handle);
    RUN_TEST(test_icmp_receive_null_handle);
    RUN_TEST(test_icmp_send_null_data);
    RUN_TEST(test_icmp_send_receive_mock);
    RUN_TEST(test_icmp_invalid_encryption);
    
    // Вывод итогов
    printf("\n=== Test Results ===\n");
    printf("Passed: %d\n", tests_passed);
    printf("Failed: %d\n", tests_failed);
    printf("Total: %d\n", tests_passed + tests_failed);
    
    return tests_failed > 0 ? 1 : 0;
} 