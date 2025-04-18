import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ChakraProvider, extendTheme } from '@chakra-ui/react';
import styled, { ThemeProvider as StyledThemeProvider } from 'styled-components';

// Components
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import Sidebar from './components/Sidebar';

// Pages
import DashboardPage from './pages/DashboardPage';
import ZondsManagementPage from './pages/ZondsManagementPage';
import IncidentsListPage from './pages/IncidentsListPage';
import AnomalyDetectionPage from './pages/AnomalyDetectionPage';
import AnomalyDetailsPage from './pages/AnomalyDetailsPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';
import CodexPage from './pages/CodexPage';
import C1BrainPage from './pages/C1BrainPage';
import SecurityPage from './pages/SecurityPage';
import TasksPage from './pages/TasksPage';
import ReportsPage from './pages/ReportsPage';
import SettingsPage from './pages/SettingsPage';
import ATSPage from './pages/ATSPage';
import IncidentDetailsPage from './pages/IncidentDetailsPage';

// Styles
const AppContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background-color: #121212;
  color: #e0e0e0;
`;

const ContentArea = styled.div`
  flex: 1;
  margin-left: 250px;
  padding: 20px;
`;

// Custom theme
const chakraTheme = extendTheme({
  colors: {
    brand: {
      50: '#e3f2fd',
      100: '#bbdefb',
      500: '#2196f3',
      600: '#1e88e5',
      700: '#1976d2',
      800: '#1565c0',
      900: '#0d47a1',
    },
    dark: {
      100: '#2d2d2d',
      200: '#212121',
      300: '#1a1a1a',
      400: '#121212',
    },
  },
  config: {
    initialColorMode: 'dark',
    useSystemColorMode: false,
  },
});

// Styled-components theme
const styledTheme = {
  bg: {
    primary: '#121212',
    secondary: '#1E1E1E',
    tertiary: '#2D2D2D',
    input: '#252525',
    hover: '#333333',
  },
  text: {
    primary: '#FFFFFF',
    secondary: '#A0A0A0',
    placeholder: '#6C6C6C',
    inverted: '#000000',
  },
  border: {
    primary: '#3A3A3A',
    secondary: '#4D4D4D',
  },
  accent: {
    primary: '#0F94FF',
    secondary: '#107EFF',
  },
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#3B82F6',
};

const App: React.FC = () => {
  return (
    <ChakraProvider theme={chakraTheme}>
      <StyledThemeProvider theme={styledTheme}>
        <AppContainer>
          <Router>
            <Sidebar />
            <ContentArea>
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<LoginPage />} />
                
                {/* Основное */}
                <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
                <Route path="/zonds" element={<ProtectedRoute><ZondsManagementPage /></ProtectedRoute>} />
                <Route path="/incidents" element={<ProtectedRoute><IncidentsListPage /></ProtectedRoute>} />
                <Route path="/incidents/:id" element={<ProtectedRoute><IncidentDetailsPage /></ProtectedRoute>} />
                <Route path="/anomalies" element={<ProtectedRoute><AnomalyDetectionPage /></ProtectedRoute>} />
                <Route path="/anomalies/:id" element={<ProtectedRoute><AnomalyDetailsPage /></ProtectedRoute>} />
                
                {/* Управление */}
                <Route path="/codex" element={<ProtectedRoute><CodexPage /></ProtectedRoute>} />
                <Route path="/c1brain" element={<ProtectedRoute><C1BrainPage /></ProtectedRoute>} />
                <Route path="/operations" element={<ProtectedRoute><TasksPage /></ProtectedRoute>} />
                <Route path="/ats" element={<ProtectedRoute><ATSPage /></ProtectedRoute>} />
                
                {/* Аналитика */}
                <Route path="/analytics" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
                <Route path="/security" element={<ProtectedRoute><SecurityPage /></ProtectedRoute>} />
                
                {/* Система */}
                <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
                <Route path="/reports" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
                
                {/* 404 Not Found */}
                <Route path="*" element={<NotFoundPage />} />
              </Routes>
            </ContentArea>
          </Router>
        </AppContainer>
      </StyledThemeProvider>
    </ChakraProvider>
  );
};

export default App; 