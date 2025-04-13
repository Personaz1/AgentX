#!/usr/bin/env python3
"""
NeuroRAT API Integration Module - Интеграция с внешними API
"""

import os
import json
import logging
import requests
import base64
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
        super().__init__()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
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


class GoogleAIIntegration(APIIntegration):
    """Integration with Google AI APIs"""
    
    def __init__(self):
        """Initialize the Google AI API integration"""
        super().__init__()
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.gemini_api_key = os.getenv("GOOGLE_GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-pro")
        self.credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2048"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    
    def _validate_env(self) -> bool:
        """Validate Google API configuration"""
        if not self.api_key and not self.gemini_api_key and not self.credentials_path:
            logger.warning("Ни один из API ключей Google не настроен")
            return False
        return True
    
    def gemini_completion(self, prompt: str, system_prompt: str = None) -> Dict[str, Any]:
        """
        Send a request to the Google Gemini API
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            API response as dictionary
        """
        if not self.gemini_api_key:
            return {"error": "Google Gemini API Key is not configured"}
        
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.gemini_model}:generateContent?key={self.gemini_api_key}"
            
            # Формируем запрос для Gemini
            data = {
                "contents": []
            }
            
            # Добавляем систем промпт если есть
            if system_prompt:
                data["contents"].append({
                    "role": "user",
                    "parts": [{"text": f"System: {system_prompt}"}]
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
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error in Gemini API request: {str(e)}")
            return {"error": str(e)}
    
    def generate_response(self, prompt: str, system_prompt: str = None) -> str:
        """
        Generate a response using Google Gemini API
        
        Args:
            prompt: The user's prompt
            system_prompt: Optional system prompt for context
            
        Returns:
            Generated text response
        """
        response = self.gemini_completion(prompt, system_prompt)
        
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


class TelegramIntegration(APIIntegration):
    """Integration with Telegram Bot API for notifications and control"""
    
    def __init__(self):
        """Initialize Telegram Bot API integration"""
        super().__init__()
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.admin_chat_id = os.getenv("TELEGRAM_ADMIN_CHAT_ID")
    
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