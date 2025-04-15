# Использование инструментов агентом (естественный язык)

Агент теперь понимает команды словами (русский/английский) и сам интерпретирует их в вызовы модулей:

- "укради cookies", "cookie stealer", "cookies"
- "укради кошелек", "wallet stealer", "btc", "eth"
- "собери инфу", "system info", "sysinfo"
- "включи кейлоггер", "keylogger"
- "включи vnc", "screen", "экран"
- "ats", "автоматический перевод"
- "lateral", "латеральное перемещение"
- "nmap scan", "network scan", "scan [ip]", "portscan"
- "hydra bruteforce", "bruteforce ssh", "bruteforce rdp", "hydra [service]"
- "metasploit", "exploit", "msfconsole"
- "hashcat", "crack hash", "hash brute"
- "mimikatz", "dump creds", "lsass dump"

## Пример:
```
> укради cookies
> включи vnc
> system info
> start keylogger
> browser stealer
> lateral move
```

Агент сам определяет нужный модуль и вызывает его. Если команда не распознана — сообщает об этом.

## Как это работает
- Агент получает команду (например, через API или reasoning-агента)
- Вызывает у себя соответствующий модуль через функцию run_module
- Возвращает результат (файл, лог, статус) на сервер или reasoning-агенту 