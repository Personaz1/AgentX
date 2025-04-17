import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ChakraProvider, extendTheme } from '@chakra-ui/react';
import styled, { ThemeProvider as StyledThemeProvider } from 'styled-components';

// Components
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import Sidebar from './components/Sidebar';

// Pages
import Dashboard from './pages/Dashboard';
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
  colors: {
    primary: '#2196f3',
    primaryDark: '#1976d2',
    secondary: '#ff4081',
    success: '#4caf50',
    warning: '#ff9800',
    error: '#f44336',
    background: '#121212',
    surface: '#1e1e1e',
    text: '#e0e0e0',
    textSecondary: '#a0a0a0',
    border: '#333333',
  },
  shadows: {
    small: '0 2px 4px rgba(0, 0, 0, 0.3)',
    medium: '0 4px 8px rgba(0, 0, 0, 0.4)',
    large: '0 8px 16px rgba(0, 0, 0, 0.5)',
  },
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
                
                {/* Protected routes */}
                <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
                <Route path="/zonds" element={<ProtectedRoute><ZondsManagementPage /></ProtectedRoute>} />
                <Route path="/incidents" element={<ProtectedRoute><IncidentsListPage /></ProtectedRoute>} />
                <Route path="/anomalies" element={<ProtectedRoute><AnomalyDetectionPage /></ProtectedRoute>} />
                <Route path="/anomalies/:id" element={<ProtectedRoute><AnomalyDetailsPage /></ProtectedRoute>} />
                <Route path="/c1brain" element={<ProtectedRoute><C1BrainPage /></ProtectedRoute>} />
                <Route path="/codex" element={<ProtectedRoute><CodexPage /></ProtectedRoute>} />
                <Route path="/security" element={<ProtectedRoute><SecurityPage /></ProtectedRoute>} />
                <Route path="/operations" element={<ProtectedRoute><TasksPage /></ProtectedRoute>} />
                <Route path="/analytics" element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
                <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
                <Route path="/billing" element={<ProtectedRoute><NotFoundPage /></ProtectedRoute>} />
                
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