#!/bin/bash
# crypto_git_file.sh - Утилита для безопасного хранения чувствительных файлов в репозитории
# Использует криптографические функции из модуля NeuroZond

VERSION="0.1-alpha"

# Цвета для вывода в терминал
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}NeuroZond CryptoGitFile ${VERSION}${NC}"
echo -e "${BLUE}Утилита для безопасного хранения чувствительных файлов${NC}"
echo 

# Функция для шифрования файла
encrypt_file() {
    local input_file=$1
    local output_file="${input_file}.encrypted"
    
    echo -e "${YELLOW}[*] Шифрование файла:${NC} $input_file"
    # TODO: Интегрировать с модулем crypto_utils.c для AES-256 шифрования
    # Временная реализация с использованием OpenSSL для демонстрации
    openssl enc -aes-256-cbc -salt -in "$input_file" -out "$output_file" -k "$CRYPTO_KEY" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] Файл успешно зашифрован:${NC} $output_file"
        return 0
    else
        echo -e "${RED}[-] Ошибка при шифровании файла${NC}"
        return 1
    fi
}

# Функция для расшифровки файла
decrypt_file() {
    local input_file=$1
    local output_file="${input_file%.encrypted}"
    
    echo -e "${YELLOW}[*] Расшифровка файла:${NC} $input_file"
    # TODO: Интегрировать с модулем crypto_utils.c для AES-256 дешифрования
    # Временная реализация с использованием OpenSSL для демонстрации
    openssl enc -d -aes-256-cbc -in "$input_file" -out "$output_file" -k "$CRYPTO_KEY" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}[+] Файл успешно расшифрован:${NC} $output_file"
        return 0
    else
        echo -e "${RED}[-] Ошибка при расшифровке файла${NC}"
        return 1
    fi
}

# Проверяем наличие ключа шифрования
if [ -z "$CRYPTO_KEY" ]; then
    # Проверяем наличие файла с ключом
    if [ -f "$HOME/.neurozond_crypto_key" ]; then
        CRYPTO_KEY=$(cat "$HOME/.neurozond_crypto_key")
    else
        echo -e "${YELLOW}[*] Ключ шифрования не найден, создаем новый...${NC}"
        # Генерируем случайный ключ
        CRYPTO_KEY=$(openssl rand -base64 32)
        # Сохраняем ключ в домашней директории
        echo "$CRYPTO_KEY" > "$HOME/.neurozond_crypto_key"
        chmod 600 "$HOME/.neurozond_crypto_key"
        echo -e "${GREEN}[+] Ключ шифрования создан и сохранен в ${NC}$HOME/.neurozond_crypto_key"
    fi
fi

# Основной код
if [ $# -lt 1 ]; then
    echo -e "${YELLOW}Использование:${NC} $0 <файл> [encrypt|decrypt]"
    echo "    По умолчанию, файлы с расширением .encrypted будут расшифрованы,"
    echo "    остальные файлы будут зашифрованы."
    exit 1
fi

FILE=$1
ACTION=$2

# Если действие не указано, определяем его автоматически
if [ -z "$ACTION" ]; then
    if [[ "$FILE" == *.encrypted ]]; then
        ACTION="decrypt"
    else
        ACTION="encrypt"
    fi
fi

# Выполняем действие
if [ "$ACTION" == "encrypt" ]; then
    encrypt_file "$FILE"
elif [ "$ACTION" == "decrypt" ]; then
    decrypt_file "$FILE"
else
    echo -e "${RED}[-] Неизвестное действие:${NC} $ACTION"
    exit 1
fi

echo -e "\n${BLUE}[*] TODO: Интеграция с git-hooks для автоматизации${NC}"
echo -e "${BLUE}[*] TODO: Использование нативного модуля crypto_utils.c вместо OpenSSL${NC}" 