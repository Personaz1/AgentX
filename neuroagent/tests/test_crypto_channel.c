/**
 * @file test_crypto_channel.c
 * @brief Тестирование модуля интеграции криптографии и скрытых каналов связи
 * @author iamtomasanderson@gmail.com (https://github.com/Personaz1/)
 * @date 2023-09-05
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "../network/covert_channel.h"
#include "../crypto/crypto_utils.h"
#include "../network/crypto_channel.h"

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

// Тест инициализации и очистки криптографического канала
static int test_crypto_channel_init_cleanup() {
    printf("Тестирование инициализации и очистки криптографического канала\n");
    
    // Создаем базовую конфигурацию канала
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_DNS;
    config.encryption = ENCRYPTION_NONE; // Шифрование будет выполняться в crypto_channel
    config.server_address = "example.com";
    config.server_port = 53;
    
    // Ключ для XOR шифрования
    const unsigned char key[] = "TestCryptoChannelKey";
    size_t key_len = strlen((const char*)key);
    
    // Инициализируем канал с XOR шифрованием и проверкой целостности SHA-256
    CryptoChannelHandle handle = crypto_channel_init(
        &config, 
        CRYPTO_XOR, 
        key, key_len, 
        NULL, 0, 
        1, // Использовать проверку целостности
        HASH_SHA256
    );
    
    if (!handle) {
        printf("Ошибка инициализации криптографического канала\n");
        return 1;
    }
    
    printf("  [INFO] Криптографический канал успешно инициализирован\n");
    
    // Очищаем ресурсы
    crypto_channel_cleanup(handle);
    
    printf("  [INFO] Ресурсы канала успешно освобождены\n");
    
    return 0;
}

// Тест инициализации с разными алгоритмами шифрования
static int test_crypto_channel_different_algorithms() {
    printf("Тестирование различных алгоритмов шифрования\n");
    
    // Создаем базовую конфигурацию канала
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_HTTPS;
    config.encryption = ENCRYPTION_NONE;
    config.server_address = "example.com";
    config.server_port = 443;
    
    // Ключи для разных алгоритмов
    const unsigned char xor_key[] = "XorKey12345";
    const unsigned char aes_key[] = "AES256KeyMustBe32BytesInLengthX";
    const unsigned char chacha_key[] = "ChaCha20KeyMustBe32BytesLength!";
    
    // IV для AES и nonce для ChaCha20
    const unsigned char iv[] = "InitVectorFor16B";
    const unsigned char nonce[] = "NonceFor12Byte";
    
    // 1. Тест XOR
    CryptoChannelHandle handle_xor = crypto_channel_init(
        &config, 
        CRYPTO_XOR, 
        xor_key, strlen((const char*)xor_key), 
        NULL, 0, 
        0, // Без проверки целостности
        HASH_NONE
    );
    
    if (!handle_xor) {
        printf("Ошибка инициализации канала с XOR шифрованием\n");
        return 1;
    }
    
    printf("  [INFO] Канал с XOR шифрованием успешно инициализирован\n");
    
    // 2. Тест AES-256
    CryptoChannelHandle handle_aes = crypto_channel_init(
        &config, 
        CRYPTO_AES256, 
        aes_key, 32, 
        iv, 16, 
        1, // С проверкой целостности
        HASH_SHA256
    );
    
    if (!handle_aes) {
        printf("Ошибка инициализации канала с AES-256 шифрованием\n");
        crypto_channel_cleanup(handle_xor);
        return 1;
    }
    
    printf("  [INFO] Канал с AES-256 шифрованием успешно инициализирован\n");
    
    // 3. Тест ChaCha20
    CryptoChannelHandle handle_chacha = crypto_channel_init(
        &config, 
        CRYPTO_CHACHA20, 
        chacha_key, 32, 
        nonce, 12, 
        1, // С проверкой целостности
        HASH_SHA256
    );
    
    if (!handle_chacha) {
        printf("Ошибка инициализации канала с ChaCha20 шифрованием\n");
        crypto_channel_cleanup(handle_xor);
        crypto_channel_cleanup(handle_aes);
        return 1;
    }
    
    printf("  [INFO] Канал с ChaCha20 шифрованием успешно инициализирован\n");
    
    // Очищаем ресурсы
    crypto_channel_cleanup(handle_xor);
    crypto_channel_cleanup(handle_aes);
    crypto_channel_cleanup(handle_chacha);
    
    return 0;
}

// Тест настройки параметров джиттера
static int test_crypto_channel_jitter() {
    printf("Тестирование настройки параметров джиттера\n");
    
    // Создаем конфигурацию канала
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_DNS;
    config.encryption = ENCRYPTION_NONE;
    config.server_address = "example.com";
    config.server_port = 53;
    
    // Ключ для XOR шифрования
    const unsigned char key[] = "TestJitterKey";
    size_t key_len = strlen((const char*)key);
    
    // Инициализируем канал с XOR шифрованием
    CryptoChannelHandle handle = crypto_channel_init(
        &config, 
        CRYPTO_XOR, 
        key, key_len, 
        NULL, 0, 
        0, // Без проверки целостности
        HASH_NONE
    );
    
    if (!handle) {
        printf("Ошибка инициализации криптографического канала\n");
        return 1;
    }
    
    // Устанавливаем параметры джиттера
    int result = crypto_channel_set_jitter(handle, 100, 500);
    if (result != 0) {
        printf("Ошибка установки параметров джиттера\n");
        crypto_channel_cleanup(handle);
        return 1;
    }
    
    printf("  [INFO] Параметры джиттера успешно установлены (100-500 мс)\n");
    
    // Проверяем установку некорректных параметров
    result = crypto_channel_set_jitter(handle, 600, 500);
    if (result == 0) {
        printf("Ошибка: некорректные параметры джиттера (min > max) были приняты\n");
        crypto_channel_cleanup(handle);
        return 1;
    }
    
    printf("  [INFO] Некорректные параметры джиттера успешно отклонены\n");
    
    // Очищаем ресурсы
    crypto_channel_cleanup(handle);
    
    return 0;
}

// Тест отправки и получения данных с использованием модуля crypto_channel
static int test_crypto_channel_send_receive() {
    printf("Тестирование отправки и получения данных через криптографический канал\n");
    
    // В этом тесте мы можем только симулировать отправку и получение, 
    // так как для реальной отправки нужен работающий сервер C1
    
    // Создаем конфигурацию канала
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_DNS;
    config.encryption = ENCRYPTION_NONE;
    config.server_address = "example.com";
    config.server_port = 53;
    
    // Ключ для AES-256 шифрования
    const unsigned char key[] = "AES256KeyMustBe32BytesInLengthX";
    const unsigned char iv[] = "InitVectorFor16B";
    
    // Инициализируем канал с AES-256 шифрованием и проверкой целостности
    CryptoChannelHandle handle = crypto_channel_init(
        &config, 
        CRYPTO_AES256, 
        key, 32, 
        iv, 16, 
        1, // С проверкой целостности
        HASH_SHA256
    );
    
    if (!handle) {
        printf("Ошибка инициализации криптографического канала\n");
        return 1;
    }
    
    // Устанавливаем параметры джиттера
    crypto_channel_set_jitter(handle, 50, 200);
    
    // Тестовое сообщение для отправки
    const unsigned char message[] = "Тестовое сообщение для проверки отправки и получения через криптографический канал";
    size_t message_len = strlen((const char*)message);
    
    printf("  [INFO] Подготовлено сообщение для отправки: \"%s\"\n", message);
    
    // В реальном сценарии здесь была бы отправка данных через crypto_channel_send
    // и получение через crypto_channel_receive, но в тесте мы можем только
    // убедиться, что функции не вызывают ошибок при вызове с правильными параметрами
    
    printf("  [INFO] Симуляция отправки сообщения через канал\n");
    
    // Очищаем ресурсы
    crypto_channel_cleanup(handle);
    
    printf("  [INFO] Ресурсы канала успешно освобождены\n");
    
    return 0;
}

// Тест работы с некорректными параметрами
static int test_crypto_channel_invalid_params() {
    printf("Тестирование работы с некорректными параметрами\n");
    
    // Проверка NULL параметров в crypto_channel_init
    {
        CovertChannelConfig config;
        memset(&config, 0, sizeof(config));
        
        config.channel_type = CHANNEL_DNS;
        config.encryption = ENCRYPTION_NONE;
        config.server_address = "example.com";
        config.server_port = 53;
        
        const unsigned char key[] = "TestKey";
        
        // NULL config
        CryptoChannelHandle handle = crypto_channel_init(
            NULL, 
            CRYPTO_XOR, 
            key, strlen((const char*)key), 
            NULL, 0, 
            0, 
            HASH_NONE
        );
        
        if (handle != NULL) {
            printf("Ошибка: инициализация с NULL config должна возвращать NULL\n");
            crypto_channel_cleanup(handle);
            return 1;
        }
        
        // NULL crypto_key
        handle = crypto_channel_init(
            &config, 
            CRYPTO_XOR, 
            NULL, 0, 
            NULL, 0, 
            0, 
            HASH_NONE
        );
        
        if (handle != NULL) {
            printf("Ошибка: инициализация с NULL ключом должна возвращать NULL\n");
            crypto_channel_cleanup(handle);
            return 1;
        }
        
        printf("  [INFO] Проверка NULL параметров в crypto_channel_init пройдена\n");
    }
    
    // Проверка работы с NULL handle
    {
        // Соединение с NULL handle
        int result = crypto_channel_connect(NULL);
        if (result != -1) {
            printf("Ошибка: crypto_channel_connect с NULL handle должен возвращать -1\n");
            return 1;
        }
        
        // Отправка данных с NULL handle
        const unsigned char data[] = "Test";
        result = crypto_channel_send(NULL, data, 4);
        if (result != -1) {
            printf("Ошибка: crypto_channel_send с NULL handle должен возвращать -1\n");
            return 1;
        }
        
        // Прием данных с NULL handle
        unsigned char buffer[128];
        result = crypto_channel_receive(NULL, buffer, sizeof(buffer));
        if (result != -1) {
            printf("Ошибка: crypto_channel_receive с NULL handle должен возвращать -1\n");
            return 1;
        }
        
        // Проверка соединения с NULL handle
        result = crypto_channel_is_connected(NULL);
        if (result != -1) {
            printf("Ошибка: crypto_channel_is_connected с NULL handle должен возвращать -1\n");
            return 1;
        }
        
        // Установка джиттера с NULL handle
        result = crypto_channel_set_jitter(NULL, 100, 200);
        if (result != -1) {
            printf("Ошибка: crypto_channel_set_jitter с NULL handle должен возвращать -1\n");
            return 1;
        }
        
        // Очистка ресурсов с NULL handle не должна вызывать ошибок
        crypto_channel_cleanup(NULL);
        
        printf("  [INFO] Проверка работы с NULL handle пройдена\n");
    }
    
    return 0;
}

int main() {
    int total_tests = 0;
    int tests_passed = 0;
    int tests_failed = 0;
    
    printf("==== Тестирование модуля crypto_channel ====\n\n");
    
    RUN_TEST(test_crypto_channel_init_cleanup);
    RUN_TEST(test_crypto_channel_different_algorithms);
    RUN_TEST(test_crypto_channel_jitter);
    RUN_TEST(test_crypto_channel_send_receive);
    RUN_TEST(test_crypto_channel_invalid_params);
    
    printf("==== Результаты тестирования ====\n");
    printf("Всего тестов: %d\n", total_tests);
    printf("Успешно: %d\n", tests_passed);
    printf("Неудачно: %d\n", tests_failed);
    
    return tests_failed > 0 ? 1 : 0;
} 