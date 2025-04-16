import React from 'react';
import { NavLink } from 'react-router-dom';
import styled from 'styled-components';

const SidebarContainer = styled.div`
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
`;

const Logo = styled.div`
  padding: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-bottom: 1px solid #333;
`;

const LogoText = styled.h1`
  font-size: 1.5rem;
  font-weight: bold;
  color: ${props => props.theme.accent.primary};
  margin: 0;
`;

const NavSection = styled.div`
  padding: 15px 0;
  border-bottom: 1px solid #333;
`;

const SectionTitle = styled.h3`
  font-size: 0.75rem;
  text-transform: uppercase;
  color: ${props => props.theme.text.tertiary};
  padding: 0 20px;
  margin-bottom: 10px;
`;

const NavItem = styled(NavLink)`
  display: flex;
  align-items: center;
  padding: 10px 20px;
  color: ${props => props.theme.text.secondary};
  text-decoration: none;
  transition: all 0.2s;
  
  &:hover {
    background-color: rgba(255, 255, 255, 0.05);
  }
  
  &.active {
    background-color: rgba(0, 114, 245, 0.1);
    color: ${props => props.theme.accent.primary};
    border-left: 3px solid ${props => props.theme.accent.primary};
  }
`;

const NavIcon = styled.span`
  margin-right: 10px;
  display: flex;
  align-items: center;
  font-size: 1.1rem;
`;

const Sidebar: React.FC = () => {
  return (
    <SidebarContainer>
      <Logo>
        <LogoText>NeuroRAT</LogoText>
      </Logo>
      
      <NavSection>
        <SectionTitle>Основное</SectionTitle>
        <NavItem to="/" className={({ isActive }) => isActive ? 'active' : ''}>
          <NavIcon>📊</NavIcon> Дашборд
        </NavItem>
        <NavItem to="/zonds" className={({ isActive }) => isActive ? 'active' : ''}>
          <NavIcon>🖥️</NavIcon> Зонды
        </NavItem>
        <NavItem to="/tasks" className={({ isActive }) => isActive ? 'active' : ''}>
          <NavIcon>📋</NavIcon> Задачи
        </NavItem>
      </NavSection>
      
      <NavSection>
        <SectionTitle>Управление</SectionTitle>
        <NavItem to="/c1brain" className={({ isActive }) => isActive ? 'active' : ''}>
          <NavIcon>🧠</NavIcon> C1Brain
        </NavItem>
        <NavItem to="/ats" className={({ isActive }) => isActive ? 'active' : ''}>
          <NavIcon>💰</NavIcon> ATS Модуль
        </NavItem>
      </NavSection>
      
      <NavSection>
        <SectionTitle>Система</SectionTitle>
        <NavItem to="/settings" className={({ isActive }) => isActive ? 'active' : ''}>
          <NavIcon>⚙️</NavIcon> Настройки
        </NavItem>
        <NavItem to="/logs" className={({ isActive }) => isActive ? 'active' : ''}>
          <NavIcon>📜</NavIcon> Журнал
        </NavItem>
      </NavSection>
    </SidebarContainer>
  );
};

export default Sidebar; 