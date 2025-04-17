/**
 * @file command_executor.h
 * @brief Header file for command execution module.
 * @author iamtomasanderson@gmail.com
 * @date 2023-09-04
 * 
 * This module provides functionality for executing system commands with various 
 * options and security features to evade detection.
 */

#ifndef COMMAND_EXECUTOR_H
#define COMMAND_EXECUTOR_H

#include <stdint.h>
#include <stddef.h>

/**
 * @brief Types of commands that can be executed
 */
typedef enum {
    COMMAND_TYPE_SHELL = 1,  ///< Shell command
    COMMAND_TYPE_PROCESS = 2, ///< Direct process execution
    COMMAND_TYPE_POWERSHELL = 3, ///< PowerShell command (Windows only)
    COMMAND_TYPE_UNKNOWN = 0 ///< Unknown command type
} CommandType;

/**
 * @brief Command execution status
 */
typedef enum {
    COMMAND_STATUS_CREATED = 0,    ///< Command has been created but not executed
    COMMAND_STATUS_RUNNING = 1,    ///< Command is currently running
    COMMAND_STATUS_COMPLETED = 2,   ///< Command has completed successfully
    COMMAND_STATUS_ERROR = 3,       ///< Command failed to execute
    COMMAND_STATUS_TIMEOUT = 4,     ///< Command execution timed out
    COMMAND_STATUS_CANCELED = 5,    ///< Command was canceled
    COMMAND_STATUS_FAILED = 6       ///< Command failed to start
} CommandStatus;

/**
 * @brief Command execution flags
 */
typedef enum {
    COMMAND_FLAG_NONE = 0,
    COMMAND_FLAG_HIDDEN = (1 << 0),      ///< Hide the command window
    COMMAND_FLAG_NO_OUTPUT = (1 << 1),   ///< Do not capture command output
    COMMAND_FLAG_DETACHED = (1 << 2),    ///< Run the command detached from the parent process
    COMMAND_FLAG_ELEVATED = (1 << 3),    ///< Run with elevated privileges if possible
    COMMAND_FLAG_BACKGROUND = (1 << 4),   ///< Run command in background
    COMMAND_FLAG_UNKNOWN = 0xFFFFFFFF   ///< Unknown command flag
} CommandFlags;

/**
 * @brief Structure for command execution
 */
typedef struct {
    CommandType type;         ///< Type of command
    CommandStatus status;     ///< Current status of the command
    char* command_line;       ///< Command line to execute
    char* working_dir;        ///< Working directory for the command
    char* output_file;        ///< File to redirect output to
    char* input_data;         ///< Input data for the command
    size_t input_length;      ///< Length of input data
    CommandFlags flags;        ///< Command flags
    uint32_t timeout_ms;       ///< Timeout in milliseconds (0 = no timeout)
    void* platform_data;      ///< Platform-specific data
} Command;

/**
 * @brief Structure for command execution result
 */
typedef struct {
    CommandStatus status;      ///< Status of the command
    int exit_code;             ///< Exit code of the command
    char* output;              ///< Output of the command
    size_t output_length;      ///< Length of the output
    uint32_t execution_time_ms; ///< Execution time in milliseconds
} CommandResult;

/**
 * @brief Initializes the command executor
 * @return 1 on success, 0 on failure
 */
int command_executor_init(void);

/**
 * @brief Creates a new command structure
 * @param type The type of command to create
 * @return A pointer to the new Command structure, or NULL on failure
 */
Command* command_create(CommandType type);

/**
 * @brief Sets the command line for a command
 * @param cmd The command structure
 * @param command_line The command line to execute
 * @return 1 on success, 0 on failure
 */
int command_set_command_line(Command* cmd, const char* command_line);

/**
 * @brief Sets the working directory for a command
 * @param cmd The command structure
 * @param working_dir The working directory
 * @return 1 on success, 0 on failure
 */
int command_set_working_dir(Command* cmd, const char* working_dir);

/**
 * @brief Sets the output file for a command
 * @param cmd The command structure
 * @param output_file The output file path
 * @return 1 on success, 0 on failure
 */
int command_set_output_file(Command* cmd, const char* output_file);

/**
 * @brief Sets the input data for a command
 * @param cmd The command structure
 * @param input_data The input data
 * @param input_length The length of the input data
 * @return 1 on success, 0 on failure
 */
int command_set_input_data(Command* cmd, const char* input_data, size_t input_length);

/**
 * @brief Sets command flags
 * @param cmd The command structure
 * @param flags The flags to set
 * @return 1 on success, 0 on failure
 */
int command_set_flags(Command* cmd, CommandFlags flags);

/**
 * @brief Sets a timeout for command execution
 * @param cmd The command structure
 * @param timeout_ms The timeout in milliseconds
 * @return 1 on success, 0 on failure
 */
int command_set_timeout(Command* cmd, uint32_t timeout_ms);

/**
 * @brief Executes a command
 * @param cmd The command structure
 * @return A pointer to a CommandResult structure, or NULL on failure
 */
CommandResult* command_execute(Command* cmd);

/**
 * @brief Gets the last error code
 * @return The last error code
 */
int command_executor_get_last_error(void);

/**
 * @brief Gets the last error message
 * @return The last error message
 */
const char* command_executor_get_error_message(void);

/**
 * @brief Frees a command structure
 * @param cmd The command structure to free
 */
void command_free(Command* cmd);

/**
 * @brief Frees a command result structure
 * @param result The command result structure to free
 */
void command_result_free(CommandResult* result);

/**
 * @brief Cleans up the command executor
 */
void command_executor_cleanup(void);

#endif /* COMMAND_EXECUTOR_H */ 