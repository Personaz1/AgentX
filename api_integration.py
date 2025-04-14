#!/usr/bin/env python3
"""
NeuroRAT API Integration Module - Интеграция с внешними API
"""

import os
import json
import logging
import requests
import base64
import tempfile
from typing import Dict, Any, List, Optional, Union
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_integration.log')
    ]
)
logger = logging.getLogger('api_integration')

# Load environment variables from .env file
load_dotenv()

class APIIntegration:
    """Base class for all API integrations"""
    
    def __init__(self):
        """Initialize the API integration"""
        self.env_loaded = self._validate_env()
    
    def _validate_env(self) -> bool:
        """Validate that required environment variables are set"""
        return True
    
    def is_available(self) -> bool:
        """Check if this API integration is available"""
        return self.env_loaded


class OpenAIIntegration(APIIntegration):
    """Integration with OpenAI API for LLM capabilities"""
    
    def __init__(self):
        """Initialize the OpenAI API integration"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        super().__init__()
    
    def _validate_env(self) -> bool:
        """Validate OpenAI API configuration"""
        if not self.api_key:
            logger.warning("OPENAI_API_KEY is not set in environment variables")
            return False
        return True
    
    def chat_completion(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Send a request to the OpenAI Chat Completion API
        
        Args:
            messages: List of message objects with role and content
            
        Returns:
            API response as dictionary
        """
        if not self.is_available():
            return {"error": "OpenAI API is not configured"}
        
        try:
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error in OpenAI API request: {str(e)}")
            return {"error": str(e)}
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate a response using OpenAI Chat API
        
        Args:
            prompt: The user's prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text response
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.chat_completion(messages)
        
        if "error" in response:
            return f"Error: {response['error']}"
        
        try:
            return response["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing OpenAI response: {str(e)}")
            return "Error: Failed to parse API response"


class GeminiIntegration:
    def __init__(self, credentials_path=None):
        """
        Инициализация класса для работы с API Gemini.
        
        Args:
            credentials_path: Путь к файлу учетных данных Google API (опционально).
        """
        self.credentials_path = credentials_path
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.is_initialized = False
        self.session = None
        
        # Инициализация при создании экземпляра
        if not self.api_key and not self.credentials_path:
            logger.warning("Не найден API ключ или путь к учетным данным для Gemini")
        else:
            self.initialize()


class GoogleAIIntegration(APIIntegration):
    """Integration with Google AI APIs"""
    
    def __init__(self):
        """Initialize the Google AI API integration"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
        super().__init__()
    
    def _validate_env(self) -> bool:
        """Validate Google API configuration"""
        if not self.api_key and not self.credentials_path:
            logger.warning("API ключ Gemini или путь к учетным данным не настроен")
            return False
        return True
    
    def gemini_completion(self, prompt: str, system_prompt: str = None, stream: bool = False) -> Dict[str, Any]:
        """
        Send a request to the Google Gemini API
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            stream: Whether to stream the response
            
        Returns:
            API response as dictionary
        """
        if not self.gemini_api_key:
            return {"error": "Google Gemini API Key is not configured"}
        
        try:
            # Проверяем формат модели и устанавливаем правильный URL
            url = f"https://generativelanguage.googleapis.com/v1/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
            logger.info(f"Using Gemini model: {self.gemini_model}")
            
            # Формируем запрос для Gemini
            data = {
                "contents": []
            }
            
            # Добавляем системный промпт если есть
            if system_prompt:
                data["contents"].append({
                    "role": "user",
                    "parts": [{"text": f"System instruction: {system_prompt}"}]
                })
            
            # Добавляем пользовательский промпт
            data["contents"].append({
                "role": "user",
                "parts": [{"text": prompt}]
            })
            
            # Добавляем параметры генерации
            data["generationConfig"] = {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_tokens,
                "topP": 0.95,
                "topK": 40
            }
            
            # Для потоковой обработки
            if stream:
                data["streamGenerationConfig"] = {
                    "streamMode": "STREAMING"
                }
                
                return self._stream_completion(url, data)
            
            logger.info(f"Sending request to Gemini API: {json.dumps(data)[:200]}...")
            response = requests.post(url, json=data)
            
            if response.status_code != 200:
                logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                return {"error": f"API error: {response.status_code} - {response.text}"}
                
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error in Gemini API request: {str(e)}")
            return {"error": str(e)}
    
    def _stream_completion(self, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform a streaming completion request and return the final result
        
        Args:
            url: The API URL
            data: The request data
            
        Returns:
            The combined API response
        """
        combined_response = {"candidates": [{"content": {"parts": [{"text": ""}]}}]}
        
        try:
            with requests.post(url, json=data, stream=True) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line.decode('utf-8').replace('data: ', ''))
                        
                        # Extract text from the chunk
                        chunk_text = ""
                        try:
                            chunk_text = chunk.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                            # Append to the combined response
                            combined_response["candidates"][0]["content"]["parts"][0]["text"] += chunk_text
                            
                            # Print to console for immediate feedback
                            print(chunk_text, end="", flush=True)
                        except (KeyError, IndexError):
                            continue
                
                print()  # New line after streaming
                return combined_response
                
        except Exception as e:
            logger.error(f"Error in streaming Gemini API request: {str(e)}")
            return {"error": str(e)}
    
    def generate_response(self, prompt: str, system_prompt: str = None, stream: bool = False) -> str:
        """
        Generate a response using Google Gemini API
        
        Args:
            prompt: The user's prompt
            system_prompt: Optional system prompt for context
            stream: Whether to stream the response
            
        Returns:
            Generated text response
        """
        response = self.gemini_completion(prompt, system_prompt, stream)
        
        if "error" in response:
            return f"Error: {response['error']}"
        
        try:
            # Извлекаем текст ответа из структуры ответа Gemini
            content = response.get("candidates", [{}])[0].get("content", {})
            parts = content.get("parts", [{}])
            text = parts[0].get("text", "Нет ответа")
            return text
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing Gemini response: {str(e)}")
            return "Error: Failed to parse API response"
    
    def generate_image(self, prompt: str) -> Dict[str, Any]:
        """
        Generate an image using the Gemini API
        
        Args:
            prompt: The prompt describing the image to generate
            
        Returns:
            Dictionary containing the image data or error
        """
        if not self.gemini_api_key:
            return {"error": "Google Gemini API Key is not configured"}
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash-exp-image-generation:generateContent?key={self.gemini_api_key}"
            
            data = {
                "contents": [
                    {
                        "role": "user", 
                        "parts": [{"text": prompt}]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.9,
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            response_json = response.json()
            
            # Обработка ответа с изображением
            try:
                image_part = None
                for part in response_json["candidates"][0]["content"]["parts"]:
                    if "inlineData" in part:
                        image_part = part["inlineData"]
                        break
                
                if image_part:
                    # Создаем временный файл для сохранения изображения
                    temp_dir = tempfile.mkdtemp()
                    image_path = os.path.join(temp_dir, "generated_image.png")
                    
                    # Декодируем и сохраняем изображение
                    with open(image_path, "wb") as f:
                        f.write(base64.b64decode(image_part["data"]))
                    
                    return {
                        "success": True,
                        "image_path": image_path,
                        "mime_type": image_part["mimeType"]
                    }
                else:
                    return {"error": "No image data in response"}
            except (KeyError, IndexError) as e:
                logger.error(f"Error processing image response: {str(e)}")
                return {"error": f"Failed to process image: {str(e)}"}
            
        except Exception as e:
            logger.error(f"Error in Gemini image generation: {str(e)}")
            return {"error": str(e)}


class TelegramIntegration(APIIntegration):
    """Integration with Telegram Bot API for notifications and control"""
    
    def __init__(self):
        """Initialize Telegram Bot API integration"""
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
        super().__init__()
    
    def _validate_env(self) -> bool:
        """Validate Telegram API configuration"""
        if not self.bot_token:
            logger.warning("TELEGRAM_BOT_TOKEN is not set in environment variables")
            return False
        if not self.admin_chat_id:
            logger.warning("TELEGRAM_ADMIN_CHAT_ID is not set in environment variables")
            return False
        return True
    
    def send_message(self, text: str, chat_id: str = None) -> Dict[str, Any]:
        """
        Send a message through Telegram Bot API
        
        Args:
            text: Message text
            chat_id: Recipient chat ID (defaults to admin chat ID)
            
        Returns:
            API response as dictionary
        """
        if not self.is_available():
            return {"ok": False, "error": "Telegram API is not configured"}
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            data = {
                "chat_id": chat_id or self.admin_chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error in Telegram API request: {str(e)}")
            return {"ok": False, "error": str(e)}
    
    def send_photo(self, photo_path: str, caption: str = None, chat_id: str = None) -> Dict[str, Any]:
        """
        Send a photo through Telegram Bot API
        
        Args:
            photo_path: Path to photo file
            caption: Optional photo caption
            chat_id: Recipient chat ID (defaults to admin chat ID)
            
        Returns:
            API response as dictionary
        """
        if not self.is_available():
            return {"ok": False, "error": "Telegram API is not configured"}
        
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/sendPhoto"
            data = {
                "chat_id": chat_id or self.admin_chat_id
            }
            
            if caption:
                data["caption"] = caption
            
            files = {
                "photo": open(photo_path, "rb")
            }
            
            response = requests.post(url, data=data, files=files)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error in Telegram API request: {str(e)}")
            return {"ok": False, "error": str(e)}


# API Factory to get the right integration
class APIFactory:
    """Factory for creating API integration instances"""
    
    @staticmethod
    def get_openai_integration() -> OpenAIIntegration:
        """Get OpenAI integration instance"""
        return OpenAIIntegration()
    
    @staticmethod
    def get_google_integration() -> GoogleAIIntegration:
        """Get Google AI integration instance"""
        return GoogleAIIntegration()
    
    @staticmethod
    def get_gemini_integration() -> GoogleAIIntegration:
        """Get Google Gemini integration instance (alias for google_integration)"""
        return GoogleAIIntegration()
    
    @staticmethod
    def get_telegram_integration() -> TelegramIntegration:
        """Get Telegram integration instance"""
        return TelegramIntegration()


# Test functionality if run directly
if __name__ == "__main__":
    print("Testing API integrations...")
    
    # Test OpenAI
    openai = APIFactory.get_openai_integration()
    if openai.is_available():
        print("✅ OpenAI API is configured properly")
        
        # Uncomment to test actual API call
        # response = openai.generate_response("Hello, what can you do?")
        # print(f"OpenAI response: {response}")
    else:
        print("❌ OpenAI API is not configured")
    
    # Test Gemini
    gemini = APIFactory.get_gemini_integration()
    if gemini.is_available() and gemini.gemini_api_key:
        print("✅ Google Gemini API is configured properly")
        
        # Uncomment to test actual API call
        # response = gemini.generate_response("Hello, what can you do?")
        # print(f"Gemini response: {response}")
    else:
        print("❌ Google Gemini API is not configured")
    
    # Test Telegram
    telegram = APIFactory.get_telegram_integration()
    if telegram.is_available():
        print("✅ Telegram API is configured properly")
        
        # Uncomment to test actual API call
        # result = telegram.send_message("API Integration test message")
        # print(f"Telegram response: {result}")
    else:
        print("❌ Telegram API is not configured") 