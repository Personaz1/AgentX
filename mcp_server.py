#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model Context Protocol (MCP) Server

MCP обеспечивает центральный узел для доступа к языковым моделям и управления контекстом
для распределенных агентов. Сервер обрабатывает запросы к LLM, управляет историей контекста
и обеспечивает унифицированный API для взаимодействия с различными языковыми моделями.

Функционал:
- REST API для управления контекстом и запросов к LLM
- Поддержка Google Gemini 2.5 Pro Preview
- Управление аутентификацией и авторизацией
- Логирование и мониторинг использования
- Кэширование запросов для оптимизации

Автор: Neuro Agent System
"""

import os
import sys
import json
import socket
import threading
import time
import logging
import base64
import hashlib
import ssl
import uuid
import argparse
import traceback
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from collections import defaultdict
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

# Google Gemini импорт
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    logging.warning("Google Generative AI package not found. Please install with: pip install google-generativeai")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_server.log')
    ]
)
logger = logging.getLogger('mcp_server')

# Создание приложения FastAPI
app = FastAPI(
    title="Model Context Protocol Server",
    description="Unified API for language model interaction and context management",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Схемы данных API
class ModelRequest(BaseModel):
    model: str = Field(..., description="Model identifier")
    messages: List[Dict[str, str]] = Field(..., description="Messages to send to the model")
    temperature: float = Field(0.7, description="Temperature parameter for generation")
    max_tokens: int = Field(1000, description="Maximum tokens to generate")
    context_id: Optional[str] = Field(None, description="Context identifier")

class ContextUpdateRequest(BaseModel):
    context_id: str = Field(..., description="Context identifier")
    messages: List[Dict[str, str]] = Field(..., description="Messages to add to context")

class ContextClearRequest(BaseModel):
    context_id: str = Field(..., description="Context identifier to clear")

# Реализация безопасности
security = HTTPBearer()

def get_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Проверка API-ключа"""
    # Упрощенная реализация - в продакшене стоит использовать более надежный метод
    api_key = credentials.credentials
    if api_key != os.environ.get("MCP_API_KEY", "dev_api_key"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    return api_key

# Хранилище контекстов (в реальном приложении стоит использовать Redis или другое решение)
contexts = {}

# Инициализация Gemini
def init_gemini():
    """Инициализация Google Gemini API"""
    if not HAS_GEMINI:
        logger.warning("Google Generative AI package not installed. Gemini integration disabled.")
        return False
    
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY environment variable not set. Gemini integration disabled.")
        return False
    
    try:
        genai.configure(api_key=api_key)
        logger.info("Google Gemini API initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize Google Gemini API: {str(e)}")
        return False

# Инициализация Gemini при запуске
gemini_enabled = init_gemini()

# Функция для вызова модели Gemini
async def query_gemini(messages, model="gemini-2.5-pro-preview-03-25", temperature=0.7, max_tokens=1000):
    """
    Отправка запроса к Google Gemini API
    """
    if not HAS_GEMINI or not gemini_enabled:
        return {"error": "Gemini API not available"}
    
    try:
        # Конвертация сообщений в формат Gemini
        gemini_messages = []
        for msg in messages:
            role = msg["role"]
            if role == "system":
                # Gemini не имеет системных сообщений, добавляем как пользовательское
                gemini_messages.append({"role": "user", "parts": [msg["content"]]})
                gemini_messages.append({"role": "model", "parts": ["I understand. I'll follow these instructions."]})
            else:
                gemini_role = "user" if role == "user" else "model"
                gemini_messages.append({"role": gemini_role, "parts": [msg["content"]]})
        
        # Создание модели и генерация ответа
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
            "top_p": 0.95,
            "top_k": 0,
        }
        
        model = genai.GenerativeModel(model_name=model, generation_config=generation_config)
        response = model.generate_content(gemini_messages)
        
        return {
            "content": response.text,
            "model": model,
            "tokens": {
                "prompt": 0,  # Gemini не возвращает количество токенов
                "completion": 0,
                "total": 0
            }
        }
    except Exception as e:
        logger.error(f"Error in Gemini API call: {str(e)}")
        return {"error": str(e)}

# Маршруты API
@app.get("/")
async def root():
    """Корневой эндпоинт, возвращает статус сервера"""
    return {
        "status": "ok", 
        "service": "MCP Server", 
        "version": "1.0.0",
        "gemini_enabled": gemini_enabled
    }

@app.post("/api/v1/models/query")
async def query_model(request: ModelRequest, api_key: str = Depends(get_api_key)):
    """Отправка запроса к языковой модели"""
    try:
        logger.info(f"Model query received: {request.model}")
        
        # Обработка и отправка запроса к модели
        if request.model.startswith("gemini"):
            model_response = await query_gemini(
                request.messages,
                model=request.model,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            if "error" in model_response:
                raise Exception(model_response["error"])
                
            response = {
                "id": str(uuid.uuid4()),
                "model": request.model,
                "created": int(time.time()),
                "content": model_response["content"],
                "tokens": model_response["tokens"]
            }
        else:
            # Для других моделей или симуляции
            logger.warning(f"Unsupported model: {request.model}, using simulated response")
            response = {
                "id": str(uuid.uuid4()),
                "model": request.model,
                "created": int(time.time()),
                "content": "Это симуляция ответа от модели. Используйте модель Gemini для реальных ответов.",
                "tokens": {
                    "prompt": 0,
                    "completion": 0,
                    "total": 0
                }
            }
        
        # Если указан context_id, обновляем контекст
        if request.context_id:
            if request.context_id not in contexts:
                contexts[request.context_id] = {
                    "created": datetime.now().isoformat(),
                    "messages": request.messages
                }
            else:
                contexts[request.context_id]["messages"].extend(request.messages)
                # Добавляем ответ модели в контекст
                contexts[request.context_id]["messages"].append({
                    "role": "assistant", 
                    "content": response["content"]
                })
        
        return response
    except Exception as e:
        logger.error(f"Error in query_model: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/context/update")
async def update_context(request: ContextUpdateRequest, api_key: str = Depends(get_api_key)):
    """Обновление контекста без запроса к модели"""
    try:
        if request.context_id not in contexts:
            contexts[request.context_id] = {
                "created": datetime.now().isoformat(),
                "messages": request.messages
            }
        else:
            contexts[request.context_id]["messages"].extend(request.messages)
        
        return {"status": "ok", "context_id": request.context_id}
    except Exception as e:
        logger.error(f"Error in update_context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/context/clear")
async def clear_context(request: ContextClearRequest, api_key: str = Depends(get_api_key)):
    """Очистка контекста для указанного идентификатора"""
    try:
        if request.context_id in contexts:
            del contexts[request.context_id]
        
        return {"status": "ok", "context_id": request.context_id}
    except Exception as e:
        logger.error(f"Error in clear_context: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/context/{context_id}")
async def get_context(context_id: str, api_key: str = Depends(get_api_key)):
    """Получение контекста по идентификатору"""
    if context_id not in contexts:
        raise HTTPException(status_code=404, detail="Context not found")
    
    return contexts[context_id]

@app.get("/api/v1/models")
async def list_models(api_key: str = Depends(get_api_key)):
    """Получение списка доступных моделей"""
    models = [
        {
            "id": "gemini-2.5-pro-preview-03-25",
            "name": "Google Gemini 2.5 Pro Preview",
            "available": gemini_enabled
        }
    ]
    return {"models": models}

# Точка входа для запуска сервера
def main():
    parser = argparse.ArgumentParser(description="MCP Server")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8089, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", type=str, default="info", help="Logging level")
    
    args = parser.parse_args()
    
    logger.info(f"Starting MCP Server on {args.host}:{args.port}")
    
    uvicorn.run(
        "mcp_server:app", 
        host=args.host, 
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )

if __name__ == "__main__":
    main() 