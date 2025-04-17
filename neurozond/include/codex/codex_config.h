/**
 * @file codex_config.h
 * @brief Файл конфигурации для модуля Codex
 * @author Team NeuroZond
 * @date 2023-09-06
 */

#ifndef NEUROZOND_CODEX_CONFIG_H
#define NEUROZOND_CODEX_CONFIG_H

/**
 * @enum codex_provider
 * @brief Поддерживаемые провайдеры LLM
 */
typedef enum {
    CODEX_PROVIDER_OPENAI,    /**< OpenAI API (ChatGPT) */
    CODEX_PROVIDER_ANTHROPIC, /**< Anthropic API (Claude) */
    CODEX_PROVIDER_CUSTOM     /**< Кастомный провайдер */
} codex_provider_t;

/**
 * @struct codex_config
 * @brief Структура конфигурации Codex
 */
typedef struct {
    /* Основные настройки */
    codex_provider_t provider;     /**< Используемый провайдер */
    char *api_key;                 /**< API ключ для провайдера */
    char *api_url;                 /**< URL базового API эндпоинта */
    
    /* Настройки модели */
    char *model;                   /**< Название модели для использования */
    float default_temperature;     /**< Температура по умолчанию (от 0.0 до 2.0) */
    int default_max_tokens;        /**< Макс. количество токенов по умолчанию */
    
    /* Настройки запросов */
    int timeout_ms;                /**< Таймаут запроса в миллисекундах */
    int max_retries;               /**< Максимальное количество попыток при ошибке */
    int retry_delay_ms;            /**< Задержка между повторными попытками */
    
    /* Настройки кэширования */
    bool enable_cache;             /**< Флаг включения кэширования */
    int cache_max_size;            /**< Максимальный размер кэша в элементах */
    int cache_ttl;                 /**< Время жизни элемента кэша в секундах */
    
    /* Параметры прокси */
    char *proxy_url;               /**< URL прокси-сервера (NULL если не используется) */
    char *proxy_user;              /**< Имя пользователя для прокси */
    char *proxy_pass;              /**< Пароль для прокси */
    
    /* Функции для кастомных провайдеров */
    void *custom_data;             /**< Пользовательские данные для кастомного провайдера */
} codex_config_t;

/**
 * @brief Создает конфигурацию с параметрами по умолчанию
 * @return Структура конфигурации по умолчанию
 */
codex_config_t codex_create_default_config(void);

/**
 * @brief Освобождает ресурсы, связанные с конфигурацией
 * @param config Конфигурация для освобождения
 */
void codex_free_config(codex_config_t *config);

/**
 * @brief Создает копию конфигурации
 * @param config Конфигурация для копирования
 * @return Копия конфигурации
 */
codex_config_t codex_copy_config(const codex_config_t *config);

/**
 * @brief Загружает конфигурацию из файла
 * @param filename Путь к файлу конфигурации
 * @param[out] config Указатель для сохранения загруженной конфигурации
 * @return 0 при успехе, -1 при ошибке
 */
int codex_load_config_from_file(const char *filename, codex_config_t *config);

/**
 * @brief Сохраняет конфигурацию в файл
 * @param filename Путь к файлу конфигурации
 * @param config Конфигурация для сохранения
 * @return 0 при успехе, -1 при ошибке
 */
int codex_save_config_to_file(const char *filename, const codex_config_t *config);

#endif /* NEUROZOND_CODEX_CONFIG_H */ 