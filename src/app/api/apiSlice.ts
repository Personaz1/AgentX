import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { RootState } from '../store';

// Базовая конфигурация API с RTK Query
export const apiSlice = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ 
    baseUrl: '/api',
    prepareHeaders: (headers, { getState }) => {
      // Получение токена из состояния Redux
      const token = (getState() as RootState).auth.token;
      
      // Добавление заголовка Authorization, если токен существует
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      
      return headers;
    },
  }),
  // Типы тегов для кэширования и инвалидации
  tagTypes: ['Zonds', 'Tasks', 'C1Brain', 'ATS'],
  // Эндпоинты будут добавляться в отдельных слайсах
  endpoints: () => ({}),
}); 