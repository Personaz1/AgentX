#!/bin/bash

# Скрипт для сборки проекта NeuroZond

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
RESET='\033[0m'

# Проверка наличия необходимых утилит
check_dependencies() {
    echo -e "${BLUE}Проверка зависимостей...${RESET}"
    
    # Проверка наличия компилятора gcc
    if ! command -v gcc &> /dev/null; then
        echo -e "${RED}Ошибка: компилятор GCC не найден. Установите GCC.${RESET}"
        exit 1
    fi
    
    # Проверка наличия make
    if ! command -v make &> /dev/null; then
        echo -e "${RED}Ошибка: утилита make не найдена. Установите make.${RESET}"
        exit 1
    fi
    
    echo -e "${GREEN}Все зависимости установлены.${RESET}"
}

# Создание необходимых директорий
create_directories() {
    echo -e "${BLUE}Создание директорий...${RESET}"
    
    mkdir -p build
    mkdir -p include
    mkdir -p executor
    mkdir -p crypto
    mkdir -p network
    mkdir -p tests
    mkdir -p examples
    
    echo -e "${GREEN}Директории созданы.${RESET}"
}

# Компиляция проекта
compile_project() {
    echo -e "${BLUE}Компиляция проекта...${RESET}"
    
    make clean
    make all
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Ошибка при компиляции проекта.${RESET}"
        exit 1
    fi
    
    echo -e "${GREEN}Проект успешно скомпилирован.${RESET}"
}

# Запуск тестов
run_tests() {
    echo -e "${BLUE}Запуск тестов...${RESET}"
    
    make runtest
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Некоторые тесты завершились с ошибкой.${RESET}"
        echo -e "${YELLOW}Проверьте вывод тестов для получения дополнительной информации.${RESET}"
    else
        echo -e "${GREEN}Все тесты успешно пройдены.${RESET}"
    fi
}

# Запуск примеров
run_examples() {
    echo -e "${BLUE}Запуск примеров...${RESET}"
    
    make runexamples
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Примеры завершились с ошибкой.${RESET}"
    else
        echo -e "${GREEN}Примеры успешно выполнены.${RESET}"
    fi
}

# Основная функция
main() {
    echo -e "${BLUE}=== Сборка проекта NeuroZond ===${RESET}"
    
    check_dependencies
    create_directories
    compile_project
    
    # Спрашиваем, нужно ли запускать тесты
    echo -e "${YELLOW}Хотите запустить тесты? (y/n)${RESET}"
    read -r run_tests_choice
    
    if [[ $run_tests_choice == "y" || $run_tests_choice == "Y" ]]; then
        run_tests
    fi
    
    # Спрашиваем, нужно ли запускать примеры
    echo -e "${YELLOW}Хотите запустить примеры? (y/n)${RESET}"
    read -r run_examples_choice
    
    if [[ $run_examples_choice == "y" || $run_examples_choice == "Y" ]]; then
        run_examples
    fi
    
    echo -e "${GREEN}=== Сборка проекта NeuroZond завершена ===${RESET}"
}

# Запуск основной функции
main 