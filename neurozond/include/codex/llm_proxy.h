/**
 * @file llm_proxy.h
 * @brief NeuroZond LLMProxy - модуль для работы с LLM API напрямую или через C1
 * @author Team NeuroZond
 * @date 2023-09-06
 */

#ifndef NEUROZOND_LLM_PROXY_H
#define NEUROZOND_LLM_PROXY_H

#include <stdbool.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Режим работы LLM прокси
 */
typedef enum {
    LLM_PROXY_MODE_DIRECT,    /**< Прямое подключение к API */
    LLM_PROXY_MODE_C1         /**< Проксирование через C1 */
} llm_proxy_mode_t;

/**
 * @brief Тип провайдера LLM
 */
typedef enum {
    LLM_PROVIDER_OPENAI,     /**< OpenAI API */
    LLM_PROVIDER_ANTHROPIC,  /**< Anthropic (Claude) API */
    LLM_PROVIDER_LOCAL,      /**< Локальная модель */
    LLM_PROVIDER_CUSTOM      /**< Пользовательский провайдер */
} llm_provider_t;

/**
 * @brief Статус операции LLM прокси
 */
typedef enum {
    LLM_PROXY_STATUS_SUCCESS = 0,           /**< Успех */
    LLM_PROXY_STATUS_ERROR_INIT = -1,       /**< Ошибка инициализации */
    LLM_PROXY_STATUS_ERROR_CONNECTION = -2, /**< Ошибка соединения */
    LLM_PROXY_STATUS_ERROR_API_KEY = -3,    /**< Некорректный API ключ */
    LLM_PROXY_STATUS_ERROR_REQUEST = -4,    /**< Ошибка запроса */
    LLM_PROXY_STATUS_ERROR_RESPONSE = -5,   /**< Ошибка ответа */
    LLM_PROXY_STATUS_ERROR_MODEL = -6,      /**< Ошибка модели */
    LLM_PROXY_STATUS_ERROR_PARAMS = -7,     /**< Некорректные параметры */
    LLM_PROXY_STATUS_ERROR_NETWORK = -8,    /**< Сетевая ошибка */
    LLM_PROXY_STATUS_ERROR_INTERNAL = -9    /**< Внутренняя ошибка */
} llm_proxy_status_t;

/**
 * @brief Опции инициализации LLM прокси
 */
typedef struct {
    llm_proxy_mode_t mode;     /**< Режим работы (прямой доступ или через C1) */
    llm_provider_t provider;   /**< Провайдер LLM */
    const char *api_key;       /**< API ключ */
    const char *model;         /**< Модель */
    const char *base_url;      /**< Базовый URL API (может быть NULL) */
    const char *c1_token;      /**< Токен для подключения к C1 (только для режима C1) */
    int timeout_ms;            /**< Таймаут в мс (0 для значения по умолчанию) */
    int max_tokens;            /**< Максимальное количество токенов в ответе */
    bool stream;               /**< Флаг потоковой передачи */
    void *c1_connector;        /**< Коннектор к C1 (только для режима C1) */
} llm_proxy_options_t;

/**
 * @brief Структура LLM прокси
 * 
 * Непрозрачная структура, содержащая внутреннее состояние прокси
 */
typedef struct llm_proxy llm_proxy_t;

/**
 * @brief Результат вызова LLM API
 */
typedef struct llm_proxy_result {
    llm_proxy_status_t status;     /**< Статус выполнения */
    char *content;                 /**< Текстовый результат */
    char *error_message;           /**< Сообщение об ошибке */
    void *raw_response;            /**< Сырой ответ от API */
    int token_count;               /**< Количество использованных токенов */
} llm_proxy_result_t;

/**
 * @brief Функция обратного вызова для обработки сообщений
 */
typedef void (*llm_proxy_message_callback_t)(const char *message, void *user_data);

/**
 * @brief Создать новый экземпляр LLM прокси
 * 
 * @param options Опции инициализации
 * @return llm_proxy_t* Указатель на созданный прокси или NULL при ошибке
 */
llm_proxy_t* llm_proxy_create(const llm_proxy_options_t *options);

/**
 * @brief Освободить ресурсы, занятые LLM прокси
 * 
 * @param proxy Указатель на прокси
 */
void llm_proxy_destroy(llm_proxy_t *proxy);

/**
 * @brief Отправить сообщение через LLM прокси
 * 
 * @param proxy Указатель на прокси
 * @param message Сообщение
 * @param result Указатель для сохранения результата
 * @return llm_proxy_status_t Статус операции
 */
llm_proxy_status_t llm_proxy_send_message(
    llm_proxy_t *proxy,
    const char *message,
    llm_proxy_result_t **result
);

/**
 * @brief Отправить код с контекстом через LLM прокси
 * 
 * @param proxy Указатель на прокси
 * @param code Код
 * @param question Вопрос или инструкция
 * @param result Указатель для сохранения результата
 * @return llm_proxy_status_t Статус операции
 */
llm_proxy_status_t llm_proxy_send_code_context(
    llm_proxy_t *proxy,
    const char *code,
    const char *question,
    llm_proxy_result_t **result
);

/**
 * @brief Отправить потоковое сообщение через LLM прокси
 * 
 * @param proxy Указатель на прокси
 * @param message Сообщение
 * @param callback Функция обратного вызова для обработки ответа
 * @param user_data Пользовательские данные для callback
 * @return llm_proxy_status_t Статус операции
 */
llm_proxy_status_t llm_proxy_send_stream_message(
    llm_proxy_t *proxy,
    const char *message,
    llm_proxy_message_callback_t callback,
    void *user_data
);

/**
 * @brief Отменить текущий запрос
 * 
 * @param proxy Указатель на прокси
 * @return llm_proxy_status_t Статус операции
 */
llm_proxy_status_t llm_proxy_cancel(llm_proxy_t *proxy);

/**
 * @brief Освободить ресурсы, занятые результатом запроса
 * 
 * @param result Указатель на результат
 */
void llm_proxy_result_destroy(llm_proxy_result_t *result);

/**
 * @brief Получить список доступных моделей
 * 
 * @param proxy Указатель на прокси
 * @param models Указатель на массив строк для сохранения моделей
 * @param count Указатель для сохранения количества моделей
 * @return llm_proxy_status_t Статус операции
 */
llm_proxy_status_t llm_proxy_get_available_models(
    llm_proxy_t *proxy,
    char ***models,
    size_t *count
);

/**
 * @brief Проверить корректность API ключа
 * 
 * @param proxy Указатель на прокси
 * @param api_key API ключ для проверки
 * @return llm_proxy_status_t Статус операции
 */
llm_proxy_status_t llm_proxy_validate_api_key(
    llm_proxy_t *proxy,
    const char *api_key
);

/**
 * @brief Получить ошибку последней операции в виде строки
 * 
 * @param proxy Указатель на прокси
 * @return const char* Строка с описанием ошибки
 */
const char* llm_proxy_get_last_error(llm_proxy_t *proxy);

#ifdef __cplusplus
}
#endif

#endif /* NEUROZOND_LLM_PROXY_H */ 