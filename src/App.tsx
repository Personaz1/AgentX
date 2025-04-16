import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ChakraProvider } from '@chakra-ui/react';
import { useAppSelector } from './app/hooks';
import { selectIsAuthenticated } from './features/auth/authSlice';
import { theme } from './utils/theme';

// Компоненты layout
import MainLayout from './components/layout/MainLayout';

// Страницы
import Dashboard from './pages/Dashboard';
import ZondsPage from './pages/ZondsPage';
import ZondDetailPage from './pages/ZondDetailPage';
import TasksPage from './pages/TasksPage';
import TaskDetailPage from './pages/TaskDetailPage';
import C1BrainPage from './pages/C1BrainPage';
import ATSPage from './pages/ATSPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';

// Компонент для защищенных маршрутов
const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

const App = () => {
  return (
    <ChakraProvider theme={theme}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          <Route 
            path="/" 
            element={
              <ProtectedRoute>
                <MainLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Dashboard />} />
            <Route path="zonds" element={<ZondsPage />} />
            <Route path="zonds/:zondId" element={<ZondDetailPage />} />
            <Route path="tasks" element={<TasksPage />} />
            <Route path="tasks/:taskId" element={<TaskDetailPage />} />
            <Route path="c1brain" element={<C1BrainPage />} />
            <Route path="ats" element={<ATSPage />} />
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ChakraProvider>
  );
};

export default App; 