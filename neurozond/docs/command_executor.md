# Модуль выполнения команд NeuroZond

## Описание

Модуль выполнения команд (`command_executor`) предназначен для выполнения системных команд на целевой системе. Он позволяет запускать команды оболочки (shell) и отдельные процессы, управлять их параметрами, перенаправлять ввод-вывод и обрабатывать результаты выполнения.

Модуль имеет кроссплатформенную реализацию, поддерживающую как UNIX-подобные системы, так и Windows.

## Основные возможности

* Запуск команд через системную оболочку или напрямую
* Перенаправление стандартного ввода и вывода
* Контроль тайм-аута выполнения команд
* Задание рабочего каталога для выполнения команд
* Управление видимостью процесса (скрытый режим)
* Подробная информация о результатах выполнения (статус, код возврата, время выполнения)
* Обработка ошибок с подробными сообщениями

## Структура модуля

* `command_executor.h` - заголовочный файл с определениями типов и функций
* `command_executor.c` - основная реализация модуля
* `command_executor_example.c` - пример использования модуля
* `test_command_executor.c` - тесты модуля

## API модуля

### Типы данных

#### CommandType

Тип команды определяет, каким образом будет выполнена команда:

```c
typedef enum {
    COMMAND_TYPE_UNKNOWN = 0,
    COMMAND_TYPE_SHELL = 1,    // Выполнение через системную оболочку
    COMMAND_TYPE_PROCESS = 2   // Запуск как отдельный процесс
} CommandType;
```

#### CommandStatus

Статус выполнения команды:

```c
typedef enum {
    COMMAND_STATUS_UNKNOWN = 0,
    COMMAND_STATUS_CREATED = 1,    // Команда создана, но не выполнена
    COMMAND_STATUS_RUNNING = 2,    // Команда выполняется
    COMMAND_STATUS_COMPLETED = 3,  // Команда успешно завершена
    COMMAND_STATUS_ERROR = 4,      // Ошибка при выполнении команды
    COMMAND_STATUS_TIMEOUT = 5,    // Превышено время выполнения команды
    COMMAND_STATUS_CANCELED = 6    // Выполнение команды отменено
} CommandStatus;
```

#### CommandFlags

Флаги для управления поведением команды:

```c
typedef enum {
    COMMAND_FLAG_NONE = 0,                  // Без флагов
    COMMAND_FLAG_HIDDEN = (1 << 0),         // Скрытый режим
    COMMAND_FLAG_NO_WINDOW = (1 << 1),      // Без окна (только Windows)
    COMMAND_FLAG_ELEVATED = (1 << 2),       // Повышенные привилегии
    COMMAND_FLAG_DETACHED = (1 << 3),       // Отсоединенный процесс
    COMMAND_FLAG_NO_OUTPUT = (1 << 4)       // Без сбора вывода
} CommandFlags;
```

#### Command

Структура для хранения параметров команды:

```c
typedef struct {
    CommandType type;              // Тип команды
    CommandStatus status;          // Статус выполнения
    char* command_line;            // Командная строка
    char* working_dir;             // Рабочая директория
    char* output_file;             // Файл для вывода (если нужно)
    char* input_data;              // Входные данные
    size_t input_length;           // Длина входных данных
    CommandFlags flags;            // Флаги команды
    uint32_t timeout_ms;           // Тайм-аут в миллисекундах
    void* platform_data;           // Платформо-зависимые данные
} Command;
```

#### CommandResult

Структура для хранения результатов выполнения команды:

```c
typedef struct {
    CommandStatus status;         // Статус выполнения
    int exit_code;                // Код возврата
    char* output;                 // Вывод команды
    size_t output_length;         // Длина вывода
    uint32_t execution_time_ms;   // Время выполнения в мс
} CommandResult;
```

### Функции

#### Инициализация и очистка

```c
int command_executor_init(void);
void command_executor_cleanup(void);
```

#### Создание и управление командой

```c
Command* command_create(CommandType type);
void command_free(Command* cmd);

int command_set_command_line(Command* cmd, const char* command_line);
int command_set_working_dir(Command* cmd, const char* working_dir);
int command_set_output_file(Command* cmd, const char* output_file);
int command_set_input_data(Command* cmd, const char* input_data, size_t input_length);
int command_set_flags(Command* cmd, CommandFlags flags);
int command_set_timeout(Command* cmd, uint32_t timeout_ms);
```

#### Выполнение команды

```c
CommandResult* command_execute(Command* cmd);
void command_result_free(CommandResult* result);
```

#### Обработка ошибок

```c
int command_executor_get_last_error(void);
const char* command_executor_get_error_message(void);
```

## Примеры использования

### Простой пример выполнения команды

```c
#include "command_executor.h"
#include <stdio.h>

int main() {
    // Инициализация модуля
    command_executor_init();
    
    // Создание команды
    Command* cmd = command_create(COMMAND_TYPE_SHELL);
    
    // Настройка параметров команды
    command_set_command_line(cmd, "echo Hello, World!");
    
    // Выполнение команды
    CommandResult* result = command_execute(cmd);
    
    // Вывод результатов
    if (result) {
        printf("Status: %d\n", result->status);
        printf("Exit code: %d\n", result->exit_code);
        printf("Output: %s\n", result->output);
        
        // Освобождение результата
        command_result_free(result);
    }
    
    // Освобождение команды
    command_free(cmd);
    
    // Очистка модуля
    command_executor_cleanup();
    
    return 0;
}
```

### Выполнение команды с тайм-аутом

```c
Command* cmd = command_create(COMMAND_TYPE_SHELL);
command_set_command_line(cmd, "sleep 10");
command_set_timeout(cmd, 5000); // 5 секунд

CommandResult* result = command_execute(cmd);

if (result && result->status == COMMAND_STATUS_TIMEOUT) {
    printf("Command timed out after 5 seconds\n");
}

command_result_free(result);
command_free(cmd);
```

### Скрытый режим

```c
Command* cmd = command_create(COMMAND_TYPE_SHELL);
command_set_command_line(cmd, "ping -c 4 localhost");
command_set_flags(cmd, COMMAND_FLAG_HIDDEN);

CommandResult* result = command_execute(cmd);
// Проверка результатов...

command_result_free(result);
command_free(cmd);
```

### Использование входных данных

```c
Command* cmd = command_create(COMMAND_TYPE_SHELL);
command_set_command_line(cmd, "grep pattern");

const char* input_data = "This line has a pattern\nThis line doesn't\nAnother pattern here\n";
command_set_input_data(cmd, input_data, strlen(input_data));

CommandResult* result = command_execute(cmd);
// Вывод будет содержать только строки с "pattern"

command_result_free(result);
command_free(cmd);
```

## Особенности реализации

### Windows

На платформе Windows модуль использует функции Windows API:
- `CreateProcess` для запуска процессов
- `CreatePipe` для создания каналов
- `ReadFile` и `WriteFile` для чтения и записи в каналы
- `WaitForSingleObject` для ожидания завершения процесса
- `TerminateProcess` для принудительного завершения

### UNIX-подобные системы

На UNIX-подобных системах (Linux, macOS) модуль использует системные вызовы:
- `fork` и `execl`/`execvp` для создания процессов
- `pipe` для создания каналов
- `read` и `write` для чтения и записи
- `waitpid` для ожидания завершения процесса
- `kill` для принудительного завершения

## Возможные расширения

* Асинхронное выполнение команд
* Поддержка перенаправления stderr отдельно от stdout
* Возможность прерывания выполнения команды
* Сбор дополнительной информации о процессе (использование CPU, памяти)
* Запуск с другими учетными данными пользователя
* Ограничение использования ресурсов (ulimit, job objects)

## Известные ограничения

* Ограниченный размер буфера вывода (1 МБ по умолчанию)
* На Windows не реализовано выполнение команд (требуется доработка)
* Упрощенный разбор командной строки для режима COMMAND_TYPE_PROCESS
* Нет поддержки интерактивных команд
* Нет поддержки установки переменных окружения 