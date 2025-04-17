/**
 * @file crypto_utils.h
 * @brief Заголовочный файл для модуля криптографических утилит
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-03
 *
 * Этот модуль предоставляет функции для шифрования, хеширования и обеспечения
 * безопасной передачи данных между NeuroZond и C1 сервером.
 */

#ifndef CRYPTO_UTILS_H
#define CRYPTO_UTILS_H

#include <stdint.h>
#include <stddef.h>

/**
 * @brief Типы поддерживаемых алгоритмов шифрования
 */
typedef enum {
    CRYPTO_NONE = 0,   /**< Без шифрования */
    CRYPTO_XOR,        /**< Простой XOR с ключом */
    CRYPTO_AES256,     /**< AES-256 в режиме CBC */
    CRYPTO_CHACHA20    /**< ChaCha20 */
} CryptoAlgorithm;

/**
 * @brief Типы поддерживаемых алгоритмов хеширования
 */
typedef enum {
    HASH_NONE = 0,     /**< Без хеширования */
    HASH_MD5,          /**< MD5 (небезопасный, только для совместимости) */
    HASH_SHA256,       /**< SHA-256 */
    HASH_BLAKE2B       /**< BLAKE2b */
} HashAlgorithm;

/**
 * @brief Структура для хранения контекста шифрования
 */
typedef struct {
    CryptoAlgorithm algorithm;  /**< Используемый алгоритм шифрования */
    uint8_t *key;               /**< Ключ шифрования */
    size_t key_len;             /**< Длина ключа */
    uint8_t *iv;                /**< Вектор инициализации (если требуется) */
    size_t iv_len;              /**< Длина вектора инициализации */
    void *context;              /**< Внутренний контекст шифрования */
} CryptoContext;

/**
 * @brief Инициализирует контекст шифрования
 *
 * @param algorithm Алгоритм шифрования
 * @param key Ключ шифрования
 * @param key_len Длина ключа
 * @param iv Вектор инициализации (может быть NULL для XOR)
 * @param iv_len Длина вектора инициализации
 * @return CryptoContext* указатель на созданный контекст или NULL при ошибке
 */
CryptoContext* crypto_init(CryptoAlgorithm algorithm, const uint8_t *key, size_t key_len, 
                          const uint8_t *iv, size_t iv_len);

/**
 * @brief Освобождает ресурсы, занятые контекстом шифрования
 *
 * @param context Контекст шифрования
 */
void crypto_cleanup(CryptoContext *context);

/**
 * @brief Шифрует данные
 *
 * @param context Контекст шифрования
 * @param plaintext Исходные данные
 * @param plaintext_len Длина исходных данных
 * @param ciphertext Буфер для зашифрованных данных
 * @param ciphertext_len Указатель на переменную, в которую будет записана длина зашифрованных данных
 * @return int 0 при успехе, код ошибки при неудаче
 */
int crypto_encrypt(CryptoContext *context, const uint8_t *plaintext, size_t plaintext_len,
                  uint8_t *ciphertext, size_t *ciphertext_len);

/**
 * @brief Расшифровывает данные
 *
 * @param context Контекст шифрования
 * @param ciphertext Зашифрованные данные
 * @param ciphertext_len Длина зашифрованных данных
 * @param plaintext Буфер для расшифрованных данных
 * @param plaintext_len Указатель на переменную, в которую будет записана длина расшифрованных данных
 * @return int 0 при успехе, код ошибки при неудаче
 */
int crypto_decrypt(CryptoContext *context, const uint8_t *ciphertext, size_t ciphertext_len,
                  uint8_t *plaintext, size_t *plaintext_len);

/**
 * @brief Вычисляет хеш от данных
 *
 * @param algorithm Алгоритм хеширования
 * @param data Данные для хеширования
 * @param data_len Длина данных
 * @param hash Буфер для хеша
 * @param hash_len Длина буфера для хеша (должна быть достаточной для выбранного алгоритма)
 * @return int 0 при успехе, код ошибки при неудаче
 */
int crypto_hash(HashAlgorithm algorithm, const uint8_t *data, size_t data_len,
               uint8_t *hash, size_t hash_len);

/**
 * @brief Генерирует случайные байты
 *
 * @param buffer Буфер для случайных данных
 * @param len Длина буфера
 * @return int 0 при успехе, код ошибки при неудаче
 */
int crypto_random_bytes(uint8_t *buffer, size_t len);

/**
 * @brief Выполняет XOR-шифрование данных с ключом
 *
 * @param data Данные для шифрования
 * @param data_len Длина данных
 * @param key Ключ шифрования
 * @param key_len Длина ключа
 */
void crypto_xor(uint8_t *data, size_t data_len, const uint8_t *key, size_t key_len);

/**
 * @brief Кодирует данные в Base64
 *
 * @param data Исходные данные
 * @param data_len Длина исходных данных
 * @param encoded Буфер для закодированных данных
 * @param encoded_len Указатель на переменную, в которую будет записана длина закодированных данных
 * @return int 0 при успехе, код ошибки при неудаче
 */
int crypto_base64_encode(const uint8_t *data, size_t data_len, 
                         char *encoded, size_t *encoded_len);

/**
 * @brief Декодирует данные из Base64
 *
 * @param encoded Закодированные данные
 * @param encoded_len Длина закодированных данных
 * @param data Буфер для декодированных данных
 * @param data_len Указатель на переменную, в которую будет записана длина декодированных данных
 * @return int 0 при успехе, код ошибки при неудаче
 */
int crypto_base64_decode(const char *encoded, size_t encoded_len,
                         uint8_t *data, size_t *data_len);

/**
 * @brief Кодирует данные в Base32
 *
 * @param data Исходные данные
 * @param data_len Длина исходных данных
 * @param encoded Буфер для закодированных данных
 * @param encoded_len Указатель на переменную, в которую будет записана длина закодированных данных
 * @return int 0 при успехе, код ошибки при неудаче
 */
int crypto_base32_encode(const uint8_t *data, size_t data_len,
                         char *encoded, size_t *encoded_len);

/**
 * @brief Декодирует данные из Base32
 *
 * @param encoded Закодированные данные
 * @param encoded_len Длина закодированных данных
 * @param data Буфер для декодированных данных
 * @param data_len Указатель на переменную, в которую будет записана длина декодированных данных
 * @return int 0 при успехе, код ошибки при неудаче
 */
int crypto_base32_decode(const char *encoded, size_t encoded_len,
                         uint8_t *data, size_t *data_len);

#endif /* CRYPTO_UTILS_H */ 