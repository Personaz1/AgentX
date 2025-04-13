#!/usr/bin/env python3
"""
Модуль для безопасного обмена ключами с использованием алгоритма Диффи-Хеллмана.
Используется для установки общего секретного ключа между агентом и сервером.
"""

import os
import base64
import hashlib
import logging
from typing import Tuple, Optional
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import dh, rsa, padding
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

# Настройка логирования
logger = logging.getLogger('key_exchange')

# Параметры Диффи-Хеллмана (можно использовать предопределенные группы из RFC)
DH_PARAMETERS = dh.generate_parameters(generator=2, key_size=2048, backend=default_backend())

class KeyExchange:
    """Класс для обмена ключами с использованием Диффи-Хеллмана."""
    
    @staticmethod
    def generate_dh_keypair() -> Tuple[dh.DHPrivateKey, dh.DHPublicKey]:
        """Генерация пары ключей для обмена Диффи-Хеллмана."""
        private_key = DH_PARAMETERS.generate_private_key()
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def serialize_public_key(public_key: dh.DHPublicKey) -> str:
        """Сериализация открытого ключа в строку base64."""
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(public_bytes).decode('utf-8')
    
    @staticmethod
    def deserialize_public_key(key_data: str) -> dh.DHPublicKey:
        """Десериализация строки base64 в открытый ключ."""
        key_bytes = base64.b64decode(key_data)
        public_key = serialization.load_pem_public_key(
            key_bytes,
            backend=default_backend()
        )
        return public_key
    
    @staticmethod
    def compute_shared_key(private_key: dh.DHPrivateKey, peer_public_key: dh.DHPublicKey) -> bytes:
        """Вычисление общего секретного ключа."""
        shared_key = private_key.exchange(peer_public_key)
        
        # Производим ключевой материал из общего секрета с помощью HKDF
        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,  # 256 бит для AES-256
            salt=None,
            info=b'handshake-key',
            backend=default_backend()
        ).derive(shared_key)
        
        return derived_key
    
    @staticmethod
    def get_key_fingerprint(key_bytes: bytes) -> str:
        """Получение отпечатка ключа для проверки."""
        return hashlib.sha256(key_bytes).hexdigest()[:16]
    
    @staticmethod
    def validate_dh_key(public_key: dh.DHPublicKey, params: dh.DHParameters = None) -> bool:
        """
        Проверка публичного ключа Диффи-Хеллмана на безопасность.
        Метод проверяет, что ключ не является тривиальным или подверженным MITM-атаке.
        
        Параметры:
        - public_key: Публичный ключ для проверки
        - params: Параметры DH (опционально), если None - используются стандартные
        
        Возвращает:
        - True, если ключ валидный и безопасный
        """
        try:
            # Получаем числовое представление ключа
            key_numbers = public_key.public_numbers()
            
            # Параметры, с которыми сравниваем
            if params is None:
                params = DH_PARAMETERS
            
            # Проверяем, что ключ в допустимом диапазоне (2 <= y <= p-2)
            p = params.parameter_numbers().p
            y = key_numbers.y
            
            if y < 2 or y >= p - 1:
                logger.warning(f"DH public key is outside safe range: {y}")
                return False
                
            # Дополнительные проверки можно добавить здесь
            # Например, проверку на порядок ключа
            
            return True
        except Exception as e:
            logger.error(f"Error validating DH key: {str(e)}")
            return False

class RSAKeyExchange:
    """Класс для обмена ключами с использованием RSA (для первичной настройки)."""
    
    @staticmethod
    def generate_rsa_keypair() -> Tuple[rsa.RSAPrivateKey, rsa.RSAPublicKey]:
        """Генерация пары ключей RSA."""
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def serialize_private_key(private_key: rsa.RSAPrivateKey, password: Optional[str] = None) -> str:
        """Сериализация закрытого ключа RSA в строку base64 (опционально с паролем)."""
        if password:
            encryption = serialization.BestAvailableEncryption(password.encode())
        else:
            encryption = serialization.NoEncryption()
            
        private_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=encryption
        )
        return base64.b64encode(private_bytes).decode('utf-8')
    
    @staticmethod
    def serialize_public_key(public_key: rsa.RSAPublicKey) -> str:
        """Сериализация открытого ключа RSA в строку base64."""
        public_bytes = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return base64.b64encode(public_bytes).decode('utf-8')
    
    @staticmethod
    def deserialize_private_key(key_data: str, password: Optional[str] = None) -> rsa.RSAPrivateKey:
        """Десериализация строки base64 в закрытый ключ RSA."""
        key_bytes = base64.b64decode(key_data)
        
        if password:
            private_key = serialization.load_pem_private_key(
                key_bytes,
                password=password.encode(),
                backend=default_backend()
            )
        else:
            private_key = serialization.load_pem_private_key(
                key_bytes,
                password=None,
                backend=default_backend()
            )
            
        return private_key
    
    @staticmethod
    def deserialize_public_key(key_data: str) -> rsa.RSAPublicKey:
        """Десериализация строки base64 в открытый ключ RSA."""
        key_bytes = base64.b64decode(key_data)
        public_key = serialization.load_pem_public_key(
            key_bytes,
            backend=default_backend()
        )
        return public_key
    
    @staticmethod
    def encrypt_key(aes_key: bytes, public_key: rsa.RSAPublicKey) -> bytes:
        """Шифрование AES-ключа с помощью открытого ключа RSA."""
        encrypted_key = public_key.encrypt(
            aes_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return encrypted_key
    
    @staticmethod
    def decrypt_key(encrypted_key: bytes, private_key: rsa.RSAPrivateKey) -> bytes:
        """Расшифровка AES-ключа с помощью закрытого ключа RSA."""
        decrypted_key = private_key.decrypt(
            encrypted_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted_key

def perform_key_exchange(is_initiator: bool = True) -> Tuple[bytes, dict]:
    """
    Выполнение полного обмена ключами. 
    
    Параметры:
    - is_initiator: True, если эта сторона инициирует обмен ключами
    
    Возвращает:
    - Финальный AES-ключ для шифрования и словарь с промежуточными данными
    """
    # Генерируем пару ключей DH
    private_key, public_key = KeyExchange.generate_dh_keypair()
    public_key_str = KeyExchange.serialize_public_key(public_key)
    
    # Если мы инициатор, мы первыми отправляем свой публичный ключ
    if is_initiator:
        # В реальном сценарии здесь произойдёт сетевой обмен:
        # 1. Отправка public_key_str другой стороне
        # 2. Получение их public_key_str
        logger.info("Initiator: Отправка публичного ключа DH")
        
        # Здесь в реальном сценарии мы получаем ответ от другой стороны
        # Для тестирования мы можем сгенерировать их ключи здесь:
        peer_private_key, peer_public_key = KeyExchange.generate_dh_keypair()
        peer_public_key_str = KeyExchange.serialize_public_key(peer_public_key)
        
        # Получаем публичный ключ партнера
        logger.info("Initiator: Получение публичного ключа партнера")
        peer_public_key = KeyExchange.deserialize_public_key(peer_public_key_str)
    else:
        # Если мы отвечающая сторона, мы ждем их публичный ключ, затем отправляем свой
        # В реальном сценарии здесь произойдёт сетевой обмен:
        # 1. Получение их public_key_str
        # 2. Отправка нашего public_key_str
        logger.info("Responder: Ожидание публичного ключа инициатора")
        
        # Для тестирования мы можем сгенерировать "их" ключи здесь:
        peer_private_key, peer_public_key = KeyExchange.generate_dh_keypair()
        peer_public_key_str = KeyExchange.serialize_public_key(peer_public_key)
        
        # Получаем публичный ключ партнера
        logger.info("Responder: Получение публичного ключа инициатора")
        peer_public_key = KeyExchange.deserialize_public_key(peer_public_key_str)
        
        # Отправляем свой публичный ключ
        logger.info("Responder: Отправка своего публичного ключа")
    
    # Вычисляем общий секретный ключ
    shared_key = KeyExchange.compute_shared_key(private_key, peer_public_key)
    key_fingerprint = KeyExchange.get_key_fingerprint(shared_key)
    
    logger.info(f"Обмен ключами завершен. Отпечаток ключа: {key_fingerprint}")
    
    # Возвращаем финальный ключ и промежуточные данные для отладки
    return shared_key, {
        "public_key": public_key_str,
        "peer_public_key": peer_public_key_str,
        "key_fingerprint": key_fingerprint
    }

def secure_first_contact(server_public_key_str: str, aes_key: bytes) -> bytes:
    """
    Безопасная передача симметричного AES-ключа с помощью асимметричного RSA.
    Используется для первого подключения агента к серверу.
    
    Параметры:
    - server_public_key_str: Публичный ключ сервера в формате base64
    - aes_key: Симметричный ключ, который нужно безопасно передать
    
    Возвращает:
    - Зашифрованный AES-ключ, который можно безопасно передать по сети
    """
    # Десериализуем публичный ключ сервера
    server_public_key = RSAKeyExchange.deserialize_public_key(server_public_key_str)
    
    # Шифруем наш AES-ключ с помощью публичного ключа сервера
    encrypted_key = RSAKeyExchange.encrypt_key(aes_key, server_public_key)
    
    return encrypted_key

def generate_agent_keypair(password: Optional[str] = None) -> Tuple[str, str]:
    """
    Генерация пары ключей RSA для агента.
    
    Параметры:
    - password: Опциональный пароль для защиты закрытого ключа
    
    Возвращает:
    - (private_key_str, public_key_str): Пара ключей в формате base64
    """
    # Генерируем пару ключей RSA
    private_key, public_key = RSAKeyExchange.generate_rsa_keypair()
    
    # Сериализуем ключи
    private_key_str = RSAKeyExchange.serialize_private_key(private_key, password)
    public_key_str = RSAKeyExchange.serialize_public_key(public_key)
    
    return private_key_str, public_key_str

if __name__ == "__main__":
    # Пример использования:
    logging.basicConfig(level=logging.INFO)
    
    # Пример для DH
    logger.info("Тест обмена ключами Диффи-Хеллмана:")
    shared_key, exchange_data = perform_key_exchange(is_initiator=True)
    logger.info(f"Отпечаток ключа: {exchange_data['key_fingerprint']}")
    
    # Пример для RSA (первичное подключение)
    logger.info("\nТест RSA для первичного подключения:")
    private_key_str, public_key_str = generate_agent_keypair()
    logger.info(f"Публичный ключ агента (или сервера): {public_key_str[:64]}...")
    
    # Симулируем передачу AES-ключа с помощью RSA
    aes_key = os.urandom(32)  # Случайный 256-битный ключ
    encrypted_key = secure_first_contact(public_key_str, aes_key)
    logger.info(f"Зашифрованный AES-ключ: {base64.b64encode(encrypted_key).decode()[:64]}...")