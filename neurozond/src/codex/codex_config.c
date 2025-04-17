/**
 * @file codex_config.c
 * @brief Реализация конфигурации модуля Codex для NeuroZond
 * @author Team NeuroZond
 * @date 2023-09-06
 */

#include "../../include/codex/codex_config.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/**
 * @brief Создание конфигурации модуля Codex со значениями по умолчанию
 * 
 * @return Указатель на созданную конфигурацию или NULL в случае ошибки
 */
codex_config_t* codex_config_create_default(void) {
    codex_config_t* config = (codex_config_t*)malloc(sizeof(codex_config_t));
    if (!config) {
        return NULL;
    }

    // Значения по умолчанию
    config->llm_mode = LLM_PROXY_MODE_DIRECT;
    config->llm_provider = LLM_PROVIDER_OPENAI;
    config->api_key = NULL;
    config->model = strdup("gpt-3.5-turbo");
    config->base_url = NULL;
    config->timeout_ms = 30000; // 30 секунд по умолчанию
    config->stream = false;
    config->max_tokens = 2048;
    config->temperature = 0.7f;
    config->c1_connector = NULL;
    config->local_storage_path = strdup("/tmp/codex_cache");
    config->max_context_size = 16384;
    config->max_response_tries = 3;
    config->cache_enabled = true;
    config->cache_ttl_seconds = 86400; // 24 часа
    config->secure_mode = true;  // Безопасный режим по умолчанию включен
    config->log_level = CODEX_LOG_INFO;
    
    return config;
}

/**
 * @brief Загрузка конфигурации из JSON файла
 * 
 * @param filename Путь к JSON файлу с конфигурацией
 * @return Указатель на созданную конфигурацию или NULL в случае ошибки
 */
codex_config_t* codex_config_load_from_file(const char* filename) {
    // Сначала создаем конфигурацию по умолчанию
    codex_config_t* config = codex_config_create_default();
    if (!config) {
        return NULL;
    }
    
    // Открываем файл
    FILE* file = fopen(filename, "r");
    if (!file) {
        codex_config_destroy(config);
        return NULL;
    }
    
    // Определяем размер файла
    fseek(file, 0, SEEK_END);
    long file_size = ftell(file);
    fseek(file, 0, SEEK_SET);
    
    // Выделяем память для содержимого файла
    char* json_content = (char*)malloc(file_size + 1);
    if (!json_content) {
        fclose(file);
        codex_config_destroy(config);
        return NULL;
    }
    
    // Читаем файл
    size_t read_size = fread(json_content, 1, file_size, file);
    fclose(file);
    
    if (read_size != file_size) {
        free(json_content);
        codex_config_destroy(config);
        return NULL;
    }
    
    json_content[file_size] = '\0';
    
    // Парсим JSON
    json_error_t error;
    json_t* root = json_loads(json_content, 0, &error);
    free(json_content);
    
    if (!root) {
        codex_config_destroy(config);
        return NULL;
    }
    
    // Извлекаем значения
    json_t* value;
    
    // LLM режим
    value = json_object_get(root, "llm_mode");
    if (json_is_string(value)) {
        const char* mode_str = json_string_value(value);
        if (strcmp(mode_str, "direct") == 0) {
            config->llm_mode = LLM_PROXY_MODE_DIRECT;
        } else if (strcmp(mode_str, "c1") == 0) {
            config->llm_mode = LLM_PROXY_MODE_C1;
        }
    }
    
    // LLM провайдер
    value = json_object_get(root, "llm_provider");
    if (json_is_string(value)) {
        const char* provider_str = json_string_value(value);
        if (strcmp(provider_str, "openai") == 0) {
            config->llm_provider = LLM_PROVIDER_OPENAI;
        } else if (strcmp(provider_str, "anthropic") == 0) {
            config->llm_provider = LLM_PROVIDER_ANTHROPIC;
        }
    }
    
    // API ключ
    value = json_object_get(root, "api_key");
    if (json_is_string(value)) {
        if (config->api_key) free(config->api_key);
        config->api_key = strdup(json_string_value(value));
    }
    
    // Модель
    value = json_object_get(root, "model");
    if (json_is_string(value)) {
        if (config->model) free(config->model);
        config->model = strdup(json_string_value(value));
    }
    
    // Base URL
    value = json_object_get(root, "base_url");
    if (json_is_string(value)) {
        if (config->base_url) free(config->base_url);
        config->base_url = strdup(json_string_value(value));
    }
    
    // Timeout
    value = json_object_get(root, "timeout_ms");
    if (json_is_integer(value)) {
        config->timeout_ms = (int)json_integer_value(value);
    }
    
    // Stream
    value = json_object_get(root, "stream");
    if (json_is_boolean(value)) {
        config->stream = json_is_true(value);
    }
    
    // Max Tokens
    value = json_object_get(root, "max_tokens");
    if (json_is_integer(value)) {
        config->max_tokens = (int)json_integer_value(value);
    }
    
    // Temperature
    value = json_object_get(root, "temperature");
    if (json_is_real(value)) {
        config->temperature = (float)json_real_value(value);
    }
    
    // Local Storage Path
    value = json_object_get(root, "local_storage_path");
    if (json_is_string(value)) {
        if (config->local_storage_path) free(config->local_storage_path);
        config->local_storage_path = strdup(json_string_value(value));
    }
    
    // Max Context Size
    value = json_object_get(root, "max_context_size");
    if (json_is_integer(value)) {
        config->max_context_size = (int)json_integer_value(value);
    }
    
    // Max Response Tries
    value = json_object_get(root, "max_response_tries");
    if (json_is_integer(value)) {
        config->max_response_tries = (int)json_integer_value(value);
    }
    
    // Cache Enabled
    value = json_object_get(root, "cache_enabled");
    if (json_is_boolean(value)) {
        config->cache_enabled = json_is_true(value);
    }
    
    // Cache TTL
    value = json_object_get(root, "cache_ttl_seconds");
    if (json_is_integer(value)) {
        config->cache_ttl_seconds = (int)json_integer_value(value);
    }
    
    // Secure Mode
    value = json_object_get(root, "secure_mode");
    if (json_is_boolean(value)) {
        config->secure_mode = json_is_true(value);
    }
    
    // Log Level
    value = json_object_get(root, "log_level");
    if (json_is_integer(value)) {
        config->log_level = (codex_log_level_t)json_integer_value(value);
    } else if (json_is_string(value)) {
        const char* level_str = json_string_value(value);
        if (strcmp(level_str, "debug") == 0) {
            config->log_level = CODEX_LOG_DEBUG;
        } else if (strcmp(level_str, "info") == 0) {
            config->log_level = CODEX_LOG_INFO;
        } else if (strcmp(level_str, "warning") == 0) {
            config->log_level = CODEX_LOG_WARNING;
        } else if (strcmp(level_str, "error") == 0) {
            config->log_level = CODEX_LOG_ERROR;
        }
    }
    
    json_decref(root);
    return config;
}

/**
 * @brief Сохранение конфигурации в JSON файл
 * 
 * @param config Указатель на конфигурацию
 * @param filename Путь к файлу для сохранения
 * @return 0 при успехе, -1 при ошибке
 */
int codex_config_save_to_file(const codex_config_t* config, const char* filename) {
    if (!config || !filename) {
        return -1;
    }
    
    json_t* root = json_object();
    if (!root) {
        return -1;
    }
    
    // LLM режим
    const char* mode_str = (config->llm_mode == LLM_PROXY_MODE_DIRECT) ? "direct" : "c1";
    json_object_set_new(root, "llm_mode", json_string(mode_str));
    
    // LLM провайдер
    const char* provider_str = (config->llm_provider == LLM_PROVIDER_OPENAI) ? "openai" : "anthropic";
    json_object_set_new(root, "llm_provider", json_string(provider_str));
    
    // API ключ
    if (config->api_key) {
        json_object_set_new(root, "api_key", json_string(config->api_key));
    }
    
    // Модель
    if (config->model) {
        json_object_set_new(root, "model", json_string(config->model));
    }
    
    // Base URL
    if (config->base_url) {
        json_object_set_new(root, "base_url", json_string(config->base_url));
    }
    
    // Timeout
    json_object_set_new(root, "timeout_ms", json_integer(config->timeout_ms));
    
    // Stream
    json_object_set_new(root, "stream", json_boolean(config->stream));
    
    // Max Tokens
    json_object_set_new(root, "max_tokens", json_integer(config->max_tokens));
    
    // Temperature
    json_object_set_new(root, "temperature", json_real(config->temperature));
    
    // Local Storage Path
    if (config->local_storage_path) {
        json_object_set_new(root, "local_storage_path", json_string(config->local_storage_path));
    }
    
    // Max Context Size
    json_object_set_new(root, "max_context_size", json_integer(config->max_context_size));
    
    // Max Response Tries
    json_object_set_new(root, "max_response_tries", json_integer(config->max_response_tries));
    
    // Cache Enabled
    json_object_set_new(root, "cache_enabled", json_boolean(config->cache_enabled));
    
    // Cache TTL
    json_object_set_new(root, "cache_ttl_seconds", json_integer(config->cache_ttl_seconds));
    
    // Secure Mode
    json_object_set_new(root, "secure_mode", json_boolean(config->secure_mode));
    
    // Log Level
    json_object_set_new(root, "log_level", json_integer(config->log_level));
    
    // Сохраняем в файл
    int ret = json_dump_file(root, filename, JSON_INDENT(4));
    json_decref(root);
    
    return (ret == 0) ? 0 : -1;
}

/**
 * @brief Установка API ключа в конфигурации
 * 
 * @param config Указатель на конфигурацию
 * @param api_key API ключ для установки
 * @return 0 при успехе, -1 при ошибке
 */
int codex_config_set_api_key(codex_config_t* config, const char* api_key) {
    if (!config) {
        return -1;
    }
    
    if (config->api_key) {
        free(config->api_key);
        config->api_key = NULL;
    }
    
    if (api_key) {
        config->api_key = strdup(api_key);
        if (!config->api_key) {
            return -1;
        }
    }
    
    return 0;
}

/**
 * @brief Установка модели в конфигурации
 * 
 * @param config Указатель на конфигурацию
 * @param model Модель для установки
 * @return 0 при успехе, -1 при ошибке
 */
int codex_config_set_model(codex_config_t* config, const char* model) {
    if (!config || !model) {
        return -1;
    }
    
    if (config->model) {
        free(config->model);
    }
    
    config->model = strdup(model);
    if (!config->model) {
        return -1;
    }
    
    return 0;
}

/**
 * @brief Установка базового URL в конфигурации
 * 
 * @param config Указатель на конфигурацию
 * @param base_url Базовый URL для установки
 * @return 0 при успехе, -1 при ошибке
 */
int codex_config_set_base_url(codex_config_t* config, const char* base_url) {
    if (!config) {
        return -1;
    }
    
    if (config->base_url) {
        free(config->base_url);
        config->base_url = NULL;
    }
    
    if (base_url) {
        config->base_url = strdup(base_url);
        if (!config->base_url) {
            return -1;
        }
    }
    
    return 0;
}

/**
 * @brief Установка пути локального хранилища в конфигурации
 * 
 * @param config Указатель на конфигурацию
 * @param path Путь для установки
 * @return 0 при успехе, -1 при ошибке
 */
int codex_config_set_local_storage_path(codex_config_t* config, const char* path) {
    if (!config || !path) {
        return -1;
    }
    
    if (config->local_storage_path) {
        free(config->local_storage_path);
    }
    
    config->local_storage_path = strdup(path);
    if (!config->local_storage_path) {
        return -1;
    }
    
    return 0;
}

/**
 * @brief Уничтожение конфигурации и освобождение ресурсов
 * 
 * @param config Указатель на конфигурацию
 */
void codex_config_destroy(codex_config_t* config) {
    if (!config) {
        return;
    }
    
    if (config->api_key) {
        free(config->api_key);
    }
    
    if (config->model) {
        free(config->model);
    }
    
    if (config->base_url) {
        free(config->base_url);
    }
    
    if (config->local_storage_path) {
        free(config->local_storage_path);
    }
    
    free(config);
} 