/**
 * @file test_codex_module.c
 * @brief Тестирование модуля Codex для NeuroZond
 * @author Team NeuroZond
 * @date 2023-09-06
 */

#include "../include/codex/codex_module.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/**
 * @brief Тестирование создания и инициализации модуля Codex
 */
void test_codex_module_create_init() {
    printf("Тест: Создание и инициализация модуля Codex... ");
    
    // Создание модуля
    codex_module_t *module = codex_module_create();
    assert(module != NULL && "Не удалось создать модуль Codex");
    
    // Инициализация с базовыми опциями
    codex_options_t options = {
        .working_directory = "/tmp",
        .target_repository = NULL,
        .allow_network = true,
        .encrypt_temp_files = false,
        .api_key = NULL, // Мы не используем реальный API ключ для тестов
        .model = NULL
    };
    
    codex_status_t status = codex_module_init(module, &options);
    assert(status == CODEX_STATUS_SUCCESS && "Ошибка инициализации модуля Codex");
    
    // Проверка версии
    const char *version = codex_module_get_version();
    assert(version != NULL && strlen(version) > 0 && "Ошибка получения версии");
    
    // Очистка
    codex_module_destroy(module);
    
    printf("OK\n");
}

/**
 * @brief Тестирование создания команды Codex для анализа файла
 */
void test_codex_command_create_analyze() {
    printf("Тест: Создание команды для анализа файла... ");
    
    const char *file_path = "/tmp/test.c";
    const char *prompt = "Найти уязвимости в коде";
    
    codex_command_t *command = codex_command_create_analyze(file_path, prompt);
    assert(command != NULL && "Не удалось создать команду");
    assert(command->type == CODEX_COMMAND_ANALYZE && "Неверный тип команды");
    assert(command->target_file != NULL && strcmp(command->target_file, file_path) == 0 && 
           "Неверный целевой файл");
    assert(command->content != NULL && strcmp(command->content, prompt) == 0 && 
           "Неверный текст команды");
    
    codex_command_destroy(command);
    
    printf("OK\n");
}

/**
 * @brief Тестирование создания команды Codex для модификации файла
 */
void test_codex_command_create_modify() {
    printf("Тест: Создание команды для модификации файла... ");
    
    const char *file_path = "/tmp/test.c";
    const char *instructions = "Исправить уязвимость переполнения буфера в функции read_input()";
    
    codex_command_t *command = codex_command_create_modify(file_path, instructions);
    assert(command != NULL && "Не удалось создать команду");
    assert(command->type == CODEX_COMMAND_MODIFY && "Неверный тип команды");
    assert(command->target_file != NULL && strcmp(command->target_file, file_path) == 0 && 
           "Неверный целевой файл");
    assert(command->content != NULL && strcmp(command->content, instructions) == 0 && 
           "Неверные инструкции");
    
    codex_command_destroy(command);
    
    printf("OK\n");
}

/**
 * @brief Тестирование создания команды Codex для выполнения команды
 */
void test_codex_command_create_execute() {
    printf("Тест: Создание команды для выполнения... ");
    
    const char *shell_command = "gcc -Wall -o test /tmp/test.c";
    
    codex_command_t *command = codex_command_create_execute(shell_command);
    assert(command != NULL && "Не удалось создать команду");
    assert(command->type == CODEX_COMMAND_EXECUTE && "Неверный тип команды");
    assert(command->content != NULL && strcmp(command->content, shell_command) == 0 && 
           "Неверная команда");
    
    codex_command_destroy(command);
    
    printf("OK\n");
}

/**
 * @brief Тестирование создания команды Codex для запроса к LLM
 */
void test_codex_command_create_ask() {
    printf("Тест: Создание команды для запроса к LLM... ");
    
    const char *prompt = "Как найти уязвимости переполнения буфера в C коде?";
    
    codex_command_t *command = codex_command_create_ask(prompt);
    assert(command != NULL && "Не удалось создать команду");
    assert(command->type == CODEX_COMMAND_ASK && "Неверный тип команды");
    assert(command->content != NULL && strcmp(command->content, prompt) == 0 && 
           "Неверный текст запроса");
    
    codex_command_destroy(command);
    
    printf("OK\n");
}

/**
 * @brief Тестирование создания команды Codex для операции с проектом
 */
void test_codex_command_create_project() {
    printf("Тест: Создание команды для операции с проектом... ");
    
    const char *operation = "clone";
    const char *args[] = {"https://github.com/example/repo.git", "/tmp/repo"};
    size_t args_count = 2;
    
    codex_command_t *command = codex_command_create_project(operation, args, args_count);
    assert(command != NULL && "Не удалось создать команду");
    assert(command->type == CODEX_COMMAND_PROJECT && "Неверный тип команды");
    assert(command->content != NULL && strcmp(command->content, operation) == 0 && 
           "Неверная операция");
    assert(command->args != NULL && command->args_count == args_count && 
           "Неверные аргументы");
    
    for (size_t i = 0; i < args_count; i++) {
        assert(command->args[i] != NULL && strcmp(command->args[i], args[i]) == 0 && 
               "Неверный аргумент");
    }
    
    codex_command_destroy(command);
    
    printf("OK\n");
}

/**
 * @brief Тестирование создания команды Codex для поиска/эксплуатации уязвимости
 */
void test_codex_command_create_exploit() {
    printf("Тест: Создание команды для поиска/эксплуатации уязвимости... ");
    
    const char *target = "/tmp/test.c";
    const char *type = "buffer-overflow";
    
    codex_command_t *command = codex_command_create_exploit(target, type);
    assert(command != NULL && "Не удалось создать команду");
    assert(command->type == CODEX_COMMAND_EXPLOIT && "Неверный тип команды");
    assert(command->target_file != NULL && strcmp(command->target_file, target) == 0 && 
           "Неверный целевой файл");
    assert(command->args != NULL && command->args_count == 1 && 
           "Неверные аргументы");
    assert(command->args[0] != NULL && strcmp(command->args[0], type) == 0 && 
           "Неверный тип уязвимости");
    
    codex_command_destroy(command);
    
    printf("OK\n");
}

/**
 * @brief Тестирование обработки команды в модуле Codex
 */
void test_codex_module_handle_command() {
    printf("Тест: Обработка команды в модуле Codex... ");
    
    // Создание и инициализация модуля
    codex_module_t *module = codex_module_create();
    assert(module != NULL && "Не удалось создать модуль Codex");
    
    codex_options_t options = {
        .working_directory = "/tmp",
        .target_repository = NULL,
        .allow_network = true,
        .encrypt_temp_files = false,
        .api_key = NULL,
        .model = NULL
    };
    
    codex_status_t status = codex_module_init(module, &options);
    assert(status == CODEX_STATUS_SUCCESS && "Ошибка инициализации модуля Codex");
    
    // Создание команды для анализа
    const char *file_path = "/tmp/test.c";
    const char *prompt = "Найти уязвимости в коде";
    
    codex_command_t *command = codex_command_create_analyze(file_path, prompt);
    assert(command != NULL && "Не удалось создать команду");
    
    // Обработка команды
    codex_result_t *result = NULL;
    status = codex_module_handle_command(module, command, &result);
    
    // В текущей реализации с заглушками должен быть успех
    assert(status == CODEX_STATUS_SUCCESS && "Ошибка обработки команды");
    assert(result != NULL && "Не получен результат");
    assert(result->content != NULL && "Пустой результат");
    
    // Очистка
    codex_result_destroy(result);
    codex_command_destroy(command);
    codex_module_destroy(module);
    
    printf("OK\n");
}

/**
 * @brief Тестирование регистрации возможностей в C1
 */
void test_codex_module_register_capabilities() {
    printf("Тест: Регистрация возможностей в C1... ");
    
    // Создание и инициализация модуля
    codex_module_t *module = codex_module_create();
    assert(module != NULL && "Не удалось создать модуль Codex");
    
    codex_options_t options = {
        .working_directory = "/tmp",
        .target_repository = NULL,
        .allow_network = true,
        .encrypt_temp_files = false,
        .api_key = NULL,
        .model = NULL
    };
    
    codex_status_t status = codex_module_init(module, &options);
    assert(status == CODEX_STATUS_SUCCESS && "Ошибка инициализации модуля Codex");
    
    // Регистрация возможностей
    status = codex_module_register_capabilities(module);
    assert(status == CODEX_STATUS_SUCCESS && "Ошибка регистрации возможностей");
    
    // Очистка
    codex_module_destroy(module);
    
    printf("OK\n");
}

/**
 * @brief Точка входа
 */
int main() {
    printf("Запуск тестов модуля Codex...\n");
    
    test_codex_module_create_init();
    test_codex_command_create_analyze();
    test_codex_command_create_modify();
    test_codex_command_create_execute();
    test_codex_command_create_ask();
    test_codex_command_create_project();
    test_codex_command_create_exploit();
    test_codex_module_handle_command();
    test_codex_module_register_capabilities();
    
    printf("Все тесты успешно пройдены!\n");
    return 0;
} 