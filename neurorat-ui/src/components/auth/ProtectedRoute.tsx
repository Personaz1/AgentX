import React from 'react';
import { Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { selectAuth } from '../../features/auth/authSlice';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  // Получаем данные аутентификации из Redux store
  const { isAuthenticated, isLoading } = useSelector(selectAuth);
  
  // Если загрузка, можно показать индикатор загрузки
  if (isLoading) {
    return <div>Загрузка...</div>;
  }

  // Если не аутентифицирован, перенаправляем на страницу логина
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Если аутентифицирован, показываем защищенный контент
  return <>{children}</>;
}; 