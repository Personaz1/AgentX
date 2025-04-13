#!/usr/bin/env python3
"""
Модуль для шифрования данных в протоколе связи агентов.
"""

import base64
import os
import json
import hashlib
from typing import Any, Dict, Optional, Tuple, Union

try:
    # Пробуем импортировать cryptography
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.backends import default_backend
    CRYPTO_AVAILABLE = True
except ImportError:
    # Если не удалось, будем использовать простое XOR-шифрование
    CRYPTO_AVAILABLE = False
    print("WARNING: cryptography не установлен. Используется небезопасное XOR-шифрование.")


class EncryptionManager:
    """
    Класс для управления шифрованием данных в протоколе.
    Использует RSA для обмена ключами и AES для шифрования сообщений.
    """
    
    def __init__(self, key_size: int = 2048):
        """
        Инициализация менеджера шифрования.
        
        Параметры:
        - key_size: Размер ключа RSA (по умолчанию 2048)
        """
        self.key_size = key_size
        self.private_key = None
        self.public_key = None
        self.remote_public_key = None
        self.shared_key = None
        
        # Генерируем ключи при инициализации
        self._generate_keypair()
    
    def _generate_keypair(self) -> None:
        """Генерация пары ключей RSA."""
        if CRYPTO_AVAILABLE:
            # Используем cryptography для генерации ключей RSA
            self.private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.key_size,
                backend=default_backend()
            )
            self.public_key = self.private_key.public_key()
        else:
            # Для простого XOR-шифрования генерируем ключ
            self.private_key = os.urandom(32)  # 256-битный ключ
            self.public_key = self.private_key  # В этом случае они одинаковы
    
    def get_public_key(self) -> str:
        """
        Возвращает публичный ключ в формате строки.
        
        Возвращает:
        - Строка, представляющая публичный ключ
        """
        if CRYPTO_AVAILABLE:
            # Получаем публичный ключ в формате PEM
            pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            )
            return base64.b64encode(pem).decode('utf-8')
        else:
            # Для XOR просто закодируем ключ в base64
            return base64.b64encode(self.public_key).decode('utf-8')
    
    def set_remote_public_key(self, key_str: str) -> None:
        """
        Устанавливает публичный ключ удаленной стороны.
        
        Параметры:
        - key_str: Строка, представляющая публичный ключ
        """
        try:
            key_data = base64.b64decode(key_str)
            
            if CRYPTO_AVAILABLE:
                # Загружаем публичный ключ из формата PEM
                self.remote_public_key = serialization.load_pem_public_key(
                    key_data,
                    backend=default_backend()
                )
                
                # Генерируем общий ключ для AES
                self._generate_shared_key()
            else:
                # Для XOR устанавливаем ключ напрямую
                self.remote_public_key = key_data
                self.shared_key = hashlib.sha256(self.private_key + self.remote_public_key).digest()
        except Exception as e:
            raise ValueError(f"Ошибка при установке публичного ключа: {str(e)}")
    
    def _generate_shared_key(self) -> None:
        """Генерация общего ключа для AES."""
        if CRYPTO_AVAILABLE and self.remote_public_key:
            # Для реального обмена мы бы использовали DH или ECDH
            # Поскольку RSA не предоставляет прямой способ генерации общего ключа,
            # мы генерируем случайный ключ и шифруем его публичным ключом получателя
            random_key = os.urandom(32)  # 256-битный ключ
            self.shared_key = random_key
    
    def encrypt(self, data: Any) -> str:
        """
        Шифрование данных.
        
        Параметры:
        - data: Данные для шифрования (строка или объект)
        
        Возвращает:
        - Зашифрованные данные в формате base64
        """
        # Конвертируем данные в строку JSON, если это не строка
        if not isinstance(data, str):
            data = json.dumps(data)
        
        # Кодируем строку в байты
        data_bytes = data.encode('utf-8')
        
        if CRYPTO_AVAILABLE and self.remote_public_key and self.shared_key:
            # Генерируем случайный вектор инициализации
            iv = os.urandom(16)
            
            # Создаем шифр AES-GCM
            cipher = Cipher(
                algorithms.AES(self.shared_key),
                modes.GCM(iv),
                backend=default_backend()
            )
            encryptor = cipher.encryptor()
            
            # Шифруем данные
            ciphertext = encryptor.update(data_bytes) + encryptor.finalize()
            
            # Комбинируем IV, тег и шифротекст
            result = {
                'iv': base64.b64encode(iv).decode('utf-8'),
                'tag': base64.b64encode(encryptor.tag).decode('utf-8'),
                'ciphertext': base64.b64encode(ciphertext).decode('utf-8')
            }
            
            return json.dumps(result)
        else:
            # Резервное XOR-шифрование
            if not self.shared_key:
                # Используем приватный ключ, если общий ключ не установлен
                key = self.private_key
            else:
                key = self.shared_key
            
            # XOR-шифрование
            result = bytearray(len(data_bytes))
            for i in range(len(data_bytes)):
                result[i] = data_bytes[i] ^ key[i % len(key)]
            
            return base64.b64encode(result).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Дешифрование данных.
        
        Параметры:
        - encrypted_data: Зашифрованные данные в формате base64
        
        Возвращает:
        - Расшифрованные данные в виде строки
        """
        try:
            if CRYPTO_AVAILABLE and self.shared_key:
                # Распаковываем данные из JSON
                data = json.loads(encrypted_data)
                iv = base64.b64decode(data['iv'])
                tag = base64.b64decode(data['tag'])
                ciphertext = base64.b64decode(data['ciphertext'])
                
                # Создаем шифр AES-GCM с тегом
                cipher = Cipher(
                    algorithms.AES(self.shared_key),
                    modes.GCM(iv, tag),
                    backend=default_backend()
                )
                decryptor = cipher.decryptor()
                
                # Дешифруем данные
                decrypted_data = decryptor.update(ciphertext) + decryptor.finalize()
                
                return decrypted_data.decode('utf-8')
            else:
                # Резервное XOR-дешифрование
                if not self.shared_key:
                    # Используем приватный ключ, если общий ключ не установлен
                    key = self.private_key
                else:
                    key = self.shared_key
                
                # Декодируем из base64
                encrypted_bytes = base64.b64decode(encrypted_data)
                
                # XOR-дешифрование
                result = bytearray(len(encrypted_bytes))
                for i in range(len(encrypted_bytes)):
                    result[i] = encrypted_bytes[i] ^ key[i % len(key)]
                
                return result.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Ошибка при дешифровании: {str(e)}")
    
    def encrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Шифрование файла.
        
        Параметры:
        - file_path: Путь к файлу для шифрования
        - output_path: Путь для сохранения зашифрованного файла (опционально)
        
        Возвращает:
        - Путь к зашифрованному файлу
        """
        if output_path is None:
            output_path = file_path + ".encrypted"
        
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            # Шифруем данные
            encrypted_data = self.encrypt(file_data)
            
            with open(output_path, 'wb') as f:
                f.write(encrypted_data.encode('utf-8'))
            
            return output_path
        except Exception as e:
            raise IOError(f"Ошибка при шифровании файла: {str(e)}")
    
    def decrypt_file(self, file_path: str, output_path: Optional[str] = None) -> str:
        """
        Дешифрование файла.
        
        Параметры:
        - file_path: Путь к зашифрованному файлу
        - output_path: Путь для сохранения расшифрованного файла (опционально)
        
        Возвращает:
        - Путь к расшифрованному файлу
        """
        if output_path is None:
            # Удаляем суффикс .encrypted, если он есть
            if file_path.endswith(".encrypted"):
                output_path = file_path[:-10]
            else:
                output_path = file_path + ".decrypted"
        
        try:
            with open(file_path, 'rb') as f:
                encrypted_data = f.read().decode('utf-8')
            
            # Дешифруем данные
            decrypted_data = self.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as f:
                # Если decrypted_data - строка, преобразуем в байты
                if isinstance(decrypted_data, str):
                    f.write(decrypted_data.encode('utf-8'))
                else:
                    f.write(decrypted_data)
            
            return output_path
        except Exception as e:
            raise IOError(f"Ошибка при дешифровании файла: {str(e)}")


class SimpleEncryptionManager:
    """
    Упрощенный менеджер шифрования, использующий только XOR.
    Используется для тестирования или когда библиотека cryptography не доступна.
    """
    
    def __init__(self):
        """Инициализация менеджера шифрования."""
        self.key = os.urandom(32)  # 256-битный ключ
        self.remote_key = None
        self.shared_key = None
    
    def get_public_key(self) -> str:
        """
        Возвращает публичный ключ в формате строки.
        
        Возвращает:
        - Строка, представляющая публичный ключ
        """
        return base64.b64encode(self.key).decode('utf-8')
    
    def set_remote_public_key(self, key_str: str) -> None:
        """
        Устанавливает публичный ключ удаленной стороны.
        
        Параметры:
        - key_str: Строка, представляющая публичный ключ
        """
        try:
            self.remote_key = base64.b64decode(key_str)
            # Генерируем общий ключ как хеш комбинации ключей
            self.shared_key = hashlib.sha256(self.key + self.remote_key).digest()
        except Exception as e:
            raise ValueError(f"Ошибка при установке публичного ключа: {str(e)}")
    
    def encrypt(self, data: Any) -> str:
        """
        Шифрование данных методом XOR.
        
        Параметры:
        - data: Данные для шифрования (строка или объект)
        
        Возвращает:
        - Зашифрованные данные в формате base64
        """
        # Конвертируем данные в строку JSON, если это не строка
        if not isinstance(data, str):
            data = json.dumps(data)
        
        # Кодируем строку в байты
        data_bytes = data.encode('utf-8')
        
        # Используем общий ключ, если он есть, иначе используем наш ключ
        key = self.shared_key if self.shared_key else self.key
        
        # XOR-шифрование
        result = bytearray(len(data_bytes))
        for i in range(len(data_bytes)):
            result[i] = data_bytes[i] ^ key[i % len(key)]
        
        return base64.b64encode(result).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Дешифрование данных методом XOR.
        
        Параметры:
        - encrypted_data: Зашифрованные данные в формате base64
        
        Возвращает:
        - Расшифрованные данные в виде строки
        """
        try:
            # Декодируем из base64
            encrypted_bytes = base64.b64decode(encrypted_data)
            
            # Используем общий ключ, если он есть, иначе используем наш ключ
            key = self.shared_key if self.shared_key else self.key
            
            # XOR-дешифрование (идентично шифрованию)
            result = bytearray(len(encrypted_bytes))
            for i in range(len(encrypted_bytes)):
                result[i] = encrypted_bytes[i] ^ key[i % len(key)]
            
            return result.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Ошибка при дешифровании: {str(e)}")


def get_encryption_manager() -> Union[EncryptionManager, SimpleEncryptionManager]:
    """
    Возвращает подходящий менеджер шифрования в зависимости от доступности библиотек.
    
    Возвращает:
    - Объект EncryptionManager, если доступен cryptography, иначе SimpleEncryptionManager
    """
    if CRYPTO_AVAILABLE:
        return EncryptionManager()
    else:
        return SimpleEncryptionManager() 