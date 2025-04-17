CC = gcc
CFLAGS = -Wall -Wextra -Werror -O2 -g
LDFLAGS = 

# В зависимости от операционной системы добавляем нужные флаги и библиотеки
ifeq ($(OS),Windows_NT)
    CFLAGS += -D_WIN32
    LDFLAGS += -lws2_32
else
    CFLAGS += -D_POSIX_C_SOURCE=200809L
    LDFLAGS += -lcrypto -lssl
endif

SRC_DIR = .
TEST_DIR = tests
BUILD_DIR = build
BIN_DIR = bin

# Исходные файлы
# Добавляем поиск .c файлов в директории injection
SOURCES = $(wildcard $(SRC_DIR)/*.c $(SRC_DIR)/network/*.c $(SRC_DIR)/executor/*.c $(SRC_DIR)/crypto/*.c $(SRC_DIR)/core/*.c $(SRC_DIR)/injection/*.c)
TEST_SOURCES = $(wildcard $(TEST_DIR)/*.c)

# Объектные файлы
OBJECTS = $(SOURCES:%.c=$(BUILD_DIR)/%.o)
TEST_OBJECTS = $(TEST_SOURCES:%.c=$(BUILD_DIR)/%.o)

# Исполняемые файлы
TARGET = $(BIN_DIR)/neurozond
TEST_TARGETS = $(TEST_SOURCES:$(TEST_DIR)/%.c=$(BIN_DIR)/%)

# Создание папок
# Добавляем создание поддиректорий для объектных файлов
$(shell mkdir -p $(BUILD_DIR) $(BIN_DIR) \
                   $(patsubst %/,$(BUILD_DIR)/%/,$(sort $(dir $(SOURCES)))) \
                   $(patsubst %/,$(BUILD_DIR)/%/,$(sort $(dir $(TEST_SOURCES)))) )

# Правило для основного бинарного файла
$(TARGET): $(OBJECTS)
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Правило для объектных файлов основной программы
$(BUILD_DIR)/%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# Правила для тестов
$(BIN_DIR)/test_%: $(BUILD_DIR)/$(TEST_DIR)/test_%.o
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

# Правило для компиляции всех тестов
tests: $(TEST_TARGETS)

# Правило для запуска всех тестов
run_tests: tests
	@echo "Запуск всех тестов..."
	@for test in $(TEST_TARGETS); do \
		echo "Выполнение $$test"; \
		$$test; \
		if [ $$? -ne 0 ]; then \
			echo "Тест $$test завершился с ошибкой!"; \
			exit 1; \
		fi; \
	done
	@echo "Все тесты выполнены успешно!"

# Правило для run_test_dns_channel
run_test_dns_channel: $(BIN_DIR)/test_dns_channel
	$(BIN_DIR)/test_dns_channel

# Правило для run_test_https_channel
run_test_https_channel: $(BIN_DIR)/test_https_channel
	$(BIN_DIR)/test_https_channel

# Правило для run_test_icmp_channel
run_test_icmp_channel: $(BIN_DIR)/test_icmp_channel
	$(BIN_DIR)/test_icmp_channel

# Правило для run_test_main
run_test_main: $(BIN_DIR)/test_main
	$(BIN_DIR)/test_main

# Правило для run_test_crypto
run_test_crypto: $(BIN_DIR)/test_crypto
	$(BIN_DIR)/test_crypto

# Очистка сборки
clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)

# Цель по умолчанию
all: $(TARGET) tests

.PHONY: all clean tests run_tests run_test_dns_channel run_test_https_channel run_test_icmp_channel run_test_main run_test_crypto 