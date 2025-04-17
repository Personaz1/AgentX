/**
 * @file test_crypto.c
 * @brief Тесты для модуля криптографических утилит
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-03
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

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
 * @brief Тест инициализации криптографического контекста
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_crypto_init() {
    // Тест инициализации с XOR шифрованием
    const uint8_t key[] = "test_key_123";
    CryptoContext *ctx = crypto_init(CRYPTO_XOR, key, strlen((char*)key), NULL, 0);
    
    if (ctx == NULL) {
        return 1;
    }
    
    // Проверка, что контекст корректно инициализирован
    assert(ctx->algorithm == CRYPTO_XOR);
    assert(ctx->key != NULL);
    assert(ctx->key_len == strlen((char*)key));
    assert(ctx->iv == NULL);
    assert(ctx->iv_len == 0);
    
    crypto_cleanup(ctx);
    
    // Тест инициализации с AES256 шифрованием
    const uint8_t aes_key[] = "AES256_key_for_testing_purposes";
    const uint8_t iv[] = "iv_for_testing";
    
    ctx = crypto_init(CRYPTO_AES256, aes_key, strlen((char*)aes_key), iv, strlen((char*)iv));
    
    if (ctx == NULL) {
        return 1;
    }
    
    // Проверка, что контекст корректно инициализирован
    assert(ctx->algorithm == CRYPTO_AES256);
    assert(ctx->key != NULL);
    assert(ctx->key_len == strlen((char*)aes_key));
    assert(ctx->iv != NULL);
    assert(ctx->iv_len == strlen((char*)iv));
    
    crypto_cleanup(ctx);
    
    return 0;
}

/**
 * @brief Тест инициализации с некорректными параметрами
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_crypto_init_invalid_params() {
    // Тест с NULL ключом
    CryptoContext *ctx = crypto_init(CRYPTO_XOR, NULL, 10, NULL, 0);
    
    if (ctx != NULL) {
        crypto_cleanup(ctx);
        return 1;
    }
    
    // Тест с нулевой длиной ключа
    const uint8_t key[] = "test_key";
    ctx = crypto_init(CRYPTO_XOR, key, 0, NULL, 0);
    
    if (ctx != NULL) {
        crypto_cleanup(ctx);
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции XOR шифрования
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_crypto_xor() {
    const uint8_t key[] = "xor_key";
    const uint8_t data[] = "test data for XOR encryption";
    uint8_t encrypted[100];
    uint8_t decrypted[100];
    
    // Копируем данные в буфер для шифрования
    memcpy(encrypted, data, sizeof(data));
    
    // Шифруем данные
    crypto_xor(encrypted, sizeof(data) - 1, key, sizeof(key) - 1);
    
    // Проверяем, что данные изменились
    if (memcmp(encrypted, data, sizeof(data) - 1) == 0) {
        return 1;
    }
    
    // Копируем зашифрованные данные для дешифрования
    memcpy(decrypted, encrypted, sizeof(data));
    
    // Дешифруем данные (повторное XOR с тем же ключом)
    crypto_xor(decrypted, sizeof(data) - 1, key, sizeof(key) - 1);
    
    // Проверяем, что данные восстановились
    if (memcmp(decrypted, data, sizeof(data) - 1) != 0) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции генерации случайных чисел
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_crypto_random_bytes() {
    uint8_t buffer1[32] = {0};
    uint8_t buffer2[32] = {0};
    
    // Генерируем случайные данные
    int result1 = crypto_random_bytes(buffer1, sizeof(buffer1));
    int result2 = crypto_random_bytes(buffer2, sizeof(buffer2));
    
    if (result1 != 0 || result2 != 0) {
        return 1;
    }
    
    // Проверяем, что сгенерированные данные не являются нулевыми
    int all_zeros1 = 1;
    int all_zeros2 = 1;
    
    for (size_t i = 0; i < sizeof(buffer1); i++) {
        if (buffer1[i] != 0) {
            all_zeros1 = 0;
        }
        if (buffer2[i] != 0) {
            all_zeros2 = 0;
        }
    }
    
    if (all_zeros1 || all_zeros2) {
        return 1;
    }
    
    // Проверяем, что два вызова генерируют разные данные
    if (memcmp(buffer1, buffer2, sizeof(buffer1)) == 0) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции шифрования и дешифрования
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_crypto_encrypt_decrypt() {
    const uint8_t key[] = "encryption_key_for_testing";
    const uint8_t plaintext[] = "This is a test message for encryption and decryption";
    uint8_t ciphertext[100];
    uint8_t decrypted[100];
    size_t ciphertext_len = sizeof(ciphertext);
    size_t decrypted_len = sizeof(decrypted);
    
    // Инициализируем контекст для XOR шифрования
    CryptoContext *ctx = crypto_init(CRYPTO_XOR, key, strlen((char*)key), NULL, 0);
    
    if (ctx == NULL) {
        return 1;
    }
    
    // Шифруем данные
    int result = crypto_encrypt(ctx, plaintext, strlen((char*)plaintext), ciphertext, &ciphertext_len);
    
    if (result != 0) {
        crypto_cleanup(ctx);
        return 1;
    }
    
    // Проверяем, что данные изменились
    if (memcmp(ciphertext, plaintext, strlen((char*)plaintext)) == 0) {
        crypto_cleanup(ctx);
        return 1;
    }
    
    // Дешифруем данные
    result = crypto_decrypt(ctx, ciphertext, ciphertext_len, decrypted, &decrypted_len);
    
    if (result != 0) {
        crypto_cleanup(ctx);
        return 1;
    }
    
    // Проверяем, что данные восстановились
    if (decrypted_len != strlen((char*)plaintext) || 
        memcmp(decrypted, plaintext, strlen((char*)plaintext)) != 0) {
        crypto_cleanup(ctx);
        return 1;
    }
    
    crypto_cleanup(ctx);
    return 0;
}

/**
 * @brief Тест функции Base64 кодирования
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_base64_encode() {
    const uint8_t data[] = "Test data for Base64 encoding";
    char encoded[100];
    size_t encoded_len = sizeof(encoded);
    
    // Кодируем данные
    int result = crypto_base64_encode(data, strlen((char*)data), encoded, &encoded_len);
    
    if (result != 0) {
        return 1;
    }
    
    // Проверяем, что закодированная строка не пустая
    if (encoded_len == 0 || encoded[0] == '\0') {
        return 1;
    }
    
    // Правильный результат должен заканчиваться на "="
    if (encoded[encoded_len - 1] != '=' && encoded[encoded_len - 2] != '=') {
        // Не все Base64 строки должны заканчиваться на "=", это зависит от длины входных данных
        // Поэтому это не является ошибкой
    }
    
    return 0;
}

/**
 * @brief Тест функции декодирования Base64
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_base64_decode() {
    // Тестовые данные и их закодированное Base64 представление
    const char *test_text = "Test Base64 decoding";
    const char *encoded = "VGVzdCBCYXNlNjQgZGVjb2Rpbmc=";
    
    uint8_t decoded[100];
    size_t decoded_len = sizeof(decoded);
    
    // Декодируем данные
    int result = crypto_base64_decode(encoded, strlen(encoded), decoded, &decoded_len);
    
    if (result != 0) {
        return 1;
    }
    
    // Проверяем, что длина декодированных данных корректна
    if (decoded_len != strlen(test_text)) {
        return 1;
    }
    
    // Проверяем, что данные декодированы правильно
    if (memcmp(decoded, test_text, decoded_len) != 0) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции кодирования и декодирования Base64
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_base64_encode_decode_cycle() {
    const uint8_t original[] = "This is a test string for Base64 encoding and decoding cycle";
    char encoded[200];
    uint8_t decoded[200];
    size_t encoded_len = sizeof(encoded);
    size_t decoded_len = sizeof(decoded);
    
    // Кодируем исходные данные
    int result = crypto_base64_encode(original, strlen((char*)original), encoded, &encoded_len);
    
    if (result != 0) {
        return 1;
    }
    
    // Декодируем обратно
    result = crypto_base64_decode(encoded, encoded_len, decoded, &decoded_len);
    
    if (result != 0) {
        return 1;
    }
    
    // Проверяем, что данные после цикла кодирования/декодирования совпадают с исходными
    if (decoded_len != strlen((char*)original) || 
        memcmp(decoded, original, decoded_len) != 0) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции Base32 кодирования
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_base32_encode() {
    const uint8_t data[] = "Test data for Base32 encoding";
    char encoded[100];
    size_t encoded_len = sizeof(encoded);
    
    // Кодируем данные
    int result = crypto_base32_encode(data, strlen((char*)data), encoded, &encoded_len);
    
    if (result != 0) {
        return 1;
    }
    
    // Проверяем, что закодированная строка не пустая
    if (encoded_len == 0 || encoded[0] == '\0') {
        return 1;
    }
    
    // Проверяем, что в строке только допустимые символы Base32
    for (size_t i = 0; i < encoded_len && encoded[i] != '='; i++) {
        if (!((encoded[i] >= 'A' && encoded[i] <= 'Z') || 
              (encoded[i] >= '2' && encoded[i] <= '7'))) {
            return 1;
        }
    }
    
    return 0;
}

/**
 * @brief Тест функции декодирования Base32
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_base32_decode() {
    // Тестовые данные и их закодированное Base32 представление
    const char *test_text = "Hello";
    const char *encoded = "JBSWY3DP";
    
    uint8_t decoded[100];
    size_t decoded_len = sizeof(decoded);
    
    // Декодируем данные
    int result = crypto_base32_decode(encoded, strlen(encoded), decoded, &decoded_len);
    
    if (result != 0) {
        printf("Decoding failed with error code: %d\n", result);
        return 1;
    }
    
    // Проверяем, что длина декодированных данных корректна
    if (decoded_len != strlen(test_text)) {
        printf("Wrong decoded length: expected %zu, got %zu\n", strlen(test_text), decoded_len);
        decoded[decoded_len] = '\0'; // добавляем нулевой символ для вывода
        printf("Decoded: %s\n", (char*)decoded);
        return 1;
    }
    
    // Проверяем, что данные декодированы правильно
    if (memcmp(decoded, test_text, decoded_len) != 0) {
        printf("Decoded data doesn't match original\n");
        decoded[decoded_len] = '\0'; // добавляем нулевой символ для вывода
        printf("Expected: %s\n", test_text);
        printf("Got: %s\n", (char*)decoded);
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции кодирования и декодирования Base32
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_base32_encode_decode_cycle() {
    const uint8_t original[] = "This is a test string for Base32 encoding and decoding cycle";
    char encoded[200];
    uint8_t decoded[200];
    size_t encoded_len = sizeof(encoded);
    size_t decoded_len = sizeof(decoded);
    
    // Кодируем исходные данные
    int result = crypto_base32_encode(original, strlen((char*)original), encoded, &encoded_len);
    
    if (result != 0) {
        return 1;
    }
    
    // Декодируем обратно
    result = crypto_base32_decode(encoded, encoded_len, decoded, &decoded_len);
    
    if (result != 0) {
        return 1;
    }
    
    // Проверяем, что данные после цикла кодирования/декодирования совпадают с исходными
    if (decoded_len != strlen((char*)original) || 
        memcmp(decoded, original, decoded_len) != 0) {
        return 1;
    }
    
    return 0;
}

/**
 * @brief Тест функции шифрования и дешифрования AES256
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_crypto_aes256() {
    // Для AES256 нужен ключ длиной 32 байта (256 бит)
    const uint8_t key[] = {
        0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10,
        0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
        0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20
    };
    
    // Для AES нужен вектор инициализации длиной 16 байт (128 бит)
    const uint8_t iv[] = {
        0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F, 0x30
    };
    
    const uint8_t plaintext[] = "This is a test message for AES256 encryption and decryption";
    uint8_t ciphertext[100];
    uint8_t decrypted[100];
    size_t ciphertext_len = sizeof(ciphertext);
    size_t decrypted_len = sizeof(decrypted);
    
    // Инициализация контекста AES256
    CryptoContext *ctx = crypto_init(CRYPTO_AES256, key, sizeof(key), iv, sizeof(iv));
    
    if (ctx == NULL) {
        printf("Failed to initialize AES256 context\n");
        return 1;
    }
    
    // Шифрование данных
    int result = crypto_encrypt(ctx, plaintext, strlen((char*)plaintext), ciphertext, &ciphertext_len);
    
    if (result != 0) {
        printf("AES256 encryption failed with code %d\n", result);
        crypto_cleanup(ctx);
        return 1;
    }
    
    // Проверяем, что данные изменились
    if (ciphertext_len != strlen((char*)plaintext) || 
        memcmp(ciphertext, plaintext, strlen((char*)plaintext)) == 0) {
        printf("AES256 encryption didn't change the data\n");
        crypto_cleanup(ctx);
        return 1;
    }
    
    // Дешифрование данных
    result = crypto_decrypt(ctx, ciphertext, ciphertext_len, decrypted, &decrypted_len);
    
    if (result != 0) {
        printf("AES256 decryption failed with code %d\n", result);
        crypto_cleanup(ctx);
        return 1;
    }
    
    // Проверяем, что данные восстановились
    if (decrypted_len != strlen((char*)plaintext) || 
        memcmp(decrypted, plaintext, strlen((char*)plaintext)) != 0) {
        printf("AES256 decryption didn't restore the original data\n");
        printf("Expected: %s\n", (char*)plaintext);
        decrypted[decrypted_len] = '\0';
        printf("Got: %s\n", (char*)decrypted);
        crypto_cleanup(ctx);
        return 1;
    }
    
    crypto_cleanup(ctx);
    return 0;
}

/**
 * @brief Тест функции шифрования и дешифрования ChaCha20
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_crypto_chacha20() {
    // Для ChaCha20 нужен ключ длиной 32 байта (256 бит)
    const uint8_t key[] = {
        0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
        0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F, 0x10,
        0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18,
        0x19, 0x1A, 0x1B, 0x1C, 0x1D, 0x1E, 0x1F, 0x20
    };
    
    // Для ChaCha20 нужен nonce длиной 12 байт (96 бит)
    const uint8_t nonce[] = {
        0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
        0x29, 0x2A, 0x2B, 0x2C
    };
    
    const uint8_t plaintext[] = "This is a test message for ChaCha20 encryption and decryption";
    uint8_t ciphertext[100];
    uint8_t decrypted[100];
    size_t ciphertext_len = sizeof(ciphertext);
    size_t decrypted_len = sizeof(decrypted);
    
    // Инициализация контекста ChaCha20
    CryptoContext *ctx = crypto_init(CRYPTO_CHACHA20, key, sizeof(key), nonce, sizeof(nonce));
    
    if (ctx == NULL) {
        printf("Failed to initialize ChaCha20 context\n");
        return 1;
    }
    
    // Шифрование данных
    int result = crypto_encrypt(ctx, plaintext, strlen((char*)plaintext), ciphertext, &ciphertext_len);
    
    if (result != 0) {
        printf("ChaCha20 encryption failed with code %d\n", result);
        crypto_cleanup(ctx);
        return 1;
    }
    
    // Проверяем, что данные изменились
    if (ciphertext_len != strlen((char*)plaintext) || 
        memcmp(ciphertext, plaintext, strlen((char*)plaintext)) == 0) {
        printf("ChaCha20 encryption didn't change the data\n");
        crypto_cleanup(ctx);
        return 1;
    }
    
    // Дешифрование данных
    result = crypto_decrypt(ctx, ciphertext, ciphertext_len, decrypted, &decrypted_len);
    
    if (result != 0) {
        printf("ChaCha20 decryption failed with code %d\n", result);
        crypto_cleanup(ctx);
        return 1;
    }
    
    // Проверяем, что данные восстановились
    if (decrypted_len != strlen((char*)plaintext) || 
        memcmp(decrypted, plaintext, strlen((char*)plaintext)) != 0) {
        printf("ChaCha20 decryption didn't restore the original data\n");
        printf("Expected: %s\n", (char*)plaintext);
        decrypted[decrypted_len] = '\0';
        printf("Got: %s\n", (char*)decrypted);
        crypto_cleanup(ctx);
        return 1;
    }
    
    crypto_cleanup(ctx);
    return 0;
}

/**
 * @brief Тест функции хеширования
 * 
 * @return int 0 при успехе, 1 при неудаче
 */
int test_crypto_hash() {
    const uint8_t data[] = "This is a test message for hashing";
    uint8_t md5_hash[16] = {0};
    uint8_t sha256_hash[32] = {0};
    uint8_t blake2b_hash[64] = {0};
    
    // Вычисляем MD5-хеш
    int result = crypto_hash(HASH_MD5, data, strlen((char*)data), md5_hash, sizeof(md5_hash));
    if (result != 0) {
        printf("MD5 hashing failed with code %d\n", result);
        return 1;
    }
    
    // Проверяем, что MD5-хеш не состоит из нулей
    int all_zeros = 1;
    for (size_t i = 0; i < sizeof(md5_hash); i++) {
        if (md5_hash[i] != 0) {
            all_zeros = 0;
            break;
        }
    }
    if (all_zeros) {
        printf("MD5 hash is all zeros\n");
        return 1;
    }
    
    // Вычисляем SHA-256 хеш
    result = crypto_hash(HASH_SHA256, data, strlen((char*)data), sha256_hash, sizeof(sha256_hash));
    if (result != 0) {
        printf("SHA-256 hashing failed with code %d\n", result);
        return 1;
    }
    
    // Проверяем, что SHA-256 хеш не состоит из нулей
    all_zeros = 1;
    for (size_t i = 0; i < sizeof(sha256_hash); i++) {
        if (sha256_hash[i] != 0) {
            all_zeros = 0;
            break;
        }
    }
    if (all_zeros) {
        printf("SHA-256 hash is all zeros\n");
        return 1;
    }
    
    // Вычисляем BLAKE2b хеш
    result = crypto_hash(HASH_BLAKE2B, data, strlen((char*)data), blake2b_hash, sizeof(blake2b_hash));
    if (result != 0) {
        printf("BLAKE2b hashing failed with code %d\n", result);
        return 1;
    }
    
    // Проверяем, что BLAKE2b хеш не состоит из нулей
    all_zeros = 1;
    for (size_t i = 0; i < sizeof(blake2b_hash); i++) {
        if (blake2b_hash[i] != 0) {
            all_zeros = 0;
            break;
        }
    }
    if (all_zeros) {
        printf("BLAKE2b hash is all zeros\n");
        return 1;
    }
    
    // Проверяем, что хеши отличаются друг от друга
    // MD5 и SHA-256
    if (memcmp(md5_hash, sha256_hash, sizeof(md5_hash)) == 0) {
        printf("MD5 and SHA-256 hashes are identical\n");
        return 1;
    }
    
    // SHA-256 и BLAKE2b
    if (memcmp(sha256_hash, blake2b_hash, sizeof(sha256_hash)) == 0) {
        printf("SHA-256 and BLAKE2b hashes are identical\n");
        return 1;
    }
    
    return 0;
}

/**
 * @brief Главная функция для запуска тестов
 * 
 * @return int Код возврата программы
 */
int main() {
    printf("=== Testing Crypto Module ===\n\n");
    
    // Запуск тестов
    RUN_TEST(test_crypto_init);
    RUN_TEST(test_crypto_init_invalid_params);
    RUN_TEST(test_crypto_xor);
    RUN_TEST(test_crypto_random_bytes);
    RUN_TEST(test_crypto_encrypt_decrypt);
    RUN_TEST(test_crypto_aes256);
    RUN_TEST(test_crypto_chacha20);
    RUN_TEST(test_crypto_hash);
    RUN_TEST(test_base64_encode);
    RUN_TEST(test_base64_decode);
    RUN_TEST(test_base64_encode_decode_cycle);
    RUN_TEST(test_base32_encode);
    RUN_TEST(test_base32_decode);
    RUN_TEST(test_base32_encode_decode_cycle);
    
    // Вывод итогов
    printf("\n=== Test Results ===\n");
    printf("Passed: %d\n", tests_passed);
    printf("Failed: %d\n", tests_failed);
    printf("Total: %d\n", tests_passed + tests_failed);
    
    return tests_failed > 0 ? 1 : 0;
} 