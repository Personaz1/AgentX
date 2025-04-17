#ifndef INJECTION_H
#define INJECTION_H

#include <stddef.h> // Для size_t

/**
 * @brief Выполняет технику Process Hollowing.
 *
 * @param target_path Путь к легитимному исполняемому файлу-жертве (UTF-8).
 * @param payload Указатель на байты шеллкода/PE для внедрения.
 * @param payload_size Размер payload в байтах.
 * @return int 0 в случае успеха, отрицательное значение в случае ошибки.
 */
int inject_hollow_process(const char* target_path, const unsigned char* payload, size_t payload_size);

// Можно добавить другие функции инъекции здесь

#endif // INJECTION_H 