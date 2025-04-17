/**
 * @file codex.c
 * @brief Реализация основного модуля Codex для NeuroZond
 * @author Team NeuroZond
 * @date 2023-09-06
 */

#include "codex/codex.h"
#include "codex/codex_config.h"
#include <curl/curl.h>
#include <jansson.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>

#define CODEX_USER_AGENT "NeuroZond-Agent/1.0"
#define MAX_ERROR_LENGTH 1024
#define MAX_RETRY_COUNT 3
#define RETRY_DELAY_MS 1000

typedef struct {
    char *data;
    size_t size;
} response_buffer_t;

struct codex_context {
    codex_config_t *config;
    char last_error[MAX_ERROR_LENGTH];
    CURL *curl;
    bool initialized;
    json_t *cache;
    time_t cache_last_cleanup;
};

// Вспомогательная функция для обработки callback curl
static size_t write_callback(void *contents, size_t size, size_t nmemb, void *userp) {
    size_t real_size = size * nmemb;
    response_buffer_t *buffer = (response_buffer_t *)userp;

    char *ptr = realloc(buffer->data, buffer->size + real_size + 1);
    if (!ptr) {
        fprintf(stderr, "Failed to allocate memory for response buffer\n");
        return 0;
    }

    buffer->data = ptr;
    memcpy(&(buffer->data[buffer->size]), contents, real_size);
    buffer->size += real_size;
    buffer->data[buffer->size] = 0;

    return real_size;
}

// Функция для вычисления хеша сообщения (для кэширования)
static char* compute_message_hash(const char* message) {
    unsigned char hash[EVP_MAX_MD_SIZE];
    unsigned int hash_len;
    EVP_MD_CTX *mdctx;
    char *hash_str;
    
    mdctx = EVP_MD_CTX_new();
    EVP_DigestInit_ex(mdctx, EVP_sha256(), NULL);
    EVP_DigestUpdate(mdctx, message, strlen(message));
    EVP_DigestFinal_ex(mdctx, hash, &hash_len);
    EVP_MD_CTX_free(mdctx);
    
    hash_str = malloc(hash_len * 2 + 1);
    if (!hash_str) return NULL;
    
    for (unsigned int i = 0; i < hash_len; i++) {
        sprintf(&hash_str[i * 2], "%02x", hash[i]);
    }
    
    return hash_str;
}

// Очистка устаревших записей кэша
static void cleanup_cache(codex_context_t *ctx) {
    time_t now = time(NULL);
    
    // Выполняем очистку не чаще, чем раз в час
    if (now - ctx->cache_last_cleanup < 3600) return;
    
    if (ctx->cache) {
        const char *key;
        json_t *value;
        json_object_foreach(ctx->cache, key, value) {
            time_t timestamp = json_integer_value(json_object_get(value, "timestamp"));
            if (now - timestamp > ctx->config->cache_ttl_seconds) {
                json_object_del(ctx->cache, key);
            }
        }
    }
    
    ctx->cache_last_cleanup = now;
}

// Проверка кэша для запроса
static json_t* check_cache(codex_context_t *ctx, const char* message_hash) {
    if (!ctx->config->cache_enabled || !ctx->cache) return NULL;
    
    cleanup_cache(ctx);
    
    json_t *cached = json_object_get(ctx->cache, message_hash);
    if (cached) {
        time_t timestamp = json_integer_value(json_object_get(cached, "timestamp"));
        time_t now = time(NULL);
        
        if (now - timestamp <= ctx->config->cache_ttl_seconds) {
            return json_deep_copy(json_object_get(cached, "response"));
        } else {
            // Удаляем устаревшую запись
            json_object_del(ctx->cache, message_hash);
        }
    }
    
    return NULL;
}

// Добавление ответа в кэш
static void add_to_cache(codex_context_t *ctx, const char* message_hash, json_t* response) {
    if (!ctx->config->cache_enabled || !ctx->cache) return;
    
    json_t *cached_item = json_object();
    if (!cached_item) return;
    
    json_object_set_new(cached_item, "timestamp", json_integer(time(NULL)));
    json_object_set_new(cached_item, "response", json_deep_copy(response));
    
    json_object_set_new(ctx->cache, message_hash, cached_item);
}

codex_context_t* codex_init(const codex_config_t *config) {
    codex_context_t *ctx = calloc(1, sizeof(codex_context_t));
    if (!ctx) {
        return NULL;
    }
    
    ctx->config = codex_config_create_default();
    if (!ctx->config) {
        free(ctx);
        return NULL;
    }
    
    // Если передана конфигурация, копируем её данные
    if (config) {
        // Освобождаем строки по умолчанию перед копированием
        free(ctx->config->api_key);
        free(ctx->config->model);
        free(ctx->config->base_url);
        free(ctx->config->local_storage_path);
        
        // Копируем структуру
        *ctx->config = *config;
        
        // Дублируем строки
        if (config->api_key) 
            ctx->config->api_key = strdup(config->api_key);
        if (config->model) 
            ctx->config->model = strdup(config->model);
        if (config->base_url) 
            ctx->config->base_url = strdup(config->base_url);
        if (config->local_storage_path) 
            ctx->config->local_storage_path = strdup(config->local_storage_path);
    }
    
    // Инициализируем curl
    curl_global_init(CURL_GLOBAL_DEFAULT);
    ctx->curl = curl_easy_init();
    if (!ctx->curl) {
        codex_destroy(ctx);
        return NULL;
    }
    
    // Инициализируем кэш, если включен
    if (ctx->config->cache_enabled) {
        ctx->cache = json_object();
        ctx->cache_last_cleanup = time(NULL);
    }
    
    ctx->initialized = true;
    return ctx;
}

void codex_destroy(codex_context_t *ctx) {
    if (!ctx) return;
    
    if (ctx->curl) {
        curl_easy_cleanup(ctx->curl);
        curl_global_cleanup();
    }
    
    if (ctx->cache) {
        json_decref(ctx->cache);
    }
    
    if (ctx->config) {
        codex_config_destroy(ctx->config);
    }
    
    free(ctx);
}

const char* codex_get_last_error(const codex_context_t *ctx) {
    if (!ctx) return "Invalid context";
    return ctx->last_error;
}

codex_response_t* codex_query(codex_context_t *ctx, const char *prompt, const codex_options_t *options) {
    if (!ctx || !ctx->initialized || !prompt) {
        if (ctx) {
            snprintf(ctx->last_error, MAX_ERROR_LENGTH, "Invalid parameters or uninitialized context");
        }
        return NULL;
    }
    
    // Применяем опции, если предоставлены
    codex_options_t effective_options;
    if (options) {
        effective_options = *options;
    } else {
        memset(&effective_options, 0, sizeof(effective_options));
        effective_options.temperature = -1.0f; // Маркер, что не задано
        effective_options.max_tokens = -1;     // Маркер, что не задано
    }
    
    // Проверяем кэш, если включен
    char *message_hash = NULL;
    json_t *cached_response = NULL;
    
    if (ctx->config->cache_enabled) {
        message_hash = compute_message_hash(prompt);
        if (message_hash) {
            cached_response = check_cache(ctx, message_hash);
            if (cached_response) {
                free(message_hash);
                
                // Создаем ответ из кэша
                codex_response_t *response = calloc(1, sizeof(codex_response_t));
                if (!response) {
                    json_decref(cached_response);
                    return NULL;
                }
                
                json_t *content = json_object_get(cached_response, "content");
                if (json_is_string(content)) {
                    response->text = strdup(json_string_value(content));
                }
                
                response->raw_json = json_dumps(cached_response, JSON_COMPACT);
                json_decref(cached_response);
                
                return response;
            }
        }
    }
    
    // Подготовка JSON для запроса
    json_t *request_json = json_object();
    json_t *messages = json_array();
    json_t *user_message = json_object();
    
    json_object_set_new(user_message, "role", json_string("user"));
    json_object_set_new(user_message, "content", json_string(prompt));
    json_array_append_new(messages, user_message);
    
    json_object_set_new(request_json, "messages", messages);
    json_object_set_new(request_json, "model", 
                       json_string(ctx->config->model ? ctx->config->model : "gpt-3.5-turbo"));
    
    if (effective_options.temperature >= 0.0f) {
        json_object_set_new(request_json, "temperature", 
                           json_real(effective_options.temperature));
    } else if (ctx->config->temperature >= 0.0f) {
        json_object_set_new(request_json, "temperature", 
                           json_real(ctx->config->temperature));
    }
    
    if (effective_options.max_tokens > 0) {
        json_object_set_new(request_json, "max_tokens", 
                           json_integer(effective_options.max_tokens));
    } else if (ctx->config->max_tokens > 0) {
        json_object_set_new(request_json, "max_tokens", 
                           json_integer(ctx->config->max_tokens));
    }
    
    // Устанавливаем stream, если включен в конфигурации
    if (ctx->config->stream) {
        json_object_set_new(request_json, "stream", json_boolean(true));
    }
    
    char *request_data = json_dumps(request_json, JSON_COMPACT);
    json_decref(request_json);
    
    if (!request_data) {
        snprintf(ctx->last_error, MAX_ERROR_LENGTH, "Failed to create JSON request");
        if (message_hash) free(message_hash);
        return NULL;
    }
    
    // Подготовка curl
    CURLcode res;
    char url[512];
    
    // Формируем URL в зависимости от провайдера
    if (ctx->config->llm_provider == LLM_PROVIDER_OPENAI) {
        snprintf(url, sizeof(url), "%s/v1/chat/completions", 
                ctx->config->base_url ? ctx->config->base_url : "https://api.openai.com");
    } else {
        snprintf(url, sizeof(url), "%s/v1/messages", 
                ctx->config->base_url ? ctx->config->base_url : "https://api.anthropic.com");
    }
    
    response_buffer_t response_buffer;
    response_buffer.data = malloc(1);
    response_buffer.size = 0;
    
    if (!response_buffer.data) {
        snprintf(ctx->last_error, MAX_ERROR_LENGTH, "Failed to allocate memory for response");
        free(request_data);
        if (message_hash) free(message_hash);
        return NULL;
    }
    
    response_buffer.data[0] = '\0';
    
    curl_easy_reset(ctx->curl);
    curl_easy_setopt(ctx->curl, CURLOPT_URL, url);
    curl_easy_setopt(ctx->curl, CURLOPT_WRITEFUNCTION, write_callback);
    curl_easy_setopt(ctx->curl, CURLOPT_WRITEDATA, (void *)&response_buffer);
    curl_easy_setopt(ctx->curl, CURLOPT_USERAGENT, CODEX_USER_AGENT);
    curl_easy_setopt(ctx->curl, CURLOPT_POSTFIELDS, request_data);
    curl_easy_setopt(ctx->curl, CURLOPT_TIMEOUT_MS, ctx->config->timeout_ms);
    
    // Устанавливаем заголовки
    struct curl_slist *headers = NULL;
    headers = curl_slist_append(headers, "Content-Type: application/json");
    
    char auth_header[256];
    if (ctx->config->llm_provider == LLM_PROVIDER_OPENAI) {
        snprintf(auth_header, sizeof(auth_header), "Authorization: Bearer %s", 
                ctx->config->api_key ? ctx->config->api_key : "");
    } else {
        snprintf(auth_header, sizeof(auth_header), "x-api-key: %s", 
                ctx->config->api_key ? ctx->config->api_key : "");
        headers = curl_slist_append(headers, "anthropic-version: 2023-06-01");
    }
    
    headers = curl_slist_append(headers, auth_header);
    curl_easy_setopt(ctx->curl, CURLOPT_HTTPHEADER, headers);
    
    // Выполняем запрос с повторными попытками при необходимости
    int retry_count = 0;
    bool request_successful = false;
    
    while (retry_count < MAX_RETRY_COUNT && !request_successful) {
        res = curl_easy_perform(ctx->curl);
        
        if (res != CURLE_OK) {
            // Ошибка CURL
            snprintf(ctx->last_error, MAX_ERROR_LENGTH, "CURL error: %s", curl_easy_strerror(res));
            retry_count++;
            
            if (retry_count < MAX_RETRY_COUNT) {
                // Ждем перед следующей попыткой
                struct timespec ts;
                ts.tv_sec = RETRY_DELAY_MS / 1000;
                ts.tv_nsec = (RETRY_DELAY_MS % 1000) * 1000000;
                nanosleep(&ts, NULL);
            }
        } else {
            long http_code = 0;
            curl_easy_getinfo(ctx->curl, CURLINFO_RESPONSE_CODE, &http_code);
            
            if (http_code >= 200 && http_code < 300) {
                // Успешный HTTP ответ
                request_successful = true;
            } else {
                // Ошибка HTTP
                snprintf(ctx->last_error, MAX_ERROR_LENGTH, "HTTP error: %ld, Response: %s", 
                        http_code, response_buffer.data);
                retry_count++;
                
                if (retry_count < MAX_RETRY_COUNT) {
                    // Ждем перед следующей попыткой
                    struct timespec ts;
                    ts.tv_sec = RETRY_DELAY_MS / 1000;
                    ts.tv_nsec = (RETRY_DELAY_MS % 1000) * 1000000;
                    nanosleep(&ts, NULL);
                    
                    // Сбрасываем буфер ответа
                    free(response_buffer.data);
                    response_buffer.data = malloc(1);
                    if (!response_buffer.data) {
                        break;
                    }
                    response_buffer.size = 0;
                    response_buffer.data[0] = '\0';
                }
            }
        }
    }
    
    curl_slist_free_all(headers);
    free(request_data);
    
    if (!request_successful) {
        free(response_buffer.data);
        if (message_hash) free(message_hash);
        return NULL;
    }
    
    // Разбор JSON ответа
    json_error_t json_error;
    json_t *response_json = json_loads(response_buffer.data, 0, &json_error);
    
    if (!response_json) {
        snprintf(ctx->last_error, MAX_ERROR_LENGTH, "JSON parse error: %s", json_error.text);
        free(response_buffer.data);
        if (message_hash) free(message_hash);
        return NULL;
    }
    
    // Создание структуры ответа
    codex_response_t *response = calloc(1, sizeof(codex_response_t));
    if (!response) {
        snprintf(ctx->last_error, MAX_ERROR_LENGTH, "Failed to allocate memory for response structure");
        json_decref(response_json);
        free(response_buffer.data);
        if (message_hash) free(message_hash);
        return NULL;
    }
    
    // Извлечение текста из ответа в зависимости от провайдера
    if (ctx->config->llm_provider == LLM_PROVIDER_OPENAI) {
        json_t *choices = json_object_get(response_json, "choices");
        if (json_is_array(choices) && json_array_size(choices) > 0) {
            json_t *choice = json_array_get(choices, 0);
            if (json_is_object(choice)) {
                json_t *message = json_object_get(choice, "message");
                if (json_is_object(message)) {
                    json_t *content = json_object_get(message, "content");
                    if (json_is_string(content)) {
                        response->text = strdup(json_string_value(content));
                    }
                }
            }
        }
    } else {
        json_t *content = json_object_get(response_json, "content");
        if (json_is_array(content) && json_array_size(content) > 0) {
            json_t *content_item = json_array_get(content, 0);
            if (json_is_object(content_item)) {
                json_t *text = json_object_get(content_item, "text");
                if (json_is_string(text)) {
                    response->text = strdup(json_string_value(text));
                }
            }
        }
    }
    
    // Если включено кэширование, добавляем ответ в кэш
    if (ctx->config->cache_enabled && message_hash) {
        add_to_cache(ctx, message_hash, response_json);
    }
    
    response->raw_json = strdup(response_buffer.data);
    
    json_decref(response_json);
    free(response_buffer.data);
    if (message_hash) free(message_hash);
    
    return response;
}

void codex_free_response(codex_response_t *response) {
    if (!response) return;
    
    if (response->text) {
        free(response->text);
    }
    
    if (response->raw_json) {
        free(response->raw_json);
    }
    
    free(response);
}

int codex_set_config(codex_context_t *ctx, const codex_config_t *config) {
    if (!ctx || !config) {
        if (ctx) {
            snprintf(ctx->last_error, MAX_ERROR_LENGTH, "Invalid parameters");
        }
        return -1;
    }
    
    // Освобождаем строки перед копированием
    free(ctx->config->api_key);
    free(ctx->config->model);
    free(ctx->config->base_url);
    free(ctx->config->local_storage_path);
    
    // Копируем структуру
    *ctx->config = *config;
    
    // Дублируем строки
    if (config->api_key) 
        ctx->config->api_key = strdup(config->api_key);
    else
        ctx->config->api_key = NULL;
        
    if (config->model) 
        ctx->config->model = strdup(config->model);
    else
        ctx->config->model = NULL;
        
    if (config->base_url) 
        ctx->config->base_url = strdup(config->base_url);
    else
        ctx->config->base_url = NULL;
        
    if (config->local_storage_path) 
        ctx->config->local_storage_path = strdup(config->local_storage_path);
    else
        ctx->config->local_storage_path = NULL;
    
    return 0;
}

const codex_config_t* codex_get_config(const codex_context_t *ctx) {
    if (!ctx) return NULL;
    return ctx->config;
}

void codex_clear_cache(codex_context_t *ctx) {
    if (!ctx || !ctx->cache) return;
    
    json_decref(ctx->cache);
    ctx->cache = json_object();
    ctx->cache_last_cleanup = time(NULL);
} 