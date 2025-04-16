import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import { RootState } from '../store';

export const api = createApi({
  reducerPath: 'api',
  baseQuery: fetchBaseQuery({ 
    baseUrl: '/api',
    prepareHeaders: (headers, { getState }) => {
      // Получаем токен из состояния Redux
      const token = (getState() as RootState).auth.token;
      
      // Если есть токен, добавляем его в заголовки запросов
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      
      return headers;
    },
  }),
  tagTypes: ['Zond', 'Task', 'Report', 'User', 'Settings'],
  endpoints: (builder) => ({}),
}); 