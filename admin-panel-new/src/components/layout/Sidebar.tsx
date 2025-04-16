import React from 'react';
import { NavLink } from 'react-router-dom';
import styled from 'styled-components';
import { FiHome, FiServer, FiList, FiBrain, FiDollarSign, FiSettings, FiFileText } from 'react-icons/fi';

const SidebarContainer = styled.div`
  width: 250px;
  height: 100vh;
  background-color: ${props => props.theme.bg.secondary};
  border-right: 1px solid ${props => props.theme.border.primary};
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 0;
`;

const Logo = styled.div`
  padding: 0 20px;
  margin-bottom: 30px;
`;

const LogoText = styled.h1`
  font-size: 1.5rem;
  font-weight: bold;
  color: ${props => props.theme.accent.primary};
  margin: 0;
`;

const NavSection = styled.div`
  margin-bottom: 25px;
`;

const SectionTitle = styled.h2`
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
    background-color: rgba(0, 114, 245, 0.05);
  }
  
  &.active {
    background-color: rgba(0, 114, 245, 0.1);
    color: ${props => props.theme.accent.primary};
    border-left: 3px solid ${props => props.theme.accent.primary};
  }
`;

const NavIcon = styled.div`
  display: flex;
  align-items: center;
  margin-right: 10px;
  font-size: 1.1rem;
`;

interface NavItemProps {
  to: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  active?: boolean;
  onClick?: () => void;
}

const Sidebar: React.FC = () => {
  return (
    <SidebarContainer>
      <Logo>
        <LogoText>NeuroRAT</LogoText>
      </Logo>
      
      <NavSection>
        <SectionTitle>Основное</SectionTitle>
        <NavItem to="/" end>
          <NavIcon><FiHome /></NavIcon>
          Дашборд
        </NavItem>
        <NavItem to="/zonds">
          <NavIcon><FiServer /></NavIcon>
          Зонды
        </NavItem>
        <NavItem to="/tasks">
          <NavIcon><FiList /></NavIcon>
          Задачи
        </NavItem>
      </NavSection>
      
      <NavSection>
        <SectionTitle>Управление</SectionTitle>
        <NavItem to="/c1brain">
          <NavIcon><FiBrain /></NavIcon>
          C1Brain
        </NavItem>
        <NavItem to="/ats">
          <NavIcon><FiDollarSign /></NavIcon>
          ATS Модуль
        </NavItem>
      </NavSection>
      
      <NavSection>
        <SectionTitle>Система</SectionTitle>
        <NavItem to="/reports">
          <NavIcon><FiFileText /></NavIcon>
          Отчёты
        </NavItem>
        <NavItem to="/settings">
          <NavIcon><FiSettings /></NavIcon>
          Настройки
        </NavItem>
      </NavSection>
    </SidebarContainer>
  );
};

export default Sidebar; 