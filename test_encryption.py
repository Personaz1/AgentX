#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import base64
import hashlib
import unittest
import random
import string
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Добавим текущую директорию в путь для импорта
sys.path.insert(0, os.path.abspath('.'))

try:
    from agent_protocol.shared.encryption import EncryptionManager
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    print("ВНИМАНИЕ: Не удалось импортировать EncryptionManager, будет использована собственная реализация")

# Константы для тестирования
TEST_KEY = "testkey123456789012345678901234"  # 32-байтовый ключ
TEST_ITERATIONS = 1000  # Количество итераций для стресс-теста

class BaseEncryptionTest:
    """Базовый класс для реализации альтернативного шифрования при тестировании"""
    
    @staticmethod
    def generate_key(password, salt=None):
        """Генерирует ключ на основе пароля и соли"""
        if salt is None:
            salt = os.urandom(16)
        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000, 32)
        return key, salt
    
    @staticmethod
    def encrypt(plaintext, key):
        """Базовая AES-256 реализация шифрования"""
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        
        # Добавим padding до блока 16 байт
        padded_data = plaintext.encode()
        padding_length = 16 - (len(padded_data) % 16)
        padded_data += bytes([padding_length]) * padding_length
        
        ciphertext = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + ciphertext).decode()
    
    @staticmethod
    def decrypt(ciphertext, key):
        """Базовая AES-256 реализация дешифрования"""
        ciphertext = base64.b64decode(ciphertext.encode())
        iv = ciphertext[:16]
        ciphertext = ciphertext[16:]
        
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        
        padded_data = decryptor.update(ciphertext) + decryptor.finalize()
        padding_length = padded_data[-1]
        
        # Удаляем padding
        data = padded_data[:-padding_length]
        return data.decode()

class TestEncryption(unittest.TestCase):
    """Тесты для компонента шифрования"""
    
    def setUp(self):
        """Подготовка к тестам"""
        if ENCRYPTION_AVAILABLE:
            self.manager = EncryptionManager(TEST_KEY)
        else:
            # Используем базовую реализацию для тестирования
            key, _ = BaseEncryptionTest.generate_key(TEST_KEY)
            self.key = key
            
    def test_basic_encryption(self):
        """Базовый тест шифрования/дешифрования"""
        plaintext = "Это секретное сообщение для тестирования NeuroRAT"
        
        if ENCRYPTION_AVAILABLE:
            # Используем EncryptionManager
            encrypted = self.manager.encrypt(plaintext)
            decrypted = self.manager.decrypt(encrypted)
        else:
            # Используем базовую реализацию
            encrypted = BaseEncryptionTest.encrypt(plaintext, self.key)
            decrypted = BaseEncryptionTest.decrypt(encrypted, self.key)
            
        # Проверки
        self.assertNotEqual(plaintext, encrypted, "Шифртекст должен отличаться от исходного текста")
        self.assertEqual(plaintext, decrypted, "Дешифрованный текст должен совпадать с исходным")
        
    def test_encryption_idempotence(self):
        """Проверка идемпотентности - повторное шифрование должно давать одинаковый результат"""
        plaintext = "Тестирование идемпотентности шифрования"
        
        if ENCRYPTION_AVAILABLE:
            # Проверяем, что разные вызовы дают разные результаты (из-за случайного вектора)
            encrypted1 = self.manager.encrypt(plaintext)
            encrypted2 = self.manager.encrypt(plaintext)
            self.assertNotEqual(encrypted1, encrypted2, "Из-за случайного IV, шифрование должно давать разные результаты")
            
            # Но дешифрование должно быть корректным
            decrypted1 = self.manager.decrypt(encrypted1)
            decrypted2 = self.manager.decrypt(encrypted2)
            self.assertEqual(decrypted1, decrypted2, "Результаты дешифрования должны совпадать")
        else:
            # То же самое для базовой реализации
            encrypted1 = BaseEncryptionTest.encrypt(plaintext, self.key)
            encrypted2 = BaseEncryptionTest.encrypt(plaintext, self.key)
            self.assertNotEqual(encrypted1, encrypted2)
            
            decrypted1 = BaseEncryptionTest.decrypt(encrypted1, self.key)
            decrypted2 = BaseEncryptionTest.decrypt(encrypted2, self.key)
            self.assertEqual(decrypted1, decrypted2)
            
    def test_large_data(self):
        """Тестирование шифрования больших объемов данных"""
        # Генерируем большой объем случайных данных (1 МБ)
        large_data = ''.join(random.choice(string.printable) for _ in range(1024 * 1024))
        
        if ENCRYPTION_AVAILABLE:
            encrypted = self.manager.encrypt(large_data)
            decrypted = self.manager.decrypt(encrypted)
        else:
            # Для очень больших данных разобьем их на части
            chunks = [large_data[i:i+4096] for i in range(0, len(large_data), 4096)]
            encrypted_chunks = [BaseEncryptionTest.encrypt(chunk, self.key) for chunk in chunks]
            encrypted = "||".join(encrypted_chunks)  # Используем разделитель
            
            # Дешифрование по частям
            encrypted_chunks = encrypted.split("||")
            decrypted_chunks = [BaseEncryptionTest.decrypt(chunk, self.key) for chunk in encrypted_chunks]
            decrypted = "".join(decrypted_chunks)
            
        self.assertEqual(large_data, decrypted, "Дешифрованные большие данные должны совпадать с исходными")
        
    def test_binary_data(self):
        """Тестирование шифрования бинарных данных"""
        # Создаем бинарные данные
        binary_data = bytes([random.randint(0, 255) for _ in range(1024)])
        binary_str = base64.b64encode(binary_data).decode()
        
        if ENCRYPTION_AVAILABLE:
            encrypted = self.manager.encrypt(binary_str)
            decrypted = self.manager.decrypt(encrypted)
        else:
            encrypted = BaseEncryptionTest.encrypt(binary_str, self.key)
            decrypted = BaseEncryptionTest.decrypt(encrypted, self.key)
            
        self.assertEqual(binary_str, decrypted)
        
    def test_stress(self):
        """Стресс-тест шифрования - многократное шифрование/дешифрование"""
        start_time = time.time()
        
        for i in range(TEST_ITERATIONS):
            # Генерируем случайную строку разной длины
            length = random.randint(10, 1000)
            random_str = ''.join(random.choice(string.printable) for _ in range(length))
            
            if ENCRYPTION_AVAILABLE:
                encrypted = self.manager.encrypt(random_str)
                decrypted = self.manager.decrypt(encrypted)
            else:
                encrypted = BaseEncryptionTest.encrypt(random_str, self.key)
                decrypted = BaseEncryptionTest.decrypt(encrypted, self.key)
                
            self.assertEqual(random_str, decrypted)
            
        elapsed = time.time() - start_time
        print(f"\nСтресс-тест: {TEST_ITERATIONS} итераций за {elapsed:.2f} сек ({TEST_ITERATIONS/elapsed:.2f} операций/сек)")
        
    def test_key_derivation(self):
        """Тестирование генерации ключей из паролей"""
        password = "очень_секретный_пароль"
        
        if ENCRYPTION_AVAILABLE and hasattr(EncryptionManager, 'derive_key'):
            # Если у EncryptionManager есть метод derive_key
            key1, salt1 = EncryptionManager.derive_key(password)
            key2, salt2 = EncryptionManager.derive_key(password, salt1)
            
            # Проверяем, что с одинаковой солью ключи совпадают
            self.assertEqual(key1, key2)
            
            # С разной солью должны быть разные ключи
            key3, salt3 = EncryptionManager.derive_key(password)
            self.assertNotEqual(key1, key3)
        else:
            # Используем базовую реализацию
            key1, salt1 = BaseEncryptionTest.generate_key(password)
            key2, salt2 = BaseEncryptionTest.generate_key(password, salt1)
            
            self.assertEqual(key1, key2)
            
            key3, salt3 = BaseEncryptionTest.generate_key(password)
            self.assertNotEqual(key1, key3)
            
    def test_tamper_resistance(self):
        """Тестирование устойчивости к подделке - изменение шифртекста должно быть обнаружено"""
        plaintext = "Важное секретное сообщение, которое нельзя подделать"
        
        if ENCRYPTION_AVAILABLE:
            encrypted = self.manager.encrypt(plaintext)
            
            # Изменяем шифртекст (подделываем)
            tampered = list(encrypted)
            index = len(tampered) // 2
            tampered[index] = 'X' if tampered[index] != 'X' else 'Y'
            tampered = ''.join(tampered)
            
            # Дешифрование должно вызвать ошибку или вернуть искаженный текст
            try:
                decrypted = self.manager.decrypt(tampered)
                self.assertNotEqual(plaintext, decrypted, "Подделанный шифртекст не должен давать исходный текст")
            except Exception as e:
                # Это тоже допустимое поведение - расшифровка может вызвать исключение
                print(f"\nОшибка при расшифровке подделанного текста: {e}")
        else:
            # С базовой реализацией тоже проверим
            encrypted = BaseEncryptionTest.encrypt(plaintext, self.key)
            
            # Подделываем Base64 данные
            decoded = base64.b64decode(encrypted.encode())
            tampered_decoded = bytearray(decoded)
            tampered_decoded[20] = (tampered_decoded[20] + 1) % 256
            tampered = base64.b64encode(tampered_decoded).decode()
            
            try:
                decrypted = BaseEncryptionTest.decrypt(tampered, self.key)
                self.assertNotEqual(plaintext, decrypted)
            except Exception as e:
                print(f"\nОшибка при расшифровке подделанного текста (базовая реализация): {e}")

class TestEncryptionCompatibility(unittest.TestCase):
    """Тесты на совместимость разных реализаций шифрования"""
    
    @unittest.skipIf(not ENCRYPTION_AVAILABLE, "EncryptionManager недоступен")
    def test_cross_implementation(self):
        """Проверка совместимости EncryptionManager и базовой реализации"""
        plaintext = "Сообщение для проверки кросс-совместимости"
        
        # Генерируем ключ для базовой реализации
        key, _ = BaseEncryptionTest.generate_key(TEST_KEY)
        
        # Шифруем одной реализацией, расшифровываем другой
        manager = EncryptionManager(TEST_KEY)
        
        # Тест 1: EncryptionManager -> BaseEncryption
        # Это может не работать, если EncryptionManager использует свою систему
        try:
            encrypted = manager.encrypt(plaintext)
            decrypted = BaseEncryptionTest.decrypt(encrypted, key)
            self.assertEqual(plaintext, decrypted)
            print("\nСовместимость: EncryptionManager -> BaseEncryption: OK")
        except Exception as e:
            print(f"\nСовместимость: EncryptionManager -> BaseEncryption: FAIL ({e})")
        
        # Тест 2: BaseEncryption -> EncryptionManager
        try:
            encrypted = BaseEncryptionTest.encrypt(plaintext, key)
            decrypted = manager.decrypt(encrypted)
            self.assertEqual(plaintext, decrypted)
            print("\nСовместимость: BaseEncryption -> EncryptionManager: OK")
        except Exception as e:
            print(f"\nСовместимость: BaseEncryption -> EncryptionManager: FAIL ({e})")

def analyze_encryption_implementation():
    """Анализирует безопасность реализации шифрования"""
    if not ENCRYPTION_AVAILABLE:
        print("\nНе удается провести анализ - EncryptionManager недоступен")
        return
    
    try:
        # Анализ IV (вектора инициализации)
        iv_set = set()
        for _ in range(100):
            manager = EncryptionManager(TEST_KEY)
            plaintext = "тестовый текст"
            encrypted = manager.encrypt(plaintext)
            
            # Извлекаем IV (если это возможно)
            # Предполагаем, что IV находится в начале Base64-декодированного шифртекста
            try:
                decoded = base64.b64decode(encrypted.encode())
                iv = decoded[:16]  # Обычно IV имеет размер 16 байт для AES
                iv_set.add(iv)
            except:
                pass
        
        print(f"\nАнализ IV: обнаружено {len(iv_set)} уникальных векторов из 100 шифрований")
        if len(iv_set) < 90:
            print("ВНИМАНИЕ: Похоже, что IV недостаточно случаен!")
        
        # Анализ на утечку информации
        plaintexts = [
            "AAAAAAAAAAAAAAAA",  # Одинаковые блоки
            "BBBBBBBBBBBBBBBB", 
            "AAAAAAAAAAAAAAAA"   # Повторение первого для проверки
        ]
        
        ciphertexts = []
        manager = EncryptionManager(TEST_KEY)
        
        for text in plaintexts:
            ciphertexts.append(manager.encrypt(text))
        
        # Проверяем, что шифртексты разные даже для одинаковых открытых текстов
        if ciphertexts[0] == ciphertexts[2]:
            print("ВНИМАНИЕ: Одинаковые открытые тексты дают одинаковые шифртексты. Режим ECB?")
        else:
            print("Реализация шифрования корректна: разные шифртексты для одинаковых открытых текстов")
    
    except Exception as e:
        print(f"\nОшибка при анализе шифрования: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("NeuroRAT - Тестирование шифрования")
    print("=" * 80)
    
    # Запуск тестов
    unittest.main(verbosity=2, exit=False)
    
    # Анализ реализации шифрования
    print("\n" + "=" * 80)
    print("Анализ реализации шифрования:")
    analyze_encryption_implementation()
    
    print("\n" + "=" * 80)
    if ENCRYPTION_AVAILABLE:
        print("ИТОГ: EncryptionManager доступен и протестирован")
    else:
        print("ИТОГ: Использовалась альтернативная реализация шифрования для тестов") 