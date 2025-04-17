/**
 * @file command_executor_example.c
 * @brief Example of using the command execution module.
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-04
 */

#include "../include/command_executor.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#define DIR_COMMAND "dir"
#define PS_COMMAND "tasklist"
#define SLEEP_COMMAND "timeout 3"
#else
#define DIR_COMMAND "ls -la"
#define PS_COMMAND "ps aux"
#define SLEEP_COMMAND "sleep 3"
#endif

/**
 * Executes a command and prints its output and status.
 * 
 * @param command_type The type of command to execute (shell or process).
 * @param command_line The command line to execute.
 * @param working_dir The working directory for the command or NULL.
 * @param input_data The input data for the command or NULL.
 * @param input_length The length of the input data.
 * @param timeout_ms The timeout in milliseconds or 0 for no timeout.
 * @param flags The command flags.
 * @param title Optional title to show before the command execution or NULL.
 * @return 1 on success, 0 on failure.
 */
int run_command_example(CommandType command_type, 
                        const char* command_line, 
                        const char* working_dir, 
                        const char* input_data, 
                        size_t input_length,
                        uint32_t timeout_ms,
                        CommandFlags flags,
                        const char* title) {
    if (title) {
        printf("\n====== %s ======\n", title);
    }
    
    printf("Executing command: %s\n", command_line);
    if (working_dir) {
        printf("Working directory: %s\n", working_dir);
    }
    
    // Создаем команду
    Command* cmd = command_create(command_type);
    if (cmd == NULL) {
        printf("Error creating command: %s\n", command_executor_get_error_message());
        return 0;
    }
    
    // Устанавливаем параметры команды
    if (!command_set_command_line(cmd, command_line)) {
        printf("Error setting command line: %s\n", command_executor_get_error_message());
        command_free(cmd);
        return 0;
    }
    
    if (working_dir && !command_set_working_dir(cmd, working_dir)) {
        printf("Error setting working directory: %s\n", command_executor_get_error_message());
        command_free(cmd);
        return 0;
    }
    
    if (input_data && !command_set_input_data(cmd, input_data, input_length)) {
        printf("Error setting input data: %s\n", command_executor_get_error_message());
        command_free(cmd);
        return 0;
    }
    
    if (timeout_ms > 0 && !command_set_timeout(cmd, timeout_ms)) {
        printf("Error setting timeout: %s\n", command_executor_get_error_message());
        command_free(cmd);
        return 0;
    }
    
    if (flags != COMMAND_FLAG_NONE && !command_set_flags(cmd, flags)) {
        printf("Error setting flags: %s\n", command_executor_get_error_message());
        command_free(cmd);
        return 0;
    }
    
    // Выполняем команду
    printf("Starting command execution...\n");
    CommandResult* result = command_execute(cmd);
    if (result == NULL) {
        printf("Error executing command: %s\n", command_executor_get_error_message());
        command_free(cmd);
        return 0;
    }
    
    // Выводим результаты
    printf("Command completed with status: ");
    switch (result->status) {
        case COMMAND_STATUS_COMPLETED:
            printf("COMPLETED\n");
            break;
        case COMMAND_STATUS_ERROR:
            printf("ERROR\n");
            break;
        case COMMAND_STATUS_TIMEOUT:
            printf("TIMEOUT\n");
            break;
        default:
            printf("UNKNOWN (%d)\n", result->status);
            break;
    }
    
    printf("Exit code: %d\n", result->exit_code);
    printf("Execution time: %u ms\n", result->execution_time_ms);
    
    if (result->output && result->output_length > 0) {
        // Определение размера для вывода 
        size_t output_len = result->output_length;
        if (output_len > 1024) { // Если вывод слишком большой, покажем только первую часть
            output_len = 1024;
            printf("Command output (first 1024 bytes of %zu):\n", result->output_length);
        } else {
            printf("Command output (%zu bytes):\n", result->output_length);
        }
        
        printf("--------------------------------------------------\n");
        printf("%.*s\n", (int)output_len, result->output);
        if (output_len < result->output_length) {
            printf("... (output truncated)\n");
        }
        printf("--------------------------------------------------\n");
    } else {
        printf("No command output.\n");
    }
    
    // Освобождаем ресурсы
    command_result_free(result);
    command_free(cmd);
    
    return 1;
}

/**
 * Main function to demonstrate command execution features.
 */
int main(int argc, char** argv) {
    // Инициализируем модуль исполнения команд
    if (!command_executor_init()) {
        printf("Failed to initialize command executor: %s\n", 
               command_executor_get_error_message());
        return 1;
    }
    
    // Примеры выполнения команд
    
    // 1. Простая команда для вывода содержимого директории
    run_command_example(COMMAND_TYPE_SHELL, DIR_COMMAND, NULL, NULL, 0, 0, 
                        COMMAND_FLAG_NONE, "Directory Listing");
    
    // 2. Команда с тайм-аутом
    run_command_example(COMMAND_TYPE_SHELL, SLEEP_COMMAND, NULL, NULL, 0, 2000, 
                        COMMAND_FLAG_NONE, "Command with Timeout (should timeout)");
    
    // 3. Команда для получения списка процессов
    run_command_example(COMMAND_TYPE_SHELL, PS_COMMAND, NULL, NULL, 0, 0, 
                        COMMAND_FLAG_NONE, "Process Listing");
    
    // 4. Команда с входными данными
    const char* input = "Test input data\nSecond line\nThird line\n";
#ifdef _WIN32
    run_command_example(COMMAND_TYPE_SHELL, "findstr \"line\"", NULL, input, strlen(input), 0, 
                        COMMAND_FLAG_NONE, "Command with Input (Windows)");
#else
    run_command_example(COMMAND_TYPE_SHELL, "grep line", NULL, input, strlen(input), 0, 
                        COMMAND_FLAG_NONE, "Command with Input (Unix)");
#endif
    
    // 5. Выполнение команды от имени другого пользователя (требует привилегий)
#ifdef _WIN32
    printf("\n====== Command as different user (requires admin privileges) ======\n");
    printf("Not implemented for Windows example.\n");
#else
    printf("\n====== Command as different user (requires sudo privileges) ======\n");
    printf("To run as different user, you would need sudo access and can use:\n");
    printf("sudo -u username command\n");
#endif
    
    // 6. Скрытый режим (в примере не покажет разницы, но полезно для реальных сценариев)
    run_command_example(COMMAND_TYPE_SHELL, "echo \"Command running in hidden mode\"", NULL, 
                        NULL, 0, 0, COMMAND_FLAG_HIDDEN, "Hidden Mode Command");
    
    // 7. Пример выполнения с указанием рабочей директории
#ifdef _WIN32
    run_command_example(COMMAND_TYPE_SHELL, DIR_COMMAND, "C:\\Windows", NULL, 0, 0, 
                        COMMAND_FLAG_NONE, "Command in Different Directory (Windows)");
#else
    run_command_example(COMMAND_TYPE_SHELL, DIR_COMMAND, "/etc", NULL, 0, 0, 
                        COMMAND_FLAG_NONE, "Command in Different Directory (Unix)");
#endif
    
    // Очищаем ресурсы исполнителя команд
    command_executor_cleanup();
    
    printf("\nAll examples completed!\n");
    return 0;
} 