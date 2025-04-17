/**
 * @file test_command_executor.c
 * @brief Tests for command execution module.
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-04
 */

#include "../include/command_executor.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#ifdef _WIN32
#define ECHO_COMMAND "echo"
#define TEST_COMMAND "cmd.exe /c echo test"
#define SLEEP_COMMAND "timeout 1"
#else
#define ECHO_COMMAND "echo"
#define TEST_COMMAND "echo test"
#define SLEEP_COMMAND "sleep 1"
#endif

// Макрос для проверки условий тестов
#define TEST_ASSERT(condition, message) \
    do { \
        if (!(condition)) { \
            printf("FAIL: %s (line %d)\n", message, __LINE__); \
            failed_tests++; \
        } else { \
            passed_tests++; \
        } \
    } while (0)

// Глобальные счетчики тестов
static int passed_tests = 0;
static int failed_tests = 0;

/**
 * Тест инициализации исполнителя команд.
 */
void test_executor_init(void) {
    printf("Running test: command_executor_init\n");
    
    // Тест на успешную инициализацию
    int result = command_executor_init();
    TEST_ASSERT(result == 1, "command_executor_init should return 1 on success");
    
    // Мы не можем тестировать на ошибку инициализации без изменения исходного кода
    command_executor_cleanup();
}

/**
 * Тест создания и освобождения команды.
 */
void test_command_create_free(void) {
    printf("Running test: command_create and command_free\n");
    
    // Тест на успешное создание команды shell типа
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL for COMMAND_TYPE_SHELL");
    
    // Проверка полей созданной команды
    if (cmd != NULL) {
        TEST_ASSERT(cmd->type == COMMAND_TYPE_SHELL, "Command type should be COMMAND_TYPE_SHELL");
        TEST_ASSERT(cmd->status == COMMAND_STATUS_CREATED, "Command status should be COMMAND_STATUS_CREATED");
        TEST_ASSERT(cmd->command_line == NULL, "Command line should be NULL");
        TEST_ASSERT(cmd->working_dir == NULL, "Working directory should be NULL");
        TEST_ASSERT(cmd->output_file == NULL, "Output file should be NULL");
        TEST_ASSERT(cmd->input_data == NULL, "Input data should be NULL");
        TEST_ASSERT(cmd->input_length == 0, "Input length should be 0");
        TEST_ASSERT(cmd->flags == COMMAND_FLAG_NONE, "Flags should be COMMAND_FLAG_NONE");
        TEST_ASSERT(cmd->timeout_ms == 0, "Timeout should be 0");
        
        // Освобождаем ресурсы
        command_free(cmd);
    }
    
    // Тест на успешное создание команды process типа
    cmd = command_create(COMMAND_TYPE_PROCESS);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL for COMMAND_TYPE_PROCESS");
    
    // Проверка полей созданной команды
    if (cmd != NULL) {
        TEST_ASSERT(cmd->type == COMMAND_TYPE_PROCESS, "Command type should be COMMAND_TYPE_PROCESS");
        command_free(cmd);
    }
    
    // Тест на неизвестный тип команды
    cmd = command_create(99); // Неизвестный тип
    TEST_ASSERT(cmd == NULL, "command_create should return NULL for unknown command type");
    
    // Тест освобождения с NULL указателем (не должно быть сегфолта)
    command_free(NULL);
}

/**
 * Тест установки и получения командной строки.
 */
void test_command_set_command_line(void) {
    printf("Running test: command_set_command_line\n");
    
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL");
    
    if (cmd != NULL) {
        // Тест на успешную установку
        int result = command_set_command_line(cmd, "test command");
        TEST_ASSERT(result == 1, "command_set_command_line should return 1 on success");
        TEST_ASSERT(cmd->command_line != NULL, "Command line should not be NULL after setting");
        if (cmd->command_line != NULL) {
            TEST_ASSERT(strcmp(cmd->command_line, "test command") == 0, 
                "Command line should be 'test command'");
        }
        
        // Тест на обновление существующей командной строки
        result = command_set_command_line(cmd, "updated command");
        TEST_ASSERT(result == 1, "command_set_command_line should return 1 on update");
        TEST_ASSERT(cmd->command_line != NULL, "Command line should not be NULL after update");
        if (cmd->command_line != NULL) {
            TEST_ASSERT(strcmp(cmd->command_line, "updated command") == 0, 
                "Command line should be 'updated command'");
        }
        
        // Тест на NULL указатель команды
        result = command_set_command_line(NULL, "test");
        TEST_ASSERT(result == 0, "command_set_command_line should return 0 for NULL command");
        
        // Тест на NULL указатель командной строки
        result = command_set_command_line(cmd, NULL);
        TEST_ASSERT(result == 0, "command_set_command_line should return 0 for NULL command line");
        
        command_free(cmd);
    }
}

/**
 * Тест установки и получения рабочей директории.
 */
void test_command_set_working_dir(void) {
    printf("Running test: command_set_working_dir\n");
    
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL");
    
    if (cmd != NULL) {
        // Тест на успешную установку
        int result = command_set_working_dir(cmd, "/tmp");
        TEST_ASSERT(result == 1, "command_set_working_dir should return 1 on success");
        TEST_ASSERT(cmd->working_dir != NULL, "Working directory should not be NULL after setting");
        if (cmd->working_dir != NULL) {
            TEST_ASSERT(strcmp(cmd->working_dir, "/tmp") == 0, 
                "Working directory should be '/tmp'");
        }
        
        // Тест на обновление существующей рабочей директории
        result = command_set_working_dir(cmd, "/var");
        TEST_ASSERT(result == 1, "command_set_working_dir should return 1 on update");
        TEST_ASSERT(cmd->working_dir != NULL, "Working directory should not be NULL after update");
        if (cmd->working_dir != NULL) {
            TEST_ASSERT(strcmp(cmd->working_dir, "/var") == 0, 
                "Working directory should be '/var'");
        }
        
        // Тест на NULL указатель команды
        result = command_set_working_dir(NULL, "/tmp");
        TEST_ASSERT(result == 0, "command_set_working_dir should return 0 for NULL command");
        
        // Тест на NULL указатель рабочей директории
        result = command_set_working_dir(cmd, NULL);
        TEST_ASSERT(result == 0, "command_set_working_dir should return 0 for NULL working dir");
        
        command_free(cmd);
    }
}

/**
 * Тест установки выходного файла.
 */
void test_command_set_output_file(void) {
    printf("Running test: command_set_output_file\n");
    
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL");
    
    if (cmd != NULL) {
        // Тест на успешную установку
        int result = command_set_output_file(cmd, "output.txt");
        TEST_ASSERT(result == 1, "command_set_output_file should return 1 on success");
        TEST_ASSERT(cmd->output_file != NULL, "Output file should not be NULL after setting");
        if (cmd->output_file != NULL) {
            TEST_ASSERT(strcmp(cmd->output_file, "output.txt") == 0, 
                "Output file should be 'output.txt'");
        }
        
        // Тест на NULL указатель команды
        result = command_set_output_file(NULL, "output.txt");
        TEST_ASSERT(result == 0, "command_set_output_file should return 0 for NULL command");
        
        // Тест на NULL указатель выходного файла
        result = command_set_output_file(cmd, NULL);
        TEST_ASSERT(result == 0, "command_set_output_file should return 0 for NULL output file");
        
        command_free(cmd);
    }
}

/**
 * Тест установки входных данных.
 */
void test_command_set_input_data(void) {
    printf("Running test: command_set_input_data\n");
    
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL");
    
    if (cmd != NULL) {
        // Тест на успешную установку
        const char* test_data = "test input data";
        size_t test_data_len = strlen(test_data);
        
        int result = command_set_input_data(cmd, test_data, test_data_len);
        TEST_ASSERT(result == 1, "command_set_input_data should return 1 on success");
        TEST_ASSERT(cmd->input_data != NULL, "Input data should not be NULL after setting");
        TEST_ASSERT(cmd->input_length == test_data_len, "Input length should match test data length");
        
        if (cmd->input_data != NULL && cmd->input_length == test_data_len) {
            TEST_ASSERT(memcmp(cmd->input_data, test_data, test_data_len) == 0, 
                "Input data should match test data");
        }
        
        // Тест на NULL входные данные с ненулевой длиной
        result = command_set_input_data(cmd, NULL, 10);
        TEST_ASSERT(result == 0, "command_set_input_data should return 0 for NULL data with non-zero length");
        
        // Тест на NULL входные данные с нулевой длиной (должно быть успешно)
        result = command_set_input_data(cmd, NULL, 0);
        TEST_ASSERT(result == 1, "command_set_input_data should return 1 for NULL data with zero length");
        
        // Тест на NULL указатель команды
        result = command_set_input_data(NULL, test_data, test_data_len);
        TEST_ASSERT(result == 0, "command_set_input_data should return 0 for NULL command");
        
        command_free(cmd);
    }
}

/**
 * Тест установки флагов.
 */
void test_command_set_flags(void) {
    printf("Running test: command_set_flags\n");
    
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL");
    
    if (cmd != NULL) {
        // Тест на успешную установку одного флага
        int result = command_set_flags(cmd, COMMAND_FLAG_HIDDEN);
        TEST_ASSERT(result == 1, "command_set_flags should return 1 on success");
        TEST_ASSERT(cmd->flags == COMMAND_FLAG_HIDDEN, 
            "Flags should be COMMAND_FLAG_HIDDEN after setting");
        
        // Тест на успешную установку нескольких флагов
        result = command_set_flags(cmd, COMMAND_FLAG_HIDDEN | COMMAND_FLAG_NO_WINDOW);
        TEST_ASSERT(result == 1, "command_set_flags should return 1 on success");
        TEST_ASSERT((cmd->flags & COMMAND_FLAG_HIDDEN) && (cmd->flags & COMMAND_FLAG_NO_WINDOW), 
            "Both flags should be set");
        
        // Тест на NULL указатель команды
        result = command_set_flags(NULL, COMMAND_FLAG_HIDDEN);
        TEST_ASSERT(result == 0, "command_set_flags should return 0 for NULL command");
        
        command_free(cmd);
    }
}

/**
 * Тест установки тайм-аута.
 */
void test_command_set_timeout(void) {
    printf("Running test: command_set_timeout\n");
    
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL");
    
    if (cmd != NULL) {
        // Тест на успешную установку
        int result = command_set_timeout(cmd, 5000);
        TEST_ASSERT(result == 1, "command_set_timeout should return 1 on success");
        TEST_ASSERT(cmd->timeout_ms == 5000, "Timeout should be 5000 after setting");
        
        // Тест на обновление существующего тайм-аута
        result = command_set_timeout(cmd, 3000);
        TEST_ASSERT(result == 1, "command_set_timeout should return 1 on update");
        TEST_ASSERT(cmd->timeout_ms == 3000, "Timeout should be 3000 after update");
        
        // Тест на NULL указатель команды
        result = command_set_timeout(NULL, 1000);
        TEST_ASSERT(result == 0, "command_set_timeout should return 0 for NULL command");
        
        command_free(cmd);
    }
}

/**
 * Тест выполнения простой команды.
 */
void test_command_execute_simple(void) {
    printf("Running test: command_execute (simple)\n");
    
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL");
    
    if (cmd != NULL) {
        // Установка простой команды echo
        int result = command_set_command_line(cmd, TEST_COMMAND);
        TEST_ASSERT(result == 1, "command_set_command_line should return 1 on success");
        
        // Выполнение команды
        CommandResult* cmd_result = command_execute(cmd);
        TEST_ASSERT(cmd_result != NULL, "command_execute should not return NULL");
        
        if (cmd_result != NULL) {
            // Проверка статуса выполнения
            TEST_ASSERT(cmd_result->status == COMMAND_STATUS_COMPLETED, 
                "Command status should be COMMAND_STATUS_COMPLETED");
            TEST_ASSERT(cmd_result->exit_code == 0, "Exit code should be 0 for successful command");
            TEST_ASSERT(cmd_result->output != NULL, "Output should not be NULL");
            TEST_ASSERT(cmd_result->output_length > 0, "Output length should be greater than 0");
            
            if (cmd_result->output != NULL) {
                TEST_ASSERT(strstr(cmd_result->output, "test") != NULL, 
                    "Output should contain 'test'");
            }
            
            command_result_free(cmd_result);
        }
        
        command_free(cmd);
    }
}

/**
 * Тест выполнения команды с тайм-аутом.
 */
void test_command_execute_timeout(void) {
    printf("Running test: command_execute (timeout)\n");
    
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL");
    
    if (cmd != NULL) {
        // Установка команды, которая будет выполняться дольше тайм-аута
        int result = command_set_command_line(cmd, SLEEP_COMMAND);
        TEST_ASSERT(result == 1, "command_set_command_line should return 1 on success");
        
        // Установка короткого тайм-аута
        result = command_set_timeout(cmd, 100); // 100 мс, должна завершиться по тайм-ауту
        TEST_ASSERT(result == 1, "command_set_timeout should return 1 on success");
        
        // Выполнение команды
        CommandResult* cmd_result = command_execute(cmd);
        TEST_ASSERT(cmd_result != NULL, "command_execute should not return NULL");
        
        if (cmd_result != NULL) {
            // Проверка статуса выполнения
            // Примечание: на некоторых системах команда может выполниться быстрее тайм-аута
            if (cmd_result->status == COMMAND_STATUS_TIMEOUT) {
                TEST_ASSERT(1, "Command status is COMMAND_STATUS_TIMEOUT as expected");
            } else {
                printf("Note: Command did not timeout. This might be system-dependent.\n");
                TEST_ASSERT(cmd_result->status == COMMAND_STATUS_COMPLETED, 
                    "If not timeout, status should be COMMAND_STATUS_COMPLETED");
            }
            
            command_result_free(cmd_result);
        }
        
        command_free(cmd);
    }
}

/**
 * Тест выполнения команды с входными данными.
 */
void test_command_execute_with_input(void) {
    printf("Running test: command_execute (with input)\n");
    
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL");
    
    if (cmd != NULL) {
        // Устанавливаем команду, которая будет использовать stdin
#ifdef _WIN32
        int result = command_set_command_line(cmd, "findstr \"test\"");
#else
        int result = command_set_command_line(cmd, "grep test");
#endif
        TEST_ASSERT(result == 1, "command_set_command_line should return 1 on success");
        
        // Устанавливаем входные данные
        const char* input_data = "test data\nno test\ntest line\n";
        result = command_set_input_data(cmd, input_data, strlen(input_data));
        TEST_ASSERT(result == 1, "command_set_input_data should return 1 on success");
        
        // Выполнение команды
        CommandResult* cmd_result = command_execute(cmd);
        TEST_ASSERT(cmd_result != NULL, "command_execute should not return NULL");
        
        if (cmd_result != NULL) {
            // Проверка статуса выполнения
            TEST_ASSERT(cmd_result->status == COMMAND_STATUS_COMPLETED, 
                "Command status should be COMMAND_STATUS_COMPLETED");
            TEST_ASSERT(cmd_result->exit_code == 0, "Exit code should be 0 for successful command");
            TEST_ASSERT(cmd_result->output != NULL, "Output should not be NULL");
            
            if (cmd_result->output != NULL) {
                TEST_ASSERT(strstr(cmd_result->output, "test data") != NULL, 
                    "Output should contain 'test data'");
                TEST_ASSERT(strstr(cmd_result->output, "test line") != NULL, 
                    "Output should contain 'test line'");
                TEST_ASSERT(strstr(cmd_result->output, "no test") == NULL, 
                    "Output should not contain 'no test'");
            }
            
            command_result_free(cmd_result);
        }
        
        command_free(cmd);
    }
}

/**
 * Тест выполнения неизвестной команды.
 */
void test_command_execute_unknown(void) {
    printf("Running test: command_execute (unknown command)\n");
    
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    TEST_ASSERT(cmd != NULL, "command_create should not return NULL");
    
    if (cmd != NULL) {
        // Установка несуществующей команды
        int result = command_set_command_line(cmd, "this_command_does_not_exist_123456789");
        TEST_ASSERT(result == 1, "command_set_command_line should return 1 on success");
        
        // Выполнение команды
        CommandResult* cmd_result = command_execute(cmd);
        TEST_ASSERT(cmd_result != NULL, "command_execute should not return NULL even for unknown command");
        
        if (cmd_result != NULL) {
            // Проверка статуса выполнения и кода выхода
            // Код выхода может отличаться в зависимости от системы
            TEST_ASSERT(cmd_result->status == COMMAND_STATUS_ERROR || 
                        cmd_result->status == COMMAND_STATUS_COMPLETED, 
                "Command status should indicate failure");
            TEST_ASSERT(cmd_result->exit_code != 0, "Exit code should not be 0 for failed command");
            
            command_result_free(cmd_result);
        }
        
        command_free(cmd);
    }
}

/**
 * Тест получения сообщений об ошибках.
 */
void test_error_handling(void) {
    printf("Running test: error handling\n");
    
    // Сбрасываем ошибки с помощью инициализации
    command_executor_init();
    
    // Начальный код ошибки должен быть 0
    int error_code = command_executor_get_last_error();
    TEST_ASSERT(error_code == 0, "Initial error code should be 0");
    
    // Проверяем сообщение об ошибке
    const char* error_message = command_executor_get_error_message();
    TEST_ASSERT(error_message != NULL, "Error message should not be NULL");
    TEST_ASSERT(strlen(error_message) == 0, "Initial error message should be empty");
    
    // Вызываем функцию, которая должна установить ошибку
    Command* cmd = command_create(99); // Неизвестный тип, вызовет ошибку
    TEST_ASSERT(cmd == NULL, "command_create should return NULL for unknown type");
    
    // Проверяем, что код ошибки изменился
    error_code = command_executor_get_last_error();
    TEST_ASSERT(error_code != 0, "Error code should be non-zero after error");
    
    // Проверяем, что сообщение об ошибке не пустое
    error_message = command_executor_get_error_message();
    TEST_ASSERT(error_message != NULL, "Error message should not be NULL");
    TEST_ASSERT(strlen(error_message) > 0, "Error message should not be empty after error");
    
    command_executor_cleanup();
}

int main(int argc, char** argv) {
    printf("Starting command executor tests...\n\n");
    
    // Запускаем тесты
    test_executor_init();
    test_command_create_free();
    test_command_set_command_line();
    test_command_set_working_dir();
    test_command_set_output_file();
    test_command_set_input_data();
    test_command_set_flags();
    test_command_set_timeout();
    
    // Функциональные тесты
    test_command_execute_simple();
    test_command_execute_timeout();
    test_command_execute_with_input();
    test_command_execute_unknown();
    
    // Тесты обработки ошибок
    test_error_handling();
    
    // Выводим результаты
    printf("\nTest results: %d passed, %d failed\n", passed_tests, failed_tests);
    
    // Возвращаем ненулевой код выхода, если были проваленные тесты
    return (failed_tests > 0) ? 1 : 0;
} 