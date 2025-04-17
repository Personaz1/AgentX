/**
 * @file llm_proxy.c
 * @brief Реализация LLM прокси для модуля Codex в NeuroZond
 * @author Team NeuroZond
 * @date 2023-09-06
 */

#include "../../include/codex/llm_proxy.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <curl/curl.h>
#include <jansson.h>

/** Максимальный размер буфера для сообщений */
#define LLM_PROXY_MAX_BUFFER_SIZE 10240

/** Базовый URL для OpenAI API */
#define OPENAI_API_BASE_URL "https://api.openai.com/v1"

/** Базовый URL для Anthropic API */
#define ANTHROPIC_API_BASE_URL "https://api.anthropic.com/v1"

/** Стандартный таймаут для запросов в мс */
#define LLM_PROXY_DEFAULT_TIMEOUT 30000

/**
 * @brief Внутренняя структура LLM прокси
 */
struct llm_proxy {
    llm_proxy_mode_t mode;              /**< Режим работы */
    llm_provider_t provider;            /**< Провайдер LLM */
    char *api_key;                      /**< API ключ */
    char *model;                        /**< Модель */
    char *base_url;                     /**< Базовый URL API */
    char *c1_token;                     /**< Токен для C1 */
    int timeout_ms;                     /**< Таймаут в мс */
    int max_tokens;                     /**< Максимальное число токенов */
    bool stream;                        /**< Флаг потоковой передачи */
    void *c1_connector;                 /**< Коннектор к C1 */
    bool initialized;                   /**< Флаг инициализации */
    CURL *curl;                         /**< CURL хендл */
    char last_error[LLM_PROXY_MAX_BUFFER_SIZE]; /**< Последняя ошибка */
};

/**
 * @brief Структура для кастомных данных CURL
 */
typedef struct {
    char *buffer;          /**< Буфер для ответа */
    size_t size;           /**< Текущий размер буфера */
    size_t capacity;       /**< Ёмкость буфера */
} curl_data_t;

/**
 * @brief Callback-функция для приема данных от CURL
 */
static size_t curl_write_callback(char *ptr, size_t size, size_t nmemb, void *userdata) {
    curl_data_t *data = (curl_data_t*)userdata;
    size_t total_size = size * nmemb;
    
    // Проверяем, есть ли место в буфере
    if (data->size + total_size >= data->capacity) {
        // Увеличиваем буфер
        size_t new_capacity = data->capacity * 2;
        if (new_capacity < data->size + total_size + 1) {
            new_capacity = data->size + total_size + 1;
        }
        
        char *new_buffer = (char*)realloc(data->buffer, new_capacity);
        if (new_buffer == NULL) {
            return 0; // Ошибка выделения памяти
        }
        
        data->buffer = new_buffer;
        data->capacity = new_capacity;
    }
    
    // Копируем данные в буфер
    memcpy(data->buffer + data->size, ptr, total_size);
    data->size += total_size;
    data->buffer[data->size] = '\0'; // Добавляем нуль-терминатор
    
    return total_size;
}

/**
 * @brief Установить последнюю ошибку в прокси
 * 
 * @param proxy Указатель на прокси
 * @param format Формат сообщения об ошибке
 * @param ... Дополнительные аргументы
 */
static void llm_proxy_set_error(llm_proxy_t *proxy, const char *format, ...) {
    if (proxy == NULL || format == NULL) {
        return;
    }
    
    va_list args;
    va_start(args, format);
    vsnprintf(proxy->last_error, LLM_PROXY_MAX_BUFFER_SIZE, format, args);
    va_end(args);
}

/**
 * @brief Создать новый экземпляр LLM прокси
 * 
 * @param options Опции инициализации
 * @return llm_proxy_t* Указатель на созданный прокси или NULL при ошибке
 */
llm_proxy_t* llm_proxy_create(const llm_proxy_options_t *options) {
    if (options == NULL) {
        return NULL;
    }
    
    llm_proxy_t *proxy = (llm_proxy_t*)calloc(1, sizeof(llm_proxy_t));
    if (proxy == NULL) {
        return NULL;
    }
    
    // Копирование опций
    proxy->mode = options->mode;
    proxy->provider = options->provider;
    proxy->timeout_ms = options->timeout_ms > 0 ? options->timeout_ms : LLM_PROXY_DEFAULT_TIMEOUT;
    proxy->stream = options->stream;
    proxy->c1_connector = options->c1_connector;
    proxy->max_tokens = options->max_tokens > 0 ? options->max_tokens : 1000; // Значение по умолчанию
    proxy->initialized = false;
    proxy->curl = NULL;
    proxy->last_error[0] = '\0';
    
    // Копирование строковых полей
    if (options->api_key != NULL) {
        proxy->api_key = strdup(options->api_key);
        if (proxy->api_key == NULL) {
            free(proxy);
            return NULL;
        }
    }
    
    if (options->model != NULL) {
        proxy->model = strdup(options->model);
        if (proxy->model == NULL) {
            free(proxy->api_key);
            free(proxy);
            return NULL;
        }
    }
    
    if (options->c1_token != NULL) {
        proxy->c1_token = strdup(options->c1_token);
        if (proxy->c1_token == NULL) {
            free(proxy->api_key);
            free(proxy->model);
            free(proxy);
            return NULL;
        }
    }
    
    if (options->base_url != NULL) {
        proxy->base_url = strdup(options->base_url);
    } else {
        // Используем стандартный URL в зависимости от провайдера
        const char *default_url = NULL;
        switch (proxy->provider) {
            case LLM_PROVIDER_OPENAI:
                default_url = OPENAI_API_BASE_URL;
                break;
            case LLM_PROVIDER_ANTHROPIC:
                default_url = ANTHROPIC_API_BASE_URL;
                break;
            default:
                // Для других провайдеров базовый URL должен быть указан явно
                break;
        }
        
        if (default_url != NULL) {
            proxy->base_url = strdup(default_url);
        }
    }
    
    // Проверяем успешность копирования строки base_url
    if (proxy->base_url == NULL) {
        free(proxy->api_key);
        free(proxy->model);
        free(proxy->c1_token);
        free(proxy);
        return NULL;
    }
    
    // Инициализация CURL (только для прямого режима)
    if (proxy->mode == LLM_PROXY_MODE_DIRECT) {
        proxy->curl = curl_easy_init();
        if (proxy->curl == NULL) {
            llm_proxy_set_error(proxy, "Ошибка инициализации CURL");
            free(proxy->api_key);
            free(proxy->model);
            free(proxy->c1_token);
            free(proxy->base_url);
            free(proxy);
            return NULL;
        }
    }
    
    proxy->initialized = true;
    return proxy;
}

/**
 * @brief Освободить ресурсы, занятые LLM прокси
 * 
 * @param proxy Указатель на прокси
 */
void llm_proxy_destroy(llm_proxy_t *proxy) {
    if (proxy == NULL) {
        return;
    }
    
    if (proxy->api_key != NULL) {
        free(proxy->api_key);
        proxy->api_key = NULL;
    }
    
    if (proxy->model != NULL) {
        free(proxy->model);
        proxy->model = NULL;
    }
    
    if (proxy->base_url != NULL) {
        free(proxy->base_url);
        proxy->base_url = NULL;
    }
    
    if (proxy->c1_token != NULL) {
        free(proxy->c1_token);
        proxy->c1_token = NULL;
    }
    
    if (proxy->curl != NULL) {
        curl_easy_cleanup(proxy->curl);
        proxy->curl = NULL;
    }
    
    proxy->initialized = false;
    free(proxy);
}

/**
 * @brief Создать новый результат LLM запроса
 * 
 * @param status Статус операции
 * @return llm_proxy_result_t* Указатель на созданный результат или NULL при ошибке
 */
static llm_proxy_result_t* llm_proxy_result_create(llm_proxy_status_t status) {
    llm_proxy_result_t *result = (llm_proxy_result_t*)calloc(1, sizeof(llm_proxy_result_t));
    if (result == NULL) {
        return NULL;
    }
    
    result->status = status;
    result->content = NULL;
    result->error_message = NULL;
    result->raw_response = NULL;
    result->token_count = 0;
    
    return result;
}

/**
 * @brief Отправить запрос к OpenAI API
 * 
 * @param proxy Указатель на прокси
 * @param endpoint Эндпоинт API
 * @param json_payload JSON-данные для отправки
 * @param result Указатель для сохранения результата
 * @return llm_proxy_status_t Статус операции
 */
static llm_proxy_status_t send_openai_request(
    llm_proxy_t *proxy,
    const char *endpoint,
    json_t *json_payload,
    llm_proxy_result_t **result
) {
    if (proxy == NULL || endpoint == NULL || json_payload == NULL || result == NULL) {
        return LLM_PROXY_STATUS_ERROR_PARAMS;
    }
    
    // Создаем полный URL
    char url[LLM_PROXY_MAX_BUFFER_SIZE];
    snprintf(url, sizeof(url), "%s%s", proxy->base_url, endpoint);
    
    // Преобразуем JSON в строку
    char *json_str = json_dumps(json_payload, 0);
    if (json_str == NULL) {
        llm_proxy_set_error(proxy, "Ошибка сериализации JSON");
        return LLM_PROXY_STATUS_ERROR_REQUEST;
    }
    
    // Инициализация данных для CURL
    curl_data_t curl_data;
    curl_data.buffer = (char*)malloc(LLM_PROXY_MAX_BUFFER_SIZE);
    curl_data.size = 0;
    curl_data.capacity = LLM_PROXY_MAX_BUFFER_SIZE;
    
    if (curl_data.buffer == NULL) {
        free(json_str);
        llm_proxy_set_error(proxy, "Ошибка выделения памяти для буфера ответа");
        return LLM_PROXY_STATUS_ERROR_INTERNAL;
    }
    
    curl_data.buffer[0] = '\0';
    
    // Настройка CURL
    curl_easy_reset(proxy->curl);
    curl_easy_setopt(proxy->curl, CURLOPT_URL, url);
    curl_easy_setopt(proxy->curl, CURLOPT_WRITEFUNCTION, curl_write_callback);
    curl_easy_setopt(proxy->curl, CURLOPT_WRITEDATA, &curl_data);
    curl_easy_setopt(proxy->curl, CURLOPT_TIMEOUT_MS, proxy->timeout_ms);
    
    // Настройка заголовков
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    
    char auth_header[LLM_PROXY_MAX_BUFFER_SIZE];
    snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", proxy->api_key);
    headers = curl_slist_append(headers, auth_header);
    
    curl_easy_setopt(proxy->curl, CURLOPT_HTTPHEADER, headers);
    
    // Настройка POST-запроса
    curl_easy_setopt(proxy->curl, CURLOPT_POST, 1L);
    curl_easy_setopt(proxy->curl, CURLOPT_POSTFIELDS, json_str);
    
    // Выполнение запроса
    CURLcode curl_code = curl_easy_perform(proxy->curl);
    
    // Освобождение ресурсов
    curl_slist_free_all(headers);
    free(json_str);
    
    // Проверка результата
    if (curl_code != CURLE_OK) {
        free(curl_data.buffer);
        llm_proxy_set_error(proxy, "Ошибка CURL: %s", curl_easy_strerror(curl_code));
        return LLM_PROXY_STATUS_ERROR_NETWORK;
    }
    
    // Получаем HTTP код ответа
    long http_code = 0;
    curl_easy_getinfo(proxy->curl, CURLINFO_RESPONSE_CODE, &http_code);
    
    // Проверяем HTTP код
    if (http_code != 200) {
        free(curl_data.buffer);
        llm_proxy_set_error(proxy, "Ошибка HTTP: %ld", http_code);
        return LLM_PROXY_STATUS_ERROR_RESPONSE;
    }
    
    // Парсим ответ JSON
    json_error_t json_error;
    json_t *json_response = json_loads(curl_data.buffer, 0, &json_error);
    
    if (json_response == NULL) {
        free(curl_data.buffer);
        llm_proxy_set_error(proxy, "Ошибка парсинга JSON: %s", json_error.text);
        return LLM_PROXY_STATUS_ERROR_RESPONSE;
    }
    
    // Извлекаем данные из ответа
    *result = llm_proxy_result_create(LLM_PROXY_STATUS_SUCCESS);
    if (*result == NULL) {
        free(curl_data.buffer);
        json_decref(json_response);
        llm_proxy_set_error(proxy, "Ошибка выделения памяти для результата");
        return LLM_PROXY_STATUS_ERROR_INTERNAL;
    }
    
    // Для OpenAI извлекаем текст из choices[0].message.content
    json_t *choices = json_object_get(json_response, "choices");
    if (json_is_array(choices) && json_array_size(choices) > 0) {
        json_t *first_choice = json_array_get(choices, 0);
        json_t *message = json_object_get(first_choice, "message");
        json_t *content = json_object_get(message, "content");
        
        if (json_is_string(content)) {
            (*result)->content = strdup(json_string_value(content));
        }
    }
    
    // Извлекаем usage.total_tokens, если есть
    json_t *usage = json_object_get(json_response, "usage");
    if (json_is_object(usage)) {
        json_t *total_tokens = json_object_get(usage, "total_tokens");
        if (json_is_integer(total_tokens)) {
            (*result)->token_count = (int)json_integer_value(total_tokens);
        }
    }
    
    // Сохраняем сырой ответ
    (*result)->raw_response = json_response;
    
    free(curl_data.buffer);
    return LLM_PROXY_STATUS_SUCCESS;
}

/**
 * @brief Отправить запрос к Anthropic API
 * 
 * @param proxy Указатель на прокси
 * @param endpoint Эндпоинт API
 * @param json_payload JSON-данные для отправки
 * @param result Указатель для сохранения результата
 * @return llm_proxy_status_t Статус операции
 */
static llm_proxy_status_t send_anthropic_request(
    llm_proxy_t *proxy,
    const char *endpoint,
    json_t *json_payload,
    llm_proxy_result_t **result
) {
    if (proxy == NULL || endpoint == NULL || json_payload == NULL || result == NULL) {
        return LLM_PROXY_STATUS_ERROR_PARAMS;
    }
    
    // Создаем полный URL
    char url[LLM_PROXY_MAX_BUFFER_SIZE];
    snprintf(url, sizeof(url), "%s%s", proxy->base_url, endpoint);
    
    // Преобразуем JSON в строку
    char *json_str = json_dumps(json_payload, 0);
    if (json_str == NULL) {
        llm_proxy_set_error(proxy, "Ошибка сериализации JSON");
        return LLM_PROXY_STATUS_ERROR_REQUEST;
    }
    
    // Инициализация данных для CURL
    curl_data_t curl_data;
    curl_data.buffer = (char*)malloc(LLM_PROXY_MAX_BUFFER_SIZE);
    curl_data.size = 0;
    curl_data.capacity = LLM_PROXY_MAX_BUFFER_SIZE;
    
    if (curl_data.buffer == NULL) {
        free(json_str);
        llm_proxy_set_error(proxy, "Ошибка выделения памяти для буфера ответа");
        return LLM_PROXY_STATUS_ERROR_INTERNAL;
    }
    
    curl_data.buffer[0] = '\0';
    
    // Настройка CURL
    curl_easy_reset(proxy->curl);
    curl_easy_setopt(proxy->curl, CURLOPT_URL, url);
    curl_easy_setopt(proxy->curl, CURLOPT_WRITEFUNCTION, curl_write_callback);
    curl_easy_setopt(proxy->curl, CURLOPT_WRITEDATA, &curl_data);
    curl_easy_setopt(proxy->curl, CURLOPT_TIMEOUT_MS, proxy->timeout_ms);
    
    // Настройка заголовков
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    
    char auth_header[LLM_PROXY_MAX_BUFFER_SIZE];
    snprintf(auth_header, sizeof(auth_header), "x-api-key: %s", proxy->api_key);
    headers = curl_slist_append(headers, auth_header);
    headers = curl_slist_append(headers, "anthropic-version: 2023-06-01");
    
    curl_easy_setopt(proxy->curl, CURLOPT_HTTPHEADER, headers);
    
    // Настройка POST-запроса
    curl_easy_setopt(proxy->curl, CURLOPT_POST, 1L);
    curl_easy_setopt(proxy->curl, CURLOPT_POSTFIELDS, json_str);
    
    // Выполнение запроса
    CURLcode curl_code = curl_easy_perform(proxy->curl);
    
    // Освобождение ресурсов
    curl_slist_free_all(headers);
    free(json_str);
    
    // Проверка результата
    if (curl_code != CURLE_OK) {
        free(curl_data.buffer);
        llm_proxy_set_error(proxy, "Ошибка CURL: %s", curl_easy_strerror(curl_code));
        return LLM_PROXY_STATUS_ERROR_NETWORK;
    }
    
    // Получаем HTTP код ответа
    long http_code = 0;
    curl_easy_getinfo(proxy->curl, CURLINFO_RESPONSE_CODE, &http_code);
    
    // Проверяем HTTP код
    if (http_code != 200) {
        free(curl_data.buffer);
        llm_proxy_set_error(proxy, "Ошибка HTTP: %ld", http_code);
        return LLM_PROXY_STATUS_ERROR_RESPONSE;
    }
    
    // Парсим ответ JSON
    json_error_t json_error;
    json_t *json_response = json_loads(curl_data.buffer, 0, &json_error);
    
    if (json_response == NULL) {
        free(curl_data.buffer);
        llm_proxy_set_error(proxy, "Ошибка парсинга JSON: %s", json_error.text);
        return LLM_PROXY_STATUS_ERROR_RESPONSE;
    }
    
    // Извлекаем данные из ответа
    *result = llm_proxy_result_create(LLM_PROXY_STATUS_SUCCESS);
    if (*result == NULL) {
        free(curl_data.buffer);
        json_decref(json_response);
        llm_proxy_set_error(proxy, "Ошибка выделения памяти для результата");
        return LLM_PROXY_STATUS_ERROR_INTERNAL;
    }
    
    // Для Anthropic извлекаем текст из content
    json_t *content = json_object_get(json_response, "content");
    if (json_is_array(content) && json_array_size(content) > 0) {
        // Проходим по массиву контента и собираем все текстовые части
        char content_buffer[LLM_PROXY_MAX_BUFFER_SIZE] = {0};
        size_t current_pos = 0;
        
        for (size_t i = 0; i < json_array_size(content); i++) {
            json_t *item = json_array_get(content, i);
            json_t *type = json_object_get(item, "type");
            
            if (json_is_string(type) && strcmp(json_string_value(type), "text") == 0) {
                json_t *text = json_object_get(item, "text");
                if (json_is_string(text)) {
                    const char *text_value = json_string_value(text);
                    size_t text_len = strlen(text_value);
                    
                    // Проверяем, достаточно ли места в буфере
                    if (current_pos + text_len < LLM_PROXY_MAX_BUFFER_SIZE - 1) {
                        strncpy(content_buffer + current_pos, text_value, LLM_PROXY_MAX_BUFFER_SIZE - current_pos - 1);
                        current_pos += text_len;
                    }
                }
            }
        }
        
        // Убеждаемся, что строка завершена нулем
        content_buffer[current_pos] = '\0';
        
        // Сохраняем собранный текст
        if (current_pos > 0) {
            (*result)->content = strdup(content_buffer);
        }
    }
    
    // Извлекаем usage.input_tokens и usage.output_tokens, если есть
    json_t *usage = json_object_get(json_response, "usage");
    if (json_is_object(usage)) {
        json_t *input_tokens = json_object_get(usage, "input_tokens");
        json_t *output_tokens = json_object_get(usage, "output_tokens");
        
        int token_count = 0;
        if (json_is_integer(input_tokens)) {
            token_count += (int)json_integer_value(input_tokens);
        }
        
        if (json_is_integer(output_tokens)) {
            token_count += (int)json_integer_value(output_tokens);
        }
        
        (*result)->token_count = token_count;
    }
    
    // Сохраняем сырой ответ
    (*result)->raw_response = json_response;
    
    free(curl_data.buffer);
    return LLM_PROXY_STATUS_SUCCESS;
}

/**
 * @brief Отправить запрос к C1 API
 * 
 * @param proxy Указатель на прокси
 * @param endpoint Эндпоинт API
 * @param json_payload JSON-данные для отправки
 * @param result Указатель для сохранения результата
 * @return llm_proxy_status_t Статус операции
 */
static llm_proxy_status_t send_c1_request(
    llm_proxy_t *proxy,
    const char *endpoint,
    json_t *json_payload,
    llm_proxy_result_t **result
) {
    if (proxy == NULL || endpoint == NULL || json_payload == NULL || result == NULL) {
        return LLM_PROXY_STATUS_ERROR_PARAMS;
    }
    
    // Создаем полный URL
    char url[LLM_PROXY_MAX_BUFFER_SIZE];
    snprintf(url, sizeof(url), "%s%s", proxy->base_url, endpoint);
    
    // Проверяем наличие необходимых полей в JSON
    json_t *system_prompt = json_object_get(json_payload, "system_prompt");
    json_t *user_prompt = json_object_get(json_payload, "user_prompt");
    
    if (!json_is_string(system_prompt) || !json_is_string(user_prompt)) {
        llm_proxy_set_error(proxy, "Отсутствуют обязательные поля system_prompt или user_prompt");
        return LLM_PROXY_STATUS_ERROR_PARAMS;
    }
    
    // Создаем новый JSON объект для C1 API
    json_t *c1_payload = json_object();
    if (c1_payload == NULL) {
        llm_proxy_set_error(proxy, "Ошибка создания JSON объекта");
        return LLM_PROXY_STATUS_ERROR_INTERNAL;
    }
    
    // Формируем запрос по формату C1 API
    json_object_set_new(c1_payload, "model", json_string(proxy->model));
    
    // Создаем массив сообщений
    json_t *messages = json_array();
    if (messages == NULL) {
        json_decref(c1_payload);
        llm_proxy_set_error(proxy, "Ошибка создания массива сообщений");
        return LLM_PROXY_STATUS_ERROR_INTERNAL;
    }
    
    // Добавляем системное сообщение
    json_t *system_message = json_object();
    json_object_set_new(system_message, "role", json_string("system"));
    json_object_set(system_message, "content", system_prompt);
    json_array_append_new(messages, system_message);
    
    // Добавляем пользовательское сообщение
    json_t *user_message = json_object();
    json_object_set_new(user_message, "role", json_string("user"));
    json_object_set(user_message, "content", user_prompt);
    json_array_append_new(messages, user_message);
    
    // Добавляем массив сообщений в основной объект
    json_object_set_new(c1_payload, "messages", messages);
    
    // Добавляем дополнительные параметры, если они есть
    json_t *temperature = json_object_get(json_payload, "temperature");
    if (json_is_number(temperature)) {
        json_object_set(c1_payload, "temperature", temperature);
    } else {
        json_object_set_new(c1_payload, "temperature", json_real(0.7));
    }
    
    // Устанавливаем токен для работы с C1
    json_object_set_new(c1_payload, "token", json_string(proxy->c1_token));
    
    // Добавляем дополнительные C1-специфичные параметры
    json_object_set_new(c1_payload, "stream", json_boolean(0));
    json_object_set_new(c1_payload, "max_tokens", json_integer(proxy->max_tokens));
    
    // Преобразуем JSON в строку
    char *json_str = json_dumps(c1_payload, 0);
    json_decref(c1_payload);
    
    if (json_str == NULL) {
        llm_proxy_set_error(proxy, "Ошибка сериализации JSON");
        return LLM_PROXY_STATUS_ERROR_REQUEST;
    }
    
    // Инициализация данных для CURL
    curl_data_t curl_data;
    curl_data.buffer = (char*)malloc(LLM_PROXY_MAX_BUFFER_SIZE);
    curl_data.size = 0;
    curl_data.capacity = LLM_PROXY_MAX_BUFFER_SIZE;
    
    if (curl_data.buffer == NULL) {
        free(json_str);
        llm_proxy_set_error(proxy, "Ошибка выделения памяти для буфера ответа");
        return LLM_PROXY_STATUS_ERROR_INTERNAL;
    }
    
    curl_data.buffer[0] = '\0';
    
    // Настройка CURL
    curl_easy_reset(proxy->curl);
    curl_easy_setopt(proxy->curl, CURLOPT_URL, url);
    curl_easy_setopt(proxy->curl, CURLOPT_WRITEFUNCTION, curl_write_callback);
    curl_easy_setopt(proxy->curl, CURLOPT_WRITEDATA, &curl_data);
    curl_easy_setopt(proxy->curl, CURLOPT_TIMEOUT_MS, proxy->timeout_ms);
    
    // Настройка заголовков
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    
    // Настройка аутентификации для C1
    char auth_header[LLM_PROXY_MAX_BUFFER_SIZE];
    snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", proxy->c1_token);
    headers = curl_slist_append(headers, auth_header);
    
    curl_easy_setopt(proxy->curl, CURLOPT_HTTPHEADER, headers);
    
    // Настройка POST-запроса
    curl_easy_setopt(proxy->curl, CURLOPT_POST, 1L);
    curl_easy_setopt(proxy->curl, CURLOPT_POSTFIELDS, json_str);
    
    // Выполнение запроса
    CURLcode curl_code = curl_easy_perform(proxy->curl);
    
    // Освобождение ресурсов
    curl_slist_free_all(headers);
    free(json_str);
    
    // Проверка результата
    if (curl_code != CURLE_OK) {
        free(curl_data.buffer);
        llm_proxy_set_error(proxy, "Ошибка CURL: %s", curl_easy_strerror(curl_code));
        return LLM_PROXY_STATUS_ERROR_NETWORK;
    }
    
    // Получаем HTTP код ответа
    long http_code = 0;
    curl_easy_getinfo(proxy->curl, CURLINFO_RESPONSE_CODE, &http_code);
    
    // Проверяем HTTP код
    if (http_code != 200) {
        free(curl_data.buffer);
        llm_proxy_set_error(proxy, "Ошибка HTTP: %ld, ответ: %s", http_code, curl_data.buffer);
        return LLM_PROXY_STATUS_ERROR_RESPONSE;
    }
    
    // Парсим ответ JSON
    json_error_t json_error;
    json_t *json_response = json_loads(curl_data.buffer, 0, &json_error);
    
    if (json_response == NULL) {
        free(curl_data.buffer);
        llm_proxy_set_error(proxy, "Ошибка парсинга JSON: %s", json_error.text);
        return LLM_PROXY_STATUS_ERROR_RESPONSE;
    }
    
    // Извлекаем данные из ответа
    *result = llm_proxy_result_create(LLM_PROXY_STATUS_SUCCESS);
    if (*result == NULL) {
        free(curl_data.buffer);
        json_decref(json_response);
        llm_proxy_set_error(proxy, "Ошибка выделения памяти для результата");
        return LLM_PROXY_STATUS_ERROR_INTERNAL;
    }
    
    // Извлекаем текст из ответа C1
    json_t *choices = json_object_get(json_response, "choices");
    if (json_is_array(choices) && json_array_size(choices) > 0) {
        json_t *first_choice = json_array_get(choices, 0);
        if (json_is_object(first_choice)) {
            json_t *message = json_object_get(first_choice, "message");
            if (json_is_object(message)) {
                json_t *content = json_object_get(message, "content");
                if (json_is_string(content)) {
                    const char *content_str = json_string_value(content);
                    (*result)->content = strdup(content_str);
                }
            }
        }
    }
    
    // Извлекаем usage, если есть
    json_t *usage = json_object_get(json_response, "usage");
    if (json_is_object(usage)) {
        json_t *prompt_tokens = json_object_get(usage, "prompt_tokens");
        json_t *completion_tokens = json_object_get(usage, "completion_tokens");
        
        int token_count = 0;
        if (json_is_integer(prompt_tokens)) {
            token_count += (int)json_integer_value(prompt_tokens);
        }
        
        if (json_is_integer(completion_tokens)) {
            token_count += (int)json_integer_value(completion_tokens);
        }
        
        (*result)->token_count = token_count;
    }
    
    // Сохраняем сырой ответ
    (*result)->raw_response = json_response;
    
    free(curl_data.buffer);
    return LLM_PROXY_STATUS_SUCCESS;
}

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
) {
    if (proxy == NULL || message == NULL || result == NULL) {
        return LLM_PROXY_STATUS_ERROR_PARAMS;
    }
    
    if (!proxy->initialized) {
        llm_proxy_set_error(proxy, "Прокси не инициализирован");
        return LLM_PROXY_STATUS_ERROR_INIT;
    }
    
    // Проверяем режим работы
    if (proxy->mode == LLM_PROXY_MODE_C1) {
        // В режиме C1 проксируем запрос через C1
        
        // Создаем JSON-данные для запроса в формате C1
        json_t *json_payload = json_object();
        if (json_payload == NULL) {
            llm_proxy_set_error(proxy, "Ошибка создания JSON объекта");
            return LLM_PROXY_STATUS_ERROR_INTERNAL;
        }
        
        // Загружаем системный и пользовательский промпты
        // В реальном коде они должны быть загружены из конфигурации или получены от C1
        const char *system_prompt = "Ты автономный мозг центра управления C1 для системы NeuroZond/NeuroRAT.";
        
        // Сохраняем промпты в JSON
        json_object_set_new(json_payload, "system_prompt", json_string(system_prompt));
        json_object_set_new(json_payload, "user_prompt", json_string(message));
        
        // Вызываем C1 API с подготовленными данными
        llm_proxy_status_t status = send_c1_request(
            proxy,
            "/api/c1/process",
            json_payload,
            result
        );
        
        // Освобождаем ресурсы
        json_decref(json_payload);
        
        return status;
    }
    
    // В прямом режиме отправляем запрос к API провайдера
    switch (proxy->provider) {
        case LLM_PROVIDER_OPENAI: {
            // Создаем JSON-данные для запроса
            json_t *json_payload = json_object();
            
            json_object_set_new(json_payload, "model", json_string(proxy->model));
            
            json_t *messages = json_array();
            json_t *user_message = json_object();
            json_object_set_new(user_message, "role", json_string("user"));
            json_object_set_new(user_message, "content", json_string(message));
            json_array_append_new(messages, user_message);
            
            json_object_set_new(json_payload, "messages", messages);
            json_object_set_new(json_payload, "temperature", json_real(0.7));
            json_object_set_new(json_payload, "max_tokens", json_integer(proxy->max_tokens));
            json_object_set_new(json_payload, "stream", json_boolean(proxy->stream));
            
            llm_proxy_status_t status = send_openai_request(
                proxy,
                "/chat/completions",
                json_payload,
                result
            );
            
            json_decref(json_payload);
            return status;
        }
        
        case LLM_PROVIDER_ANTHROPIC: {
            // Создаем JSON-данные для запроса
            json_t *json_payload = json_object();
            
            json_object_set_new(json_payload, "model", json_string(proxy->model));
            json_object_set_new(json_payload, "prompt", json_string(message));
            json_object_set_new(json_payload, "max_tokens_to_sample", json_integer(proxy->max_tokens));
            json_object_set_new(json_payload, "temperature", json_real(0.7));
            json_object_set_new(json_payload, "stream", json_boolean(proxy->stream));
            
            llm_proxy_status_t status = send_anthropic_request(
                proxy,
                "/complete",
                json_payload,
                result
            );
            
            json_decref(json_payload);
            return status;
        }
        
        default:
            llm_proxy_set_error(proxy, "Неподдерживаемый провайдер LLM: %d", proxy->provider);
            return LLM_PROXY_STATUS_ERROR_PARAMS;
    }
}

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
) {
    if (proxy == NULL || code == NULL || question == NULL || result == NULL) {
        return LLM_PROXY_STATUS_ERROR_PARAMS;
    }
    
    if (!proxy->initialized) {
        llm_proxy_set_error(proxy, "Прокси не инициализирован");
        return LLM_PROXY_STATUS_ERROR_INIT;
    }
    
    // Формируем сообщение с кодом и вопросом
    char *message = (char*)malloc(strlen(code) + strlen(question) + 100);
    if (message == NULL) {
        llm_proxy_set_error(proxy, "Ошибка выделения памяти для сообщения");
        return LLM_PROXY_STATUS_ERROR_INTERNAL;
    }
    
    sprintf(message, "Code:\n```\n%s\n```\n\nQuestion: %s", code, question);
    
    // Отправляем сообщение
    llm_proxy_status_t status = llm_proxy_send_message(proxy, message, result);
    
    free(message);
    return status;
}

/**
 * @brief Освободить ресурсы, занятые результатом запроса
 * 
 * @param result Указатель на результат
 */
void llm_proxy_result_destroy(llm_proxy_result_t *result) {
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
    
    if (result->raw_response != NULL) {
        json_decref((json_t*)result->raw_response);
        result->raw_response = NULL;
    }
    
    free(result);
}

/**
 * @brief Получить ошибку последней операции в виде строки
 * 
 * @param proxy Указатель на прокси
 * @return const char* Строка с описанием ошибки
 */
const char* llm_proxy_get_last_error(llm_proxy_t *proxy) {
    if (proxy == NULL) {
        return "NULL proxy";
    }
    
    return proxy->last_error;
} 