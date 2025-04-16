import React, { useState } from 'react';
import styled from 'styled-components';

// Типы
interface Zond {
  id: string;
  name: string;
  ip: string;
  country: string;
  status: 'online' | 'offline' | 'error';
  os: string;
  lastSeen: string;
  activeTasks: number;
}

// Стилизованные компоненты
const Container = styled.div`
  padding: 20px 0;
`;

const Title = styled.h1`
  font-size: 1.8rem;
  margin-bottom: 20px;
  color: ${props => props.theme.text.primary};
`;

const ControlPanel = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
`;

const SearchInput = styled.input`
  padding: 10px;
  border-radius: 4px;
  background-color: ${props => props.theme.bg.tertiary};
  border: 1px solid #444;
  color: ${props => props.theme.text.primary};
  width: 300px;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent.primary};
  }
  
  @media (max-width: 768px) {
    width: 100%;
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 10px;
`;

const Button = styled.button`
  padding: 10px 15px;
  border-radius: 4px;
  background-color: ${props => props.theme.accent.primary};
  color: white;
  border: none;
  cursor: pointer;
  
  &:hover {
    background-color: ${props => props.theme.accent.secondary};
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background-color: ${props => props.theme.bg.secondary};
  border-radius: 8px;
  overflow: hidden;
`;

const Th = styled.th`
  text-align: left;
  padding: 15px;
  border-bottom: 1px solid #444;
  color: ${props => props.theme.text.secondary};
  font-weight: 500;
`;

const Td = styled.td`
  padding: 15px;
  border-bottom: 1px solid #444;
  color: ${props => props.theme.text.primary};
`;

const StatusBadge = styled.span<{ status: 'online' | 'offline' | 'error' }>`
  display: inline-block;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  background-color: ${props => 
    props.status === 'online' ? 'rgba(40, 167, 69, 0.2)' :
    props.status === 'offline' ? 'rgba(220, 53, 69, 0.2)' :
    'rgba(255, 193, 7, 0.2)'
  };
  color: ${props => 
    props.status === 'online' ? props.theme.success :
    props.status === 'offline' ? props.theme.danger :
    props.theme.warning
  };
`;

const ActionLink = styled.a`
  color: ${props => props.theme.accent.primary};
  text-decoration: none;
  margin-right: 10px;
  cursor: pointer;
  
  &:hover {
    text-decoration: underline;
  }
`;

const ZondsList: React.FC = () => {
  const [search, setSearch] = useState('');
  
  // Моковые данные зондов
  const zonds: Zond[] = [
    { id: 'zond-001', name: 'Desktop-RU-Moscow-01', ip: '192.168.1.100', country: 'Россия', status: 'online', os: 'Windows 10', lastSeen: '1 мин назад', activeTasks: 2 },
    { id: 'zond-002', name: 'Mobile-RU-SPB-01', ip: '192.168.1.101', country: 'Россия', status: 'online', os: 'Android 11', lastSeen: '5 мин назад', activeTasks: 0 },
    { id: 'zond-003', name: 'Server-DE-Berlin-01', ip: '192.168.1.102', country: 'Германия', status: 'offline', os: 'Ubuntu 20.04', lastSeen: '3 часа назад', activeTasks: 0 },
    { id: 'zond-004', name: 'Desktop-UK-London-01', ip: '192.168.1.103', country: 'Великобритания', status: 'online', os: 'Windows 11', lastSeen: '15 мин назад', activeTasks: 1 },
    { id: 'zond-005', name: 'Mobile-FR-Paris-01', ip: '192.168.1.104', country: 'Франция', status: 'error', os: 'iOS 15', lastSeen: '30 мин назад', activeTasks: 0 },
  ];
  
  // Фильтрация зондов по поиску
  const filteredZonds = zonds.filter(zond => 
    zond.name.toLowerCase().includes(search.toLowerCase()) ||
    zond.id.toLowerCase().includes(search.toLowerCase()) ||
    zond.ip.includes(search) ||
    zond.country.toLowerCase().includes(search.toLowerCase())
  );
  
  return (
    <Container>
      <Title>Управление зондами</Title>
      
      <ControlPanel>
        <SearchInput 
          type="text" 
          placeholder="Поиск по имени, ID, IP или стране..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        
        <ActionButtons>
          <Button>Добавить зонд</Button>
          <Button>Массовые действия</Button>
        </ActionButtons>
      </ControlPanel>
      
      <Table>
        <thead>
          <tr>
            <Th>ID</Th>
            <Th>Имя</Th>
            <Th>IP</Th>
            <Th>Страна</Th>
            <Th>Статус</Th>
            <Th>ОС</Th>
            <Th>Последняя активность</Th>
            <Th>Активные задачи</Th>
            <Th>Действия</Th>
          </tr>
        </thead>
        <tbody>
          {filteredZonds.map(zond => (
            <tr key={zond.id}>
              <Td>{zond.id}</Td>
              <Td>{zond.name}</Td>
              <Td>{zond.ip}</Td>
              <Td>{zond.country}</Td>
              <Td>
                <StatusBadge status={zond.status}>
                  {zond.status === 'online' ? 'Онлайн' : 
                   zond.status === 'offline' ? 'Офлайн' : 'Ошибка'}
                </StatusBadge>
              </Td>
              <Td>{zond.os}</Td>
              <Td>{zond.lastSeen}</Td>
              <Td>{zond.activeTasks}</Td>
              <Td>
                <ActionLink href={`/zonds/${zond.id}`}>Детали</ActionLink>
                <ActionLink>Задачи</ActionLink>
                <ActionLink>Удалить</ActionLink>
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Container>
  );
};

export default ZondsList; 