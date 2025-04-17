/**
 * @file agent_loop.h
 * @brief NeuroZond Agent - модуль агентного программирования для автоматизации кодирования
 * @author Team NeuroZond
 * @date 2023-07-30
 */

#ifndef NEUROZOND_AGENT_LOOP_H
#define NEUROZOND_AGENT_LOOP_H

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Тип политики утверждения действий
 */
typedef enum {
    AGENT_APPROVAL_POLICY_SUGGEST,    /**< Только предлагать изменения */
    AGENT_APPROVAL_POLICY_AUTO_EDIT,  /**< Автоматически применять изменения в файлах */
    AGENT_APPROVAL_POLICY_FULL_AUTO   /**< Автоматически выполнять любые команды */
} agent_approval_policy_t;

/**
 * @brief Тип сообщения агента
 */
typedef enum {
    AGENT_MESSAGE_TYPE_TEXT,          /**< Текстовое сообщение */
    AGENT_MESSAGE_TYPE_FUNCTION_CALL, /**< Вызов функции */
    AGENT_MESSAGE_TYPE_FUNCTION_RESULT /**< Результат выполнения функции */
} agent_message_type_t;

/**
 * @brief Структура сообщения агента
 */
typedef struct agent_message {
    agent_message_type_t type;        /**< Тип сообщения */
    char *id;                         /**< Уникальный идентификатор сообщения */
    char *content;                    /**< Содержимое сообщения */
    void *metadata;                   /**< Дополнительные метаданные */
} agent_message_t;

/**
 * @brief Структура конфигурации агента
 */
typedef struct agent_config {
    char *model;                      /**< Модель LLM */
    char *api_key;                    /**< API ключ */
    char *base_url;                   /**< Базовый URL API */
    char *instructions;               /**< Инструкции для агента */
    int timeout_ms;                   /**< Таймаут ожидания ответа */
    agent_approval_policy_t approval_policy; /**< Политика утверждения действий */
    bool full_stdout;                 /**< Выводить полный stdout/stderr */
    bool disable_network;             /**< Отключить сетевой доступ в песочнице */
} agent_config_t;

/**
 * @brief Результат выполнения команды
 */
typedef struct agent_exec_result {
    char *stdout_output;             /**< Вывод stdout */
    char *stderr_output;             /**< Вывод stderr */
    int exit_code;                   /**< Код возврата */
    int duration_ms;                 /**< Длительность выполнения в мс */
} agent_exec_result_t;

/**
 * @brief Структура подтверждения команды
 */
typedef struct agent_command_confirmation {
    bool approved;                   /**< Флаг подтверждения */
    char *message;                   /**< Сообщение для отклонения */
} agent_command_confirmation_t;

/**
 * @brief Прототип функции обратного вызова для сообщений
 */
typedef void (*agent_message_callback_t)(agent_message_t *message, void *user_data);

/**
 * @brief Прототип функции обратного вызова для индикации загрузки
 */
typedef void (*agent_loading_callback_t)(bool loading, void *user_data);

/**
 * @brief Прототип функции обратного вызова для подтверждения команды
 */
typedef agent_command_confirmation_t* (*agent_command_confirmation_callback_t)(
    char **command, 
    void *apply_patch, 
    void *user_data
);

/**
 * @brief Структура цикла агента
 */
typedef struct agent_loop {
    agent_config_t *config;          /**< Конфигурация агента */
    void *llm_connector;             /**< Коннектор к LLM API */
    void *sandbox_manager;           /**< Менеджер песочницы */
    void *file_manager;              /**< Менеджер файлов */
    
    char *session_id;                /**< ID текущей сессии */
    bool canceled;                   /**< Флаг отмены выполнения */
    bool terminated;                 /**< Флаг завершения работы */
    
    agent_message_callback_t on_message;       /**< Колбэк сообщений */
    agent_loading_callback_t on_loading;       /**< Колбэк индикации загрузки */
    agent_command_confirmation_callback_t get_command_confirmation; /**< Колбэк подтверждения команды */
    
    void *user_data;                 /**< Пользовательские данные для колбэков */
} agent_loop_t;

/**
 * @brief Создать новую конфигурацию агента
 * 
 * @param model Модель LLM
 * @param api_key API ключ
 * @param approval_policy Политика утверждения действий
 * @return agent_config_t* Указатель на созданную конфигурацию
 */
agent_config_t* agent_config_create(const char *model, const char *api_key, agent_approval_policy_t approval_policy);

/**
 * @brief Освободить память, занятую конфигурацией
 * 
 * @param config Указатель на конфигурацию
 */
void agent_config_destroy(agent_config_t *config);

/**
 * @brief Создать новый цикл агента
 * 
 * @param config Конфигурация агента
 * @return agent_loop_t* Указатель на созданный цикл агента
 */
agent_loop_t* agent_loop_create(agent_config_t *config);

/**
 * @brief Освободить память, занятую циклом агента
 * 
 * @param loop Указатель на цикл агента
 */
void agent_loop_destroy(agent_loop_t *loop);

/**
 * @brief Установить колбэк для сообщений агента
 * 
 * @param loop Указатель на цикл агента
 * @param callback Функция обратного вызова
 * @param user_data Пользовательские данные
 */
void agent_loop_set_message_callback(agent_loop_t *loop, agent_message_callback_t callback, void *user_data);

/**
 * @brief Установить колбэк для индикации загрузки
 * 
 * @param loop Указатель на цикл агента
 * @param callback Функция обратного вызова
 * @param user_data Пользовательские данные
 */
void agent_loop_set_loading_callback(agent_loop_t *loop, agent_loading_callback_t callback, void *user_data);

/**
 * @brief Установить колбэк для подтверждения команды
 * 
 * @param loop Указатель на цикл агента
 * @param callback Функция обратного вызова
 * @param user_data Пользовательские данные
 */
void agent_loop_set_command_confirmation_callback(agent_loop_t *loop, agent_command_confirmation_callback_t callback, void *user_data);

/**
 * @brief Запустить цикл агента с указанным промптом
 * 
 * @param loop Указатель на цикл агента
 * @param prompt Текст промпта
 * @return int Код возврата (0 - успех, другие значения - ошибка)
 */
int agent_loop_run(agent_loop_t *loop, const char *prompt);

/**
 * @brief Отменить текущее выполнение агента
 * 
 * @param loop Указатель на цикл агента
 */
void agent_loop_cancel(agent_loop_t *loop);

/**
 * @brief Полностью остановить агента и освободить ресурсы
 * 
 * @param loop Указатель на цикл агента
 */
void agent_loop_terminate(agent_loop_t *loop);

/**
 * @brief Создать новое сообщение агента
 * 
 * @param type Тип сообщения
 * @param content Содержимое сообщения
 * @return agent_message_t* Указатель на созданное сообщение
 */
agent_message_t* agent_message_create(agent_message_type_t type, const char *content);

/**
 * @brief Освободить память, занятую сообщением
 * 
 * @param message Указатель на сообщение
 */
void agent_message_destroy(agent_message_t *message);

#ifdef __cplusplus
}
#endif

#endif /* NEUROZOND_AGENT_LOOP_H */ 