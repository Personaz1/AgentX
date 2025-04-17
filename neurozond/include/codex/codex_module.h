/**
 * @file codex_module.h
 * @brief NeuroZond CodexModule - модуль "агентного программирования" для манипуляций с кодом
 * @author Team NeuroZond
 * @date 2023-09-06
 */

#ifndef NEUROZOND_CODEX_MODULE_H
#define NEUROZOND_CODEX_MODULE_H

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Статус операции Codex
 */
typedef enum {
    CODEX_STATUS_SUCCESS = 0,           /**< Успех */
    CODEX_STATUS_ERROR_INIT = -1,       /**< Ошибка инициализации */
    CODEX_STATUS_ERROR_CONNECTION = -2, /**< Ошибка соединения */
    CODEX_STATUS_ERROR_PARAMS = -3,     /**< Некорректные параметры */
    CODEX_STATUS_ERROR_FILE = -4,       /**< Ошибка файловой операции */
    CODEX_STATUS_ERROR_COMMAND = -5,    /**< Ошибка выполнения команды */
    CODEX_STATUS_ERROR_LLM = -6,        /**< Ошибка LLM */
    CODEX_STATUS_ERROR_INTERNAL = -7    /**< Внутренняя ошибка */
} codex_status_t;

/**
 * @brief Тип команды для Codex
 */
typedef enum {
    CODEX_COMMAND_ANALYZE,         /**< Анализ файла/проекта */
    CODEX_COMMAND_MODIFY,          /**< Модификация файла */
    CODEX_COMMAND_EXECUTE,         /**< Выполнение команды */
    CODEX_COMMAND_ASK,             /**< Запрос к LLM */
    CODEX_COMMAND_PROJECT,         /**< Операция с проектом */
    CODEX_COMMAND_EXPLOIT          /**< Поиск/эксплуатация уязвимости */
} codex_command_type_t;

/**
 * @brief Опции Codex модуля
 */
typedef struct codex_options {
    const char *working_directory; /**< Рабочая директория */
    const char *target_repository; /**< Целевой репозиторий */
    bool allow_network;            /**< Разрешить сетевой доступ */
    bool encrypt_temp_files;       /**< Шифровать временные файлы */
    const char *api_key;           /**< API ключ (опционально) */
    const char *model;             /**< Модель LLM (опционально) */
} codex_options_t;

/**
 * @brief Структура модуля Codex
 * 
 * Непрозрачная структура, содержащая внутреннее состояние модуля
 */
typedef struct codex_module codex_module_t;

/**
 * @brief Структура результата выполнения команды Codex
 */
typedef struct codex_result {
    codex_status_t status;          /**< Статус выполнения */
    char *content;                  /**< Текстовый результат */
    char **modified_files;          /**< Список модифицированных файлов */
    size_t modified_files_count;    /**< Количество модифицированных файлов */
    char *error_message;            /**< Сообщение об ошибке */
} codex_result_t;

/**
 * @brief Структура команды для Codex
 */
typedef struct codex_command {
    codex_command_type_t type;     /**< Тип команды */
    const char *id;                /**< ID команды */
    const char *content;           /**< Содержимое команды */
    const char *target_file;       /**< Целевой файл (опционально) */
    const char **args;             /**< Дополнительные аргументы */
    size_t args_count;             /**< Количество аргументов */
} codex_command_t;

/**
 * @brief Создать новый экземпляр модуля Codex
 * 
 * @return codex_module_t* Указатель на созданный модуль или NULL при ошибке
 */
codex_module_t* codex_module_create(void);

/**
 * @brief Инициализировать модуль Codex с указанными опциями
 * 
 * @param module Указатель на модуль
 * @param options Опции инициализации
 * @return codex_status_t Статус операции
 */
codex_status_t codex_module_init(codex_module_t *module, const codex_options_t *options);

/**
 * @brief Освободить ресурсы, занятые модулем Codex
 * 
 * @param module Указатель на модуль
 */
void codex_module_destroy(codex_module_t *module);

/**
 * @brief Обработать команду в модуле Codex
 * 
 * @param module Указатель на модуль
 * @param command Команда для обработки
 * @param result Указатель для сохранения результата
 * @return codex_status_t Статус операции
 */
codex_status_t codex_module_handle_command(
    codex_module_t *module,
    const codex_command_t *command,
    codex_result_t **result
);

/**
 * @brief Освободить ресурсы, занятые результатом выполнения команды
 * 
 * @param result Указатель на результат
 */
void codex_result_destroy(codex_result_t *result);

/**
 * @brief Создать команду Codex для анализа файла
 * 
 * @param file_path Путь к анализируемому файлу
 * @param prompt Вопрос или инструкция для анализа
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_analyze(const char *file_path, const char *prompt);

/**
 * @brief Создать команду Codex для модификации файла
 * 
 * @param file_path Путь к модифицируемому файлу
 * @param instructions Инструкции по модификации
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_modify(const char *file_path, const char *instructions);

/**
 * @brief Создать команду Codex для выполнения команды в системе
 * 
 * @param shell_command Команда для выполнения
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_execute(const char *shell_command);

/**
 * @brief Создать команду Codex для запроса к LLM
 * 
 * @param prompt Запрос
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_ask(const char *prompt);

/**
 * @brief Создать команду Codex для операции с проектом
 * 
 * @param operation Операция с проектом (clone, pull, status, etc.)
 * @param args Аргументы операции
 * @param args_count Количество аргументов
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_project(
    const char *operation,
    const char **args,
    size_t args_count
);

/**
 * @brief Создать команду Codex для поиска/эксплуатации уязвимости
 * 
 * @param target Целевой файл или директория
 * @param type Тип уязвимости
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_exploit(const char *target, const char *type);

/**
 * @brief Освободить ресурсы, занятые командой Codex
 * 
 * @param command Указатель на команду
 */
void codex_command_destroy(codex_command_t *command);

/**
 * @brief Зарегистрировать возможности Codex модуля в C1
 * 
 * @param module Указатель на модуль
 * @return codex_status_t Статус операции
 */
codex_status_t codex_module_register_capabilities(codex_module_t *module);

/**
 * @brief Получить версию Codex модуля
 * 
 * @return const char* Строка с версией
 */
const char* codex_module_get_version(void);

#ifdef __cplusplus
}
#endif

#endif /* NEUROZOND_CODEX_MODULE_H */ 