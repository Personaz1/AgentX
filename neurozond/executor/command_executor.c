/**
 * @file command_executor.c
 * @brief Implementation of command execution module.
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-04
 */

#include "../include/command_executor.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#include <process.h>
#else
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <sys/time.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#endif

// Максимальный размер буфера для захвата вывода команды
#define MAX_OUTPUT_BUFFER 1048576 // 1MB

// Структура для хранения информации об ошибке
typedef struct {
    int code;
    char message[256];
} ErrorInfo;

// Глобальная переменная для хранения последней ошибки
static ErrorInfo last_error = {0, ""};

// Инициализирует исполнитель команд
int command_executor_init(void) {
    // Сбрасываем последнюю ошибку
    last_error.code = 0;
    last_error.message[0] = '\0';
    
    // На Windows возможно потребуется инициализация COM или других подсистем
    
    return 1; // Успех
}

// Очищает ресурсы исполнителя команд
void command_executor_cleanup(void) {
    // На Windows возможно потребуется освобождение COM или других подсистем
}

// Утилита для установки информации об ошибке
static void set_last_error(int code, const char* message) {
    last_error.code = code;
    strncpy(last_error.message, message, sizeof(last_error.message) - 1);
    last_error.message[sizeof(last_error.message) - 1] = '\0';
}

// Создает новую команду
Command* command_create(CommandType type) {
    // Проверка на поддерживаемые типы команд
    if (type != COMMAND_TYPE_SHELL && type != COMMAND_TYPE_PROCESS) {
        set_last_error(1, "Unsupported command type");
        return NULL;
    }
    
    // Выделяем память для команды
    Command* cmd = (Command*)calloc(1, sizeof(Command));
    if (cmd == NULL) {
        set_last_error(2, "Memory allocation failed");
        return NULL;
    }
    
    // Инициализируем поля структуры
    cmd->type = type;
    cmd->status = COMMAND_STATUS_CREATED;
    cmd->command_line = NULL;
    cmd->working_dir = NULL;
    cmd->output_file = NULL;
    cmd->input_data = NULL;
    cmd->input_length = 0;
    cmd->flags = COMMAND_FLAG_NONE;
    cmd->timeout_ms = 0; // без тайм-аута по умолчанию
    cmd->platform_data = NULL;
    
    return cmd;
}

// Освобождает ресурсы команды
void command_free(Command* cmd) {
    if (cmd == NULL) {
        return;
    }
    
    // Освобождаем строковые поля
    if (cmd->command_line) free(cmd->command_line);
    if (cmd->working_dir) free(cmd->working_dir);
    if (cmd->output_file) free(cmd->output_file);
    if (cmd->input_data) free(cmd->input_data);
    
    // Освобождаем платформо-зависимые данные, если они есть
    if (cmd->platform_data) {
        // В зависимости от платформы, может потребоваться специальное освобождение
        free(cmd->platform_data);
    }
    
    // Наконец, освобождаем саму структуру
    free(cmd);
}

// Устанавливает командную строку
int command_set_command_line(Command* cmd, const char* command_line) {
    if (cmd == NULL || command_line == NULL) {
        set_last_error(3, "Invalid parameters");
        return 0;
    }
    
    // Освобождаем предыдущую командную строку, если она была
    if (cmd->command_line) {
        free(cmd->command_line);
    }
    
    // Копируем новую командную строку
    cmd->command_line = strdup(command_line);
    if (cmd->command_line == NULL) {
        set_last_error(2, "Memory allocation failed");
        return 0;
    }
    
    return 1;
}

// Устанавливает рабочую директорию
int command_set_working_dir(Command* cmd, const char* working_dir) {
    if (cmd == NULL || working_dir == NULL) {
        set_last_error(3, "Invalid parameters");
        return 0;
    }
    
    // Освобождаем предыдущую рабочую директорию, если она была
    if (cmd->working_dir) {
        free(cmd->working_dir);
    }
    
    // Копируем новую рабочую директорию
    cmd->working_dir = strdup(working_dir);
    if (cmd->working_dir == NULL) {
        set_last_error(2, "Memory allocation failed");
        return 0;
    }
    
    return 1;
}

// Устанавливает файл для вывода
int command_set_output_file(Command* cmd, const char* output_file) {
    if (cmd == NULL || output_file == NULL) {
        set_last_error(3, "Invalid parameters");
        return 0;
    }
    
    // Освобождаем предыдущий файл вывода, если он был
    if (cmd->output_file) {
        free(cmd->output_file);
    }
    
    // Копируем новый файл вывода
    cmd->output_file = strdup(output_file);
    if (cmd->output_file == NULL) {
        set_last_error(2, "Memory allocation failed");
        return 0;
    }
    
    return 1;
}

// Устанавливает входные данные
int command_set_input_data(Command* cmd, const char* input_data, size_t input_length) {
    if (cmd == NULL || (input_data == NULL && input_length > 0)) {
        set_last_error(3, "Invalid parameters");
        return 0;
    }
    
    // Освобождаем предыдущие входные данные, если они были
    if (cmd->input_data) {
        free(cmd->input_data);
        cmd->input_data = NULL;
        cmd->input_length = 0;
    }
    
    // Если данных нет, просто возвращаем успех
    if (input_data == NULL || input_length == 0) {
        return 1;
    }
    
    // Копируем новые входные данные
    cmd->input_data = (char*)malloc(input_length);
    if (cmd->input_data == NULL) {
        set_last_error(2, "Memory allocation failed");
        return 0;
    }
    
    memcpy(cmd->input_data, input_data, input_length);
    cmd->input_length = input_length;
    
    return 1;
}

// Устанавливает флаги команды
int command_set_flags(Command* cmd, CommandFlags flags) {
    if (cmd == NULL) {
        set_last_error(3, "Invalid parameters");
        return 0;
    }
    
    cmd->flags = flags;
    return 1;
}

// Устанавливает тайм-аут команды
int command_set_timeout(Command* cmd, uint32_t timeout_ms) {
    if (cmd == NULL) {
        set_last_error(3, "Invalid parameters");
        return 0;
    }
    
    cmd->timeout_ms = timeout_ms;
    return 1;
}

// Получает код последней ошибки
int command_executor_get_last_error(void) {
    return last_error.code;
}

// Получает сообщение о последней ошибке
const char* command_executor_get_error_message(void) {
    return last_error.message;
}

// Создает результат выполнения команды
static CommandResult* create_command_result(void) {
    CommandResult* result = (CommandResult*)calloc(1, sizeof(CommandResult));
    if (result == NULL) {
        set_last_error(2, "Memory allocation failed");
        return NULL;
    }
    
    result->status = COMMAND_STATUS_CREATED;
    result->exit_code = -1;
    result->output = NULL;
    result->output_length = 0;
    result->execution_time_ms = 0;
    
    return result;
}

// Освобождает результат выполнения команды
void command_result_free(CommandResult* result) {
    if (result == NULL) {
        return;
    }
    
    if (result->output) {
        free(result->output);
    }
    
    free(result);
}

#ifdef _WIN32
// Структура для передачи данных в поток чтения вывода
typedef struct {
    HANDLE hPipe;
    char* buffer;
    size_t* buffer_pos;
    size_t buffer_size;
    ErrorInfo* error_info;
} ReadPipeThreadData;

// Функция потока для чтения данных из пайпа (stdout или stderr)
static DWORD WINAPI ReadPipeThread(LPVOID lpParam) {
    ReadPipeThreadData* data = (ReadPipeThreadData*)lpParam;
    DWORD dwRead;
    CHAR chBuf[4096];
    BOOL bSuccess = FALSE;

    while (1) {
        // Читаем из пайпа
        bSuccess = ReadFile(data->hPipe, chBuf, sizeof(chBuf), &dwRead, NULL);
        
        // Если чтение не удалось или прочитано 0 байт (пайп закрыт с другой стороны)
        if (!bSuccess || dwRead == 0) {
            if (GetLastError() == ERROR_BROKEN_PIPE) {
                break; // Пайп закрыт, это нормально
            } else if (GetLastError() != ERROR_SUCCESS) {
                 // Произошла ошибка чтения, кроме закрытия пайпа
                 if (data->error_info->code == 0) { // Устанавливаем ошибку, если она еще не установлена
                     char error_msg[256];
                     snprintf(error_msg, sizeof(error_msg), "ReadFile failed with error %lu", GetLastError());
                     set_last_error(7, error_msg); // Используем статический set_last_error
                     data->error_info->code = last_error.code; // Копируем для потока
                     strncpy(data->error_info->message, last_error.message, sizeof(data->error_info->message) -1);
                 }
                 break;
            }
             // Если bSuccess == TRUE и dwRead == 0, значит достигнут конец файла (пайп закрыт)
             if (dwRead == 0 && bSuccess) {
                 break;
             }
        }

        // Копируем прочитанные данные в общий буфер вывода
        if (*(data->buffer_pos) + dwRead < data->buffer_size -1) {
            memcpy(data->buffer + *(data->buffer_pos), chBuf, dwRead);
            *(data->buffer_pos) += dwRead;
        } else {
            // Буфер переполнен, прекращаем чтение
             if (data->error_info->code == 0) {
                 set_last_error(8, "Output buffer overflow");
                 data->error_info->code = last_error.code;
                 strncpy(data->error_info->message, last_error.message, sizeof(data->error_info->message) -1);
             }
            break;
        }
    }
    
    return 0; // Успешное завершение потока
}


// Выполняет команду в Windows
static CommandResult* execute_command_windows(Command* cmd) {
    CommandResult* result = create_command_result();
    if (result == NULL) {
        return NULL;
    }
    
    if (cmd->command_line == NULL) {
        set_last_error(3, "No command line specified");
        result->status = COMMAND_STATUS_ERROR;
        return result;
    }

    cmd->status = COMMAND_STATUS_RUNNING;

    HANDLE hChildStdinRd = NULL, hChildStdinWr = NULL;
    HANDLE hChildStdoutRd = NULL, hChildStdoutWr = NULL;
    HANDLE hChildStderrRd = NULL, hChildStderrWr = NULL;
    SECURITY_ATTRIBUTES saAttr;

    // Устанавливаем атрибуты безопасности для наследования хендлов пайпов
    saAttr.nLength = sizeof(SECURITY_ATTRIBUTES);
    saAttr.bInheritHandle = TRUE;
    saAttr.lpSecurityDescriptor = NULL;

    // Создаем пайп для stdout дочернего процесса
    if (!CreatePipe(&hChildStdoutRd, &hChildStdoutWr, &saAttr, 0)) {
        set_last_error(4, "Stdout pipe creation failed");
        result->status = COMMAND_STATUS_ERROR;
        goto cleanup;
    }
    // Убеждаемся, что хендл для чтения stdout НЕ наследуется
    if (!SetHandleInformation(hChildStdoutRd, HANDLE_FLAG_INHERIT, 0)) {
         set_last_error(4, "Stdout SetHandleInformation failed");
         result->status = COMMAND_STATUS_ERROR;
         goto cleanup;
    }


    // Создаем пайп для stderr дочернего процесса
    if (!CreatePipe(&hChildStderrRd, &hChildStderrWr, &saAttr, 0)) {
        set_last_error(4, "Stderr pipe creation failed");
        result->status = COMMAND_STATUS_ERROR;
        goto cleanup;
    }
     // Убеждаемся, что хендл для чтения stderr НЕ наследуется
    if (!SetHandleInformation(hChildStderrRd, HANDLE_FLAG_INHERIT, 0)) {
         set_last_error(4, "Stderr SetHandleInformation failed");
         result->status = COMMAND_STATUS_ERROR;
         goto cleanup;
    }

    // Создаем пайп для stdin дочернего процесса, если есть входные данные
    if (cmd->input_data != NULL && cmd->input_length > 0) {
        if (!CreatePipe(&hChildStdinRd, &hChildStdinWr, &saAttr, 0)) {
            set_last_error(4, "Stdin pipe creation failed");
            result->status = COMMAND_STATUS_ERROR;
            goto cleanup;
        }
        // Убеждаемся, что хендл для записи stdin НЕ наследуется
        if (!SetHandleInformation(hChildStdinWr, HANDLE_FLAG_INHERIT, 0)) {
             set_last_error(4, "Stdin SetHandleInformation failed");
             result->status = COMMAND_STATUS_ERROR;
             goto cleanup;
        }
    }


    // Настраиваем структуры для CreateProcess
    PROCESS_INFORMATION piProcInfo;
    STARTUPINFO siStartInfo;
    BOOL bSuccess = FALSE;

    ZeroMemory(&piProcInfo, sizeof(PROCESS_INFORMATION));
    ZeroMemory(&siStartInfo, sizeof(STARTUPINFO));
    siStartInfo.cb = sizeof(STARTUPINFO);
    siStartInfo.hStdError = hChildStderrWr;
    siStartInfo.hStdOutput = hChildStdoutWr;
    siStartInfo.dwFlags |= STARTF_USESTDHANDLES;

    // Устанавливаем stdin, если он есть
    if (hChildStdinRd != NULL) {
        siStartInfo.hStdInput = hChildStdinRd;
    } else {
        siStartInfo.hStdInput = GetStdHandle(STD_INPUT_HANDLE); // Используем stdin родителя, если пайп не создан
    }


    // Устанавливаем флаги создания процесса
    DWORD dwCreationFlags = 0;
    if (cmd->flags & COMMAND_FLAG_HIDDEN) {
        dwCreationFlags |= CREATE_NO_WINDOW;
         // Можно добавить DETACHED_PROCESS, если нужно полностью отвязать
         // dwCreationFlags |= DETACHED_PROCESS; 
    }

    // Засекаем время начала
    LARGE_INTEGER frequency, start_time, end_time;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&start_time);

    // Создаем дочерний процесс
    // CreateProcess требует неконстантную строку для командной строки
    char* cmd_line_mutable = strdup(cmd->command_line);
    if (cmd_line_mutable == NULL) {
         set_last_error(2, "Memory allocation failed for command line copy");
         result->status = COMMAND_STATUS_ERROR;
         goto cleanup_cmdline;
    }

    bSuccess = CreateProcess(
        NULL,             // Имя приложения (используем командную строку)
        cmd_line_mutable, // Командная строка (должна быть изменяемой)
        NULL,             // Атрибуты безопасности процесса
        NULL,             // Атрибуты безопасности потока
        TRUE,             // Наследование хендлов
        dwCreationFlags,  // Флаги создания
        NULL,             // Использовать переменные окружения родителя
        cmd->working_dir, // Рабочая директория
        &siStartInfo,     // Указатель на STARTUPINFO
        &piProcInfo       // Указатель на PROCESS_INFORMATION
    );
    
    free(cmd_line_mutable); // Освобождаем копию командной строки

    // Проверяем результат CreateProcess
    if (!bSuccess) {
        char error_msg[256];
        snprintf(error_msg, sizeof(error_msg), "CreateProcess failed with error %lu", GetLastError());
        set_last_error(5, error_msg);
        result->status = COMMAND_STATUS_ERROR;
        goto cleanup;
    }

    // Закрываем ненужные хендлы пайпов в родительском процессе
    // Важно закрыть хендлы записи stdout/stderr и чтения stdin,
    // чтобы ReadFile/WriteFile в дочернем и родительском процессах работали корректно
    CloseHandle(hChildStdoutWr); hChildStdoutWr = NULL;
    CloseHandle(hChildStderrWr); hChildStderrWr = NULL;
    if (hChildStdinRd != NULL) {
        CloseHandle(hChildStdinRd); hChildStdinRd = NULL;
    }


    // Если есть входные данные, пишем их в stdin дочернего процесса
    if (hChildStdinWr != NULL) {
        DWORD dwWritten;
        bSuccess = WriteFile(hChildStdinWr, cmd->input_data, cmd->input_length, &dwWritten, NULL);
        // Закрываем хендл записи в stdin ПОСЛЕ записи, чтобы дочерний процесс увидел EOF
        CloseHandle(hChildStdinWr); hChildStdinWr = NULL; 
        if (!bSuccess || dwWritten != cmd->input_length) {
            set_last_error(9, "Failed to write to child stdin");
            // Не прерываем выполнение, но устанавливаем ошибку
            result->status = COMMAND_STATUS_ERROR; // Отмечаем, что была ошибка
        }
    }


    // Готовим буфер для вывода
    char* output_buffer = (char*)malloc(MAX_OUTPUT_BUFFER);
    if (output_buffer == NULL) {
        set_last_error(2, "Memory allocation failed for output buffer");
        result->status = COMMAND_STATUS_ERROR;
        // Пытаемся завершить дочерний процесс перед выходом
        TerminateProcess(piProcInfo.hProcess, 1); 
        goto cleanup_process;
    }
    size_t output_pos = 0;
    output_buffer[0] = '\0';

    // Структуры для передачи данных в потоки чтения
    ErrorInfo read_error_info = {0, ""}; // Ошибка, специфичная для потоков чтения
    ReadPipeThreadData stdout_thread_data = {hChildStdoutRd, output_buffer, &output_pos, MAX_OUTPUT_BUFFER, &read_error_info};
    ReadPipeThreadData stderr_thread_data = {hChildStderrRd, output_buffer, &output_pos, MAX_OUTPUT_BUFFER, &read_error_info};
    
    // Создаем потоки для чтения stdout и stderr
    HANDLE hThreadStdout = CreateThread(NULL, 0, ReadPipeThread, &stdout_thread_data, 0, NULL);
    HANDLE hThreadStderr = CreateThread(NULL, 0, ReadPipeThread, &stderr_thread_data, 0, NULL);

    if (hThreadStdout == NULL || hThreadStderr == NULL) {
         set_last_error(10, "Failed to create read threads");
         result->status = COMMAND_STATUS_ERROR;
         TerminateProcess(piProcInfo.hProcess, 1);
         if (hThreadStdout) CloseHandle(hThreadStdout);
         if (hThreadStderr) CloseHandle(hThreadStderr);
         free(output_buffer);
         goto cleanup_process;
    }

    // Ждем завершения дочернего процесса И потоков чтения
    HANDLE hWaitHandles[] = { piProcInfo.hProcess, hThreadStdout, hThreadStderr };
    DWORD dwTimeout = (cmd->timeout_ms > 0) ? cmd->timeout_ms : INFINITE;
    DWORD dwWaitResult;

    // Ждем завершения процесса ИЛИ истечения тайм-аута
    dwWaitResult = WaitForSingleObject(piProcInfo.hProcess, dwTimeout);

    if (dwWaitResult == WAIT_OBJECT_0) {
        // Процесс завершился сам
        result->status = COMMAND_STATUS_COMPLETED;
    } else if (dwWaitResult == WAIT_TIMEOUT) {
        // Тайм-аут, принудительно завершаем процесс
        set_last_error(11, "Command timed out");
        TerminateProcess(piProcInfo.hProcess, 1); // Завершаем с кодом 1
        result->status = COMMAND_STATUS_TIMEOUT;
         // Даем немного времени потокам чтения заметить закрытие пайпов
         Sleep(50); 
    } else {
        // Ошибка ожидания
        char error_msg[256];
        snprintf(error_msg, sizeof(error_msg), "WaitForSingleObject failed with error %lu", GetLastError());
        set_last_error(6, error_msg);
        result->status = COMMAND_STATUS_ERROR;
        TerminateProcess(piProcInfo.hProcess, 1); // На всякий случай завершаем
         Sleep(50);
    }

    // Ждем завершения потоков чтения (с небольшим тайм-аутом, чтобы не зависнуть)
    // Они должны завершиться сами, так как пайпы будут закрыты после завершения дочернего процесса
     WaitForSingleObject(hThreadStdout, 1000); 
     WaitForSingleObject(hThreadStderr, 1000); 

    // Закрываем хендлы потоков чтения
    CloseHandle(hThreadStdout);
    CloseHandle(hThreadStderr);
    
    // Получаем код завершения процесса
    DWORD dwExitCode;
    if (GetExitCodeProcess(piProcInfo.hProcess, &dwExitCode)) {
        result->exit_code = (int)dwExitCode;
         // Если процесс был убит по тайм-ауту, статус уже установлен
         if (result->status == COMMAND_STATUS_COMPLETED && dwExitCode != 0) {
             // Если процесс завершился сам, но с ненулевым кодом, считаем это ошибкой выполнения
             //result->status = COMMAND_STATUS_ERROR; // Решаем, считать ли ненулевой код ошибкой
         }
    } else {
        // Не удалось получить код завершения
        if (result->status != COMMAND_STATUS_TIMEOUT){ // Не перезаписываем ошибку таймаута
             char error_msg[256];
             snprintf(error_msg, sizeof(error_msg), "GetExitCodeProcess failed with error %lu", GetLastError());
             set_last_error(12, error_msg);
             result->status = COMMAND_STATUS_ERROR;
        }
        result->exit_code = -1;
    }

    // Засекаем время окончания
    QueryPerformanceCounter(&end_time);
    result->execution_time_ms = (uint32_t)(((end_time.QuadPart - start_time.QuadPart) * 1000) / frequency.QuadPart);

    // Завершаем строку вывода нулем
    output_buffer[output_pos] = '\0';
    result->output = output_buffer; // Передаем владение буфером результату
    result->output_length = output_pos;
    
    // Проверяем, не возникла ли ошибка в потоках чтения
     if (read_error_info.code != 0 && result->status != COMMAND_STATUS_TIMEOUT) {
         // Если была ошибка чтения и это не тайм-аут, обновляем глобальную ошибку
         // и статус результата
         set_last_error(read_error_info.code, read_error_info.message);
         result->status = COMMAND_STATUS_ERROR;
     }


cleanup_process:
    // Закрываем хендлы процесса и основного потока
    CloseHandle(piProcInfo.hProcess);
    CloseHandle(piProcInfo.hThread);

cleanup:
    // Закрываем оставшиеся хендлы пайпов (если они не были закрыты ранее)
    if (hChildStdoutRd) CloseHandle(hChildStdoutRd);
    if (hChildStdoutWr) CloseHandle(hChildStdoutWr);
    if (hChildStderrRd) CloseHandle(hChildStderrRd);
    if (hChildStderrWr) CloseHandle(hChildStderrWr);
    if (hChildStdinRd) CloseHandle(hChildStdinRd);
    if (hChildStdinWr) CloseHandle(hChildStdinWr);
    
cleanup_cmdline: 
    // Нет дополнительной очистки для cmd_line_mutable здесь, так как free вызывается раньше

    // Обновляем статус команды
    cmd->status = result->status;
    return result;
}
#else
// Выполняет команду в Unix-подобных системах
static CommandResult* execute_command_unix(Command* cmd) {
    CommandResult* result = create_command_result();
    if (result == NULL) {
        return NULL;
    }
    
    // Если нет командной строки, возвращаем ошибку
    if (cmd->command_line == NULL) {
        set_last_error(3, "No command line specified");
        result->status = COMMAND_STATUS_ERROR;
        return result;
    }
    
    // Устанавливаем статус команды как выполняющейся
    cmd->status = COMMAND_STATUS_RUNNING;
    
    // Создаем пайпы для stdout и stderr
    int stdout_pipe[2];
    int stderr_pipe[2];
    int stdin_pipe[2] = {-1, -1};
    
    if (pipe(stdout_pipe) != 0 || pipe(stderr_pipe) != 0) {
        set_last_error(4, "Failed to create pipes");
        result->status = COMMAND_STATUS_ERROR;
        return result;
    }
    
    // Если есть входные данные, создаем stdin pipe
    if (cmd->input_data != NULL && cmd->input_length > 0) {
        if (pipe(stdin_pipe) != 0) {
            close(stdout_pipe[0]);
            close(stdout_pipe[1]);
            close(stderr_pipe[0]);
            close(stderr_pipe[1]);
            set_last_error(4, "Failed to create stdin pipe");
            result->status = COMMAND_STATUS_ERROR;
            return result;
        }
    }
    
    // Засекаем время начала выполнения
    struct timeval start_time, end_time;
    gettimeofday(&start_time, NULL);
    
    // Форкаем процесс
    pid_t pid = fork();
    if (pid < 0) {
        // Ошибка при форке
        close(stdout_pipe[0]);
        close(stdout_pipe[1]);
        close(stderr_pipe[0]);
        close(stderr_pipe[1]);
        if (stdin_pipe[0] != -1) {
            close(stdin_pipe[0]);
            close(stdin_pipe[1]);
        }
        set_last_error(5, "Failed to fork process");
        result->status = COMMAND_STATUS_ERROR;
        return result;
    } 
    else if (pid == 0) {
        // Дочерний процесс
        
        // Перенаправляем stdout и stderr в пайпы
        close(stdout_pipe[0]);
        dup2(stdout_pipe[1], STDOUT_FILENO);
        close(stdout_pipe[1]);
        
        close(stderr_pipe[0]);
        dup2(stderr_pipe[1], STDERR_FILENO);
        close(stderr_pipe[1]);
        
        // Если есть входные данные, перенаправляем stdin
        if (stdin_pipe[0] != -1) {
            close(stdin_pipe[1]);
            dup2(stdin_pipe[0], STDIN_FILENO);
            close(stdin_pipe[0]);
        }
        
        // Если указана рабочая директория, переходим в нее
        if (cmd->working_dir != NULL) {
            if (chdir(cmd->working_dir) != 0) {
                fprintf(stderr, "Failed to change directory to %s\n", cmd->working_dir);
                exit(127);
            }
        }
        
        // Если команда должна быть выполнена в скрытом режиме
        if (cmd->flags & COMMAND_FLAG_HIDDEN) {
            // В Unix мы можем отсоединить процесс от терминала
            setsid();
        }
        
        // Выполняем команду через shell или напрямую
        if (cmd->type == COMMAND_TYPE_SHELL) {
            execl("/bin/sh", "sh", "-c", cmd->command_line, NULL);
        } else {
            // Для простого процесса нужно разобрать командную строку на аргументы
            // Это упрощенная версия, которая не обрабатывает сложные случаи с кавычками и т.д.
            char* args[64] = {NULL}; // Ограничиваем до 64 аргументов
            char* cmd_copy = strdup(cmd->command_line);
            char* token = strtok(cmd_copy, " \t");
            int i = 0;
            
            while (token != NULL && i < 63) {
                args[i++] = token;
                token = strtok(NULL, " \t");
            }
            
            execvp(args[0], args);
            free(cmd_copy);
        }
        
        // Если дошли до сюда, значит execl/execvp завершилась с ошибкой
        fprintf(stderr, "Failed to execute command: %s\n", strerror(errno));
        exit(127);
    } 
    else {
        // Родительский процесс
        
        // Закрываем ненужные концы пайпов
        close(stdout_pipe[1]);
        close(stderr_pipe[1]);
        
        // Если есть входные данные, пишем их в stdin процесса
        if (stdin_pipe[1] != -1) {
            close(stdin_pipe[0]);
            write(stdin_pipe[1], cmd->input_data, cmd->input_length);
            close(stdin_pipe[1]);
        }
        
        // Устанавливаем неблокирующий режим для чтения
        fcntl(stdout_pipe[0], F_SETFL, O_NONBLOCK);
        fcntl(stderr_pipe[0], F_SETFL, O_NONBLOCK);
        
        // Буфер для чтения вывода
        char* output_buffer = (char*)malloc(MAX_OUTPUT_BUFFER);
        if (output_buffer == NULL) {
            close(stdout_pipe[0]);
            close(stderr_pipe[0]);
            set_last_error(2, "Memory allocation failed");
            result->status = COMMAND_STATUS_ERROR;
            return result;
        }
        
        size_t output_pos = 0;
        int status = 0;
        pid_t wait_result;
        int done = 0;
        
        // Время окончания тайм-аута
        struct timeval timeout_end;
        if (cmd->timeout_ms > 0) {
            gettimeofday(&timeout_end, NULL);
            timeout_end.tv_sec += cmd->timeout_ms / 1000;
            timeout_end.tv_usec += (cmd->timeout_ms % 1000) * 1000;
            if (timeout_end.tv_usec >= 1000000) {
                timeout_end.tv_sec += 1;
                timeout_end.tv_usec -= 1000000;
            }
        }
        
        // Ждем завершения процесса, периодически проверяя наличие данных и тайм-аут
        while (!done) {
            // Проверяем, завершился ли процесс
            wait_result = waitpid(pid, &status, WNOHANG);
            if (wait_result == pid) {
                // Процесс завершился
                done = 1;
            } 
            else if (wait_result < 0) {
                // Ошибка ожидания
                if (errno != EINTR) {
                    done = 1;
                    set_last_error(6, "Failed to wait for process");
                    result->status = COMMAND_STATUS_ERROR;
                }
            }
            
            // Проверяем тайм-аут
            if (!done && cmd->timeout_ms > 0) {
                struct timeval now;
                gettimeofday(&now, NULL);
                if (now.tv_sec > timeout_end.tv_sec || 
                    (now.tv_sec == timeout_end.tv_sec && now.tv_usec >= timeout_end.tv_usec)) {
                    // Тайм-аут истек, убиваем процесс
                    kill(pid, SIGTERM);
                    usleep(100000); // Даем процессу 100 мс на завершение
                    kill(pid, SIGKILL); // Принудительное завершение, если не сработал SIGTERM
                    waitpid(pid, &status, 0); // Ждем завершения процесса
                    done = 1;
                    result->status = COMMAND_STATUS_TIMEOUT;
                }
            }
            
            // Читаем данные из stdout
            if (output_pos < MAX_OUTPUT_BUFFER - 1) {
                char buf[4096];
                int bytes_read = read(stdout_pipe[0], buf, sizeof(buf) - 1);
                if (bytes_read > 0) {
                    // Добавляем данные в буфер вывода
                    size_t copy_size = bytes_read;
                    if (output_pos + copy_size > MAX_OUTPUT_BUFFER - 1) {
                        copy_size = MAX_OUTPUT_BUFFER - 1 - output_pos;
                    }
                    memcpy(output_buffer + output_pos, buf, copy_size);
                    output_pos += copy_size;
                }
            }
            
            // Читаем данные из stderr
            if (output_pos < MAX_OUTPUT_BUFFER - 1) {
                char buf[4096];
                int bytes_read = read(stderr_pipe[0], buf, sizeof(buf) - 1);
                if (bytes_read > 0) {
                    // Добавляем данные в буфер вывода
                    size_t copy_size = bytes_read;
                    if (output_pos + copy_size > MAX_OUTPUT_BUFFER - 1) {
                        copy_size = MAX_OUTPUT_BUFFER - 1 - output_pos;
                    }
                    memcpy(output_buffer + output_pos, buf, copy_size);
                    output_pos += copy_size;
                }
            }
            
            // Если процесс еще выполняется, добавляем небольшую задержку
            if (!done) {
                usleep(10000); // 10 мс
            }
        }
        
        // Закрываем пайпы
        close(stdout_pipe[0]);
        close(stderr_pipe[0]);
        
        // Читаем оставшиеся данные из буферов stdout и stderr
        char buf[4096];
        int bytes_read;
        
        // Переводим обратно в блокирующий режим для последнего чтения
        fcntl(stdout_pipe[0], F_SETFL, 0);
        fcntl(stderr_pipe[0], F_SETFL, 0);
        
        while ((bytes_read = read(stdout_pipe[0], buf, sizeof(buf) - 1)) > 0) {
            if (output_pos + bytes_read < MAX_OUTPUT_BUFFER - 1) {
                memcpy(output_buffer + output_pos, buf, bytes_read);
                output_pos += bytes_read;
            } else {
                break;
            }
        }
        
        while ((bytes_read = read(stderr_pipe[0], buf, sizeof(buf) - 1)) > 0) {
            if (output_pos + bytes_read < MAX_OUTPUT_BUFFER - 1) {
                memcpy(output_buffer + output_pos, buf, bytes_read);
                output_pos += bytes_read;
            } else {
                break;
            }
        }
        
        // Определяем статус завершения
        if (result->status != COMMAND_STATUS_TIMEOUT) {
            if (WIFEXITED(status)) {
                result->exit_code = WEXITSTATUS(status);
                result->status = COMMAND_STATUS_COMPLETED;
            } else if (WIFSIGNALED(status)) {
                result->exit_code = 128 + WTERMSIG(status);
                result->status = COMMAND_STATUS_ERROR;
            } else {
                result->exit_code = -1;
                result->status = COMMAND_STATUS_ERROR;
            }
        }
        
        // Засекаем время окончания выполнения
        gettimeofday(&end_time, NULL);
        
        // Вычисляем время выполнения в миллисекундах
        result->execution_time_ms = (end_time.tv_sec - start_time.tv_sec) * 1000 + 
                                   (end_time.tv_usec - start_time.tv_usec) / 1000;
        
        // Сохраняем вывод команды
        output_buffer[output_pos] = '\0';
        result->output = output_buffer;
        result->output_length = output_pos;
        
        // Обновляем статус команды
        cmd->status = result->status;
    }
    
    return result;
}
#endif

// Выполняет команду
CommandResult* command_execute(Command* cmd) {
    if (cmd == NULL) {
        set_last_error(3, "Invalid parameters");
        return NULL;
    }
    
    // Проверяем, что командная строка задана
    if (cmd->command_line == NULL) {
        set_last_error(3, "Command line not set");
        return NULL;
    }
    
    // Выполняем команду в зависимости от платформы
#ifdef _WIN32
    return execute_command_windows(cmd);
#else
    return execute_command_unix(cmd);
#endif
} 