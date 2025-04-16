import React from 'react';
import styled from 'styled-components';

const NavbarWrapper = styled.nav`
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
`;

const Logo = styled.div`
  font-size: 1.2rem;
  font-weight: bold;
  color: ${props => props.theme.text.primary};
`;

const NavActions = styled.div`
  display: flex;
  align-items: center;
`;

const StatusIndicator = styled.div`
  display: flex;
  align-items: center;
  margin-right: 20px;
`;

const StatusDot = styled.div<{ status: 'online' | 'offline' | 'error' }>`
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 8px;
  background-color: ${props => 
    props.status === 'online' ? props.theme.success :
    props.status === 'offline' ? props.theme.danger :
    props.theme.warning
  };
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
`;

const Avatar = styled.div`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background-color: ${props => props.theme.accent.primary};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  margin-right: 10px;
`;

const Username = styled.span`
  color: ${props => props.theme.text.primary};
`;

const Navbar: React.FC = () => {
  // В реальном приложении эти данные будут приходить через props или контекст
  const systemStatus = 'online';
  const username = 'Admin';

  return (
    <NavbarWrapper>
      <Logo>NeuroRAT</Logo>
      
      <NavActions>
        <StatusIndicator>
          <StatusDot status={systemStatus as 'online' | 'offline' | 'error'} />
          <span>Система {systemStatus === 'online' ? 'онлайн' : 'офлайн'}</span>
        </StatusIndicator>
        
        <UserInfo>
          <Avatar>{username[0]}</Avatar>
          <Username>{username}</Username>
        </UserInfo>
      </NavActions>
    </NavbarWrapper>
  );
};

export default Navbar; 