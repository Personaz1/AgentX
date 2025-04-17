/**
 * @file sandbox_manager.h
 * @brief NeuroZond Agent - модуль песочницы для безопасного выполнения команд
 * @author Team NeuroZond
 * @date 2023-07-30
 */

#ifndef NEUROZOND_SANDBOX_MANAGER_H
#define NEUROZOND_SANDBOX_MANAGER_H

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Тип песочницы
 */
typedef enum {
    SANDBOX_TYPE_NONE,            /**< Без песочницы */
    SANDBOX_TYPE_MACOS_SEATBELT,  /**< macOS Seatbelt */
    SANDBOX_TYPE_LINUX_NAMESPACE, /**< Linux namespaces */
    SANDBOX_TYPE_DOCKER           /**< Docker контейнер */
} sandbox_type_t;

/**
 * @brief Конфигурация песочницы
 */
typedef struct sandbox_config {
    sandbox_type_t type;          /**< Тип песочницы */
    char *working_dir;            /**< Рабочая директория */
    char **writable_paths;        /**< Массив путей с правом записи */
    size_t writable_paths_count;  /**< Количество путей с правом записи */
    bool network_enabled;         /**< Флаг доступа к сети */
    char **allowed_commands;      /**< Массив разрешенных команд */
    size_t allowed_commands_count; /**< Количество разрешенных команд */
    int timeout_ms;               /**< Таймаут выполнения команд в мс */
} sandbox_config_t;

/**
 * @brief Результат выполнения команды
 */
typedef struct exec_result {
    char *stdout_output;         /**< Вывод stdout */
    char *stderr_output;         /**< Вывод stderr */
    int exit_code;               /**< Код возврата */
    int duration_ms;             /**< Длительность выполнения в мс */
} exec_result_t;

/**
 * @brief Менеджер песочницы
 */
typedef struct sandbox_manager {
    sandbox_config_t *config;     /**< Конфигурация песочницы */
    void *private_data;           /**< Приватные данные реализации */
} sandbox_manager_t;

/**
 * @brief Создать конфигурацию песочницы
 * 
 * @param type Тип песочницы
 * @param working_dir Рабочая директория
 * @return sandbox_config_t* Указатель на созданную конфигурацию
 */
sandbox_config_t* sandbox_config_create(sandbox_type_t type, const char *working_dir);

/**
 * @brief Освободить память, занятую конфигурацией песочницы
 * 
 * @param config Указатель на конфигурацию
 */
void sandbox_config_destroy(sandbox_config_t *config);

/**
 * @brief Добавить путь с правом записи в конфигурацию песочницы
 * 
 * @param config Указатель на конфигурацию
 * @param path Путь с правом записи
 * @return int Код возврата (0 - успех, другие значения - ошибка)
 */
int sandbox_config_add_writable_path(sandbox_config_t *config, const char *path);

/**
 * @brief Добавить разрешенную команду в конфигурацию песочницы
 * 
 * @param config Указатель на конфигурацию
 * @param command Разрешенная команда
 * @return int Код возврата (0 - успех, другие значения - ошибка)
 */
int sandbox_config_add_allowed_command(sandbox_config_t *config, const char *command);

/**
 * @brief Создать менеджер песочницы
 * 
 * @param config Конфигурация песочницы
 * @return sandbox_manager_t* Указатель на созданный менеджер
 */
sandbox_manager_t* sandbox_manager_create(sandbox_config_t *config);

/**
 * @brief Освободить память, занятую менеджером песочницы
 * 
 * @param manager Указатель на менеджер
 */
void sandbox_manager_destroy(sandbox_manager_t *manager);

/**
 * @brief Определить доступный тип песочницы в системе
 * 
 * @return sandbox_type_t Доступный тип песочницы
 */
sandbox_type_t sandbox_get_available_type(void);

/**
 * @brief Выполнить команду в песочнице
 * 
 * @param manager Указатель на менеджер песочницы
 * @param command Массив аргументов команды (NULL-терминированный)
 * @param working_dir Рабочая директория (NULL для использования из конфигурации)
 * @param timeout_ms Таймаут выполнения в мс (0 для использования из конфигурации)
 * @return exec_result_t* Результат выполнения команды
 */
exec_result_t* sandbox_exec_command(
    sandbox_manager_t *manager,
    char **command,
    const char *working_dir,
    int timeout_ms
);

/**
 * @brief Проверить, безопасна ли команда для выполнения
 * 
 * @param manager Указатель на менеджер песочницы
 * @param command Массив аргументов команды (NULL-терминированный)
 * @return bool true, если команда безопасна, false в противном случае
 */
bool sandbox_is_command_safe(sandbox_manager_t *manager, char **command);

/**
 * @brief Освободить память, занятую результатом выполнения команды
 * 
 * @param result Указатель на результат
 */
void exec_result_destroy(exec_result_t *result);

/**
 * @brief Проверить наличие Docker в системе
 * 
 * @return bool true, если Docker доступен, false в противном случае
 */
bool sandbox_is_docker_available(void);

/**
 * @brief Проверить поддержку Seatbelt в системе (macOS)
 * 
 * @return bool true, если Seatbelt доступен, false в противном случае
 */
bool sandbox_is_seatbelt_available(void);

/**
 * @brief Проверить поддержку namespaces в системе (Linux)
 * 
 * @return bool true, если namespaces доступны, false в противном случае
 */
bool sandbox_is_namespace_available(void);

#ifdef __cplusplus
}
#endif

#endif /* NEUROZOND_SANDBOX_MANAGER_H */ 