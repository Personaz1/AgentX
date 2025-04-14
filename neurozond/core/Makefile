# Makefile для компиляции модуля обхода EDR и примеров
# Версия для Windows с использованием MinGW

# Компилятор и флаги
CC = gcc
CFLAGS = -Wall -Wextra -O2 -I.
LDFLAGS = -lpsapi -ladvapi32

# Директории
CORE_DIR = .
EXAMPLES_DIR = ../examples
TESTS_DIR = ../tests
OBJ_DIR = ../obj
BIN_DIR = ../bin

# Исходные файлы
CORE_SRCS = $(CORE_DIR)/edr_evasion.c $(CORE_DIR)/process_masquerading.c
EXAMPLES_SRCS = $(EXAMPLES_DIR)/edr_evasion_demo.c
TESTS_SRCS = $(TESTS_DIR)/edr_evasion_test.c

# Объектные файлы
CORE_OBJS = $(patsubst $(CORE_DIR)/%.c, $(OBJ_DIR)/%.o, $(CORE_SRCS))
EXAMPLES_OBJS = $(patsubst $(EXAMPLES_DIR)/%.c, $(OBJ_DIR)/%.o, $(EXAMPLES_SRCS))
TESTS_OBJS = $(patsubst $(TESTS_DIR)/%.c, $(OBJ_DIR)/%.o, $(TESTS_SRCS))

# Исполняемые файлы
EXAMPLES_BINS = $(patsubst $(EXAMPLES_DIR)/%.c, $(BIN_DIR)/%.exe, $(EXAMPLES_SRCS))
TESTS_BINS = $(patsubst $(TESTS_DIR)/%.c, $(BIN_DIR)/%.exe, $(TESTS_SRCS))

# Цели
.PHONY: all clean directories examples tests

all: directories examples tests

# Создание директорий
directories:
	@mkdir -p $(OBJ_DIR)
	@mkdir -p $(BIN_DIR)

# Компиляция основных модулей
$(OBJ_DIR)/%.o: $(CORE_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# Компиляция примеров
$(OBJ_DIR)/%.o: $(EXAMPLES_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# Компиляция тестов
$(OBJ_DIR)/%.o: $(TESTS_DIR)/%.c
	$(CC) $(CFLAGS) -c $< -o $@

# Линковка примеров
$(BIN_DIR)/edr_evasion_demo.exe: $(OBJ_DIR)/edr_evasion_demo.o $(OBJ_DIR)/edr_evasion.o
	$(CC) $^ -o $@ $(LDFLAGS)

# Линковка тестов
$(BIN_DIR)/edr_evasion_test.exe: $(OBJ_DIR)/edr_evasion_test.o $(OBJ_DIR)/edr_evasion.o
	$(CC) $^ -o $@ $(LDFLAGS)

# Сборка примеров
examples: $(EXAMPLES_BINS)

# Сборка тестов
tests: $(TESTS_BINS)

# Очистка
clean:
	rm -rf $(OBJ_DIR)/*.o
	rm -rf $(BIN_DIR)/*.exe

# Запуск примеров
run-examples: examples
	$(BIN_DIR)/edr_evasion_demo.exe

# Запуск тестов
run-tests: tests
	$(BIN_DIR)/edr_evasion_test.exe 