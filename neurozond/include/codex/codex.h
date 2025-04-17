/**
 * @file codex.h
 * @brief Основной интерфейс модуля Codex для NeuroZond
 * @author Team NeuroZond
 * @date 2023-09-06
 */

#ifndef NEUROZOND_CODEX_H
#define NEUROZOND_CODEX_H

#include <stdbool.h>
#include "codex/codex_config.h"

/**
 * @struct codex_context
 * @brief Контекст для работы с API LLM
 */
typedef struct codex_context codex_context_t;

/**
 * @struct codex_options
 * @brief Опции для отдельного запроса к LLM
 */
typedef struct {
    float temperature;    /**< Температура для генерации (от 0.0 до 2.0) */
    int max_tokens;       /**< Максимальное количество токенов в ответе */
    bool stream;          /**< Флаг потокового режима ответа */
} codex_options_t;

/**
 * @struct codex_response
 * @brief Структура, содержащая ответ от LLM
 */
typedef struct {
    char *text;           /**< Текстовый ответ */
    char *raw_json;       /**< Сырой JSON ответ */
    // Поля для метаданных ответа можно добавить позже
} codex_response_t;

/**
 * @brief Инициализирует контекст Codex с заданной конфигурацией
 * @param config Конфигурация (может быть NULL для использования по умолчанию)
 * @return Указатель на контекст или NULL в случае ошибки
 */
codex_context_t* codex_init(const codex_config_t *config);

/**
 * @brief Освобождает ресурсы, связанные с контекстом Codex
 * @param ctx Контекст для освобождения
 */
void codex_destroy(codex_context_t *ctx);

/**
 * @brief Получает текст последней ошибки
 * @param ctx Контекст Codex
 * @return Строка, содержащая описание последней ошибки
 */
const char* codex_get_last_error(const codex_context_t *ctx);

/**
 * @brief Отправляет запрос к API LLM
 * @param ctx Контекст Codex
 * @param prompt Запрос пользователя
 * @param options Опции запроса (может быть NULL для использования по умолчанию)
 * @return Структура ответа или NULL в случае ошибки
 */
codex_response_t* codex_query(codex_context_t *ctx, const char *prompt, const codex_options_t *options);

/**
 * @brief Освобождает ресурсы, связанные с ответом
 * @param response Структура ответа для освобождения
 */
void codex_free_response(codex_response_t *response);

/**
 * @brief Устанавливает новую конфигурацию для контекста
 * @param ctx Контекст Codex
 * @param config Новая конфигурация
 * @return 0 в случае успеха, -1 в случае ошибки
 */
int codex_set_config(codex_context_t *ctx, const codex_config_t *config);

/**
 * @brief Получает текущую конфигурацию контекста
 * @param ctx Контекст Codex
 * @return Указатель на конфигурацию
 */
const codex_config_t* codex_get_config(const codex_context_t *ctx);

/**
 * @brief Очищает кэш ответов
 * @param ctx Контекст Codex
 */
void codex_clear_cache(codex_context_t *ctx);

#endif /* NEUROZOND_CODEX_H */ 