#!/usr/bin/env python3
"""
Тестирование интеграции с Gemini API
"""

import os
import sys
import json
import argparse
from api_integration import APIFactory

def test_text_generation(prompt, system_prompt=None, stream=False):
    """
    Тестирует генерацию текста с помощью Gemini API
    
    Args:
        prompt: Запрос для модели
        system_prompt: Системный промпт для настройки поведения модели
        stream: Использовать потоковую передачу ответа
    """
    gemini = APIFactory.get_gemini_integration()
    
    if not gemini.is_available():
        print("❌ Google Gemini API не настроен. Проверьте переменные окружения.")
        return
    
    print(f"\n🤖 Запрос: {prompt}")
    if system_prompt:
        print(f"📝 Системный промпт: {system_prompt}")
    
    print("\n🔍 Ответ:")
    response = gemini.generate_response(prompt, system_prompt, stream)
    
    if not stream:  # Если не стриминг, выводим ответ
        print(response)

def test_image_generation(prompt):
    """
    Тестирует генерацию изображений с помощью Gemini API
    
    Args:
        prompt: Описание желаемого изображения
    """
    gemini = APIFactory.get_gemini_integration()
    
    if not gemini.is_available():
        print("❌ Google Gemini API не настроен. Проверьте переменные окружения.")
        return
    
    print(f"\n🖼️ Запрос на генерацию изображения: {prompt}")
    print("\n⏳ Генерация изображения...")
    
    result = gemini.generate_image(prompt)
    
    if "error" in result:
        print(f"❌ Ошибка: {result['error']}")
    else:
        print(f"✅ Изображение создано и сохранено в: {result['image_path']}")
        print(f"📊 Тип изображения: {result['mime_type']}")

def main():
    """Основная функция скрипта"""
    parser = argparse.ArgumentParser(description="Тестирование интеграции с Gemini API")
    parser.add_argument("--prompt", type=str, help="Запрос для модели", 
                        default="Опиши себя и свои возможности.")
    parser.add_argument("--system", type=str, help="Системный промпт", 
                        default="Ты - ИИ-помощник внутри системы NeuroRAT. Отвечай кратко и по существу.")
    parser.add_argument("--stream", action="store_true", help="Использовать потоковую передачу ответа")
    parser.add_argument("--image", type=str, help="Генерация изображения по запросу")
    
    args = parser.parse_args()
    
    print("🧪 Тестирование интеграции с Gemini API")
    
    if args.image:
        test_image_generation(args.image)
    else:
        test_text_generation(args.prompt, args.system, args.stream)

if __name__ == "__main__":
    main() 