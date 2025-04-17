CC = gcc
CFLAGS = -Wall -Wextra -g -O0
LDFLAGS = -lm

# Директории
SRC_DIR = ../
TEST_DIR = ./
BUILD_DIR = ./build

# Исходные файлы
TEST_SRC = $(wildcard $(TEST_DIR)*.c)
SRC_FILES = $(SRC_DIR)/network/covert_channel.c \
           $(SRC_DIR)/network/dns_channel.c

# Объектные файлы
TEST_OBJ = $(patsubst $(TEST_DIR)%.c,$(BUILD_DIR)/%.o,$(TEST_SRC))
SRC_OBJ = $(patsubst $(SRC_DIR)%.c,$(BUILD_DIR)/%.o,$(SRC_FILES))

# Исполняемые файлы
TEST_BIN = $(patsubst $(TEST_DIR)%.c,$(BUILD_DIR)/%,$(TEST_SRC))

# Создание директорий
$(shell mkdir -p $(BUILD_DIR))
$(shell mkdir -p $(BUILD_DIR)/network)

# Правило по умолчанию
all: $(TEST_BIN)

# Компиляция тестов
$(BUILD_DIR)/test_covert_channel: $(BUILD_DIR)/test_covert_channel.o $(SRC_OBJ)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Компиляция объектных файлов тестов
$(BUILD_DIR)/%.o: $(TEST_DIR)%.c
	$(CC) $(CFLAGS) -I$(SRC_DIR) -c $< -o $@

# Компиляция объектных файлов исходников
$(BUILD_DIR)/%.o: $(SRC_DIR)%.c
	mkdir -p $(dir $@)
	$(CC) $(CFLAGS) -I$(SRC_DIR) -c $< -o $@

# Запуск тестов
run: $(TEST_BIN)
	@echo "Running tests..."
	@for test in $^; do \
		echo "\nRunning $$test"; \
		$$test; \
	done

# Очистка
clean:
	rm -rf $(BUILD_DIR)

.PHONY: all run clean 