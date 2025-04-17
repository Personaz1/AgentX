/**
 * @file codex_module.c
 * @brief Реализация модуля Codex для NeuroZond
 * @author Team NeuroZond
 * @date 2023-09-06
 */

#include "../../include/codex/codex_module.h"
#include "../../include/codex/llm_proxy.h"

#include <stdlib.h>
#include <string.h>
#include <stdio.h>

/** Версия модуля Codex */
#define CODEX_MODULE_VERSION "1.0.0"

/** Максимальная длина пути к файлу */
#define CODEX_MAX_PATH_LENGTH 4096

/** Максимальный размер буфера для сообщений */
#define CODEX_MAX_BUFFER_SIZE 10240

/**
 * @brief Внутренняя структура модуля Codex
 */
struct codex_module {
    bool initialized;                   /**< Флаг инициализации */
    char *working_directory;            /**< Рабочая директория */
    char *target_repository;            /**< Целевой репозиторий */
    bool allow_network;                 /**< Разрешить сетевой доступ */
    bool encrypt_temp_files;            /**< Шифровать временные файлы */
    llm_proxy_t *llm_proxy;             /**< Прокси для работы с LLM */
    void *command_executor;             /**< Исполнитель команд */
    void *file_manager;                 /**< Менеджер файлов */
    void *c1_connector;                 /**< Коннектор к C1 */
    char *session_id;                   /**< ID текущей сессии */
    char last_error[CODEX_MAX_BUFFER_SIZE]; /**< Последняя ошибка */
};

/**
 * @brief Внутренняя структура команды Codex
 */
struct codex_command_internal {
    codex_command_type_t type;          /**< Тип команды */
    char *id;                           /**< ID команды */
    char *content;                      /**< Содержимое команды */
    char *target_file;                  /**< Целевой файл */
    char **args;                        /**< Дополнительные аргументы */
    size_t args_count;                  /**< Количество аргументов */
};

/**
 * @brief Установить последнюю ошибку в модуле
 * 
 * @param module Указатель на модуль
 * @param format Формат сообщения ошибки
 * @param ... Дополнительные аргументы
 */
static void codex_set_error(codex_module_t *module, const char *format, ...) {
    if (module == NULL || format == NULL) {
        return;
    }
    
    va_list args;
    va_start(args, format);
    vsnprintf(module->last_error, CODEX_MAX_BUFFER_SIZE, format, args);
    va_end(args);
}

/**
 * @brief Создать новый экземпляр модуля Codex
 * 
 * @return codex_module_t* Указатель на созданный модуль или NULL при ошибке
 */
codex_module_t* codex_module_create(void) {
    codex_module_t *module = (codex_module_t*)calloc(1, sizeof(codex_module_t));
    if (module == NULL) {
        return NULL;
    }
    
    module->initialized = false;
    module->working_directory = NULL;
    module->target_repository = NULL;
    module->allow_network = false;
    module->encrypt_temp_files = false;
    module->llm_proxy = NULL;
    module->command_executor = NULL;
    module->file_manager = NULL;
    module->c1_connector = NULL;
    module->session_id = NULL;
    module->last_error[0] = '\0';
    
    return module;
}

/**
 * @brief Инициализировать модуль Codex с указанными опциями
 * 
 * @param module Указатель на модуль
 * @param options Опции инициализации
 * @return codex_status_t Статус операции
 */
codex_status_t codex_module_init(codex_module_t *module, const codex_options_t *options) {
    if (module == NULL) {
        return CODEX_STATUS_ERROR_PARAMS;
    }
    
    if (options == NULL) {
        codex_set_error(module, "Не указаны опции инициализации");
        return CODEX_STATUS_ERROR_PARAMS;
    }
    
    // Копирование опций
    if (options->working_directory != NULL) {
        module->working_directory = strdup(options->working_directory);
        if (module->working_directory == NULL) {
            codex_set_error(module, "Ошибка выделения памяти для рабочей директории");
            return CODEX_STATUS_ERROR_INIT;
        }
    }
    
    if (options->target_repository != NULL) {
        module->target_repository = strdup(options->target_repository);
        if (module->target_repository == NULL) {
            codex_set_error(module, "Ошибка выделения памяти для целевого репозитория");
            free(module->working_directory);
            module->working_directory = NULL;
            return CODEX_STATUS_ERROR_INIT;
        }
    }
    
    module->allow_network = options->allow_network;
    module->encrypt_temp_files = options->encrypt_temp_files;
    
    // Инициализация LLM прокси, если указаны ключ API и модель
    if (options->api_key != NULL && options->model != NULL) {
        llm_proxy_options_t llm_options = {
            .mode = LLM_PROXY_MODE_DIRECT,
            .provider = LLM_PROVIDER_OPENAI,
            .api_key = options->api_key,
            .model = options->model,
            .base_url = NULL,
            .timeout_ms = 30000,
            .stream = false,
            .c1_connector = NULL
        };
        
        module->llm_proxy = llm_proxy_create(&llm_options);
        if (module->llm_proxy == NULL) {
            codex_set_error(module, "Ошибка инициализации LLM прокси");
            free(module->working_directory);
            free(module->target_repository);
            module->working_directory = NULL;
            module->target_repository = NULL;
            return CODEX_STATUS_ERROR_INIT;
        }
    }
    
    // Генерация уникального ID сессии
    char session_id[37]; // 36 символов + завершающий нуль
    // В реальном коде здесь должна быть генерация UUID
    snprintf(session_id, sizeof(session_id), "codex-%08x-%08x-%08x-%08x", 
             rand(), rand(), rand(), rand());
    module->session_id = strdup(session_id);
    
    // Инициализация других компонентов будет добавлена позже
    
    module->initialized = true;
    return CODEX_STATUS_SUCCESS;
}

/**
 * @brief Освободить ресурсы, занятые модулем Codex
 * 
 * @param module Указатель на модуль
 */
void codex_module_destroy(codex_module_t *module) {
    if (module == NULL) {
        return;
    }
    
    if (module->working_directory != NULL) {
        free(module->working_directory);
        module->working_directory = NULL;
    }
    
    if (module->target_repository != NULL) {
        free(module->target_repository);
        module->target_repository = NULL;
    }
    
    if (module->session_id != NULL) {
        free(module->session_id);
        module->session_id = NULL;
    }
    
    if (module->llm_proxy != NULL) {
        llm_proxy_destroy(module->llm_proxy);
        module->llm_proxy = NULL;
    }
    
    // Освобождение других ресурсов будет добавлено позже
    
    module->initialized = false;
    free(module);
}

/**
 * @brief Создать новый результат Codex
 * 
 * @param status Статус операции
 * @return codex_result_t* Указатель на созданный результат или NULL при ошибке
 */
static codex_result_t* codex_result_create(codex_status_t status) {
    codex_result_t *result = (codex_result_t*)calloc(1, sizeof(codex_result_t));
    if (result == NULL) {
        return NULL;
    }
    
    result->status = status;
    result->content = NULL;
    result->modified_files = NULL;
    result->modified_files_count = 0;
    result->error_message = NULL;
    
    return result;
}

/**
 * @brief Обработать команду анализа файла
 * 
 * @param module Указатель на модуль
 * @param command Команда
 * @param result Указатель для сохранения результата
 * @return codex_status_t Статус операции
 */
static codex_status_t handle_analyze_command(
    codex_module_t *module,
    const codex_command_t *command,
    codex_result_t **result
) {
    // Заглушка, реальная реализация будет добавлена позже
    *result = codex_result_create(CODEX_STATUS_SUCCESS);
    if (*result == NULL) {
        codex_set_error(module, "Ошибка выделения памяти для результата");
        return CODEX_STATUS_ERROR_INTERNAL;
    }
    
    const char *placeholder = "Анализ файла выполнен успешно";
    (*result)->content = strdup(placeholder);
    
    return CODEX_STATUS_SUCCESS;
}

/**
 * @brief Обработать команду модификации файла
 * 
 * @param module Указатель на модуль
 * @param command Команда
 * @param result Указатель для сохранения результата
 * @return codex_status_t Статус операции
 */
static codex_status_t handle_modify_command(
    codex_module_t *module,
    const codex_command_t *command,
    codex_result_t **result
) {
    // Заглушка, реальная реализация будет добавлена позже
    *result = codex_result_create(CODEX_STATUS_SUCCESS);
    if (*result == NULL) {
        codex_set_error(module, "Ошибка выделения памяти для результата");
        return CODEX_STATUS_ERROR_INTERNAL;
    }
    
    const char *placeholder = "Модификация файла выполнена успешно";
    (*result)->content = strdup(placeholder);
    
    // Добавление модифицированного файла в список
    (*result)->modified_files = (char**)malloc(sizeof(char*));
    if ((*result)->modified_files != NULL) {
        (*result)->modified_files[0] = command->target_file ? strdup(command->target_file) : NULL;
        (*result)->modified_files_count = 1;
    }
    
    return CODEX_STATUS_SUCCESS;
}

/**
 * @brief Обработать команду выполнения
 * 
 * @param module Указатель на модуль
 * @param command Команда
 * @param result Указатель для сохранения результата
 * @return codex_status_t Статус операции
 */
static codex_status_t handle_execute_command(
    codex_module_t *module,
    const codex_command_t *command,
    codex_result_t **result
) {
    // Заглушка, реальная реализация будет добавлена позже
    *result = codex_result_create(CODEX_STATUS_SUCCESS);
    if (*result == NULL) {
        codex_set_error(module, "Ошибка выделения памяти для результата");
        return CODEX_STATUS_ERROR_INTERNAL;
    }
    
    const char *placeholder = "Команда выполнена успешно";
    (*result)->content = strdup(placeholder);
    
    return CODEX_STATUS_SUCCESS;
}

/**
 * @brief Обработать команду запроса к LLM
 * 
 * @param module Указатель на модуль
 * @param command Команда
 * @param result Указатель для сохранения результата
 * @return codex_status_t Статус операции
 */
static codex_status_t handle_ask_command(
    codex_module_t *module,
    const codex_command_t *command,
    codex_result_t **result
) {
    if (module->llm_proxy == NULL) {
        codex_set_error(module, "LLM прокси не инициализирован");
        return CODEX_STATUS_ERROR_LLM;
    }
    
    llm_proxy_result_t *llm_result = NULL;
    llm_proxy_status_t llm_status = llm_proxy_send_message(
        module->llm_proxy,
        command->content,
        &llm_result
    );
    
    if (llm_status != LLM_PROXY_STATUS_SUCCESS || llm_result == NULL) {
        codex_set_error(module, "Ошибка отправки сообщения в LLM: %s",
                       llm_proxy_get_last_error(module->llm_proxy));
        if (llm_result != NULL) {
            llm_proxy_result_destroy(llm_result);
        }
        return CODEX_STATUS_ERROR_LLM;
    }
    
    *result = codex_result_create(CODEX_STATUS_SUCCESS);
    if (*result == NULL) {
        codex_set_error(module, "Ошибка выделения памяти для результата");
        llm_proxy_result_destroy(llm_result);
        return CODEX_STATUS_ERROR_INTERNAL;
    }
    
    (*result)->content = strdup(llm_result->content);
    llm_proxy_result_destroy(llm_result);
    
    return CODEX_STATUS_SUCCESS;
}

/**
 * @brief Обработать команду операции с проектом
 * 
 * @param module Указатель на модуль
 * @param command Команда
 * @param result Указатель для сохранения результата
 * @return codex_status_t Статус операции
 */
static codex_status_t handle_project_command(
    codex_module_t *module,
    const codex_command_t *command,
    codex_result_t **result
) {
    // Заглушка, реальная реализация будет добавлена позже
    *result = codex_result_create(CODEX_STATUS_SUCCESS);
    if (*result == NULL) {
        codex_set_error(module, "Ошибка выделения памяти для результата");
        return CODEX_STATUS_ERROR_INTERNAL;
    }
    
    const char *placeholder = "Операция с проектом выполнена успешно";
    (*result)->content = strdup(placeholder);
    
    return CODEX_STATUS_SUCCESS;
}

/**
 * @brief Обработать команду поиска/эксплуатации уязвимости
 * 
 * @param module Указатель на модуль
 * @param command Команда
 * @param result Указатель для сохранения результата
 * @return codex_status_t Статус операции
 */
static codex_status_t handle_exploit_command(
    codex_module_t *module,
    const codex_command_t *command,
    codex_result_t **result
) {
    // Заглушка, реальная реализация будет добавлена позже
    *result = codex_result_create(CODEX_STATUS_SUCCESS);
    if (*result == NULL) {
        codex_set_error(module, "Ошибка выделения памяти для результата");
        return CODEX_STATUS_ERROR_INTERNAL;
    }
    
    const char *placeholder = "Поиск/эксплуатация уязвимости выполнены успешно";
    (*result)->content = strdup(placeholder);
    
    return CODEX_STATUS_SUCCESS;
}

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
) {
    if (module == NULL || command == NULL || result == NULL) {
        return CODEX_STATUS_ERROR_PARAMS;
    }
    
    if (!module->initialized) {
        codex_set_error(module, "Модуль не инициализирован");
        return CODEX_STATUS_ERROR_INIT;
    }
    
    // Выбор обработчика в зависимости от типа команды
    switch (command->type) {
        case CODEX_COMMAND_ANALYZE:
            return handle_analyze_command(module, command, result);
        
        case CODEX_COMMAND_MODIFY:
            return handle_modify_command(module, command, result);
        
        case CODEX_COMMAND_EXECUTE:
            return handle_execute_command(module, command, result);
        
        case CODEX_COMMAND_ASK:
            return handle_ask_command(module, command, result);
        
        case CODEX_COMMAND_PROJECT:
            return handle_project_command(module, command, result);
        
        case CODEX_COMMAND_EXPLOIT:
            return handle_exploit_command(module, command, result);
        
        default:
            codex_set_error(module, "Неизвестный тип команды: %d", command->type);
            return CODEX_STATUS_ERROR_PARAMS;
    }
}

/**
 * @brief Освободить ресурсы, занятые результатом выполнения команды
 * 
 * @param result Указатель на результат
 */
void codex_result_destroy(codex_result_t *result) {
    if (result == NULL) {
        return;
    }
    
    if (result->content != NULL) {
        free(result->content);
        result->content = NULL;
    }
    
    if (result->error_message != NULL) {
        free(result->error_message);
        result->error_message = NULL;
    }
    
    if (result->modified_files != NULL) {
        for (size_t i = 0; i < result->modified_files_count; i++) {
            if (result->modified_files[i] != NULL) {
                free(result->modified_files[i]);
            }
        }
        free(result->modified_files);
        result->modified_files = NULL;
    }
    
    result->modified_files_count = 0;
    free(result);
}

/**
 * @brief Создать команду Codex
 * 
 * @param type Тип команды
 * @param id ID команды
 * @param content Содержимое команды
 * @param target_file Целевой файл (может быть NULL)
 * @param args Дополнительные аргументы (может быть NULL)
 * @param args_count Количество аргументов
 * @return codex_command_t* Указатель на созданную команду
 */
static codex_command_t* codex_command_create(
    codex_command_type_t type,
    const char *id,
    const char *content,
    const char *target_file,
    const char **args,
    size_t args_count
) {
    codex_command_t *command = (codex_command_t*)calloc(1, sizeof(codex_command_t));
    if (command == NULL) {
        return NULL;
    }
    
    command->type = type;
    command->id = id ? strdup(id) : NULL;
    command->content = content ? strdup(content) : NULL;
    command->target_file = target_file ? strdup(target_file) : NULL;
    
    if (args != NULL && args_count > 0) {
        command->args = (const char**)malloc(sizeof(char*) * args_count);
        if (command->args != NULL) {
            command->args_count = args_count;
            for (size_t i = 0; i < args_count; i++) {
                ((char**)command->args)[i] = args[i] ? strdup(args[i]) : NULL;
            }
        } else {
            command->args_count = 0;
        }
    } else {
        command->args = NULL;
        command->args_count = 0;
    }
    
    return command;
}

/**
 * @brief Создать команду Codex для анализа файла
 * 
 * @param file_path Путь к анализируемому файлу
 * @param prompt Вопрос или инструкция для анализа
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_analyze(const char *file_path, const char *prompt) {
    return codex_command_create(
        CODEX_COMMAND_ANALYZE,
        NULL, // ID будет сгенерирован автоматически
        prompt,
        file_path,
        NULL,
        0
    );
}

/**
 * @brief Создать команду Codex для модификации файла
 * 
 * @param file_path Путь к модифицируемому файлу
 * @param instructions Инструкции по модификации
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_modify(const char *file_path, const char *instructions) {
    return codex_command_create(
        CODEX_COMMAND_MODIFY,
        NULL, // ID будет сгенерирован автоматически
        instructions,
        file_path,
        NULL,
        0
    );
}

/**
 * @brief Создать команду Codex для выполнения команды в системе
 * 
 * @param shell_command Команда для выполнения
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_execute(const char *shell_command) {
    return codex_command_create(
        CODEX_COMMAND_EXECUTE,
        NULL, // ID будет сгенерирован автоматически
        shell_command,
        NULL,
        NULL,
        0
    );
}

/**
 * @brief Создать команду Codex для запроса к LLM
 * 
 * @param prompt Запрос
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_ask(const char *prompt) {
    return codex_command_create(
        CODEX_COMMAND_ASK,
        NULL, // ID будет сгенерирован автоматически
        prompt,
        NULL,
        NULL,
        0
    );
}

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
) {
    return codex_command_create(
        CODEX_COMMAND_PROJECT,
        NULL, // ID будет сгенерирован автоматически
        operation,
        NULL,
        args,
        args_count
    );
}

/**
 * @brief Создать команду Codex для поиска/эксплуатации уязвимости
 * 
 * @param target Целевой файл или директория
 * @param type Тип уязвимости
 * @return codex_command_t* Указатель на созданную команду
 */
codex_command_t* codex_command_create_exploit(const char *target, const char *type) {
    const char *args[] = { type };
    return codex_command_create(
        CODEX_COMMAND_EXPLOIT,
        NULL, // ID будет сгенерирован автоматически
        NULL,
        target,
        args,
        1
    );
}

/**
 * @brief Освободить ресурсы, занятые командой Codex
 * 
 * @param command Указатель на команду
 */
void codex_command_destroy(codex_command_t *command) {
    if (command == NULL) {
        return;
    }
    
    if (command->id != NULL) {
        free((void*)command->id);
    }
    
    if (command->content != NULL) {
        free((void*)command->content);
    }
    
    if (command->target_file != NULL) {
        free((void*)command->target_file);
    }
    
    if (command->args != NULL) {
        for (size_t i = 0; i < command->args_count; i++) {
            if (command->args[i] != NULL) {
                free((void*)command->args[i]);
            }
        }
        free((void*)command->args);
    }
    
    free(command);
}

/**
 * @brief Зарегистрировать возможности Codex модуля в C1
 * 
 * @param module Указатель на модуль
 * @return codex_status_t Статус операции
 */
codex_status_t codex_module_register_capabilities(codex_module_t *module) {
    if (module == NULL) {
        return CODEX_STATUS_ERROR_PARAMS;
    }
    
    if (!module->initialized) {
        codex_set_error(module, "Модуль не инициализирован");
        return CODEX_STATUS_ERROR_INIT;
    }
    
    // Заглушка, реальная реализация будет добавлена позже
    return CODEX_STATUS_SUCCESS;
}

/**
 * @brief Получить версию Codex модуля
 * 
 * @return const char* Строка с версией
 */
const char* codex_module_get_version(void) {
    return CODEX_MODULE_VERSION;
} 