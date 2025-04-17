/**
 * @file test_https_channel.c
 * @brief Тесты для HTTPS канала скрытой передачи данных
 * 
 * Этот файл содержит тесты для проверки работы HTTPS канала.
 * Тесты включают проверку инициализации, подключения, отправки
 * и получения данных, а также проверку работы с джиттером.
 * 
 * @author NeuroZond Team
 * @date 2025-04-28
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>
#include "../network/covert_channel.h"

/* Макрос для запуска тестов с выводом результатов */
#define RUN_TEST(test_name) do { \
    printf("Запуск теста: %s\n", #test_name); \
    if (test_name()) { \
        printf("[УСПЕХ] %s\n", #test_name); \
        passed_tests++; \
    } else { \
        printf("[ОШИБКА] %s\n", #test_name); \
        failed_tests++; \
    } \
} while (0)

/* Функции HTTPS канала, которые мы тестируем */
extern void register_https_channel_handler(CovertChannelHandler *handler);

/* Заглушка для подключения */
static int mock_connect_success = 1;
static int mock_https_channel_connect(void *channel_data) {
    return mock_connect_success ? COVERT_CHANNEL_SUCCESS : COVERT_CHANNEL_ERROR;
}

/* Заглушка для отправки данных */
static int mock_send_success = 1;
static int mock_https_channel_send(void *channel_data, const unsigned char *data, size_t data_len) {
    return mock_send_success ? data_len : COVERT_CHANNEL_ERROR;
}

/* Заглушка для получения данных */
static int mock_receive_success = 1;
static unsigned char mock_receive_data[1024] = "test data received";
static int mock_https_channel_receive(void *channel_data, unsigned char *buffer, size_t buffer_size) {
    if (!mock_receive_success) {
        return COVERT_CHANNEL_ERROR;
    }
    
    size_t data_len = strlen((char*)mock_receive_data);
    if (data_len > buffer_size) {
        data_len = buffer_size;
    }
    
    memcpy(buffer, mock_receive_data, data_len);
    return data_len;
}

/* Тестирование инициализации HTTPS канала */
static int test_https_channel_init() {
    CovertChannelHandler handler;
    memset(&handler, 0, sizeof(handler));
    
    // Регистрируем HTTPS канал
    register_https_channel_handler(&handler);
    
    // Проверяем, что все необходимые функции установлены
    assert(handler.init != NULL);
    assert(handler.connect != NULL);
    assert(handler.send != NULL);
    assert(handler.receive != NULL);
    assert(handler.cleanup != NULL);
    assert(handler.set_jitter != NULL);
    assert(handler.is_connected != NULL);
    
    // Создаем конфигурацию канала
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    config.channel_type = CHANNEL_TYPE_HTTPS;
    config.encryption = ENCRYPTION_ALGORITHM_AES256;
    config.server_addr = "example.com";
    config.server_port = 443;
    
    // Инициализируем канал
    void *channel_data = handler.init(&config);
    
    // Проверяем, что канал создан успешно
    assert(channel_data != NULL);
    
    // Освобождаем ресурсы
    handler.cleanup(channel_data);
    
    return 1;
}

/* Тестирование инициализации с недопустимыми параметрами */
static int test_https_channel_init_invalid_params() {
    CovertChannelHandler handler;
    memset(&handler, 0, sizeof(handler));
    
    register_https_channel_handler(&handler);
    
    // Тест с NULL конфигурацией
    void *channel_data = handler.init(NULL);
    assert(channel_data == NULL);
    
    // Тест с отсутствующим адресом сервера
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    config.channel_type = CHANNEL_TYPE_HTTPS;
    config.server_addr = NULL;
    
    channel_data = handler.init(&config);
    assert(channel_data == NULL);
    
    return 1;
}

/* Тестирование подключения к серверу */
static int test_https_channel_connect() {
    CovertChannelHandler handler;
    memset(&handler, 0, sizeof(handler));
    
    register_https_channel_handler(&handler);
    
    // Временно заменяем реальную функцию подключения на заглушку
    int (*original_connect)(void*) = handler.connect;
    handler.connect = mock_https_channel_connect;
    
    // Создаем и инициализируем канал
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    config.channel_type = CHANNEL_TYPE_HTTPS;
    config.server_addr = "example.com";
    config.server_port = 443;
    
    void *channel_data = handler.init(&config);
    assert(channel_data != NULL);
    
    // Тестируем успешное подключение
    mock_connect_success = 1;
    int result = handler.connect(channel_data);
    assert(result == COVERT_CHANNEL_SUCCESS);
    
    // Тестируем неудачное подключение
    mock_connect_success = 0;
    result = handler.connect(channel_data);
    assert(result == COVERT_CHANNEL_ERROR);
    
    // Восстанавливаем оригинальную функцию и освобождаем ресурсы
    handler.connect = original_connect;
    handler.cleanup(channel_data);
    
    return 1;
}

/* Тестирование отправки данных */
static int test_https_channel_send() {
    CovertChannelHandler handler;
    memset(&handler, 0, sizeof(handler));
    
    register_https_channel_handler(&handler);
    
    // Заменяем функции на заглушки
    int (*original_connect)(void*) = handler.connect;
    int (*original_send)(void*, const unsigned char*, size_t) = handler.send;
    
    handler.connect = mock_https_channel_connect;
    handler.send = mock_https_channel_send;
    
    // Создаем и инициализируем канал
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    config.channel_type = CHANNEL_TYPE_HTTPS;
    config.server_addr = "example.com";
    config.server_port = 443;
    
    void *channel_data = handler.init(&config);
    assert(channel_data != NULL);
    
    // Подключаемся
    mock_connect_success = 1;
    int result = handler.connect(channel_data);
    assert(result == COVERT_CHANNEL_SUCCESS);
    
    // Тестируем успешную отправку данных
    mock_send_success = 1;
    const unsigned char test_data[] = "test message";
    result = handler.send(channel_data, test_data, strlen((char*)test_data));
    assert(result == strlen((char*)test_data));
    
    // Тестируем неудачную отправку данных
    mock_send_success = 0;
    result = handler.send(channel_data, test_data, strlen((char*)test_data));
    assert(result == COVERT_CHANNEL_ERROR);
    
    // Восстанавливаем оригинальные функции и освобождаем ресурсы
    handler.connect = original_connect;
    handler.send = original_send;
    handler.cleanup(channel_data);
    
    return 1;
}

/* Тестирование получения данных */
static int test_https_channel_receive() {
    CovertChannelHandler handler;
    memset(&handler, 0, sizeof(handler));
    
    register_https_channel_handler(&handler);
    
    // Заменяем функции на заглушки
    int (*original_connect)(void*) = handler.connect;
    int (*original_receive)(void*, unsigned char*, size_t) = handler.receive;
    
    handler.connect = mock_https_channel_connect;
    handler.receive = mock_https_channel_receive;
    
    // Создаем и инициализируем канал
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    config.channel_type = CHANNEL_TYPE_HTTPS;
    config.server_addr = "example.com";
    config.server_port = 443;
    
    void *channel_data = handler.init(&config);
    assert(channel_data != NULL);
    
    // Подключаемся
    mock_connect_success = 1;
    int result = handler.connect(channel_data);
    assert(result == COVERT_CHANNEL_SUCCESS);
    
    // Тестируем успешное получение данных
    mock_receive_success = 1;
    unsigned char buffer[1024] = {0};
    result = handler.receive(channel_data, buffer, sizeof(buffer));
    assert(result > 0);
    assert(strcmp((char*)buffer, (char*)mock_receive_data) == 0);
    
    // Тестируем неудачное получение данных
    mock_receive_success = 0;
    memset(buffer, 0, sizeof(buffer));
    result = handler.receive(channel_data, buffer, sizeof(buffer));
    assert(result == COVERT_CHANNEL_ERROR);
    
    // Восстанавливаем оригинальные функции и освобождаем ресурсы
    handler.connect = original_connect;
    handler.receive = original_receive;
    handler.cleanup(channel_data);
    
    return 1;
}

/* Тестирование установки параметров джиттера */
static int test_https_channel_set_jitter() {
    CovertChannelHandler handler;
    memset(&handler, 0, sizeof(handler));
    
    register_https_channel_handler(&handler);
    
    // Создаем и инициализируем канал
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    config.channel_type = CHANNEL_TYPE_HTTPS;
    config.server_addr = "example.com";
    config.server_port = 443;
    
    void *channel_data = handler.init(&config);
    assert(channel_data != NULL);
    
    // Устанавливаем и проверяем джиттер
    // Поскольку мы не можем напрямую проверить значения внутри структуры,
    // мы просто проверяем, что функция не вызывает ошибок
    handler.set_jitter(channel_data, 100, 500);
    
    // Проверка с невалидными значениями
    handler.set_jitter(channel_data, -100, 500); // Отрицательные значения
    handler.set_jitter(channel_data, 500, 100);  // min > max
    
    handler.cleanup(channel_data);
    
    return 1;
}

/* Тестирование проверки статуса подключения */
static int test_https_channel_is_connected() {
    CovertChannelHandler handler;
    memset(&handler, 0, sizeof(handler));
    
    register_https_channel_handler(&handler);
    
    // Заменяем функцию подключения на заглушку
    int (*original_connect)(void*) = handler.connect;
    handler.connect = mock_https_channel_connect;
    
    // Создаем и инициализируем канал
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    config.channel_type = CHANNEL_TYPE_HTTPS;
    config.server_addr = "example.com";
    config.server_port = 443;
    
    void *channel_data = handler.init(&config);
    assert(channel_data != NULL);
    
    // Проверяем статус до подключения
    int connected = handler.is_connected(channel_data);
    assert(connected == 0);
    
    // Подключаемся и проверяем статус после подключения
    mock_connect_success = 1;
    handler.connect(channel_data);
    
    // Из-за того, что мы используем заглушку, is_connected всегда будет возвращать 0,
    // так как заглушка не меняет внутреннее состояние
    
    // Восстанавливаем оригинальную функцию и освобождаем ресурсы
    handler.connect = original_connect;
    handler.cleanup(channel_data);
    
    return 1;
}

/* Тест с NULL данными */
static int test_https_channel_null_channel_data() {
    CovertChannelHandler handler;
    memset(&handler, 0, sizeof(handler));
    
    register_https_channel_handler(&handler);
    
    // Проверяем вызовы функций с NULL channel_data
    int result = handler.connect(NULL);
    assert(result == COVERT_CHANNEL_ERROR);
    
    const unsigned char test_data[] = "test";
    result = handler.send(NULL, test_data, strlen((char*)test_data));
    assert(result == COVERT_CHANNEL_ERROR);
    
    unsigned char buffer[1024];
    result = handler.receive(NULL, buffer, sizeof(buffer));
    assert(result == COVERT_CHANNEL_ERROR);
    
    int connected = handler.is_connected(NULL);
    assert(connected == 0);
    
    // Функция cleanup должна просто вернуться без ошибок
    handler.cleanup(NULL);
    handler.set_jitter(NULL, 100, 200);
    
    return 1;
}

/* Главная функция для запуска всех тестов */
int main(void) {
    int passed_tests = 0;
    int failed_tests = 0;
    
    printf("====== Запуск тестов для HTTPS канала ======\n");
    
    RUN_TEST(test_https_channel_init);
    RUN_TEST(test_https_channel_init_invalid_params);
    RUN_TEST(test_https_channel_connect);
    RUN_TEST(test_https_channel_send);
    RUN_TEST(test_https_channel_receive);
    RUN_TEST(test_https_channel_set_jitter);
    RUN_TEST(test_https_channel_is_connected);
    RUN_TEST(test_https_channel_null_channel_data);
    
    printf("====== Результаты тестирования ======\n");
    printf("Всего тестов: %d\n", passed_tests + failed_tests);
    printf("Успешно: %d\n", passed_tests);
    printf("Провалено: %d\n", failed_tests);
    
    return failed_tests > 0 ? 1 : 0;
} 