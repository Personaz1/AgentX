/**
 * @brief Получает данные по скрытому каналу HTTPS
 * 
 * @param handle Дескриптор канала
 * @param buffer Буфер для получаемых данных
 * @param buffer_size Размер буфера
 * @return int Количество полученных байт или -1 при ошибке, 0 если данных нет
 */
int https_channel_receive(CovertChannelHandle handle, unsigned char *buffer, size_t buffer_size);

/**
 * @brief Проверяет, активно ли соединение с сервером C2
 * 
 * @param handle Дескриптор канала
 * @return bool true, если соединение активно, иначе false
 */
bool https_channel_check_connection(CovertChannelHandle handle);

/**
 * @brief Освобождает ресурсы, связанные с каналом HTTPS
 * 
 * @param handle Дескриптор канала
 */
void https_channel_cleanup(CovertChannelHandle handle);

#ifdef __cplusplus
}
#endif

#endif // HTTPS_CHANNEL_H