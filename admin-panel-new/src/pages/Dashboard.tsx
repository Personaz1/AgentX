import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FiActivity, FiServer, FiAlertTriangle, FiCpu, FiRefreshCw } from 'react-icons/fi';
import { ZondConnectionStatus } from '../types';

const DashboardContainer = styled.div`
  padding: 24px;
  width: 100%;
`;

const Title = styled.h1`
  font-size: 24px;
  margin-bottom: 24px;
  font-weight: 600;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
`;

const StatCard = styled.div`
  background: #1a1c23;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
`;

const StatIcon = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  font-size: 24px;
`;

const StatInfo = styled.div`
  flex: 1;
`;

const StatValue = styled.div`
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 4px;
`;

const StatLabel = styled.div`
  font-size: 14px;
  color: #8a94a6;
`;

const ZondsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
  margin-bottom: 32px;
`;

const ZondCard = styled.div`
  background: #1a1c23;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const ZondHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
`;

const ZondName = styled.div`
  font-size: 18px;
  font-weight: 600;
`;

const ZondStatus = styled.div<{ status: ZondConnectionStatus }>`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: ${props => {
    switch (props.status) {
      case ZondConnectionStatus.ACTIVE:
        return '#10B981';
      case ZondConnectionStatus.INACTIVE:
        return '#6B7280';
      case ZondConnectionStatus.CONNECTING:
        return '#F59E0B';
      case ZondConnectionStatus.ERROR:
        return '#EF4444';
      case ZondConnectionStatus.COMPROMISED:
        return '#7C3AED';
      default:
        return '#6B7280';
    }
  }};
  color: white;
`;

const ZondInfo = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
`;

const ZondInfoItem = styled.div`
  margin-bottom: 8px;
`;

const ZondInfoLabel = styled.div`
  font-size: 12px;
  color: #8a94a6;
  margin-bottom: 4px;
`;

const ZondInfoValue = styled.div`
  font-size: 14px;
`;

const LoadingIndicator = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  font-size: 16px;
  color: #8a94a6;
  
  svg {
    margin-right: 8px;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
`;

interface DashboardStats {
  activeZonds: number;
  totalZonds: number;
  alertsCount: number;
  systemLoad: number;
}

interface Zond {
  id: string;
  name: string;
  status: ZondConnectionStatus;
  ipAddress: string;
  os: string;
  version: string;
  lastSeen: string;
  cpuUsage: number;
  ramUsage: number;
  location: string;
}

const Dashboard: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats>({
    activeZonds: 0,
    totalZonds: 0,
    alertsCount: 0,
    systemLoad: 0
  });
  const [zonds, setZonds] = useState<Zond[]>([]);

  useEffect(() => {
    // Имитация загрузки данных
    const fetchData = async () => {
      setLoading(true);
      try {
        // В реальном приложении здесь будет запрос к API
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Моковые данные
        setStats({
          activeZonds: 12,
          totalZonds: 18,
          alertsCount: 3,
          systemLoad: 42
        });
        
        setZonds([
          {
            id: '1',
            name: 'Zond-Moscow-01',
            status: ZondConnectionStatus.ACTIVE,
            ipAddress: '192.168.1.101',
            os: 'Windows 10',
            version: '1.2.5',
            lastSeen: '2023-09-15 13:45:22',
            cpuUsage: 23,
            ramUsage: 41,
            location: 'Moscow, RU'
          },
          {
            id: '2',
            name: 'Zond-SPB-03',
            status: ZondConnectionStatus.ACTIVE,
            ipAddress: '192.168.2.35',
            os: 'Linux Ubuntu 20.04',
            version: '1.2.5',
            lastSeen: '2023-09-15 13:43:11',
            cpuUsage: 12,
            ramUsage: 35,
            location: 'St. Petersburg, RU'
          },
          {
            id: '3',
            name: 'Zond-Kiev-02',
            status: ZondConnectionStatus.ERROR,
            ipAddress: '192.168.3.204',
            os: 'macOS 11.6',
            version: '1.2.4',
            lastSeen: '2023-09-15 10:22:53',
            cpuUsage: 0,
            ramUsage: 0,
            location: 'Kiev, UA'
          },
          {
            id: '4',
            name: 'Zond-Minsk-01',
            status: ZondConnectionStatus.INACTIVE,
            ipAddress: '192.168.4.115',
            os: 'Windows Server 2019',
            version: '1.2.3',
            lastSeen: '2023-09-14 18:11:45',
            cpuUsage: 0,
            ramUsage: 0,
            location: 'Minsk, BY'
          },
          {
            id: '5',
            name: 'Zond-Kazan-01',
            status: ZondConnectionStatus.CONNECTING,
            ipAddress: '192.168.5.67',
            os: 'Linux CentOS 8',
            version: '1.2.5',
            lastSeen: '2023-09-15 13:40:01',
            cpuUsage: 8,
            ramUsage: 22,
            location: 'Kazan, RU'
          },
          {
            id: '6',
            name: 'Zond-Secret-C1',
            status: ZondConnectionStatus.COMPROMISED,
            ipAddress: '10.11.12.13',
            os: 'Unknown',
            version: '1.2.5 (Modified)',
            lastSeen: '2023-09-15 13:42:16',
            cpuUsage: 76,
            ramUsage: 89,
            location: 'Unknown'
          }
        ]);
      } catch (error) {
        console.error('Ошибка при загрузке данных дашборда:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  if (loading) {
    return (
      <LoadingIndicator>
        <FiRefreshCw size={20} />
        Загрузка данных дашборда...
      </LoadingIndicator>
    );
  }
  
  return (
    <DashboardContainer>
      <Title>Панель управления</Title>
      
      <StatsGrid>
        <StatCard>
          <StatIcon style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10B981' }}>
            <FiServer />
          </StatIcon>
          <StatInfo>
            <StatValue>{stats.activeZonds}</StatValue>
            <StatLabel>Активных зондов</StatLabel>
          </StatInfo>
        </StatCard>
        
        <StatCard>
          <StatIcon style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3B82F6' }}>
            <FiServer />
          </StatIcon>
          <StatInfo>
            <StatValue>{stats.totalZonds}</StatValue>
            <StatLabel>Всего зондов</StatLabel>
          </StatInfo>
        </StatCard>
        
        <StatCard>
          <StatIcon style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#EF4444' }}>
            <FiAlertTriangle />
          </StatIcon>
          <StatInfo>
            <StatValue>{stats.alertsCount}</StatValue>
            <StatLabel>Активных алертов</StatLabel>
          </StatInfo>
        </StatCard>
        
        <StatCard>
          <StatIcon style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#F59E0B' }}>
            <FiCpu />
          </StatIcon>
          <StatInfo>
            <StatValue>{stats.systemLoad}%</StatValue>
            <StatLabel>Загрузка системы</StatLabel>
          </StatInfo>
        </StatCard>
      </StatsGrid>
      
      <Title>Зонды</Title>
      
      <ZondsGrid>
        {zonds.map(zond => (
          <ZondCard key={zond.id}>
            <ZondHeader>
              <ZondName>{zond.name}</ZondName>
              <ZondStatus status={zond.status}>
                {zond.status === ZondConnectionStatus.ACTIVE && 'Активен'}
                {zond.status === ZondConnectionStatus.INACTIVE && 'Неактивен'}
                {zond.status === ZondConnectionStatus.CONNECTING && 'Подключение'}
                {zond.status === ZondConnectionStatus.ERROR && 'Ошибка'}
                {zond.status === ZondConnectionStatus.COMPROMISED && 'Скомпрометирован'}
              </ZondStatus>
            </ZondHeader>
            
            <ZondInfo>
              <ZondInfoItem>
                <ZondInfoLabel>IP-адрес</ZondInfoLabel>
                <ZondInfoValue>{zond.ipAddress}</ZondInfoValue>
              </ZondInfoItem>
              
              <ZondInfoItem>
                <ZondInfoLabel>Расположение</ZondInfoLabel>
                <ZondInfoValue>{zond.location}</ZondInfoValue>
              </ZondInfoItem>
              
              <ZondInfoItem>
                <ZondInfoLabel>ОС</ZondInfoLabel>
                <ZondInfoValue>{zond.os}</ZondInfoValue>
              </ZondInfoItem>
              
              <ZondInfoItem>
                <ZondInfoLabel>Версия</ZondInfoLabel>
                <ZondInfoValue>{zond.version}</ZondInfoValue>
              </ZondInfoItem>
              
              <ZondInfoItem>
                <ZondInfoLabel>Последняя активность</ZondInfoLabel>
                <ZondInfoValue>{zond.lastSeen}</ZondInfoValue>
              </ZondInfoItem>
              
              <ZondInfoItem>
                <ZondInfoLabel>Загрузка CPU/RAM</ZondInfoLabel>
                <ZondInfoValue>
                  {zond.status === ZondConnectionStatus.ACTIVE || 
                   zond.status === ZondConnectionStatus.CONNECTING || 
                   zond.status === ZondConnectionStatus.COMPROMISED
                    ? `${zond.cpuUsage}% / ${zond.ramUsage}%`
                    : 'N/A'}
                </ZondInfoValue>
              </ZondInfoItem>
            </ZondInfo>
          </ZondCard>
        ))}
      </ZondsGrid>
    </DashboardContainer>
  );
};

export default Dashboard; 