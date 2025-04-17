/**
 * @file command_executor.c
 * @brief Implementation of the command execution module for NeuroZond.
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-04
 * 
 * This module provides functionality for executing system commands with various options and
 * security features to evade detection. It supports command execution with timeout, redirection
 * of output, and process hiding techniques.
 */

#include "../include/command_executor.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#include <process.h>
#else
#include <unistd.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <signal.h>
#include <pthread.h>
#include <fcntl.h>
#endif

#define MAX_OUTPUT_BUFFER 8192

typedef struct CommandExecutorContext {
    int initialized;
    int last_error;
    char error_message[256];
} CommandExecutorContext;

static CommandExecutorContext g_executor_ctx = {0};

/**
 * @brief Initializes the command executor
 * @return 1 on success, 0 on failure
 */
int command_executor_init(void) {
    if (g_executor_ctx.initialized) {
        return 1; // Already initialized
    }
    
    g_executor_ctx.initialized = 1;
    g_executor_ctx.last_error = 0;
    memset(g_executor_ctx.error_message, 0, sizeof(g_executor_ctx.error_message));
    
    return 1;
}

/**
 * @brief Creates a new command structure
 * @param type The type of command to create
 * @return A pointer to the new Command structure, or NULL on failure
 */
Command* command_create(CommandType type) {
    if (!g_executor_ctx.initialized) {
        return NULL;
    }
    
    Command* cmd = (Command*)calloc(1, sizeof(Command));
    if (!cmd) {
        g_executor_ctx.last_error = errno;
        strncpy(g_executor_ctx.error_message, "Failed to allocate memory for command", sizeof(g_executor_ctx.error_message) - 1);
        return NULL;
    }
    
    cmd->type = type;
    cmd->status = COMMAND_STATUS_CREATED;
    cmd->flags = 0;
    cmd->timeout_ms = 0; // No timeout by default
    
    return cmd;
}

/**
 * @brief Sets the command line for a command
 * @param cmd The command structure
 * @param command_line The command line to execute
 * @return 1 on success, 0 on failure
 */
int command_set_command_line(Command* cmd, const char* command_line) {
    if (!cmd || !command_line) {
        return 0;
    }
    
    if (cmd->command_line) {
        free(cmd->command_line);
    }
    
    cmd->command_line = strdup(command_line);
    if (!cmd->command_line) {
        g_executor_ctx.last_error = errno;
        strncpy(g_executor_ctx.error_message, "Failed to allocate memory for command line", sizeof(g_executor_ctx.error_message) - 1);
        return 0;
    }
    
    return 1;
}

/**
 * @brief Sets the working directory for a command
 * @param cmd The command structure
 * @param working_dir The working directory
 * @return 1 on success, 0 on failure
 */
int command_set_working_dir(Command* cmd, const char* working_dir) {
    if (!cmd || !working_dir) {
        return 0;
    }
    
    if (cmd->working_dir) {
        free(cmd->working_dir);
    }
    
    cmd->working_dir = strdup(working_dir);
    if (!cmd->working_dir) {
        g_executor_ctx.last_error = errno;
        strncpy(g_executor_ctx.error_message, "Failed to allocate memory for working directory", sizeof(g_executor_ctx.error_message) - 1);
        return 0;
    }
    
    return 1;
}

/**
 * @brief Sets the output file for a command
 * @param cmd The command structure
 * @param output_file The output file path
 * @return 1 on success, 0 on failure
 */
int command_set_output_file(Command* cmd, const char* output_file) {
    if (!cmd || !output_file) {
        return 0;
    }
    
    if (cmd->output_file) {
        free(cmd->output_file);
    }
    
    cmd->output_file = strdup(output_file);
    if (!cmd->output_file) {
        g_executor_ctx.last_error = errno;
        strncpy(g_executor_ctx.error_message, "Failed to allocate memory for output file", sizeof(g_executor_ctx.error_message) - 1);
        return 0;
    }
    
    return 1;
}

/**
 * @brief Sets the input data for a command
 * @param cmd The command structure
 * @param input_data The input data
 * @param input_length The length of the input data
 * @return 1 on success, 0 on failure
 */
int command_set_input_data(Command* cmd, const void* input_data, size_t input_length) {
    if (!cmd || (!input_data && input_length > 0)) {
        return 0;
    }
    
    if (cmd->input_data) {
        free(cmd->input_data);
        cmd->input_data = NULL;
        cmd->input_length = 0;
    }
    
    if (input_length > 0) {
        cmd->input_data = malloc(input_length);
        if (!cmd->input_data) {
            g_executor_ctx.last_error = errno;
            strncpy(g_executor_ctx.error_message, "Failed to allocate memory for input data", sizeof(g_executor_ctx.error_message) - 1);
            return 0;
        }
        
        memcpy(cmd->input_data, input_data, input_length);
        cmd->input_length = input_length;
    }
    
    return 1;
}

/**
 * @brief Sets command flags
 * @param cmd The command structure
 * @param flags The flags to set
 * @return 1 on success, 0 on failure
 */
int command_set_flags(Command* cmd, unsigned int flags) {
    if (!cmd) {
        return 0;
    }
    
    cmd->flags = flags;
    return 1;
}

/**
 * @brief Sets a timeout for command execution
 * @param cmd The command structure
 * @param timeout_ms The timeout in milliseconds
 * @return 1 on success, 0 on failure
 */
int command_set_timeout(Command* cmd, unsigned int timeout_ms) {
    if (!cmd) {
        return 0;
    }
    
    cmd->timeout_ms = timeout_ms;
    return 1;
}

/**
 * @brief Frees a command structure
 * @param cmd The command structure to free
 */
void command_free(Command* cmd) {
    if (!cmd) {
        return;
    }
    
    if (cmd->command_line) {
        free(cmd->command_line);
    }
    
    if (cmd->working_dir) {
        free(cmd->working_dir);
    }
    
    if (cmd->output_file) {
        free(cmd->output_file);
    }
    
    if (cmd->input_data) {
        free(cmd->input_data);
    }
    
    free(cmd);
}

/**
 * @brief Frees a command result structure
 * @param result The command result structure to free
 */
void command_result_free(CommandResult* result) {
    if (!result) {
        return;
    }
    
    if (result->output) {
        free(result->output);
    }
    
    free(result);
}

#ifdef _WIN32
// Windows-specific implementation of command execution
static CommandResult* execute_command_windows(Command* cmd) {
    CommandResult* result = (CommandResult*)calloc(1, sizeof(CommandResult));
    if (!result) {
        g_executor_ctx.last_error = errno;
        strncpy(g_executor_ctx.error_message, "Failed to allocate memory for command result", sizeof(g_executor_ctx.error_message) - 1);
        return NULL;
    }
    
    result->start_time = time(NULL);
    
    SECURITY_ATTRIBUTES sa;
    HANDLE hReadPipe = NULL, hWritePipe = NULL;
    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    char* output = NULL;
    DWORD bytesRead, totalBytes = 0;
    DWORD exitCode = 0;
    
    // Set up security attributes for pipe
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.bInheritHandle = TRUE;
    sa.lpSecurityDescriptor = NULL;
    
    // Create pipe for command output
    if (!CreatePipe(&hReadPipe, &hWritePipe, &sa, 0)) {
        g_executor_ctx.last_error = GetLastError();
        result->exit_code = -1;
        result->status = COMMAND_STATUS_FAILED;
        strncpy(g_executor_ctx.error_message, "Failed to create pipe", sizeof(g_executor_ctx.error_message) - 1);
        return result;
    }
    
    // Ensure the read handle is not inherited
    SetHandleInformation(hReadPipe, HANDLE_FLAG_INHERIT, 0);
    
    // Set up process startup info
    ZeroMemory(&si, sizeof(STARTUPINFO));
    si.cb = sizeof(STARTUPINFO);
    si.hStdError = hWritePipe;
    si.hStdOutput = hWritePipe;
    si.dwFlags |= STARTF_USESTDHANDLES;
    
    // If input data is provided, set up stdin redirection
    HANDLE hInputRead = NULL, hInputWrite = NULL;
    if (cmd->input_data && cmd->input_length > 0) {
        if (!CreatePipe(&hInputRead, &hInputWrite, &sa, 0)) {
            g_executor_ctx.last_error = GetLastError();
            CloseHandle(hReadPipe);
            CloseHandle(hWritePipe);
            result->exit_code = -1;
            result->status = COMMAND_STATUS_FAILED;
            strncpy(g_executor_ctx.error_message, "Failed to create input pipe", sizeof(g_executor_ctx.error_message) - 1);
            return result;
        }
        
        SetHandleInformation(hInputWrite, HANDLE_FLAG_INHERIT, 0);
        si.hStdInput = hInputRead;
    } else {
        // No input data, use default stdin
        si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    }
    
    // Create the process
    if (!CreateProcess(NULL, cmd->command_line, NULL, NULL, TRUE, 
                      ((cmd->flags & COMMAND_FLAG_HIDDEN) ? CREATE_NO_WINDOW : 0), 
                      NULL, cmd->working_dir, &si, &pi)) {
        g_executor_ctx.last_error = GetLastError();
        CloseHandle(hReadPipe);
        CloseHandle(hWritePipe);
        if (hInputRead) CloseHandle(hInputRead);
        if (hInputWrite) CloseHandle(hInputWrite);
        result->exit_code = -1;
        result->status = COMMAND_STATUS_FAILED;
        snprintf(g_executor_ctx.error_message, sizeof(g_executor_ctx.error_message) - 1, 
                "Failed to create process: %d", g_executor_ctx.last_error);
        return result;
    }
    
    // Write input data if provided
    if (cmd->input_data && cmd->input_length > 0 && hInputWrite) {
        DWORD bytesWritten;
        WriteFile(hInputWrite, cmd->input_data, cmd->input_length, &bytesWritten, NULL);
        CloseHandle(hInputWrite);
    }
    
    // Close write end of pipe
    CloseHandle(hWritePipe);
    if (hInputRead) CloseHandle(hInputRead);
    
    // Allocate buffer for output
    output = (char*)malloc(MAX_OUTPUT_BUFFER);
    if (!output) {
        CloseHandle(hReadPipe);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
        result->exit_code = -1;
        result->status = COMMAND_STATUS_FAILED;
        strncpy(g_executor_ctx.error_message, "Failed to allocate memory for output buffer", sizeof(g_executor_ctx.error_message) - 1);
        return result;
    }
    
    // Read output from pipe
    char buffer[4096];
    BOOL bSuccess = FALSE;
    
    while (1) {
        bSuccess = ReadFile(hReadPipe, buffer, sizeof(buffer) - 1, &bytesRead, NULL);
        if (!bSuccess || bytesRead == 0) break;
        
        // Ensure buffer has enough space
        if (totalBytes + bytesRead >= MAX_OUTPUT_BUFFER) {
            char* new_output = (char*)realloc(output, totalBytes + bytesRead + 1);
            if (!new_output) {
                free(output);
                CloseHandle(hReadPipe);
                CloseHandle(pi.hProcess);
                CloseHandle(pi.hThread);
                result->exit_code = -1;
                result->status = COMMAND_STATUS_FAILED;
                strncpy(g_executor_ctx.error_message, "Failed to reallocate memory for output buffer", sizeof(g_executor_ctx.error_message) - 1);
                return result;
            }
            output = new_output;
        }
        
        memcpy(output + totalBytes, buffer, bytesRead);
        totalBytes += bytesRead;
        output[totalBytes] = '\0';
    }
    
    // Wait for process to complete or timeout
    DWORD waitResult;
    if (cmd->timeout_ms > 0) {
        waitResult = WaitForSingleObject(pi.hProcess, cmd->timeout_ms);
        if (waitResult == WAIT_TIMEOUT) {
            TerminateProcess(pi.hProcess, 1);
            result->status = COMMAND_STATUS_TIMEOUT;
            result->exit_code = -1;
        }
    } else {
        waitResult = WaitForSingleObject(pi.hProcess, INFINITE);
    }
    
    // Get exit code
    GetExitCodeProcess(pi.hProcess, &exitCode);
    result->exit_code = exitCode;
    
    if (waitResult == WAIT_OBJECT_0) {
        result->status = (exitCode == 0) ? COMMAND_STATUS_COMPLETED : COMMAND_STATUS_ERROR;
    }
    
    // Clean up
    CloseHandle(hReadPipe);
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    
    result->output = output;
    result->output_length = totalBytes;
    result->end_time = time(NULL);
    
    return result;
}
#else
// Unix-specific implementation of command execution
typedef struct {
    Command* cmd;
    pthread_t thread;
    int pipe_fd[2];
    pid_t child_pid;
    int status;
    CommandResult* result;
} CommandThread;

static void* timeout_thread(void* arg) {
    CommandThread* cmd_thread = (CommandThread*)arg;
    sleep(cmd_thread->cmd->timeout_ms / 1000);
    
    // Check if the process is still running
    int status;
    pid_t result = waitpid(cmd_thread->child_pid, &status, WNOHANG);
    if (result == 0) {
        // Process is still running, kill it
        kill(cmd_thread->child_pid, SIGKILL);
        cmd_thread->status = COMMAND_STATUS_TIMEOUT;
    }
    
    return NULL;
}

static CommandResult* execute_command_unix(Command* cmd) {
    CommandResult* result = (CommandResult*)calloc(1, sizeof(CommandResult));
    if (!result) {
        g_executor_ctx.last_error = errno;
        strncpy(g_executor_ctx.error_message, "Failed to allocate memory for command result", sizeof(g_executor_ctx.error_message) - 1);
        return NULL;
    }
    
    result->start_time = time(NULL);
    
    int pipe_fd[2];
    int input_pipe_fd[2] = {-1, -1};
    pid_t pid;
    
    // Create pipe for command output
    if (pipe(pipe_fd) < 0) {
        g_executor_ctx.last_error = errno;
        result->exit_code = -1;
        result->status = COMMAND_STATUS_FAILED;
        strncpy(g_executor_ctx.error_message, "Failed to create pipe", sizeof(g_executor_ctx.error_message) - 1);
        return result;
    }
    
    // Create pipe for command input if needed
    if (cmd->input_data && cmd->input_length > 0) {
        if (pipe(input_pipe_fd) < 0) {
            g_executor_ctx.last_error = errno;
            close(pipe_fd[0]);
            close(pipe_fd[1]);
            result->exit_code = -1;
            result->status = COMMAND_STATUS_FAILED;
            strncpy(g_executor_ctx.error_message, "Failed to create input pipe", sizeof(g_executor_ctx.error_message) - 1);
            return result;
        }
    }
    
    // Fork process
    pid = fork();
    
    if (pid < 0) {
        // Fork failed
        g_executor_ctx.last_error = errno;
        close(pipe_fd[0]);
        close(pipe_fd[1]);
        if (input_pipe_fd[0] >= 0) close(input_pipe_fd[0]);
        if (input_pipe_fd[1] >= 0) close(input_pipe_fd[1]);
        result->exit_code = -1;
        result->status = COMMAND_STATUS_FAILED;
        strncpy(g_executor_ctx.error_message, "Failed to fork process", sizeof(g_executor_ctx.error_message) - 1);
        return result;
    } else if (pid == 0) {
        // Child process
        
        // Redirect stdout and stderr to pipe
        close(pipe_fd[0]);  // Close read end
        dup2(pipe_fd[1], STDOUT_FILENO);
        dup2(pipe_fd[1], STDERR_FILENO);
        close(pipe_fd[1]);
        
        // Redirect stdin from input pipe if needed
        if (input_pipe_fd[0] >= 0) {
            close(input_pipe_fd[1]);  // Close write end
            dup2(input_pipe_fd[0], STDIN_FILENO);
            close(input_pipe_fd[0]);
        }
        
        // Change working directory if specified
        if (cmd->working_dir) {
            if (chdir(cmd->working_dir) != 0) {
                exit(1);
            }
        }
        
        // Execute command
        execl("/bin/sh", "sh", "-c", cmd->command_line, NULL);
        
        // If execl returns, it failed
        exit(1);
    }
    
    // Parent process
    close(pipe_fd[1]); // Close write end
    
    // Write input data if provided
    if (input_pipe_fd[1] >= 0) {
        close(input_pipe_fd[0]); // Close read end
        write(input_pipe_fd[1], cmd->input_data, cmd->input_length);
        close(input_pipe_fd[1]);
    }
    
    // Start timeout thread if timeout is specified
    pthread_t timeout_tid;
    CommandThread cmd_thread;
    if (cmd->timeout_ms > 0) {
        cmd_thread.cmd = cmd;
        cmd_thread.child_pid = pid;
        cmd_thread.status = COMMAND_STATUS_RUNNING;
        cmd_thread.result = result;
        
        if (pthread_create(&timeout_tid, NULL, timeout_thread, &cmd_thread) != 0) {
            g_executor_ctx.last_error = errno;
            strncpy(g_executor_ctx.error_message, "Failed to create timeout thread", sizeof(g_executor_ctx.error_message) - 1);
        }
    }
    
    // Read output from pipe
    char buffer[4096];
    char* output = (char*)malloc(MAX_OUTPUT_BUFFER);
    if (!output) {
        close(pipe_fd[0]);
        result->exit_code = -1;
        result->status = COMMAND_STATUS_FAILED;
        strncpy(g_executor_ctx.error_message, "Failed to allocate memory for output buffer", sizeof(g_executor_ctx.error_message) - 1);
        return result;
    }
    
    size_t total_bytes = 0;
    ssize_t bytes_read;
    
    while ((bytes_read = read(pipe_fd[0], buffer, sizeof(buffer) - 1)) > 0) {
        // Ensure buffer has enough space
        if (total_bytes + bytes_read >= MAX_OUTPUT_BUFFER) {
            char* new_output = (char*)realloc(output, total_bytes + bytes_read + 1);
            if (!new_output) {
                free(output);
                close(pipe_fd[0]);
                result->exit_code = -1;
                result->status = COMMAND_STATUS_FAILED;
                strncpy(g_executor_ctx.error_message, "Failed to reallocate memory for output buffer", sizeof(g_executor_ctx.error_message) - 1);
                return result;
            }
            output = new_output;
        }
        
        memcpy(output + total_bytes, buffer, bytes_read);
        total_bytes += bytes_read;
        output[total_bytes] = '\0';
    }
    
    close(pipe_fd[0]);
    
    // Wait for process to complete
    int status;
    waitpid(pid, &status, 0);
    
    // Join timeout thread if it was created
    if (cmd->timeout_ms > 0) {
        pthread_cancel(timeout_tid);
        pthread_join(timeout_tid, NULL);
        
        if (cmd_thread.status == COMMAND_STATUS_TIMEOUT) {
            result->status = COMMAND_STATUS_TIMEOUT;
            result->exit_code = -1;
        } else {
            if (WIFEXITED(status)) {
                result->exit_code = WEXITSTATUS(status);
                result->status = (result->exit_code == 0) ? COMMAND_STATUS_COMPLETED : COMMAND_STATUS_ERROR;
            } else {
                result->exit_code = -1;
                result->status = COMMAND_STATUS_ERROR;
            }
        }
    } else {
        if (WIFEXITED(status)) {
            result->exit_code = WEXITSTATUS(status);
            result->status = (result->exit_code == 0) ? COMMAND_STATUS_COMPLETED : COMMAND_STATUS_ERROR;
        } else {
            result->exit_code = -1;
            result->status = COMMAND_STATUS_ERROR;
        }
    }
    
    result->output = output;
    result->output_length = total_bytes;
    result->end_time = time(NULL);
    
    return result;
}
#endif

/**
 * @brief Executes a command
 * @param cmd The command structure
 * @return A pointer to a CommandResult structure, or NULL on failure
 */
CommandResult* command_execute(Command* cmd) {
    if (!g_executor_ctx.initialized || !cmd || !cmd->command_line) {
        return NULL;
    }
    
    cmd->status = COMMAND_STATUS_RUNNING;
    
#ifdef _WIN32
    return execute_command_windows(cmd);
#else
    return execute_command_unix(cmd);
#endif
}

/**
 * @brief Gets the last error code
 * @return The last error code
 */
int command_executor_get_last_error(void) {
    return g_executor_ctx.last_error;
}

/**
 * @brief Gets the last error message
 * @return The last error message
 */
const char* command_executor_get_error_message(void) {
    return g_executor_ctx.error_message;
}

/**
 * @brief Cleans up the command executor
 */
void command_executor_cleanup(void) {
    if (!g_executor_ctx.initialized) {
        return;
    }
    
    g_executor_ctx.initialized = 0;
    g_executor_ctx.last_error = 0;
    memset(g_executor_ctx.error_message, 0, sizeof(g_executor_ctx.error_message));
} 