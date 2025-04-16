import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FiAlertCircle, FiBarChart2, FiSearch, FiRefreshCw, FiFilter, FiDownload, FiChevronDown, FiChevronUp } from 'react-icons/fi';

// Типы данных
interface Alert {
  id: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description: string;
  source: string;
  sourceIp: string;
  destinationIp: string;
  protocol: string;
  status: 'new' | 'investigating' | 'resolved' | 'false_positive';
  mitreTactic?: string;
  mitreId?: string;
}

interface NetworkActivity {
  id: string;
  timestamp: string;
  sourceIp: string;
  destinationIp: string;
  protocol: string;
  port: number;
  bytes: number;
  packets: number;
  isBlocked: boolean;
  isAnomaly: boolean;
}

// Styled Components
const PageContainer = styled.div`
  padding: 24px;
  height: 100%;
  overflow-y: auto;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const Title = styled.h1`
  font-size: 24px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 10px;
`;

const Button = styled.button<{ primary?: boolean }>`
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 15px;
  border-radius: 5px;
  border: none;
  background: ${props => props.primary ? '#3182ce' : '#2D3748'};
  color: white;
  cursor: pointer;
  font-weight: 500;
  
  &:hover {
    opacity: 0.9;
  }
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const Panel = styled.div`
  background: #1A202C;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const PanelHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #2D3748;
  border-bottom: 1px solid #4A5568;
`;

const PanelTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const PanelContent = styled.div`
  padding: 20px;
`;

const SearchBar = styled.div`
  display: flex;
  margin-bottom: 20px;
  gap: 10px;
`;

const SearchInput = styled.input`
  flex: 1;
  background: #2D3748;
  border: 1px solid #4A5568;
  border-radius: 5px;
  padding: 8px 15px;
  color: white;
  font-size: 14px;
  
  &:focus {
    outline: none;
    border-color: #3182ce;
  }
  
  &::placeholder {
    color: #A0AEC0;
  }
`;

const FilterButton = styled.button`
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 15px;
  border-radius: 5px;
  border: 1px solid #4A5568;
  background: #2D3748;
  color: white;
  cursor: pointer;
  
  &:hover {
    background: #3C4A5F;
  }
`;

const AlertsContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const AlertItem = styled.div<{ severity: string, expanded: boolean }>`
  background: #2D3748;
  border-radius: 6px;
  border-left: 4px solid ${props => {
    switch(props.severity) {
      case 'critical': return '#E53E3E';
      case 'high': return '#DD6B20';
      case 'medium': return '#D69E2E';
      case 'low': return '#38A169';
      default: return '#3182CE';
    }
  }};
  overflow: hidden;
`;

const AlertHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  cursor: pointer;
`;

const AlertTitle = styled.div`
  font-weight: 600;
  flex: 1;
`;

const AlertMeta = styled.div`
  display: flex;
  gap: 15px;
  align-items: center;
`;

const AlertTimestamp = styled.div`
  font-size: 12px;
  color: #A0AEC0;
`;

const Badge = styled.span<{ type?: string }>`
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  background: ${props => {
    switch(props.type) {
      case 'critical': return '#E53E3E';
      case 'high': return '#DD6B20';
      case 'medium': return '#D69E2E';
      case 'low': return '#38A169';
      case 'new': return '#3182CE';
      case 'investigating': return '#D69E2E';
      case 'resolved': return '#38A169';
      case 'false_positive': return '#718096';
      default: return '#4A5568';
    }
  }};
  color: white;
`;

const AlertDetails = styled.div<{ expanded: boolean }>`
  padding: ${props => props.expanded ? '0 15px 15px 15px' : '0'};
  max-height: ${props => props.expanded ? '500px' : '0'};
  opacity: ${props => props.expanded ? '1' : '0'};
  transition: all 0.3s ease;
  overflow: hidden;
`;

const DetailGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-bottom: 15px;
`;

const DetailItem = styled.div`
  display: flex;
  flex-direction: column;
  gap: 3px;
`;

const DetailLabel = styled.div`
  font-size: 12px;
  color: #A0AEC0;
`;

const DetailValue = styled.div`
  font-size: 14px;
`;

const Description = styled.div`
  background: #1A202C;
  padding: 12px;
  border-radius: 5px;
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 15px;
`;

const MitreTag = styled.div`
  display: inline-flex;
  align-items: center;
  background: #4A5568;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  gap: 5px;
  margin-right: 5px;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-bottom: 20px;
`;

const StatCard = styled.div`
  background: #2D3748;
  border-radius: 8px;
  padding: 15px;
`;

const StatLabel = styled.div`
  font-size: 13px;
  color: #A0AEC0;
  margin-bottom: 5px;
`;

const StatValue = styled.div`
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 5px;
`;

const StatPercentage = styled.div<{ positive: boolean }>`
  font-size: 12px;
  color: ${props => props.positive ? '#38A169' : '#E53E3E'};
  display: flex;
  align-items: center;
  gap: 3px;
`;

const ActivityTable = styled.table`
  width: 100%;
  border-collapse: collapse;
`;

const TableHead = styled.thead`
  background: #2D3748;
  border-bottom: 1px solid #4A5568;
  
  th {
    padding: 12px 15px;
    text-align: left;
    font-weight: 600;
    font-size: 13px;
  }
`;

const TableBody = styled.tbody`
  tr {
    border-bottom: 1px solid #2D3748;
    
    &:hover {
      background: #2D3748;
    }
  }
  
  td {
    padding: 12px 15px;
    font-size: 13px;
  }
`;

const Pagination = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
`;

const PaginationText = styled.div`
  font-size: 13px;
  color: #A0AEC0;
`;

const PaginationButtons = styled.div`
  display: flex;
  gap: 5px;
`;

const PaginationButton = styled.button<{ active?: boolean }>`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: ${props => props.active ? '#3182CE' : '#2D3748'};
  border: none;
  border-radius: 4px;
  color: white;
  cursor: pointer;
  
  &:hover {
    background: ${props => props.active ? '#3182CE' : '#4A5568'};
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

// Компонент страницы
const IntrusionDetectionPage: React.FC = () => {
  // Состояния
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [networkActivity, setNetworkActivity] = useState<NetworkActivity[]>([]);
  const [expandedAlertId, setExpandedAlertId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(5);
  
  // Статистика
  const [stats, setStats] = useState({
    totalAlerts: 0,
    criticalAlerts: 0,
    resolvedAlerts: 0,
    falsePositives: 0,
    detectionRate: 0,
    previousWeekChange: 12, // процентное изменение по сравнению с прошлой неделей
  });
  
  // Эффект для загрузки данных
  useEffect(() => {
    // Имитация загрузки данных с сервера
    loadMockData();
  }, []);
  
  const loadMockData = () => {
    // Мок-данные для демонстрации
    const mockAlerts: Alert[] = [
      {
        id: "a1",
        timestamp: "2023-05-15T14:32:00",
        severity: "critical",
        title: "Обнаружена атака грубой силы на учетные данные",
        description: "Множественные неудачные попытки аутентификации с одного IP-адреса. Возможна атака брутфорса на учетные записи администраторов.",
        source: "Firewall",
        sourceIp: "182.68.45.12",
        destinationIp: "10.0.0.5",
        protocol: "TCP",
        status: "new",
        mitreTactic: "Initial Access",
        mitreId: "T1110"
      },
      {
        id: "a2",
        timestamp: "2023-05-15T12:17:00",
        severity: "high",
        title: "Обнаружен подозрительный процесс PowerShell",
        description: "PowerShell выполняет команды с закодированными параметрами. Возможно использование вредоносных скриптов для получения доступа к системе.",
        source: "EDR",
        sourceIp: "10.0.0.45",
        destinationIp: "23.64.12.5",
        protocol: "TCP",
        status: "investigating",
        mitreTactic: "Execution",
        mitreId: "T1059.001"
      },
      {
        id: "a3",
        timestamp: "2023-05-14T23:45:00",
        severity: "medium",
        title: "Необычный трафик DNS",
        description: "Обнаружен аномально большой объем DNS-запросов к необычным доменам. Возможно, используется DNS-туннелирование для экфильтрации данных.",
        source: "Network Monitor",
        sourceIp: "10.0.0.156",
        destinationIp: "8.8.8.8",
        protocol: "UDP",
        status: "investigating",
        mitreTactic: "Exfiltration",
        mitreId: "T1048.003"
      },
      {
        id: "a4",
        timestamp: "2023-05-14T18:12:00",
        severity: "low",
        title: "Неавторизованное подключение к SMB",
        description: "Обнаружено неавторизованное подключение к SMB-ресурсам. Возможно, происходит сканирование сети или попытка доступа к общим ресурсам.",
        source: "IDS",
        sourceIp: "10.0.0.89",
        destinationIp: "10.0.0.5",
        protocol: "TCP",
        status: "resolved",
        mitreTactic: "Lateral Movement",
        mitreId: "T1021.002"
      },
      {
        id: "a5",
        timestamp: "2023-05-14T09:23:00",
        severity: "high",
        title: "Обнаружено выполнение вредоносного скрипта",
        description: "На рабочей станции выполняется подозрительный скрипт, который пытается модифицировать системные файлы и отключить защитные механизмы.",
        source: "Antivirus",
        sourceIp: "10.0.0.77",
        destinationIp: "185.45.13.98",
        protocol: "TCP",
        status: "new",
        mitreTactic: "Defense Evasion",
        mitreId: "T1562.001"
      }
    ];
    
    const mockNetworkActivity: NetworkActivity[] = [
      {
        id: "n1",
        timestamp: "2023-05-15T14:36:22",
        sourceIp: "182.68.45.12",
        destinationIp: "10.0.0.5",
        protocol: "TCP",
        port: 22,
        bytes: 4562,
        packets: 34,
        isBlocked: true,
        isAnomaly: true
      },
      {
        id: "n2",
        timestamp: "2023-05-15T14:35:18",
        sourceIp: "182.68.45.12",
        destinationIp: "10.0.0.5",
        protocol: "TCP",
        port: 22,
        bytes: 3245,
        packets: 28,
        isBlocked: true,
        isAnomaly: true
      },
      {
        id: "n3",
        timestamp: "2023-05-15T14:12:05",
        sourceIp: "10.0.0.45",
        destinationIp: "23.64.12.5",
        protocol: "HTTP",
        port: 80,
        bytes: 89756,
        packets: 127,
        isBlocked: false,
        isAnomaly: true
      },
      {
        id: "n4",
        timestamp: "2023-05-15T13:58:41",
        sourceIp: "10.0.0.156",
        destinationIp: "8.8.8.8",
        protocol: "UDP",
        port: 53,
        bytes: 15678,
        packets: 234,
        isBlocked: false,
        isAnomaly: true
      },
      {
        id: "n5",
        timestamp: "2023-05-15T13:45:12",
        sourceIp: "10.0.0.22",
        destinationIp: "172.16.0.5",
        protocol: "TCP",
        port: 443,
        bytes: 245678,
        packets: 345,
        isBlocked: false,
        isAnomaly: false
      }
    ];
    
    setAlerts(mockAlerts);
    setNetworkActivity(mockNetworkActivity);
    
    // Обновляем статистику
    setStats({
      totalAlerts: mockAlerts.length,
      criticalAlerts: mockAlerts.filter(alert => alert.severity === 'critical').length,
      resolvedAlerts: mockAlerts.filter(alert => alert.status === 'resolved').length,
      falsePositives: mockAlerts.filter(alert => alert.status === 'false_positive').length,
      detectionRate: 85,
      previousWeekChange: 12
    });
  };
  
  // Обработчики
  const toggleAlertExpand = (id: string) => {
    if (expandedAlertId === id) {
      setExpandedAlertId(null);
    } else {
      setExpandedAlertId(id);
    }
  };
  
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  };
  
  // Фильтрация оповещений
  const filteredAlerts = alerts.filter(alert => {
    const matchesSearch = 
      alert.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alert.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      alert.sourceIp.includes(searchQuery) ||
      alert.destinationIp.includes(searchQuery);
      
    const matchesSeverity = severityFilter === 'all' || alert.severity === severityFilter;
    const matchesStatus = statusFilter === 'all' || alert.status === statusFilter;
    
    return matchesSearch && matchesSeverity && matchesStatus;
  });
  
  // Пагинация
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentAlerts = filteredAlerts.slice(indexOfFirstItem, indexOfLastItem);
  const totalPages = Math.ceil(filteredAlerts.length / itemsPerPage);
  
  const paginate = (pageNumber: number) => setCurrentPage(pageNumber);
  
  return (
    <PageContainer>
      <Header>
        <Title><FiAlertCircle size={22} /> Система обнаружения вторжений</Title>
        <ActionButtons>
          <Button><FiRefreshCw /> Обновить</Button>
          <Button><FiFilter /> Фильтры</Button>
          <Button primary><FiDownload /> Экспорт</Button>
        </ActionButtons>
      </Header>
      
      <StatsGrid>
        <StatCard>
          <StatLabel>Всего оповещений</StatLabel>
          <StatValue>{stats.totalAlerts}</StatValue>
          <StatPercentage positive={stats.previousWeekChange > 0}>
            {stats.previousWeekChange > 0 ? <FiChevronUp /> : <FiChevronDown />}
            {Math.abs(stats.previousWeekChange)}% с прошлой недели
          </StatPercentage>
        </StatCard>
        
        <StatCard>
          <StatLabel>Критические оповещения</StatLabel>
          <StatValue>{stats.criticalAlerts}</StatValue>
          <StatPercentage positive={false}>
            <FiChevronUp />
            25% с прошлой недели
          </StatPercentage>
        </StatCard>
        
        <StatCard>
          <StatLabel>Показатель обнаружения</StatLabel>
          <StatValue>{stats.detectionRate}%</StatValue>
          <StatPercentage positive={true}>
            <FiChevronUp />
            8% с прошлой недели
          </StatPercentage>
        </StatCard>
        
        <StatCard>
          <StatLabel>Ложные срабатывания</StatLabel>
          <StatValue>{stats.falsePositives}</StatValue>
          <StatPercentage positive={true}>
            <FiChevronDown />
            15% с прошлой недели
          </StatPercentage>
        </StatCard>
      </StatsGrid>
      
      <Grid>
        <Panel>
          <PanelHeader>
            <PanelTitle><FiAlertCircle size={18} /> Оповещения безопасности</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <SearchBar>
              <SearchInput 
                placeholder="Поиск по оповещениям, IP-адресам..."
                value={searchQuery}
                onChange={handleSearchChange}
              />
              <FilterButton>
                <FiFilter size={16} />
                Фильтры
              </FilterButton>
            </SearchBar>
            
            <AlertsContainer>
              {currentAlerts.map(alert => (
                <AlertItem key={alert.id} severity={alert.severity} expanded={expandedAlertId === alert.id}>
                  <AlertHeader onClick={() => toggleAlertExpand(alert.id)}>
                    <AlertTitle>{alert.title}</AlertTitle>
                    <AlertMeta>
                      <Badge type={alert.severity}>{alert.severity}</Badge>
                      <Badge type={alert.status}>{alert.status}</Badge>
                      <AlertTimestamp>{new Date(alert.timestamp).toLocaleString('ru-RU')}</AlertTimestamp>
                      {expandedAlertId === alert.id ? <FiChevronUp /> : <FiChevronDown />}
                    </AlertMeta>
                  </AlertHeader>
                  
                  <AlertDetails expanded={expandedAlertId === alert.id}>
                    <Description>{alert.description}</Description>
                    
                    <DetailGrid>
                      <DetailItem>
                        <DetailLabel>Источник</DetailLabel>
                        <DetailValue>{alert.source}</DetailValue>
                      </DetailItem>
                      <DetailItem>
                        <DetailLabel>Протокол</DetailLabel>
                        <DetailValue>{alert.protocol}</DetailValue>
                      </DetailItem>
                      <DetailItem>
                        <DetailLabel>IP источника</DetailLabel>
                        <DetailValue>{alert.sourceIp}</DetailValue>
                      </DetailItem>
                      <DetailItem>
                        <DetailLabel>IP назначения</DetailLabel>
                        <DetailValue>{alert.destinationIp}</DetailValue>
                      </DetailItem>
                    </DetailGrid>
                    
                    {alert.mitreTactic && (
                      <div>
                        <DetailLabel>MITRE ATT&CK</DetailLabel>
                        <div style={{ marginTop: '5px' }}>
                          <MitreTag>{alert.mitreTactic} ({alert.mitreId})</MitreTag>
                        </div>
                      </div>
                    )}
                  </AlertDetails>
                </AlertItem>
              ))}
            </AlertsContainer>
            
            <Pagination>
              <PaginationText>
                Показано {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, filteredAlerts.length)} из {filteredAlerts.length}
              </PaginationText>
              <PaginationButtons>
                <PaginationButton
                  onClick={() => paginate(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  &lt;
                </PaginationButton>
                
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(number => (
                  <PaginationButton
                    key={number}
                    active={currentPage === number}
                    onClick={() => paginate(number)}
                  >
                    {number}
                  </PaginationButton>
                ))}
                
                <PaginationButton
                  onClick={() => paginate(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  &gt;
                </PaginationButton>
              </PaginationButtons>
            </Pagination>
          </PanelContent>
        </Panel>
        
        <Panel>
          <PanelHeader>
            <PanelTitle><FiBarChart2 size={18} /> Сетевая активность</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <ActivityTable>
              <TableHead>
                <tr>
                  <th>Время</th>
                  <th>Источник</th>
                  <th>Назначение</th>
                  <th>Порт</th>
                  <th>Статус</th>
                </tr>
              </TableHead>
              <TableBody>
                {networkActivity.map(activity => (
                  <tr key={activity.id}>
                    <td>{new Date(activity.timestamp).toLocaleTimeString('ru-RU')}</td>
                    <td>{activity.sourceIp}</td>
                    <td>{activity.destinationIp}</td>
                    <td>{activity.protocol} / {activity.port}</td>
                    <td>
                      {activity.isBlocked ? (
                        <Badge type="high">Заблокировано</Badge>
                      ) : activity.isAnomaly ? (
                        <Badge type="medium">Аномалия</Badge>
                      ) : (
                        <Badge type="low">Нормально</Badge>
                      )}
                    </td>
                  </tr>
                ))}
              </TableBody>
            </ActivityTable>
          </PanelContent>
        </Panel>
      </Grid>
    </PageContainer>
  );
};

export default IntrusionDetectionPage; 