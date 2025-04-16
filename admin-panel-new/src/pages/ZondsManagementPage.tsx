import React, { useState } from 'react';
import styled from 'styled-components';

// Типы
enum ZondStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  CONNECTING = 'connecting',
  ERROR = 'error',
  COMPROMISED = 'compromised'
}

interface Zond {
  id: string;
  name: string;
  status: ZondStatus;
  ipAddress: string;
  location: string;
  os: string;
  version: string;
  lastSeen: string;
  cpuUsage: number;
  ramUsage: number;
  diskUsage: number;
  activeProcesses: number;
  connectedSince?: string;
  ping: number;
  activeOperations: number;
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

const StatsPanel = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const StatCard = styled.div`
  background-color: ${props => props.theme.bg.secondary};
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  text-align: center;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: 600;
  color: ${props => props.theme.text.primary};
  margin-bottom: 5px;
`;

const StatLabel = styled.div`
  font-size: 0.9rem;
  color: ${props => props.theme.text.secondary};
`;

const ControlPanel = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const SearchAndFilter = styled.div`
  display: flex;
  gap: 15px;
`;

const SearchInput = styled.input`
  padding: 10px 15px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.border.primary};
  background-color: ${props => props.theme.bg.input};
  color: ${props => props.theme.text.primary};
  width: 300px;
  
  &::placeholder {
    color: ${props => props.theme.text.placeholder};
  }
`;

const FilterSelect = styled.select`
  padding: 10px 15px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.border.primary};
  background-color: ${props => props.theme.bg.input};
  color: ${props => props.theme.text.primary};
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent.primary};
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 10px;
`;

const Button = styled.button<{variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning'}>`
  padding: 10px 15px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  
  background-color: ${props => 
    props.variant === 'danger' ? props.theme.danger :
    props.variant === 'success' ? props.theme.success :
    props.variant === 'warning' ? props.theme.warning :
    props.variant === 'secondary' ? props.theme.bg.tertiary :
    props.theme.accent.primary
  };
  
  color: ${props => 
    props.variant === 'secondary' ? props.theme.text.primary :
    'white'
  };
  
  &:hover {
    opacity: 0.9;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ZondGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const ZondCard = styled.div<{status: ZondStatus}>`
  background-color: ${props => props.theme.bg.secondary};
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  border-left: 4px solid ${props => 
    props.status === ZondStatus.ACTIVE ? props.theme.success :
    props.status === ZondStatus.INACTIVE ? props.theme.text.secondary :
    props.status === ZondStatus.CONNECTING ? props.theme.warning :
    props.status === ZondStatus.COMPROMISED ? props.theme.danger :
    props.theme.danger
  };
`;

const ZondHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
`;

const ZondName = styled.h3`
  font-size: 1.2rem;
  color: ${props => props.theme.text.primary};
  margin: 0;
`;

const ZondStatus = styled.div<{status: ZondStatus}>`
  display: flex;
  align-items: center;
  gap: 5px;
`;

const StatusDot = styled.div<{status: ZondStatus}>`
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background-color: ${props => 
    props.status === ZondStatus.ACTIVE ? props.theme.success :
    props.status === ZondStatus.INACTIVE ? props.theme.text.secondary :
    props.status === ZondStatus.CONNECTING ? props.theme.warning :
    props.status === ZondStatus.COMPROMISED ? props.theme.danger :
    props.theme.danger
  };
`;

const StatusText = styled.span<{status: ZondStatus}>`
  font-size: 0.8rem;
  color: ${props => 
    props.status === ZondStatus.ACTIVE ? props.theme.success :
    props.status === ZondStatus.INACTIVE ? props.theme.text.secondary :
    props.status === ZondStatus.CONNECTING ? props.theme.warning :
    props.status === ZondStatus.COMPROMISED ? props.theme.danger :
    props.theme.danger
  };
`;

const ZondInfo = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 15px;
`;

const InfoItem = styled.div`
  margin-bottom: 5px;
`;

const InfoLabel = styled.div`
  font-size: 0.8rem;
  color: ${props => props.theme.text.secondary};
  margin-bottom: 2px;
`;

const InfoValue = styled.div`
  font-size: 0.9rem;
  color: ${props => props.theme.text.primary};
  font-weight: 500;
`;

const UsageSection = styled.div`
  margin-bottom: 15px;
`;

const UsageTitle = styled.div`
  font-size: 0.9rem;
  color: ${props => props.theme.text.secondary};
  margin-bottom: 10px;
`;

const UsageBar = styled.div`
  height: 8px;
  background-color: ${props => props.theme.bg.tertiary};
  border-radius: 4px;
  margin-bottom: 5px;
  overflow: hidden;
`;

const UsageFill = styled.div<{percentage: number; color?: string}>`
  height: 100%;
  width: ${props => props.percentage}%;
  background-color: ${props => 
    props.color ? props.color :
    props.percentage > 80 ? props.theme.danger :
    props.percentage > 60 ? props.theme.warning :
    props.theme.success
  };
  border-radius: 4px;
`;

const UsageLabel = styled.div`
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: ${props => props.theme.text.secondary};
`;

const ActionBar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const ZondActions = styled.div`
  display: flex;
  gap: 10px;
`;

const IconButton = styled.button<{variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning'}>`
  padding: 8px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  background-color: ${props => 
    props.variant === 'danger' ? props.theme.danger :
    props.variant === 'success' ? props.theme.success :
    props.variant === 'warning' ? props.theme.warning :
    props.variant === 'secondary' ? props.theme.bg.tertiary :
    props.theme.accent.primary
  };
  color: white;
  
  &:hover {
    opacity: 0.9;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const ActiveTasksBadge = styled.div`
  padding: 3px 8px;
  border-radius: 12px;
  background-color: ${props => props.theme.accent.secondary};
  color: ${props => props.theme.text.primary};
  font-size: 0.8rem;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
`;

const ZondsManagementPage: React.FC = () => {
  // Состояния компонента
  const [zonds, setZonds] = useState<Zond[]>([
    {
      id: 'z1',
      name: 'Moscow-Desktop-01',
      status: ZondStatus.ACTIVE,
      ipAddress: '195.24.65.12',
      location: 'Москва, Россия',
      os: 'Windows 10 Pro',
      version: '1.3.2',
      lastSeen: '2023-10-15 14:30:12',
      cpuUsage: 45,
      ramUsage: 60,
      diskUsage: 78,
      activeProcesses: 24,
      connectedSince: '2023-10-12 09:15:23',
      ping: 42,
      activeOperations: 2
    },
    {
      id: 'z2',
      name: 'SPB-Mobile-03',
      status: ZondStatus.ERROR,
      ipAddress: '91.142.84.71',
      location: 'Санкт-Петербург, Россия',
      os: 'Android 13',
      version: '1.3.0',
      lastSeen: '2023-10-15 10:15:33',
      cpuUsage: 22,
      ramUsage: 45,
      diskUsage: 50,
      activeProcesses: 12,
      ping: 180,
      activeOperations: 0
    },
    {
      id: 'z3',
      name: 'Kazan-Desktop-02',
      status: ZondStatus.ACTIVE,
      ipAddress: '178.45.112.34',
      location: 'Казань, Россия',
      os: 'Ubuntu 22.04 LTS',
      version: '1.3.2',
      lastSeen: '2023-10-15 14:28:45',
      cpuUsage: 32,
      ramUsage: 55,
      diskUsage: 62,
      activeProcesses: 18,
      connectedSince: '2023-10-14 23:45:11',
      ping: 65,
      activeOperations: 1
    },
    {
      id: 'z4',
      name: 'Kiev-Mobile-01',
      status: ZondStatus.INACTIVE,
      ipAddress: '84.56.128.43',
      location: 'Киев, Украина',
      os: 'iOS 16.2',
      version: '1.2.8',
      lastSeen: '2023-10-14 18:22:56',
      cpuUsage: 0,
      ramUsage: 0,
      diskUsage: 36,
      activeProcesses: 0,
      ping: 0,
      activeOperations: 0
    },
    {
      id: 'z5',
      name: 'Minsk-Desktop-01',
      status: ZondStatus.CONNECTING,
      ipAddress: '37.214.56.89',
      location: 'Минск, Беларусь',
      os: 'Windows 11 Home',
      version: '1.3.1',
      lastSeen: '2023-10-15 14:15:22',
      cpuUsage: 12,
      ramUsage: 35,
      diskUsage: 45,
      activeProcesses: 8,
      ping: 124,
      activeOperations: 0
    },
    {
      id: 'z6',
      name: 'Moscow-Server-01',
      status: ZondStatus.COMPROMISED,
      ipAddress: '195.24.67.89',
      location: 'Москва, Россия',
      os: 'CentOS 8',
      version: '1.3.2',
      lastSeen: '2023-10-15 12:45:32',
      cpuUsage: 92,
      ramUsage: 85,
      diskUsage: 54,
      activeProcesses: 42,
      ping: 87,
      activeOperations: 3
    }
  ]);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Получаем статистику по зондам
  const totalZonds = zonds.length;
  const activeZonds = zonds.filter(zond => zond.status === ZondStatus.ACTIVE).length;
  const inactiveZonds = zonds.filter(zond => zond.status === ZondStatus.INACTIVE).length;
  const errorZonds = zonds.filter(zond => [ZondStatus.ERROR, ZondStatus.COMPROMISED].includes(zond.status)).length;
  
  // Форматируем статус зонда на русский
  const getStatusText = (status: ZondStatus): string => {
    switch(status) {
      case ZondStatus.ACTIVE: return 'Активен';
      case ZondStatus.INACTIVE: return 'Не активен';
      case ZondStatus.CONNECTING: return 'Подключение';
      case ZondStatus.ERROR: return 'Ошибка';
      case ZondStatus.COMPROMISED: return 'Скомпрометирован';
      default: return 'Неизвестно';
    }
  };
  
  // Фильтрация зондов
  const filteredZonds = zonds.filter(zond => {
    const matchesSearch = zond.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          zond.ipAddress.includes(searchQuery) ||
                          zond.location.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (statusFilter === 'all') return matchesSearch;
    return matchesSearch && zond.status === statusFilter;
  });
  
  // Обработчики событий
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };
  
  const handleStatusFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
  };
  
  const handleConnect = (id: string) => {
    setZonds(prev => prev.map(zond => 
      zond.id === id ? {...zond, status: ZondStatus.CONNECTING} : zond
    ));
    
    // Имитация успешного подключения через 2 секунды
    setTimeout(() => {
      setZonds(prev => prev.map(zond => 
        zond.id === id ? {
          ...zond, 
          status: ZondStatus.ACTIVE, 
          connectedSince: new Date().toISOString().replace('T', ' ').substring(0, 19)
        } : zond
      ));
    }, 2000);
  };
  
  const handleDisconnect = (id: string) => {
    setZonds(prev => prev.map(zond => 
      zond.id === id ? {...zond, status: ZondStatus.INACTIVE, connectedSince: undefined} : zond
    ));
  };
  
  const handleDelete = (id: string) => {
    if (window.confirm('Вы уверены, что хотите удалить этот зонд?')) {
      setZonds(prev => prev.filter(zond => zond.id !== id));
    }
  };
  
  return (
    <Container>
      <Title>Управление зондами</Title>
      
      <StatsPanel>
        <StatCard>
          <StatValue>{totalZonds}</StatValue>
          <StatLabel>Всего зондов</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{activeZonds}</StatValue>
          <StatLabel>Активных</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{inactiveZonds}</StatValue>
          <StatLabel>Не активных</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{errorZonds}</StatValue>
          <StatLabel>С ошибками</StatLabel>
        </StatCard>
      </StatsPanel>
      
      <ControlPanel>
        <SearchAndFilter>
          <SearchInput 
            type="text" 
            placeholder="Поиск по имени, IP или местоположению" 
            value={searchQuery}
            onChange={handleSearchChange}
          />
          <FilterSelect value={statusFilter} onChange={handleStatusFilterChange}>
            <option value="all">Все статусы</option>
            <option value={ZondStatus.ACTIVE}>Активные</option>
            <option value={ZondStatus.INACTIVE}>Не активные</option>
            <option value={ZondStatus.CONNECTING}>Подключение</option>
            <option value={ZondStatus.ERROR}>Ошибка</option>
            <option value={ZondStatus.COMPROMISED}>Скомпрометированы</option>
          </FilterSelect>
        </SearchAndFilter>
        
        <ActionButtons>
          <Button>Добавить новый зонд</Button>
          <Button variant="warning">Обновить все</Button>
        </ActionButtons>
      </ControlPanel>
      
      <ZondGrid>
        {filteredZonds.map(zond => (
          <ZondCard key={zond.id} status={zond.status}>
            <ZondHeader>
              <ZondName>{zond.name}</ZondName>
              <ZondStatus status={zond.status}>
                <StatusDot status={zond.status} />
                <StatusText status={zond.status}>{getStatusText(zond.status)}</StatusText>
              </ZondStatus>
            </ZondHeader>
            
            <ZondInfo>
              <InfoItem>
                <InfoLabel>IP адрес</InfoLabel>
                <InfoValue>{zond.ipAddress}</InfoValue>
              </InfoItem>
              <InfoItem>
                <InfoLabel>Версия</InfoLabel>
                <InfoValue>{zond.version}</InfoValue>
              </InfoItem>
              <InfoItem>
                <InfoLabel>Расположение</InfoLabel>
                <InfoValue>{zond.location}</InfoValue>
              </InfoItem>
              <InfoItem>
                <InfoLabel>Операционная система</InfoLabel>
                <InfoValue>{zond.os}</InfoValue>
              </InfoItem>
              <InfoItem>
                <InfoLabel>Последняя активность</InfoLabel>
                <InfoValue>{zond.lastSeen}</InfoValue>
              </InfoItem>
              <InfoItem>
                <InfoLabel>Пинг</InfoLabel>
                <InfoValue>{zond.ping > 0 ? `${zond.ping} мс` : 'N/A'}</InfoValue>
              </InfoItem>
              {zond.connectedSince && (
                <InfoItem>
                  <InfoLabel>Подключен с</InfoLabel>
                  <InfoValue>{zond.connectedSince}</InfoValue>
                </InfoItem>
              )}
              <InfoItem>
                <InfoLabel>Активные процессы</InfoLabel>
                <InfoValue>{zond.activeProcesses}</InfoValue>
              </InfoItem>
            </ZondInfo>
            
            <UsageSection>
              <UsageTitle>Использование ресурсов</UsageTitle>
              
              <InfoLabel>CPU</InfoLabel>
              <UsageBar>
                <UsageFill percentage={zond.cpuUsage} />
              </UsageBar>
              <UsageLabel>
                <span>0%</span>
                <span>{zond.cpuUsage}%</span>
                <span>100%</span>
              </UsageLabel>
              
              <InfoLabel>Память</InfoLabel>
              <UsageBar>
                <UsageFill percentage={zond.ramUsage} />
              </UsageBar>
              <UsageLabel>
                <span>0%</span>
                <span>{zond.ramUsage}%</span>
                <span>100%</span>
              </UsageLabel>
              
              <InfoLabel>Диск</InfoLabel>
              <UsageBar>
                <UsageFill percentage={zond.diskUsage} />
              </UsageBar>
              <UsageLabel>
                <span>0%</span>
                <span>{zond.diskUsage}%</span>
                <span>100%</span>
              </UsageLabel>
            </UsageSection>
            
            <ActionBar>
              {zond.activeOperations > 0 && (
                <ActiveTasksBadge>
                  {zond.activeOperations} активных задач
                </ActiveTasksBadge>
              )}
              <ZondActions>
                {zond.status !== ZondStatus.ACTIVE && zond.status !== ZondStatus.CONNECTING && (
                  <Button 
                    variant="success" 
                    onClick={() => handleConnect(zond.id)}
                    disabled={zond.status === ZondStatus.CONNECTING}
                  >
                    Подключить
                  </Button>
                )}
                
                {zond.status === ZondStatus.ACTIVE && (
                  <Button 
                    variant="warning" 
                    onClick={() => handleDisconnect(zond.id)}
                  >
                    Отключить
                  </Button>
                )}
                
                {zond.status === ZondStatus.ACTIVE && (
                  <Button variant="primary">
                    Команды
                  </Button>
                )}
                
                <Button 
                  variant="danger"
                  onClick={() => handleDelete(zond.id)}
                >
                  Удалить
                </Button>
              </ZondActions>
            </ActionBar>
          </ZondCard>
        ))}
      </ZondGrid>
    </Container>
  );
};

export default ZondsManagementPage; 