/**
 * @file test_llm_proxy.c
 * @brief Тестирование LLM прокси для модуля Codex в NeuroZond
 * @author Team NeuroZond
 * @date 2023-09-06
 */

#include "../include/codex/llm_proxy.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/**
 * @brief Тестирование создания и уничтожения LLM прокси
 */
void test_llm_proxy_create_destroy() {
    printf("Тест: Создание и уничтожение LLM прокси... ");
    
    // Создание с прямым режимом
    llm_proxy_options_t options_direct = {
        .mode = LLM_PROXY_MODE_DIRECT,
        .provider = LLM_PROVIDER_OPENAI,
        .api_key = "test_key",
        .model = "gpt-3.5-turbo",
        .base_url = NULL,
        .timeout_ms = 5000,
        .stream = false,
        .c1_connector = NULL
    };
    
    llm_proxy_t *proxy_direct = llm_proxy_create(&options_direct);
    assert(proxy_direct != NULL && "Не удалось создать прокси в прямом режиме");
    
    // Уничтожение прокси
    llm_proxy_destroy(proxy_direct);
    
    // Создание с режимом C1
    llm_proxy_options_t options_c1 = {
        .mode = LLM_PROXY_MODE_C1,
        .provider = LLM_PROVIDER_OPENAI,
        .api_key = NULL,
        .model = "gpt-3.5-turbo",
        .base_url = NULL,
        .timeout_ms = 5000,
        .stream = false,
        .c1_connector = (void*)0x12345678 // Фиктивный указатель, просто для теста
    };
    
    llm_proxy_t *proxy_c1 = llm_proxy_create(&options_c1);
    assert(proxy_c1 != NULL && "Не удалось создать прокси в режиме C1");
    
    // Уничтожение прокси
    llm_proxy_destroy(proxy_c1);
    
    printf("OK\n");
}

/**
 * @brief Тестирование создания и освобождения результата LLM запроса
 */
void test_llm_proxy_result() {
    printf("Тест: Создание и освобождение результата LLM запроса... ");
    
    // Эта функция не доступна напрямую, так что нам нужно использовать другие функции, 
    // которые создают и возвращают результат
    
    // Создание прокси
    llm_proxy_options_t options = {
        .mode = LLM_PROXY_MODE_DIRECT,
        .provider = LLM_PROVIDER_OPENAI,
        .api_key = "test_key", // Не настоящий ключ
        .model = "gpt-3.5-turbo",
        .base_url = NULL,
        .timeout_ms = 5000,
        .stream = false,
        .c1_connector = NULL
    };
    
    llm_proxy_t *proxy = llm_proxy_create(&options);
    assert(proxy != NULL && "Не удалось создать прокси");
    
    // Отправка сообщения (должна вернуть ошибку из-за неверного ключа API, но результат должен быть создан)
    llm_proxy_result_t *result = NULL;
    llm_proxy_status_t status = llm_proxy_send_message(proxy, "Тестовое сообщение", &result);
    
    // В этом случае status может быть ошибкой из-за недействительного ключа API,
    // но result не должен быть NULL, он должен содержать информацию об ошибке
    if (result != NULL) {
        llm_proxy_result_destroy(result);
    }
    
    // Уничтожение прокси
    llm_proxy_destroy(proxy);
    
    printf("OK\n");
}

/**
 * @brief Тестирование получения последней ошибки
 */
void test_llm_proxy_get_last_error() {
    printf("Тест: Получение последней ошибки... ");
    
    // Создание прокси
    llm_proxy_options_t options = {
        .mode = LLM_PROXY_MODE_DIRECT,
        .provider = LLM_PROVIDER_OPENAI,
        .api_key = "test_key", // Не настоящий ключ
        .model = "gpt-3.5-turbo",
        .base_url = NULL,
        .timeout_ms = 5000,
        .stream = false,
        .c1_connector = NULL
    };
    
    llm_proxy_t *proxy = llm_proxy_create(&options);
    assert(proxy != NULL && "Не удалось создать прокси");
    
    // Отправка сообщения (должна вернуть ошибку из-за неверного ключа API)
    llm_proxy_result_t *result = NULL;
    llm_proxy_status_t status = llm_proxy_send_message(proxy, "Тестовое сообщение", &result);
    
    // Должна быть установлена ошибка
    const char *error = llm_proxy_get_last_error(proxy);
    assert(error != NULL && "Не удалось получить последнюю ошибку");
    
    // Очистка
    if (result != NULL) {
        llm_proxy_result_destroy(result);
    }
    
    llm_proxy_destroy(proxy);
    
    printf("OK\n");
}

/**
 * @brief Тестирование отправки кода с контекстом
 */
void test_llm_proxy_send_code_context() {
    printf("Тест: Отправка кода с контекстом... ");
    
    // Создание прокси
    llm_proxy_options_t options = {
        .mode = LLM_PROXY_MODE_DIRECT,
        .provider = LLM_PROVIDER_OPENAI,
        .api_key = "test_key", // Не настоящий ключ
        .model = "gpt-3.5-turbo",
        .base_url = NULL,
        .timeout_ms = 5000,
        .stream = false,
        .c1_connector = NULL
    };
    
    llm_proxy_t *proxy = llm_proxy_create(&options);
    assert(proxy != NULL && "Не удалось создать прокси");
    
    // Пример кода и вопроса
    const char *code = "int main() {\n    printf(\"Hello, world!\\n\");\n    return 0;\n}";
    const char *question = "Объясни, что делает этот код?";
    
    // Отправка кода с контекстом
    llm_proxy_result_t *result = NULL;
    llm_proxy_status_t status = llm_proxy_send_code_context(proxy, code, question, &result);
    
    // Очистка
    if (result != NULL) {
        llm_proxy_result_destroy(result);
    }
    
    llm_proxy_destroy(proxy);
    
    printf("OK\n");
}

/**
 * @brief Тестирование работы с другим провайдером (Anthropic)
 */
void test_llm_proxy_anthropic() {
    printf("Тест: Работа с провайдером Anthropic... ");
    
    // Создание прокси
    llm_proxy_options_t options = {
        .mode = LLM_PROXY_MODE_DIRECT,
        .provider = LLM_PROVIDER_ANTHROPIC,
        .api_key = "test_key", // Не настоящий ключ
        .model = "claude-2",
        .base_url = NULL,
        .timeout_ms = 5000,
        .stream = false,
        .c1_connector = NULL
    };
    
    llm_proxy_t *proxy = llm_proxy_create(&options);
    assert(proxy != NULL && "Не удалось создать прокси");
    
    // Отправка сообщения
    llm_proxy_result_t *result = NULL;
    llm_proxy_status_t status = llm_proxy_send_message(proxy, "Тестовое сообщение", &result);
    
    // Очистка
    if (result != NULL) {
        llm_proxy_result_destroy(result);
    }
    
    llm_proxy_destroy(proxy);
    
    printf("OK\n");
}

/**
 * @brief Тестирование работы в режиме C1
 */
void test_llm_proxy_c1_mode() {
    printf("Тест: Работа в режиме C1... ");
    
    // Создание прокси
    llm_proxy_options_t options = {
        .mode = LLM_PROXY_MODE_C1,
        .provider = LLM_PROVIDER_OPENAI,
        .api_key = NULL,
        .model = "gpt-3.5-turbo",
        .base_url = NULL,
        .timeout_ms = 5000,
        .stream = false,
        .c1_connector = (void*)0x12345678 // Фиктивный указатель, просто для теста
    };
    
    llm_proxy_t *proxy = llm_proxy_create(&options);
    assert(proxy != NULL && "Не удалось создать прокси");
    
    // Отправка сообщения
    llm_proxy_result_t *result = NULL;
    llm_proxy_status_t status = llm_proxy_send_message(proxy, "Тестовое сообщение", &result);
    
    // Должен быть создан результат, даже если это заглушка
    assert(result != NULL && "Не удалось получить результат");
    
    // Очистка
    llm_proxy_result_destroy(result);
    llm_proxy_destroy(proxy);
    
    printf("OK\n");
}

/**
 * @brief Точка входа
 */
int main() {
    printf("Запуск тестов LLM прокси...\n");
    
    test_llm_proxy_create_destroy();
    test_llm_proxy_result();
    test_llm_proxy_get_last_error();
    test_llm_proxy_send_code_context();
    test_llm_proxy_anthropic();
    test_llm_proxy_c1_mode();
    
    printf("Все тесты успешно пройдены!\n");
    return 0;
} 