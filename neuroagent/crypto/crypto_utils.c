/**
 * @file crypto_utils.c
 * @brief Реализация криптографических утилит
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-03
 *
 * Реализация функций для шифрования, хеширования и обеспечения
 * безопасной передачи данных между NeuroZond и C1 сервером.
 */

#include "crypto_utils.h"
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#include <wincrypt.h>
#pragma comment(lib, "advapi32.lib")
#else
#include <fcntl.h>
#include <unistd.h>
#endif

/* Таблица символов для Base64 */
static const char base64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

/* Таблица символов для Base32 */
static const char base32_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";

/**
 * @brief Инициализирует контекст шифрования
 */
CryptoContext* crypto_init(CryptoAlgorithm algorithm, const uint8_t *key, size_t key_len, 
                          const uint8_t *iv, size_t iv_len) {
    if (key == NULL || key_len == 0) {
        return NULL;
    }

    CryptoContext *ctx = (CryptoContext*)malloc(sizeof(CryptoContext));
    if (ctx == NULL) {
        return NULL;
    }

    ctx->algorithm = algorithm;
    
    /* Копируем ключ */
    ctx->key = (uint8_t*)malloc(key_len);
    if (ctx->key == NULL) {
        free(ctx);
        return NULL;
    }
    memcpy(ctx->key, key, key_len);
    ctx->key_len = key_len;
    
    /* Копируем вектор инициализации, если он предоставлен */
    if (iv != NULL && iv_len > 0) {
        ctx->iv = (uint8_t*)malloc(iv_len);
        if (ctx->iv == NULL) {
            free(ctx->key);
            free(ctx);
            return NULL;
        }
        memcpy(ctx->iv, iv, iv_len);
        ctx->iv_len = iv_len;
    } else {
        ctx->iv = NULL;
        ctx->iv_len = 0;
    }
    
    ctx->context = NULL;  /* Будет инициализировано при необходимости */
    
    return ctx;
}

/**
 * @brief Освобождает ресурсы, занятые контекстом шифрования
 */
void crypto_cleanup(CryptoContext *context) {
    if (context == NULL) {
        return;
    }
    
    if (context->key != NULL) {
        /* Перед освобождением памяти затираем ключ */
        memset(context->key, 0, context->key_len);
        free(context->key);
    }
    
    if (context->iv != NULL) {
        /* Затираем вектор инициализации */
        memset(context->iv, 0, context->iv_len);
        free(context->iv);
    }
    
    /* Освобождаем контекст алгоритма, если он был создан */
    if (context->context != NULL) {
        free(context->context);
    }
    
    /* Затираем и освобождаем основную структуру */
    memset(context, 0, sizeof(CryptoContext));
    free(context);
}

/**
 * @brief Генерирует случайные байты
 */
int crypto_random_bytes(uint8_t *buffer, size_t len) {
    if (buffer == NULL || len == 0) {
        return -1;
    }

#ifdef _WIN32
    HCRYPTPROV hCryptProv;
    if (!CryptAcquireContext(&hCryptProv, NULL, NULL, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT)) {
        return -1;
    }
    
    BOOL result = CryptGenRandom(hCryptProv, (DWORD)len, buffer);
    CryptReleaseContext(hCryptProv, 0);
    
    return result ? 0 : -1;
#else
    int fd = open("/dev/urandom", O_RDONLY);
    if (fd < 0) {
        return -1;
    }
    
    ssize_t bytes_read = read(fd, buffer, len);
    close(fd);
    
    return (bytes_read == (ssize_t)len) ? 0 : -1;
#endif
}

/**
 * @brief Выполняет XOR-шифрование данных с ключом
 */
void crypto_xor(uint8_t *data, size_t data_len, const uint8_t *key, size_t key_len) {
    if (data == NULL || key == NULL || data_len == 0 || key_len == 0) {
        return;
    }
    
    for (size_t i = 0; i < data_len; i++) {
        data[i] ^= key[i % key_len];
    }
}

/**
 * @brief Простая реализация AES256 шифрования (упрощенная для демонстрации)
 * В реальном приложении следует использовать библиотеку OpenSSL или подобную
 */
static int aes256_encrypt_impl(const uint8_t *data, size_t data_len,
                          uint8_t *encrypted_data, size_t *encrypted_len,
                          const uint8_t *key, size_t key_len,
                          const uint8_t *iv, size_t iv_len) {
    if (data == NULL || encrypted_data == NULL || encrypted_len == NULL ||
        key == NULL || key_len == 0) {
        return -1;
    }
    
    // Проверяем, что выходной буфер достаточного размера
    if (*encrypted_len < data_len) {
        *encrypted_len = data_len;
        return -2;
    }
    
    // В демонстрационной версии просто делаем XOR с ключом и IV
    // В реальной реализации нужно использовать полноценный AES256
    memcpy(encrypted_data, data, data_len);
    
    // XOR с IV, если он предоставлен
    if (iv != NULL && iv_len > 0) {
        for (size_t i = 0; i < data_len; i++) {
            encrypted_data[i] ^= iv[i % iv_len];
        }
    }
    
    // XOR с ключом
    for (size_t i = 0; i < data_len; i++) {
        encrypted_data[i] ^= key[i % key_len];
    }
    
    *encrypted_len = data_len;
    return 0;
}

/**
 * @brief Простая реализация AES256 дешифрования (упрощенная для демонстрации)
 * В реальном приложении следует использовать библиотеку OpenSSL или подобную
 */
static int aes256_decrypt_impl(const uint8_t *encrypted_data, size_t encrypted_len,
                          uint8_t *decrypted_data, size_t *decrypted_len,
                          const uint8_t *key, size_t key_len,
                          const uint8_t *iv, size_t iv_len) {
    // Для XOR шифрования и дешифрование - это одна и та же операция
    return aes256_encrypt_impl(encrypted_data, encrypted_len, decrypted_data, decrypted_len,
                          key, key_len, iv, iv_len);
}

/**
 * @brief Простая реализация ChaCha20 шифрования (упрощенная для демонстрации)
 * В реальном приложении следует использовать библиотеку OpenSSL или подобную
 */
static int chacha20_encrypt_impl(const uint8_t *data, size_t data_len,
                            uint8_t *encrypted_data, size_t *encrypted_len,
                            const uint8_t *key, size_t key_len,
                            const uint8_t *nonce, size_t nonce_len) {
    if (data == NULL || encrypted_data == NULL || encrypted_len == NULL ||
        key == NULL || key_len == 0) {
        return -1;
    }
    
    // Проверяем, что выходной буфер достаточного размера
    if (*encrypted_len < data_len) {
        *encrypted_len = data_len;
        return -2;
    }
    
    // В демонстрационной версии просто делаем XOR с ключом и nonce
    // В реальной реализации нужно использовать полноценный ChaCha20
    memcpy(encrypted_data, data, data_len);
    
    // XOR с nonce, если он предоставлен
    if (nonce != NULL && nonce_len > 0) {
        for (size_t i = 0; i < data_len; i++) {
            encrypted_data[i] ^= nonce[i % nonce_len];
        }
    }
    
    // XOR с ключом
    for (size_t i = 0; i < data_len; i++) {
        encrypted_data[i] ^= key[i % key_len];
    }
    
    *encrypted_len = data_len;
    return 0;
}

/**
 * @brief Простая реализация ChaCha20 дешифрования (упрощенная для демонстрации)
 * В реальном приложении следует использовать библиотеку OpenSSL или подобную
 */
static int chacha20_decrypt_impl(const uint8_t *encrypted_data, size_t encrypted_len,
                            uint8_t *decrypted_data, size_t *decrypted_len,
                            const uint8_t *key, size_t key_len,
                            const uint8_t *nonce, size_t nonce_len) {
    // Для XOR шифрования и дешифрование - это одна и та же операция
    return chacha20_encrypt_impl(encrypted_data, encrypted_len, decrypted_data, decrypted_len,
                            key, key_len, nonce, nonce_len);
}

/**
 * @brief Шифрует данные
 */
int crypto_encrypt(CryptoContext *context, const uint8_t *plaintext, size_t plaintext_len,
                  uint8_t *ciphertext, size_t *ciphertext_len) {
    if (context == NULL || plaintext == NULL || ciphertext == NULL || ciphertext_len == NULL || 
        plaintext_len == 0 || *ciphertext_len < plaintext_len) {
        return -1;
    }
    
    switch (context->algorithm) {
        case CRYPTO_NONE:
            /* Просто копируем данные без изменений */
            memcpy(ciphertext, plaintext, plaintext_len);
            *ciphertext_len = plaintext_len;
            return 0;
            
        case CRYPTO_XOR:
            /* Копируем данные и применяем XOR */
            memcpy(ciphertext, plaintext, plaintext_len);
            crypto_xor(ciphertext, plaintext_len, context->key, context->key_len);
            *ciphertext_len = plaintext_len;
            return 0;
            
        case CRYPTO_AES256:
            /* Используем AES256 шифрование */
            return aes256_encrypt_impl(plaintext, plaintext_len, ciphertext, ciphertext_len, 
                                  context->key, context->key_len, context->iv, context->iv_len);
            
        case CRYPTO_CHACHA20:
            /* Используем ChaCha20 шифрование */
            return chacha20_encrypt_impl(plaintext, plaintext_len, ciphertext, ciphertext_len,
                                    context->key, context->key_len, context->iv, context->iv_len);
            
        default:
            return -1;
    }
}

/**
 * @brief Расшифровывает данные
 */
int crypto_decrypt(CryptoContext *context, const uint8_t *ciphertext, size_t ciphertext_len,
                  uint8_t *plaintext, size_t *plaintext_len) {
    if (context == NULL || ciphertext == NULL || plaintext == NULL || plaintext_len == NULL || 
        ciphertext_len == 0 || *plaintext_len < ciphertext_len) {
        return -1;
    }
    
    switch (context->algorithm) {
        case CRYPTO_NONE:
            /* Просто копируем данные без изменений */
            memcpy(plaintext, ciphertext, ciphertext_len);
            *plaintext_len = ciphertext_len;
            return 0;
            
        case CRYPTO_XOR:
            /* Для XOR шифрование и расшифрование - одна и та же операция */
            memcpy(plaintext, ciphertext, ciphertext_len);
            crypto_xor(plaintext, ciphertext_len, context->key, context->key_len);
            *plaintext_len = ciphertext_len;
            return 0;
            
        case CRYPTO_AES256:
            /* Используем AES256 дешифрование */
            return aes256_decrypt_impl(ciphertext, ciphertext_len, plaintext, plaintext_len,
                                  context->key, context->key_len, context->iv, context->iv_len);
            
        case CRYPTO_CHACHA20:
            /* Используем ChaCha20 дешифрование */
            return chacha20_decrypt_impl(ciphertext, ciphertext_len, plaintext, plaintext_len,
                                    context->key, context->key_len, context->iv, context->iv_len);
            
        default:
            return -1;
    }
}

/**
 * @brief Вычисляет хеш от данных
 */
int crypto_hash(HashAlgorithm algorithm, const uint8_t *data, size_t data_len,
               uint8_t *hash, size_t hash_len) {
    if (data == NULL || hash == NULL || data_len == 0 || hash_len == 0) {
        return -1;
    }
    
    // В зависимости от алгоритма хеширования
    switch (algorithm) {
        case HASH_NONE:
            /* Не вычисляем хеш, просто возвращаем успех */
            return 0;
            
        case HASH_MD5:
            /* Простая имитация MD5 (не использовать в реальных приложениях) */
            if (hash_len < 16) {
                return -2; // Недостаточно места для MD5 хеша
            }
            
            // Заполняем хеш простой функцией на основе XOR
            for (size_t i = 0; i < 16; i++) {
                hash[i] = 0;
                for (size_t j = i; j < data_len; j += 16) {
                    hash[i] ^= data[j];
                }
            }
            return 0;
            
        case HASH_SHA256:
            /* Простая имитация SHA-256 (не использовать в реальных приложениях) */
            if (hash_len < 32) {
                return -2; // Недостаточно места для SHA-256 хеша
            }
            
            // Заполняем хеш простой функцией на основе XOR
            for (size_t i = 0; i < 32; i++) {
                hash[i] = 0;
                for (size_t j = i; j < data_len; j += 32) {
                    hash[i] ^= data[j];
                }
                // Немного "перемешиваем" для разнообразия
                hash[i] = (hash[i] << 3) | (hash[i] >> 5);
            }
            return 0;
            
        case HASH_BLAKE2B:
            /* Простая имитация BLAKE2b (не использовать в реальных приложениях) */
            if (hash_len < 64) {
                return -2; // Недостаточно места для BLAKE2b хеша
            }
            
            // Заполняем хеш простой функцией на основе XOR
            for (size_t i = 0; i < 64; i++) {
                hash[i] = 0;
                for (size_t j = i; j < data_len; j += 64) {
                    hash[i] ^= data[j];
                }
                // Немного "перемешиваем" для разнообразия
                hash[i] = (hash[i] << 5) | (hash[i] >> 3);
            }
            return 0;
            
        default:
            return -1;
    }
}

/**
 * @brief Кодирует данные в Base64
 */
int crypto_base64_encode(const uint8_t *data, size_t data_len, 
                         char *encoded, size_t *encoded_len) {
    if (data == NULL || encoded == NULL || encoded_len == NULL || data_len == 0) {
        return -1;
    }
    
    /* Расчет необходимого размера для закодированных данных */
    size_t needed_len = ((data_len + 2) / 3) * 4 + 1; /* +1 для завершающего нуля */
    
    if (*encoded_len < needed_len) {
        *encoded_len = needed_len;
        return -1;
    }
    
    size_t i, j = 0;
    uint32_t bit_stream = 0;
    int bit_count = 0;
    
    for (i = 0; i < data_len; i++) {
        bit_stream = (bit_stream << 8) | data[i];
        bit_count += 8;
        
        while (bit_count >= 6) {
            bit_count -= 6;
            encoded[j++] = base64_table[(bit_stream >> bit_count) & 0x3F];
        }
    }
    
    /* Обработка оставшихся битов */
    if (bit_count > 0) {
        encoded[j++] = base64_table[(bit_stream << (6 - bit_count)) & 0x3F];
    }
    
    /* Добавление padding '=' символов */
    while (j % 4 != 0) {
        encoded[j++] = '=';
    }
    
    encoded[j] = '\0';
    *encoded_len = j;
    
    return 0;
}

/**
 * @brief Декодирует данные из Base64
 */
int crypto_base64_decode(const char *encoded, size_t encoded_len,
                         uint8_t *data, size_t *data_len) {
    if (encoded == NULL || data == NULL || data_len == NULL || encoded_len == 0) {
        return -1;
    }
    
    // Таблица для декодирования Base64
    static const int base64_decode_table[256] = {
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, 63,
        52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, -1, -1, -1,
        -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14,
        15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1,
        -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
        41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
    };
    
    // Расчет максимального размера декодированных данных (оценка)
    size_t max_decoded_len = (encoded_len / 4) * 3;
    
    if (*data_len < max_decoded_len) {
        *data_len = max_decoded_len;
        return -1;
    }
    
    size_t i, j = 0;
    int sextet_a, sextet_b, sextet_c, sextet_d;
    uint32_t triple;
    
    for (i = 0; i < encoded_len; i += 4) {
        // Получаем 4 символа из входной строки
        sextet_a = (i + 0 < encoded_len) ? base64_decode_table[(unsigned char)encoded[i + 0]] : -1;
        sextet_b = (i + 1 < encoded_len) ? base64_decode_table[(unsigned char)encoded[i + 1]] : -1;
        sextet_c = (i + 2 < encoded_len) ? base64_decode_table[(unsigned char)encoded[i + 2]] : -1;
        sextet_d = (i + 3 < encoded_len) ? base64_decode_table[(unsigned char)encoded[i + 3]] : -1;
        
        // Проверяем, что символы действительны
        if (sextet_a == -1 || sextet_b == -1) {
            break; // Недостаточно символов или некорректные символы
        }
        
        // Собираем триплет
        triple = ((uint32_t)sextet_a << 18) | ((uint32_t)sextet_b << 12);
        
        if (sextet_c != -1) {
            triple |= ((uint32_t)sextet_c << 6);
        }
        
        if (sextet_d != -1) {
            triple |= (uint32_t)sextet_d;
        }
        
        // Разбиваем триплет на отдельные байты и записываем в выходной буфер
        if (j < *data_len) data[j++] = (triple >> 16) & 0xFF;
        if (sextet_c != -1 && j < *data_len) data[j++] = (triple >> 8) & 0xFF;
        if (sextet_d != -1 && j < *data_len) data[j++] = triple & 0xFF;
        
        // Если достигли символа конца строки или padding '='
        if (encoded[i + 2] == '=' || encoded[i + 3] == '=') {
            break;
        }
    }
    
    *data_len = j;
    return 0;
}

/**
 * @brief Кодирует данные в Base32
 */
int crypto_base32_encode(const uint8_t *data, size_t data_len,
                         char *encoded, size_t *encoded_len) {
    if (data == NULL || encoded == NULL || encoded_len == NULL || data_len == 0) {
        return -1;
    }
    
    /* Расчет необходимого размера для закодированных данных */
    size_t needed_len = ((data_len * 8 + 4) / 5) + 1; /* +1 для завершающего нуля */
    
    if (*encoded_len < needed_len) {
        *encoded_len = needed_len;
        return -1;
    }
    
    size_t i, j = 0;
    uint32_t bit_stream = 0;
    int bit_count = 0;
    
    for (i = 0; i < data_len; i++) {
        bit_stream = (bit_stream << 8) | data[i];
        bit_count += 8;
        
        while (bit_count >= 5) {
            bit_count -= 5;
            encoded[j++] = base32_table[(bit_stream >> bit_count) & 0x1F];
        }
    }
    
    /* Обработка оставшихся битов */
    if (bit_count > 0) {
        encoded[j++] = base32_table[(bit_stream << (5 - bit_count)) & 0x1F];
    }
    
    /* Добавление padding '=' символов */
    while (j % 8 != 0) {
        encoded[j++] = '=';
    }
    
    encoded[j] = '\0';
    *encoded_len = j;
    
    return 0;
}

/**
 * @brief Декодирует данные из Base32
 */
int crypto_base32_decode(const char *encoded, size_t encoded_len,
                         uint8_t *data, size_t *data_len) {
    if (encoded == NULL || data == NULL || data_len == NULL || encoded_len == 0) {
        return -1;
    }
    
    // Таблица для декодирования Base32
    static const int base32_decode_table[256] = {
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, 26, 27, 28, 29, 30, 31, -1, -1, -1, -1, -1, -1, -1, -1,
        -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14,
        15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1,
        -1,  0,  1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14,
        15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
        -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1
    };
    
    // Расчет максимального размера декодированных данных
    size_t max_decoded_len = (encoded_len * 5) / 8 + 1;
    
    if (*data_len < max_decoded_len) {
        *data_len = max_decoded_len;
        return -1;
    }
    
    size_t i, j = 0;
    uint64_t buffer = 0; // Увеличим размер буфера для накопления битов
    int bits_left = 0;
    
    for (i = 0; i < encoded_len; i++) {
        // Пропускаем пробелы и символы '='
        if (encoded[i] == ' ' || encoded[i] == '\t' || encoded[i] == '\n' || 
            encoded[i] == '\r' || encoded[i] == '=') {
            continue;
        }
        
        // Получаем значение символа
        int val = base32_decode_table[(unsigned char)encoded[i]];
        
        // Проверяем, что символ действителен
        if (val == -1) {
            continue; // Пропускаем некорректные символы
        }
        
        // Добавляем 5 бит в буфер
        buffer = (buffer << 5) | (val & 0x1F);
        bits_left += 5;
        
        // Если накопилось 8 или более бит, можем извлечь байт
        if (bits_left >= 8) {
            bits_left -= 8;
            if (j < *data_len) {
                data[j++] = (buffer >> bits_left) & 0xFF;
            }
        }
    }
    
    *data_len = j;
    return 0;
} 