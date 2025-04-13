#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import argparse
import logging
import subprocess
import platform
import json
import shutil
import datetime
from concurrent.futures import ThreadPoolExecutor
import importlib.util

# Настройка журналирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("NeuroRAT-TestRunner")

# Список тестовых модулей
TEST_MODULES = [
    "test_encryption.py",
    "test_neurorat.py",
    "test_llm_processor.py",
    "test_neurorat_agent.py",
    "test_agent_server.py",
    "test_agent_modules.py",
    "test_security.py",
    "test_evasion.py",
    "test_load.py",
    "test_compatibility.py"
]

def check_dependencies():
    """Проверяет наличие необходимых зависимостей для тестирования"""
    try:
        import pytest
        import unittest
        import requests
        import cryptography
        logger.info("Все базовые зависимости установлены")
        return True
    except ImportError as e:
        logger.error(f"Отсутствует необходимая зависимость: {e}")
        logger.info("Установите зависимости командой: pip install pytest requests cryptography")
        return False

def generate_system_info():
    """Собирает информацию о системе"""
    system_info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "processor": platform.processor(),
        "hostname": platform.node(),
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    # Проверка доступности agent_protocol
    try:
        import agent_protocol
        system_info["agent_protocol_available"] = True
    except ImportError:
        system_info["agent_protocol_available"] = False
    
    return system_info

def run_unittest_module(module_path, output_dir):
    """Запускает указанный unittest-модуль"""
    if not os.path.exists(module_path):
        logger.warning(f"Модуль {module_path} не найден")
        return {"module": module_path, "status": "skipped", "reason": "file_not_found"}
    
    logger.info(f"Запуск теста: {module_path}")
    
    # Создаем директорию для логов
    log_file = os.path.join(output_dir, f"{os.path.basename(module_path)}.log")
    
    # Запускаем тест как отдельный процесс
    process = subprocess.Popen(
        [sys.executable, module_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    
    # Сохраняем вывод в лог-файл
    with open(log_file, 'w') as f:
        f.write("=== STDOUT ===\n")
        f.write(stdout)
        f.write("\n\n=== STDERR ===\n")
        f.write(stderr)
    
    # Анализируем результат
    if process.returncode == 0:
        status = "passed"
    else:
        status = "failed"
    
    return {
        "module": module_path,
        "status": status,
        "returncode": process.returncode,
        "log_file": log_file
    }

def run_pytest_module(module_path, output_dir):
    """Запускает указанный модуль с помощью pytest"""
    if not os.path.exists(module_path):
        logger.warning(f"Модуль {module_path} не найден")
        return {"module": module_path, "status": "skipped", "reason": "file_not_found"}
    
    logger.info(f"Запуск pytest: {module_path}")
    
    # Имя файла для отчета JUnit
    xml_report = os.path.join(output_dir, f"{os.path.basename(module_path)}.xml")
    html_report = os.path.join(output_dir, f"{os.path.basename(module_path)}.html")
    
    # Запускаем pytest
    process = subprocess.Popen(
        [
            sys.executable, "-m", "pytest", module_path,
            "--junitxml", xml_report,
            "--html", html_report,
            "-v"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    
    stdout, stderr = process.communicate()
    
    # Сохраняем вывод в лог-файл
    log_file = os.path.join(output_dir, f"pytest_{os.path.basename(module_path)}.log")
    with open(log_file, 'w') as f:
        f.write("=== STDOUT ===\n")
        f.write(stdout)
        f.write("\n\n=== STDERR ===\n")
        f.write(stderr)
    
    # Анализируем результат
    if process.returncode == 0:
        status = "passed"
    else:
        status = "failed"
    
    return {
        "module": module_path,
        "status": status,
        "returncode": process.returncode,
        "log_file": log_file,
        "xml_report": xml_report if os.path.exists(xml_report) else None,
        "html_report": html_report if os.path.exists(html_report) else None
    }

def generate_summary_report(results, output_dir, system_info):
    """Генерирует итоговый отчет"""
    summary = {
        "timestamp": datetime.datetime.now().isoformat(),
        "system_info": system_info,
        "results": results,
        "stats": {
            "total": len(results),
            "passed": sum(1 for r in results if r["status"] == "passed"),
            "failed": sum(1 for r in results if r["status"] == "failed"),
            "skipped": sum(1 for r in results if r["status"] == "skipped")
        }
    }
    
    # Сохраняем JSON-отчет
    summary_json = os.path.join(output_dir, "summary_report.json")
    with open(summary_json, 'w') as f:
        json.dump(summary, f, indent=2)
    
    # Создаем HTML-отчет
    summary_html = os.path.join(output_dir, "summary_report.html")
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NeuroRAT Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #3498db; margin-top: 30px; }}
        .stats {{ display: flex; margin: 20px 0; }}
        .stat-box {{ flex: 1; padding: 15px; margin: 0 10px; border-radius: 5px; color: white; text-align: center; }}
        .passed {{ background-color: #27ae60; }}
        .failed {{ background-color: #e74c3c; }}
        .skipped {{ background-color: #f39c12; }}
        .total {{ background-color: #2980b9; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background-color: #3498db; color: white; }}
        tr:hover {{ background-color: #f5f5f5; }}
        .status-passed {{ color: #27ae60; font-weight: bold; }}
        .status-failed {{ color: #e74c3c; font-weight: bold; }}
        .status-skipped {{ color: #f39c12; font-weight: bold; }}
        .system-info {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .time {{ color: #7f8c8d; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>NeuroRAT Test Report</h1>
        <div class="time">Generated on: {summary["timestamp"]}</div>
        
        <h2>System Information</h2>
        <div class="system-info">
            <p><strong>Platform:</strong> {system_info["platform"]}</p>
            <p><strong>Python Version:</strong> {system_info["python_version"]}</p>
            <p><strong>Processor:</strong> {system_info["processor"]}</p>
            <p><strong>Hostname:</strong> {system_info["hostname"]}</p>
            <p><strong>Agent Protocol Available:</strong> {system_info["agent_protocol_available"]}</p>
        </div>
        
        <h2>Test Summary</h2>
        <div class="stats">
            <div class="stat-box total">
                <h3>Total</h3>
                <div class="stat-value">{summary["stats"]["total"]}</div>
            </div>
            <div class="stat-box passed">
                <h3>Passed</h3>
                <div class="stat-value">{summary["stats"]["passed"]}</div>
            </div>
            <div class="stat-box failed">
                <h3>Failed</h3>
                <div class="stat-value">{summary["stats"]["failed"]}</div>
            </div>
            <div class="stat-box skipped">
                <h3>Skipped</h3>
                <div class="stat-value">{summary["stats"]["skipped"]}</div>
            </div>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <tr>
                <th>Module</th>
                <th>Status</th>
                <th>Reports</th>
            </tr>
    """
    
    for result in results:
        status_class = f"status-{result['status']}"
        reports = []
        
        if result.get("log_file") and os.path.exists(result["log_file"]):
            log_filename = os.path.basename(result["log_file"])
            reports.append(f'<a href="{log_filename}">Log</a>')
        
        if result.get("html_report") and os.path.exists(result["html_report"]):
            html_filename = os.path.basename(result["html_report"])
            reports.append(f'<a href="{html_filename}">HTML</a>')
            
        if result.get("xml_report") and os.path.exists(result["xml_report"]):
            xml_filename = os.path.basename(result["xml_report"])
            reports.append(f'<a href="{xml_filename}">XML</a>')
        
        html_content += f"""
            <tr>
                <td>{os.path.basename(result["module"])}</td>
                <td class="{status_class}">{result["status"].upper()}</td>
                <td>{'  |  '.join(reports)}</td>
            </tr>
        """
    
    html_content += """
        </table>
    </div>
</body>
</html>
    """
    
    with open(summary_html, 'w') as f:
        f.write(html_content)
    
    return summary

def run_all_tests(output_dir, workers=4, use_pytest=True):
    """Запускает все тесты параллельно"""
    logger.info(f"Запуск всех тестов с использованием {workers} потоков")
    
    # Создаем директорию для результатов, если она не существует
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Получаем информацию о системе
    system_info = generate_system_info()
    
    # Сохраняем информацию о системе
    with open(os.path.join(output_dir, "system_info.json"), 'w') as f:
        json.dump(system_info, f, indent=2)
    
    # Запускаем тесты параллельно
    results = []
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        
        for module in TEST_MODULES:
            if use_pytest and importlib.util.find_spec("pytest"):
                future = executor.submit(run_pytest_module, module, output_dir)
            else:
                future = executor.submit(run_unittest_module, module, output_dir)
            futures.append(future)
        
        for future in futures:
            results.append(future.result())
    
    # Генерируем итоговый отчет
    summary = generate_summary_report(results, output_dir, system_info)
    
    # Выводим краткую статистику
    stats = summary["stats"]
    logger.info(f"Тестирование завершено: Всего {stats['total']}, Успешно {stats['passed']}, Сбои {stats['failed']}, Пропущено {stats['skipped']}")
    
    # Открываем отчет в браузере, если это возможно
    summary_html = os.path.join(output_dir, "summary_report.html")
    if os.path.exists(summary_html):
        logger.info(f"Отчет сохранен в: {summary_html}")
        try:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(summary_html)}")
        except:
            pass
    
    return stats['failed'] == 0

def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="NeuroRAT Test Runner")
    parser.add_argument("--output-dir", default="test_results", help="Директория для результатов тестов")
    parser.add_argument("--workers", type=int, default=4, help="Количество параллельных потоков для тестов")
    parser.add_argument("--use-pytest", action="store_true", help="Использовать pytest вместо unittest")
    args = parser.parse_args()
    
    # Проверяем зависимости
    if not check_dependencies():
        return 1
    
    # Запускаем все тесты
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output_dir, timestamp)
    
    success = run_all_tests(
        output_dir=output_dir,
        workers=args.workers,
        use_pytest=args.use_pytest
    )
    
    # Создаем символическую ссылку на последний отчет
    latest_link = os.path.join(args.output_dir, "latest")
    if os.path.exists(latest_link):
        if os.path.islink(latest_link):
            os.unlink(latest_link)
        else:
            shutil.rmtree(latest_link)
    
    try:
        os.symlink(os.path.abspath(output_dir), os.path.abspath(latest_link))
        logger.info(f"Создана ссылка на последний отчет: {latest_link}")
    except Exception as e:
        logger.warning(f"Не удалось создать символическую ссылку: {e}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 