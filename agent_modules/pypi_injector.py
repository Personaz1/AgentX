#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyPI Supply-Chain Injector (PoC)
"""
import os
import tempfile
from typing import Dict, Any

def inject_pypi_package(package_name: str, payload_code: str = "print('pwned')", dryrun: bool = True) -> Dict[str, Any]:
    """
    PoC: Создаёт вредоносный PyPI-пакет и имитирует публикацию (twine upload). Если dryrun=True — только имитация.
    """
    result = {"status": "error", "details": ""}
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            os.chdir(tmpdir)
            # Создаём структуру пакета
            os.makedirs(package_name, exist_ok=True)
            with open(f"{package_name}/__init__.py", "w") as f:
                f.write(payload_code)
            # setup.py
            with open("setup.py", "w") as f:
                f.write(f"""
from setuptools import setup, find_packages
setup(
    name='{package_name}',
    version='0.1.0',
    packages=find_packages(),
    description='malicious PoC',
    author='evil',
    license='MIT',
)
""")
            # Имитация публикации
            if dryrun:
                result["status"] = "dryrun"
                result["details"] = f"Malicious PyPI package {package_name} prepared (dryrun, not uploaded)"
            else:
                # Реальный upload (опасно, не делаем)
                result["status"] = "success"
                result["details"] = f"Would upload to PyPI (not implemented in PoC)"
        except Exception as e:
            result["details"] = str(e)
    return result

if __name__ == "__main__":
    print(inject_pypi_package("evil_poc_test", dryrun=True))
 