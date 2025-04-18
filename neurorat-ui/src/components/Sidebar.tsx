import React from 'react';
import { NavLink } from 'react-router-dom';
import styled from 'styled-components';
import { 
  FiHome, 
  FiServer, 
  FiList, 
  FiActivity, 
  FiSettings, 
  FiFileText, 
  FiAlertTriangle, 
  FiCode, 
  FiCpu,
  FiBarChart2,
  FiDatabase,
  FiDollarSign,
  FiShield
} from 'react-icons/fi';
import { darkTheme } from '../theme';

// Типизация для темы styled-components
type Theme = typeof darkTheme;

const SidebarContainer = styled.div<{ theme: Theme }>`
  width: 250px;
  height: 100vh;
  position: fixed;
  top: 0;
  left: 0;
  background-color: ${({ theme }) => theme.bg.secondary};
  color: ${({ theme }) => theme.text.primary};
  padding: 20px 0;
  border-right: 1px solid ${({ theme }) => theme.border.primary};
  overflow-y: auto;
`;

const Logo = styled.div<{ theme: Theme }>`
  font-size: 22px;
  font-weight: bold;
  text-align: center;
  margin-bottom: 30px;
  padding: 0 20px;
  color: ${({ theme }) => theme.accent.primary};
`;

const NavSection = styled.div`
  margin-bottom: 25px;
  padding: 0 15px;
`;

const SectionTitle = styled.div<{ theme: Theme }>`
  font-size: 12px;
  text-transform: uppercase;
  color: ${({ theme }) => theme.text.secondary};
  margin-bottom: 10px;
  padding: 0 10px;
  letter-spacing: 0.5px;
`;

const NavItem = styled(NavLink)<{ theme: Theme }>`
  display: flex;
  align-items: center;
  padding: 10px;
  margin-bottom: 5px;
  text-decoration: none;
  color: ${({ theme }) => theme.text.primary};
  border-radius: 5px;
  transition: all 0.2s ease;

  &:hover {
    background-color: ${({ theme }) => theme.bg.hover};
  }

  &.active {
    background-color: ${({ theme }) => theme.accent.primary};
    color: ${({ theme }) => theme.text.inverted};
  }
`;

const NavIcon = styled.div`
  margin-right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
`;

const Sidebar: React.FC = () => {
  return (
    <SidebarContainer>
      <Logo>NeuroZond</Logo>

      <NavSection>
        <SectionTitle>Основное</SectionTitle>
        <NavItem to="/dashboard">
          <NavIcon><FiHome /></NavIcon>
          Дашборд
        </NavItem>
        <NavItem to="/zonds">
          <NavIcon><FiServer /></NavIcon>
          Зонды
        </NavItem>
        <NavItem to="/incidents">
          <NavIcon><FiAlertTriangle /></NavIcon>
          Инциденты
        </NavItem>
        <NavItem to="/anomalies">
          <NavIcon><FiBarChart2 /></NavIcon>
          Аномалии
        </NavItem>
      </NavSection>

      <NavSection>
        <SectionTitle>Управление</SectionTitle>
        <NavItem to="/codex">
          <NavIcon><FiCode /></NavIcon>
          Codex
        </NavItem>
        <NavItem to="/c1brain">
          <NavIcon><FiCpu /></NavIcon>
          C1 Brain
        </NavItem>
        <NavItem to="/operations">
          <NavIcon><FiList /></NavIcon>
          Операции
        </NavItem>
        <NavItem to="/ats">
          <NavIcon><FiDollarSign /></NavIcon>
          ATS Модуль
        </NavItem>
      </NavSection>

      <NavSection>
        <SectionTitle>Аналитика</SectionTitle>
        <NavItem to="/analytics">
          <NavIcon><FiActivity /></NavIcon>
          Отчёты
        </NavItem>
        <NavItem to="/security">
          <NavIcon><FiShield /></NavIcon>
          Безопасность
        </NavItem>
      </NavSection>

      <NavSection>
        <SectionTitle>Система</SectionTitle>
        <NavItem to="/settings">
          <NavIcon><FiSettings /></NavIcon>
          Настройки
        </NavItem>
        <NavItem to="/reports">
          <NavIcon><FiFileText /></NavIcon>
          Логи
        </NavItem>
      </NavSection>
    </SidebarContainer>
  );
};

export default Sidebar; 