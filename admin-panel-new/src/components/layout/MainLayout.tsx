import React, { useState } from 'react';
import { Outlet } from 'react-router-dom';
import styled from 'styled-components';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

// Типы
interface MainLayoutProps {
  children?: React.ReactNode;
}

// Стили компонентов
const LayoutContainer = styled.div`
  display: flex;
  height: 100vh;
  width: 100%;
`;

const MainContent = styled.main`
  flex: 1;
  overflow-y: auto;
  padding: 2rem;
  background-color: ${props => props.theme.bg.primary};
`;

const ContentWrapper = styled.div`
  max-width: 1400px;
  margin: 0 auto;
`;

// Основной компонент макета
const MainLayout: React.FC<MainLayoutProps> = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);

  // Переключение боковой панели
  const toggleSidebar = () => {
    setSidebarOpen(!sidebarOpen);
  };

  return (
    <LayoutContainer>
      {/* Боковая панель */}
      <Sidebar isOpen={sidebarOpen} />
      
      {/* Основное содержимое */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Верхняя панель */}
        <TopBar toggleSidebar={toggleSidebar} />
        
        {/* Контент страницы */}
        <MainContent>
          <ContentWrapper>
            <Outlet />
          </ContentWrapper>
        </MainContent>
      </div>
    </LayoutContainer>
  );
};

export default MainLayout; 