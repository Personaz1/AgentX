/**
 * @file test_main.c
 * @brief Тесты для основного модуля NeuroZond
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-11
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

// Мок-функции для API скрытых каналов
typedef void* covert_channel_handle_t;

enum CovertChannelType {
    CHANNEL_TYPE_DNS,
    CHANNEL_TYPE_HTTPS,
    CHANNEL_TYPE_ICMP
};

enum EncryptionType {
    ENCRYPTION_TYPE_NONE,
    ENCRYPTION_TYPE_XOR,
    ENCRYPTION_TYPE_AES256,
    ENCRYPTION_TYPE_CHACHA20
};

int covert_channel_module_init(void) {
    return 0;
}

int covert_channel_init(covert_channel_handle_t* handle, enum CovertChannelType type, const char* server, void* config) {
    static int mock_handle_counter = 1;
    
    if (!handle || !server) return -1;
    
    // Проверяем тип канала
    if (type != CHANNEL_TYPE_DNS && type != CHANNEL_TYPE_HTTPS && type != CHANNEL_TYPE_ICMP) {
        return -2;
    }
    
    // Создаем фейковый дескриптор
    *handle = (covert_channel_handle_t)(intptr_t)mock_handle_counter++;
    
    return 0;
}

int covert_channel_set_jitter(covert_channel_handle_t handle, uint32_t min_jitter_ms, uint32_t max_jitter_ms) {
    if (!handle) return -1;
    if (min_jitter_ms > max_jitter_ms) return -2;
    return 0;
}

int covert_channel_connect(covert_channel_handle_t handle) {
    static int connect_counter = 0;
    
    if (!handle) return -1;
    
    // Симулируем неудачное подключение каждое третье обращение
    connect_counter++;
    if (connect_counter % 3 == 0) {
        return -3;
    }
    
    return 0;
}

int covert_channel_send(covert_channel_handle_t handle, const uint8_t* data, size_t data_len) {
    if (!handle || !data || data_len == 0) return -1;
    return 0;
}

int covert_channel_receive(covert_channel_handle_t handle, uint8_t* buffer, size_t buffer_size, size_t* bytes_received) {
    static int receive_counter = 0;
    
    if (!handle || !buffer || buffer_size == 0 || !bytes_received) return -1;
    
    // Симулируем разные ответы
    receive_counter++;
    
    if (receive_counter % 5 == 0) {
        // Симулируем ошибку приема
        return -2;
    }
    else if (receive_counter % 3 == 0) {
        // Симулируем отсутствие данных
        *bytes_received = 0;
        return 0;
    }
    else {
        // Симулируем получение данных
        const char* test_data = "TEST_DATA";
        size_t test_data_len = strlen(test_data);
        
        *bytes_received = test_data_len < buffer_size ? test_data_len : buffer_size;
        memcpy(buffer, test_data, *bytes_received);
        
        return 0;
    }
}

int covert_channel_cleanup(covert_channel_handle_t handle) {
    if (!handle) return -1;
    return 0;
}

// Включаем файл с основным модулем для тестирования
// Используем другие имена для функций, чтобы избежать конфликтов
#define main test_main
#define main_loop test_main_loop
#define parse_arguments test_parse_arguments
#define init_params test_init_params
#define print_usage test_print_usage
#define create_channel test_create_channel

// Переопределяем sleep_ms, чтобы не ждать в тестах
#ifdef _WIN32
#undef sleep_ms
#define sleep_ms(ms) (void)(ms)
#else
#undef sleep_ms
#define sleep_ms(ms) (void)(ms)
#endif

// Объявляем прототипы функций, которые будем тестировать
void init_params(void* params);
int parse_arguments(int argc, char* argv[], void* params);
void* create_channel(const void* params, enum CovertChannelType channel_type);
int main_loop(const void* params);

// Объявляем структуру для параметров, чтобы не включать весь файл
typedef struct {
    char* c1_server;
    enum CovertChannelType primary_channel;
    enum CovertChannelType fallback_channel;
    enum EncryptionType encryption;
    uint32_t min_jitter_ms;
    uint32_t max_jitter_ms;
    uint32_t poll_interval_ms;
    uint32_t retry_interval_ms;
    char* encryption_key;
    int verbose;
} cmd_params_t;

#include "../main.c"

// Убираем переопределения
#undef main
#undef main_loop
#undef parse_arguments
#undef init_params
#undef print_usage
#undef create_channel
#undef sleep_ms

// Тесты для функции init_params
void test_init_params() {
    printf("Тест инициализации параметров...\n");
    
    cmd_params_t params;
    init_params(&params);
    
    assert(params.c1_server == NULL);
    assert(params.primary_channel == CHANNEL_TYPE_HTTPS);
    assert(params.fallback_channel == CHANNEL_TYPE_DNS);
    assert(params.encryption == ENCRYPTION_TYPE_AES256);
    assert(params.min_jitter_ms == 1000);
    assert(params.max_jitter_ms == 5000);
    assert(params.poll_interval_ms == DEFAULT_POLL_INTERVAL);
    assert(params.retry_interval_ms == DEFAULT_RETRY_INTERVAL);
    assert(params.encryption_key == NULL);
    assert(params.verbose == 0);
    
    printf("OK\n");
}

// Тесты для функции parse_arguments
void test_parse_arguments() {
    printf("Тесты для разбора аргументов командной строки...\n");
    
    // Тест с минимальными параметрами
    {
        cmd_params_t params;
        init_params(&params);
        
        char* argv[] = {"program", "-s", "example.com"};
        int argc = sizeof(argv) / sizeof(argv[0]);
        
        int result = parse_arguments(argc, argv, &params);
        assert(result == 0);
        assert(strcmp(params.c1_server, "example.com") == 0);
        assert(params.primary_channel == CHANNEL_TYPE_HTTPS);
        assert(params.fallback_channel == CHANNEL_TYPE_DNS);
    }
    
    // Тест с полными параметрами
    {
        cmd_params_t params;
        init_params(&params);
        
        char* argv[] = {
            "program",
            "-s", "example.com",
            "-p", "dns",
            "-f", "icmp",
            "-e", "chacha20",
            "-k", "testkey123",
            "-j", "500-1500",
            "-i", "5000",
            "-r", "30000",
            "-v"
        };
        int argc = sizeof(argv) / sizeof(argv[0]);
        
        int result = parse_arguments(argc, argv, &params);
        assert(result == 0);
        assert(strcmp(params.c1_server, "example.com") == 0);
        assert(params.primary_channel == CHANNEL_TYPE_DNS);
        assert(params.fallback_channel == CHANNEL_TYPE_ICMP);
        assert(params.encryption == ENCRYPTION_TYPE_CHACHA20);
        assert(strcmp(params.encryption_key, "testkey123") == 0);
        assert(params.min_jitter_ms == 500);
        assert(params.max_jitter_ms == 1500);
        assert(params.poll_interval_ms == 5000);
        assert(params.retry_interval_ms == 30000);
        assert(params.verbose == 1);
    }
    
    // Тест с неверными параметрами
    {
        cmd_params_t params;
        init_params(&params);
        
        char* argv[] = {"program", "-x", "unknown"};
        int argc = sizeof(argv) / sizeof(argv[0]);
        
        int result = parse_arguments(argc, argv, &params);
        assert(result == -1);
    }
    
    // Тест с отсутствующим обязательным параметром
    {
        cmd_params_t params;
        init_params(&params);
        
        char* argv[] = {"program", "-p", "dns"};
        int argc = sizeof(argv) / sizeof(argv[0]);
        
        int result = parse_arguments(argc, argv, &params);
        assert(result == -1);
    }
    
    // Тест с параметром помощи
    {
        cmd_params_t params;
        init_params(&params);
        
        char* argv[] = {"program", "-h"};
        int argc = sizeof(argv) / sizeof(argv[0]);
        
        int result = parse_arguments(argc, argv, &params);
        assert(result == 1);
    }
    
    printf("OK\n");
}

// Тесты для функции create_channel
void test_create_channel() {
    printf("Тесты создания канала связи...\n");
    
    // Тест создания DNS канала
    {
        cmd_params_t params;
        init_params(&params);
        params.c1_server = "example.com";
        params.verbose = 1;
        
        covert_channel_handle_t handle = create_channel(&params, CHANNEL_TYPE_DNS);
        assert(handle != NULL);
    }
    
    // Тест создания HTTPS канала
    {
        cmd_params_t params;
        init_params(&params);
        params.c1_server = "example.com";
        
        covert_channel_handle_t handle = create_channel(&params, CHANNEL_TYPE_HTTPS);
        assert(handle != NULL);
    }
    
    // Тест создания ICMP канала
    {
        cmd_params_t params;
        init_params(&params);
        params.c1_server = "example.com";
        
        covert_channel_handle_t handle = create_channel(&params, CHANNEL_TYPE_ICMP);
        assert(handle != NULL);
    }
    
    // Тест с NULL параметрами
    {
        covert_channel_handle_t handle = create_channel(NULL, CHANNEL_TYPE_DNS);
        assert(handle == NULL);
    }
    
    printf("OK\n");
}

// Мок для основного цикла, чтобы он завершался после нескольких итераций
int mock_main_loop_iteration = 0;
int mock_original_while_condition() {
    mock_main_loop_iteration++;
    return mock_main_loop_iteration < 10; // Выполняем 10 итераций цикла
}

// Тест для основного цикла работы
void test_main_loop() {
    printf("Тест основного цикла работы...\n");
    
    cmd_params_t params;
    init_params(&params);
    params.c1_server = "example.com";
    params.verbose = 1;
    
    // Заменяем бесконечный цикл на конечный для тестирования
    #define while(cond) while(mock_original_while_condition())
    
    int result = main_loop(&params);
    
    #undef while
    
    // Проверка, что цикл отработал успешно
    assert(mock_main_loop_iteration == 10);
    
    printf("OK\n");
}

int main() {
    printf("Запуск тестов основного модуля NeuroZond...\n");
    
    test_init_params();
    test_parse_arguments();
    test_create_channel();
    test_main_loop();
    
    printf("Все тесты пройдены успешно!\n");
    return 0;
} 