/**
 * @file test_crypto_channel_integration.c
 * @brief Интеграционный тест взаимодействия криптографического модуля и скрытых каналов связи
 * @author iamtomasanderson@gmail.com (https://github.com/Personaz1/)
 * @date 2023-09-05
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "../network/covert_channel.h"
#include "../crypto/crypto_utils.h"

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

// Тест шифрования данных для передачи по DNS каналу
static int test_crypto_dns_channel() {
    printf("Тестирование интеграции криптографического модуля с DNS каналом\n");
    
    // Исходные данные для передачи
    const unsigned char plaintext[] = "Секретное сообщение для передачи через DNS канал";
    size_t plaintext_len = strlen((const char*)plaintext);
    
    // Ключ шифрования
    const unsigned char key[] = "Crypto4NeuroZond";
    size_t key_len = strlen((const char*)key);
    
    // Буферы для промежуточных данных
    unsigned char encrypted[256];
    unsigned char decrypted[256];
    size_t encrypted_len = sizeof(encrypted);
    size_t decrypted_len = sizeof(decrypted);
    
    // Инициализация криптографического контекста (XOR шифрование подходит для DNS канала)
    CryptoContext *crypto_ctx = crypto_init(CRYPTO_XOR, key, key_len, NULL, 0);
    if (!crypto_ctx) {
        printf("Ошибка инициализации криптографического контекста\n");
        return 1;
    }
    
    // Шифрование данных
    int result = crypto_encrypt(crypto_ctx, plaintext, plaintext_len, encrypted, &encrypted_len);
    if (result != 0) {
        printf("Ошибка шифрования данных: %d\n", result);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    printf("  [INFO] Данные зашифрованы, размер: %zu байт\n", encrypted_len);
    
    // Создаем конфигурацию DNS канала
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_DNS;
    config.encryption = ENCRYPTION_NONE; // Шифрование уже выполнено отдельно
    config.server_address = "example.com";
    config.server_port = 53;
    config.encryption_key = NULL; // Не используем встроенное шифрование канала
    config.encryption_key_len = 0;
    
    // Инициализация канала
    CovertChannelHandle channel = covert_channel_init(&config);
    if (!channel) {
        printf("Ошибка инициализации DNS канала\n");
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Установка параметров Jitter для маскировки трафика
    covert_channel_set_jitter(channel, 50, 200);
    
    printf("  [INFO] DNS канал инициализирован, готов к передаче данных\n");
    
    // В реальности здесь был бы вызов covert_channel_send(channel, encrypted, encrypted_len);
    // Для теста мы просто симулируем передачу и получение данных
    
    printf("  [INFO] Имитация передачи %zu байт зашифрованных данных\n", encrypted_len);
    
    // В реальности здесь был бы вызов covert_channel_receive для получения данных
    // Для теста мы предполагаем, что получили те же данные, что отправили
    
    // Дешифрование полученных данных
    result = crypto_decrypt(crypto_ctx, encrypted, encrypted_len, decrypted, &decrypted_len);
    if (result != 0) {
        printf("Ошибка дешифрования данных: %d\n", result);
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Проверка корректности дешифрования
    if (decrypted_len != plaintext_len || memcmp(decrypted, plaintext, plaintext_len) != 0) {
        printf("Ошибка: расшифрованные данные не совпадают с исходными\n");
        printf("Исходный текст: %s\n", plaintext);
        decrypted[decrypted_len] = '\0';
        printf("Расшифрованный текст: %s\n", decrypted);
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    printf("  [INFO] Данные успешно расшифрованы, контроль целостности пройден\n");
    
    // Освобождение ресурсов
    covert_channel_cleanup(channel);
    crypto_cleanup(crypto_ctx);
    
    return 0;
}

// Тест шифрования данных для передачи по HTTPS каналу с использованием AES-256
static int test_crypto_https_channel() {
    printf("Тестирование интеграции криптографического модуля с HTTPS каналом\n");
    
    // Исходные данные для передачи
    const unsigned char plaintext[] = "Секретное сообщение для передачи через защищенный HTTPS канал";
    size_t plaintext_len = strlen((const char*)plaintext);
    
    // Ключ и IV для AES-256
    const unsigned char key[] = "AES256KeyForNeuroZondHTTPSChannel";
    size_t key_len = 32; // 256 бит
    
    const unsigned char iv[] = "InitVectorForAES";
    size_t iv_len = 16; // 128 бит
    
    // Буферы для промежуточных данных
    unsigned char encrypted[512];
    unsigned char decrypted[512];
    size_t encrypted_len = sizeof(encrypted);
    size_t decrypted_len = sizeof(decrypted);
    
    // Инициализация криптографического контекста (AES-256 шифрование для HTTPS канала)
    CryptoContext *crypto_ctx = crypto_init(CRYPTO_AES256, key, key_len, iv, iv_len);
    if (!crypto_ctx) {
        printf("Ошибка инициализации криптографического контекста AES-256\n");
        return 1;
    }
    
    // Шифрование данных
    int result = crypto_encrypt(crypto_ctx, plaintext, plaintext_len, encrypted, &encrypted_len);
    if (result != 0) {
        printf("Ошибка шифрования данных AES-256: %d\n", result);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    printf("  [INFO] Данные зашифрованы AES-256, размер: %zu байт\n", encrypted_len);
    
    // Кодирование в Base64 для передачи по HTTPS
    char base64_buffer[1024];
    size_t base64_len = sizeof(base64_buffer);
    
    result = crypto_base64_encode(encrypted, encrypted_len, base64_buffer, &base64_len);
    if (result != 0) {
        printf("Ошибка кодирования в Base64: %d\n", result);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    printf("  [INFO] Данные закодированы в Base64, размер: %zu байт\n", base64_len);
    
    // Создаем конфигурацию HTTPS канала
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_HTTPS;
    config.encryption = ENCRYPTION_NONE; // Шифрование уже выполнено отдельно
    config.server_address = "example.com";
    config.server_port = 443;
    config.encryption_key = NULL;
    config.encryption_key_len = 0;
    
    // Инициализация канала
    CovertChannelHandle channel = covert_channel_init(&config);
    if (!channel) {
        printf("Ошибка инициализации HTTPS канала\n");
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Установка параметров Jitter для маскировки трафика
    covert_channel_set_jitter(channel, 100, 500);
    
    printf("  [INFO] HTTPS канал инициализирован, готов к передаче данных\n");
    
    // В реальности здесь был бы вызов для отправки и получения данных
    // Для теста мы просто симулируем передачу и получение данных
    
    printf("  [INFO] Имитация передачи %zu байт Base64-данных через HTTPS\n", base64_len);
    
    // Декодирование из Base64
    unsigned char decoded_buffer[512];
    size_t decoded_len = sizeof(decoded_buffer);
    
    result = crypto_base64_decode(base64_buffer, base64_len, decoded_buffer, &decoded_len);
    if (result != 0) {
        printf("Ошибка декодирования из Base64: %d\n", result);
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Проверка, что декодированные данные совпадают с зашифрованными
    if (decoded_len != encrypted_len || memcmp(decoded_buffer, encrypted, encrypted_len) != 0) {
        printf("Ошибка: декодированные данные не совпадают с зашифрованными\n");
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Дешифрование полученных данных
    result = crypto_decrypt(crypto_ctx, decoded_buffer, decoded_len, decrypted, &decrypted_len);
    if (result != 0) {
        printf("Ошибка дешифрования данных AES-256: %d\n", result);
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Проверка корректности дешифрования
    if (decrypted_len != plaintext_len || memcmp(decrypted, plaintext, plaintext_len) != 0) {
        printf("Ошибка: расшифрованные данные не совпадают с исходными\n");
        printf("Исходный текст: %s\n", plaintext);
        decrypted[decrypted_len] = '\0';
        printf("Расшифрованный текст: %s\n", decrypted);
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    printf("  [INFO] Данные успешно расшифрованы, контроль целостности пройден\n");
    
    // Освобождение ресурсов
    covert_channel_cleanup(channel);
    crypto_cleanup(crypto_ctx);
    
    return 0;
}

// Тест шифрования данных для передачи по ICMP каналу с использованием ChaCha20
static int test_crypto_icmp_channel() {
    printf("Тестирование интеграции криптографического модуля с ICMP каналом\n");
    
    // Исходные данные для передачи
    const unsigned char plaintext[] = "Секретное сообщение для передачи через ICMP канал с ChaCha20";
    size_t plaintext_len = strlen((const char*)plaintext);
    
    // Ключ и nonce для ChaCha20
    const unsigned char key[] = "ChaCha20KeyForNeuroZondICMPChannel!";
    size_t key_len = 32; // 256 бит
    
    const unsigned char nonce[] = "NonceChaCha20";
    size_t nonce_len = 12; // 96 бит
    
    // Буферы для промежуточных данных
    unsigned char encrypted[512];
    unsigned char decrypted[512];
    size_t encrypted_len = sizeof(encrypted);
    size_t decrypted_len = sizeof(decrypted);
    
    // Инициализация криптографического контекста (ChaCha20 шифрование для ICMP канала)
    CryptoContext *crypto_ctx = crypto_init(CRYPTO_CHACHA20, key, key_len, nonce, nonce_len);
    if (!crypto_ctx) {
        printf("Ошибка инициализации криптографического контекста ChaCha20\n");
        return 1;
    }
    
    // Шифрование данных
    int result = crypto_encrypt(crypto_ctx, plaintext, plaintext_len, encrypted, &encrypted_len);
    if (result != 0) {
        printf("Ошибка шифрования данных ChaCha20: %d\n", result);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    printf("  [INFO] Данные зашифрованы ChaCha20, размер: %zu байт\n", encrypted_len);
    
    // Создание хеша для контроля целостности
    unsigned char hash[32]; // SHA-256
    result = crypto_hash(HASH_SHA256, plaintext, plaintext_len, hash, sizeof(hash));
    if (result != 0) {
        printf("Ошибка создания хеша SHA-256: %d\n", result);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    printf("  [INFO] Создан SHA-256 хеш для контроля целостности\n");
    
    // Создаем конфигурацию ICMP канала
    CovertChannelConfig config;
    memset(&config, 0, sizeof(config));
    
    config.channel_type = CHANNEL_ICMP;
    config.encryption = ENCRYPTION_NONE; // Шифрование уже выполнено отдельно
    config.server_address = "example.com";
    config.server_port = 0; // Не используется для ICMP
    config.encryption_key = NULL;
    config.encryption_key_len = 0;
    
    // Инициализация канала
    CovertChannelHandle channel = covert_channel_init(&config);
    if (!channel) {
        printf("Ошибка инициализации ICMP канала\n");
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Установка параметров Jitter для маскировки трафика
    covert_channel_set_jitter(channel, 150, 600);
    
    printf("  [INFO] ICMP канал инициализирован, готов к передаче данных\n");
    
    // Подготовка пакета с данными и хешем
    unsigned char packet[1024];
    size_t packet_pos = 0;
    
    // Добавляем размер зашифрованных данных (4 байта)
    uint32_t data_size = (uint32_t)encrypted_len;
    packet[packet_pos++] = (data_size >> 24) & 0xFF;
    packet[packet_pos++] = (data_size >> 16) & 0xFF;
    packet[packet_pos++] = (data_size >> 8) & 0xFF;
    packet[packet_pos++] = data_size & 0xFF;
    
    // Добавляем зашифрованные данные
    memcpy(packet + packet_pos, encrypted, encrypted_len);
    packet_pos += encrypted_len;
    
    // Добавляем хеш
    memcpy(packet + packet_pos, hash, sizeof(hash));
    packet_pos += sizeof(hash);
    
    printf("  [INFO] Подготовлен пакет данных с SHA-256 хешем, размер: %zu байт\n", packet_pos);
    
    // В реальности здесь был бы вызов для отправки и получения данных
    // Для теста мы просто симулируем передачу и получение данных
    
    printf("  [INFO] Имитация передачи %zu байт данных через ICMP канал\n", packet_pos);
    
    // Разбор полученного пакета
    unsigned char received_packet[1024];
    memcpy(received_packet, packet, packet_pos); // Имитация получения данных
    
    // Получаем размер данных
    uint32_t received_data_size = 
        ((uint32_t)received_packet[0] << 24) |
        ((uint32_t)received_packet[1] << 16) |
        ((uint32_t)received_packet[2] << 8) |
        ((uint32_t)received_packet[3]);
    
    if (received_data_size != encrypted_len) {
        printf("Ошибка: размер данных не совпадает\n");
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Получаем зашифрованные данные
    unsigned char received_encrypted[512];
    memcpy(received_encrypted, received_packet + 4, received_data_size);
    
    // Получаем хеш
    unsigned char received_hash[32];
    memcpy(received_hash, received_packet + 4 + received_data_size, sizeof(hash));
    
    // Дешифрование полученных данных
    result = crypto_decrypt(crypto_ctx, received_encrypted, received_data_size, decrypted, &decrypted_len);
    if (result != 0) {
        printf("Ошибка дешифрования данных ChaCha20: %d\n", result);
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Проверка корректности дешифрования
    if (decrypted_len != plaintext_len || memcmp(decrypted, plaintext, plaintext_len) != 0) {
        printf("Ошибка: расшифрованные данные не совпадают с исходными\n");
        printf("Исходный текст: %s\n", plaintext);
        decrypted[decrypted_len] = '\0';
        printf("Расшифрованный текст: %s\n", decrypted);
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Вычисляем хеш расшифрованных данных для проверки целостности
    unsigned char calculated_hash[32];
    result = crypto_hash(HASH_SHA256, decrypted, decrypted_len, calculated_hash, sizeof(calculated_hash));
    if (result != 0) {
        printf("Ошибка создания хеша SHA-256 для проверки: %d\n", result);
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    // Сравниваем полученный хеш с вычисленным
    if (memcmp(received_hash, calculated_hash, sizeof(hash)) != 0) {
        printf("Ошибка: хеш данных не совпадает - нарушена целостность\n");
        covert_channel_cleanup(channel);
        crypto_cleanup(crypto_ctx);
        return 1;
    }
    
    printf("  [INFO] Данные успешно расшифрованы, контроль целостности пройден\n");
    
    // Освобождение ресурсов
    covert_channel_cleanup(channel);
    crypto_cleanup(crypto_ctx);
    
    return 0;
}

// Тест комбинированного использования разных каналов с разными алгоритмами шифрования
static int test_combined_channels() {
    printf("Тестирование комбинированного использования разных каналов связи\n");
    
    // Базовая конфигурация для всех каналов
    CovertChannelConfig config_dns;
    CovertChannelConfig config_https;
    CovertChannelConfig config_icmp;
    
    memset(&config_dns, 0, sizeof(config_dns));
    memset(&config_https, 0, sizeof(config_https));
    memset(&config_icmp, 0, sizeof(config_icmp));
    
    // Настройка DNS канала
    config_dns.channel_type = CHANNEL_DNS;
    config_dns.encryption = ENCRYPTION_XOR;
    config_dns.server_address = "c1.example.com";
    config_dns.server_port = 53;
    config_dns.encryption_key = (unsigned char*)"DNSChannelKey";
    config_dns.encryption_key_len = 12;
    
    // Настройка HTTPS канала
    config_https.channel_type = CHANNEL_HTTPS;
    config_https.encryption = ENCRYPTION_AES256;
    config_https.server_address = "c1.example.com";
    config_https.server_port = 443;
    config_https.encryption_key = (unsigned char*)"HTTPSChannelKey";
    config_https.encryption_key_len = 14;
    
    // Настройка ICMP канала
    config_icmp.channel_type = CHANNEL_ICMP;
    config_icmp.encryption = ENCRYPTION_CHACHA20;
    config_icmp.server_address = "c1.example.com";
    config_icmp.server_port = 0;
    config_icmp.encryption_key = (unsigned char*)"ICMPChannelKey";
    config_icmp.encryption_key_len = 13;
    
    // Инициализация каналов связи
    CovertChannelHandle handle_dns = covert_channel_init(&config_dns);
    if (!handle_dns) {
        printf("Ошибка инициализации DNS канала\n");
        return 1;
    }
    
    CovertChannelHandle handle_https = covert_channel_init(&config_https);
    if (!handle_https) {
        printf("Ошибка инициализации HTTPS канала\n");
        covert_channel_cleanup(handle_dns);
        return 1;
    }
    
    CovertChannelHandle handle_icmp = covert_channel_init(&config_icmp);
    if (!handle_icmp) {
        printf("Ошибка инициализации ICMP канала\n");
        covert_channel_cleanup(handle_https);
        covert_channel_cleanup(handle_dns);
        return 1;
    }
    
    printf("  [INFO] Все каналы связи успешно инициализированы\n");
    
    // Установка разных параметров джиттера для каждого канала
    covert_channel_set_jitter(handle_dns, 50, 150);
    covert_channel_set_jitter(handle_https, 100, 300);
    covert_channel_set_jitter(handle_icmp, 200, 700);
    
    // Тестовое сообщение для отправки по всем каналам
    const char* message = "Тестовое сообщение для отправки по нескольким каналам связи";
    printf("  [INFO] Подготовлено сообщение: \"%s\"\n", message);
    
    // В реальном сценарии, здесь бы происходила отправка разных частей сообщения по
    // разным каналам связи для повышения скрытности и отказоустойчивости
    
    printf("  [INFO] Имитация отправки частей сообщения через разные каналы связи\n");
    
    // Очистка ресурсов
    covert_channel_cleanup(handle_dns);
    covert_channel_cleanup(handle_https);
    covert_channel_cleanup(handle_icmp);
    
    printf("  [INFO] Все каналы связи успешно освобождены\n");
    
    return 0;
}

// Главная функция, запускающая все тесты
int main() {
    int total_tests = 0;
    int tests_passed = 0;
    int tests_failed = 0;
    
    printf("==== Интеграционные тесты криптографического модуля и скрытых каналов связи ====\n\n");
    
    RUN_TEST(test_crypto_dns_channel);
    RUN_TEST(test_crypto_https_channel);
    RUN_TEST(test_crypto_icmp_channel);
    RUN_TEST(test_combined_channels);
    
    printf("==== Результаты тестирования ====\n");
    printf("Всего тестов: %d\n", total_tests);
    printf("Успешно: %d\n", tests_passed);
    printf("Неудачно: %d\n", tests_failed);
    
    return tests_failed > 0 ? 1 : 0;
} 