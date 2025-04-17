/**
 * @file test_integration.c
 * @brief Интеграционный тест для модулей NeuroZond
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-04
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "../network/covert_channel.h"
#include "../crypto/crypto_utils.h"

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
 * @brief Тестирует шифрование данных перед отправкой через скрытый канал
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_crypto_with_covert_channel() {
    // Данные для передачи
    const uint8_t plaintext[] = "Secret message for transmission through covert channel";
    // Ключ для шифрования
    const uint8_t key[] = "encryption_key_for_testing";
    
    // Буферы для промежуточных данных
    uint8_t encrypted[100];
    uint8_t decrypted[100];
    size_t encrypted_len = sizeof(encrypted);
    size_t decrypted_len = sizeof(decrypted);
    
    // Инициализация криптографического контекста (XOR шифрование)
    CryptoContext *crypto_ctx = crypto_init(CRYPTO_XOR, key, strlen((char*)key), NULL, 0);
    
    if (crypto_ctx == NULL) {
        printf("Failed to initialize crypto context\n");
        return 1;
    }
    
    // Шифрование данных
    int result = crypto_encrypt(crypto_ctx, plaintext, strlen((char*)plaintext), 
                              encrypted, &encrypted_len);
    
    if (result != 0) {
        printf("Encryption failed with code %d\n", result);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Создание конфигурации скрытого канала связи
    covert_channel_config channel_config;
    memset(&channel_config, 0, sizeof(channel_config));
    
    channel_config.type = COVERT_CHANNEL_DNS;
    channel_config.encryption = ENCRYPTION_NONE; // Шифрование уже выполнено
    channel_config.c1_address = "example.com";
    channel_config.c1_port = 53;
    channel_config.encryption_key = NULL;
    channel_config.key_length = 0;
    
    // Инициализация скрытого канала
    covert_channel_handle channel = covert_channel_init(&channel_config);
    
    if (channel == NULL) {
        printf("Failed to initialize covert channel\n");
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Установка параметров jitter (имитация реальной передачи)
    covert_channel_set_jitter(channel, 100, 500);
    
    // Имитация отправки данных по скрытому каналу (без реальной отправки в тестах)
    printf("  [INFO] Sending %zu bytes of encrypted data through DNS channel\n", encrypted_len);
    
    // Тут был бы вызов covert_channel_send(channel, encrypted, encrypted_len)
    
    // Имитация получения данных (предполагаем, что получили те же данные, что отправили)
    
    // Дешифрование полученных данных
    result = crypto_decrypt(crypto_ctx, encrypted, encrypted_len, 
                          decrypted, &decrypted_len);
    
    if (result != 0) {
        printf("Decryption failed with code %d\n", result);
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Проверка, что данные после шифрования/дешифрования совпадают с исходными
    if (decrypted_len != strlen((char*)plaintext) || 
        memcmp(decrypted, plaintext, decrypted_len) != 0) {
        printf("Data mismatch after encryption/decryption\n");
        printf("Original: %s\n", (char*)plaintext);
        decrypted[decrypted_len] = '\0';
        printf("Decrypted: %s\n", (char*)decrypted);
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Освобождение ресурсов
    covert_channel_cleanup(channel);
    crypto_cleanup(crypto_ctx);
    
    return 0;
}

/**
 * @brief Тестирует использование хеширования для проверки целостности данных при передаче
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_hash_for_data_integrity() {
    // Данные для передачи
    const uint8_t data[] = "Data that needs integrity verification";
    uint8_t hash[32]; // SHA-256 хеш
    size_t hash_len = sizeof(hash);
    
    // Вычисляем хеш данных
    int result = crypto_hash(HASH_SHA256, data, strlen((char*)data), hash, hash_len);
    
    if (result != 0) {
        printf("Hash calculation failed with code %d\n", result);
        return 1;
    }
    
    // Создание конфигурации скрытого канала связи
    covert_channel_config channel_config;
    memset(&channel_config, 0, sizeof(channel_config));
    
    channel_config.type = COVERT_CHANNEL_HTTPS;
    channel_config.encryption = ENCRYPTION_NONE;
    channel_config.c1_address = "example.com";
    channel_config.c1_port = 443;
    channel_config.encryption_key = NULL;
    channel_config.key_length = 0;
    
    // Инициализация скрытого канала
    covert_channel_handle channel = covert_channel_init(&channel_config);
    
    if (channel == NULL) {
        printf("Failed to initialize covert channel\n");
        return 1;
    }
    
    // Подготовка буфера с данными и хешем
    uint8_t buffer[512];
    size_t buffer_pos = 0;
    
    // Добавляем размер данных (4 байта)
    uint32_t data_size = (uint32_t)strlen((char*)data);
    buffer[buffer_pos++] = (data_size >> 24) & 0xFF;
    buffer[buffer_pos++] = (data_size >> 16) & 0xFF;
    buffer[buffer_pos++] = (data_size >> 8) & 0xFF;
    buffer[buffer_pos++] = data_size & 0xFF;
    
    // Добавляем данные
    memcpy(buffer + buffer_pos, data, data_size);
    buffer_pos += data_size;
    
    // Добавляем хеш
    memcpy(buffer + buffer_pos, hash, hash_len);
    buffer_pos += hash_len;
    
    printf("  [INFO] Prepared %zu bytes of data with SHA-256 hash for transmission\n", buffer_pos);
    
    // Имитация отправки данных по скрытому каналу (без реальной отправки в тестах)
    
    // Имитация получения данных (предполагаем, что получили те же данные, что отправили)
    
    // Извлечение данных и хеша из полученного буфера
    uint8_t received_buffer[512];
    memcpy(received_buffer, buffer, buffer_pos);
    
    // Получаем размер данных
    uint32_t received_data_size = 
        ((uint32_t)received_buffer[0] << 24) |
        ((uint32_t)received_buffer[1] << 16) |
        ((uint32_t)received_buffer[2] << 8) |
        ((uint32_t)received_buffer[3]);
    
    if (received_data_size != data_size) {
        printf("Data size mismatch: expected %u, got %u\n", data_size, received_data_size);
        covert_channel_cleanup(channel);
        return 1;
    }
    
    // Получаем данные
    uint8_t received_data[256];
    memcpy(received_data, received_buffer + 4, received_data_size);
    
    // Получаем хеш
    uint8_t received_hash[32];
    memcpy(received_hash, received_buffer + 4 + received_data_size, hash_len);
    
    // Проверяем данные
    if (memcmp(received_data, data, received_data_size) != 0) {
        printf("Data mismatch\n");
        covert_channel_cleanup(channel);
        return 1;
    }
    
    // Вычисляем хеш полученных данных
    uint8_t calculated_hash[32];
    result = crypto_hash(HASH_SHA256, received_data, received_data_size, 
                       calculated_hash, sizeof(calculated_hash));
    
    if (result != 0) {
        printf("Hash calculation for received data failed with code %d\n", result);
        covert_channel_cleanup(channel);
        return 1;
    }
    
    // Сравниваем полученный хеш с вычисленным
    if (memcmp(received_hash, calculated_hash, hash_len) != 0) {
        printf("Hash mismatch - data integrity check failed\n");
        covert_channel_cleanup(channel);
        return 1;
    }
    
    printf("  [INFO] Data integrity verified successfully using SHA-256\n");
    
    // Освобождение ресурсов
    covert_channel_cleanup(channel);
    
    return 0;
}

/**
 * @brief Главная функция для запуска тестов
 * 
 * @return int Код возврата программы
 */
int main() {
    printf("=== Running Integration Tests ===\n\n");
    
    // Запуск тестов
    RUN_TEST(test_crypto_with_covert_channel);
    RUN_TEST(test_hash_for_data_integrity);
    
    // Вывод итогов
    printf("\n=== Test Results ===\n");
    printf("Passed: %d\n", tests_passed);
    printf("Failed: %d\n", tests_failed);
    printf("Total: %d\n", tests_passed + tests_failed);
    
    return tests_failed > 0 ? 1 : 0;
} 