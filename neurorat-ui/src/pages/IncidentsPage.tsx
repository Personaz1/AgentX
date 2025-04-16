import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { 
  Incident, 
  IncidentStatus, 
  IncidentSeverity, 
  IncidentType 
} from '../types';

// Styled Components
const Container = styled.div`
  padding: 24px;
  height: 100%;
  overflow: auto;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 24px;
  font-weight: bold;
  color: ${props => props.theme.colors.text.primary};
`;

const StatsContainer = styled.div`
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
`;

const StatCard = styled.div`
  background: ${props => props.theme.colors.background.card};
  border-radius: 8px;
  padding: 16px;
  flex: 1;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const StatValue = styled.div`
  font-size: 24px;
  font-weight: bold;
  color: ${props => props.theme.colors.text.primary};
`;

const StatLabel = styled.div`
  font-size: 14px;
  color: ${props => props.theme.colors.text.secondary};
  margin-top: 4px;
`;

const FiltersContainer = styled.div`
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
`;

const SearchInput = styled.input`
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.colors.border.main};
  background: ${props => props.theme.colors.background.input};
  color: ${props => props.theme.colors.text.primary};
  flex: 1;
  min-width: 250px;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary.main};
  }
`;

const Select = styled.select`
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.colors.border.main};
  background: ${props => props.theme.colors.background.input};
  color: ${props => props.theme.colors.text.primary};

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary.main};
  }
`;

const Button = styled.button`
  padding: 8px 16px;
  border-radius: 4px;
  background: ${props => props.theme.colors.primary.main};
  color: white;
  border: none;
  cursor: pointer;
  font-weight: bold;

  &:hover {
    background: ${props => props.theme.colors.primary.dark};
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background: ${props => props.theme.colors.background.card};
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const TableHead = styled.thead`
  background: ${props => props.theme.colors.background.paper};
  border-bottom: 1px solid ${props => props.theme.colors.border.main};
`;

const TableRow = styled.tr`
  cursor: pointer;
  
  &:hover {
    background: ${props => props.theme.colors.background.hover};
  }

  &:not(:last-child) {
    border-bottom: 1px solid ${props => props.theme.colors.border.light};
  }
`;

const TableHeaderCell = styled.th`
  text-align: left;
  padding: 16px;
  font-weight: bold;
  color: ${props => props.theme.colors.text.primary};
`;

const TableCell = styled.td`
  padding: 16px;
  color: ${props => props.theme.colors.text.primary};
`;

const SeverityBadge = styled.span<{ severity: IncidentSeverity }>`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  background: ${props => {
    switch (props.severity) {
      case IncidentSeverity.LOW:
        return '#E8F5E9';
      case IncidentSeverity.MEDIUM:
        return '#FFF8E1';
      case IncidentSeverity.HIGH:
        return '#FFEBEE';
      case IncidentSeverity.CRITICAL:
        return '#B71C1C';
      default:
        return '#E0E0E0';
    }
  }};
  color: ${props => {
    switch (props.severity) {
      case IncidentSeverity.LOW:
        return '#2E7D32';
      case IncidentSeverity.MEDIUM:
        return '#F57F17';
      case IncidentSeverity.HIGH:
        return '#C62828';
      case IncidentSeverity.CRITICAL:
        return '#FFFFFF';
      default:
        return '#616161';
    }
  }};
`;

const StatusBadge = styled.span<{ status: IncidentStatus }>`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
  background: ${props => {
    switch (props.status) {
      case IncidentStatus.NEW:
        return '#E3F2FD';
      case IncidentStatus.INVESTIGATING:
        return '#FFF3E0';
      case IncidentStatus.MITIGATING:
        return '#E1F5FE';
      case IncidentStatus.RESOLVED:
        return '#E8F5E9';
      case IncidentStatus.CLOSED:
        return '#EEEEEE';
      default:
        return '#E0E0E0';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case IncidentStatus.NEW:
        return '#1565C0';
      case IncidentStatus.INVESTIGATING:
        return '#EF6C00';
      case IncidentStatus.MITIGATING:
        return '#0288D1';
      case IncidentStatus.RESOLVED:
        return '#2E7D32';
      case IncidentStatus.CLOSED:
        return '#616161';
      default:
        return '#616161';
    }
  }};
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  color: ${props => props.theme.colors.text.secondary};
  text-align: center;
`;

const EmptyStateIcon = styled.div`
  font-size: 48px;
  margin-bottom: 16px;
`;

const Pagination = styled.div`
  display: flex;
  justify-content: center;
  margin-top: 24px;
  gap: 8px;
`;

const PageButton = styled.button<{ active?: boolean }>`
  width: 36px;
  height: 36px;
  border-radius: 4px;
  border: 1px solid ${props => props.active 
    ? props.theme.colors.primary.main 
    : props.theme.colors.border.main};
  background: ${props => props.active 
    ? props.theme.colors.primary.main 
    : props.theme.colors.background.input};
  color: ${props => props.active 
    ? 'white' 
    : props.theme.colors.text.primary};
  cursor: pointer;
  
  &:hover {
    background: ${props => props.active 
      ? props.theme.colors.primary.dark 
      : props.theme.colors.background.hover};
  }
`;

// Моковые данные для инцидентов
const mockIncidents: Incident[] = [
  {
    id: '1',
    title: 'Атака методом перебора на веб-сервер',
    description: 'Обнаружено большое количество неудачных попыток аутентификации с различных IP-адресов',
    status: IncidentStatus.INVESTIGATING,
    severity: IncidentSeverity.MEDIUM,
    type: IncidentType.UNAUTHORIZED_ACCESS,
    affectedSystems: ['Веб-сервер', 'Система аутентификации'],
    affectedZonds: ['zond-001', 'zond-005'],
    detectionSource: 'IDS',
    detectedAt: '2023-11-15T14:30:00Z',
    reportedBy: 'system',
    tags: ['brute-force', 'authentication', 'web'],
    comments: [
      {
        id: '1',
        author: 'Иван Петров',
        text: 'Начато расследование. Обнаружено более 3000 попыток входа за 2 часа.',
        createdAt: '2023-11-15T14:45:00Z'
      }
    ],
    actions: [
      {
        id: '1',
        type: 'status_change',
        description: 'Статус изменён на "Расследуется"',
        performedBy: 'Иван Петров',
        performedAt: '2023-11-15T14:45:00Z'
      }
    ]
  },
  {
    id: '2',
    title: 'Подозрительная активность вредоносного ПО на рабочей станции',
    description: 'Обнаружены признаки активности трояна на рабочей станции маркетингового отдела',
    status: IncidentStatus.MITIGATING,
    severity: IncidentSeverity.HIGH,
    type: IncidentType.MALWARE,
    affectedSystems: ['Рабочая станция RK-234', 'Файловый сервер'],
    affectedZonds: ['zond-008'],
    detectionSource: 'EDR',
    detectedAt: '2023-11-14T09:15:00Z',
    reportedBy: 'system',
    assignedTo: 'Алексей Смирнов',
    tags: ['trojan', 'marketing', 'workstation'],
    comments: [
      {
        id: '1',
        author: 'Алексей Смирнов',
        text: 'Начат анализ активности. Изолировал систему от сети.',
        createdAt: '2023-11-14T09:30:00Z'
      }
    ],
    actions: [
      {
        id: '1',
        type: 'status_change',
        description: 'Статус изменён на "Смягчение последствий"',
        performedBy: 'Алексей Смирнов',
        performedAt: '2023-11-14T11:20:00Z'
      }
    ]
  },
  {
    id: '3',
    title: 'Утечка данных через API',
    description: 'Обнаружена подозрительная активность с повышенным объемом запросов к API с данными клиентов',
    status: IncidentStatus.NEW,
    severity: IncidentSeverity.CRITICAL,
    type: IncidentType.DATA_BREACH,
    affectedSystems: ['API-сервер', 'База данных клиентов'],
    detectionSource: 'SIEM',
    detectedAt: '2023-11-15T18:10:00Z',
    reportedBy: 'system',
    tags: ['api', 'data-leak', 'customer-data'],
    comments: [],
    actions: []
  },
  {
    id: '4',
    title: 'Фишинговая кампания на сотрудников',
    description: 'Обнаружена массовая рассылка фишинговых писем, имитирующих корпоративные уведомления',
    status: IncidentStatus.RESOLVED,
    severity: IncidentSeverity.MEDIUM,
    type: IncidentType.PHISHING,
    affectedSystems: ['Почтовый сервер', 'Корпоративные учетные записи'],
    detectionSource: 'Email Security Gateway',
    detectedAt: '2023-11-12T08:45:00Z',
    reportedBy: 'system',
    assignedTo: 'Мария Козлова',
    resolvedAt: '2023-11-13T16:30:00Z',
    resolvedBy: 'Мария Козлова',
    rootCause: 'Внешняя фишинговая кампания, нацеленная на сотрудников компании',
    resolution: 'Блокировка отправителей, удаление писем из почтовых ящиков, проведение обучения по информационной безопасности',
    tags: ['phishing', 'email', 'training'],
    comments: [
      {
        id: '1',
        author: 'Мария Козлова',
        text: 'Выполнен анализ всех писем. 23 сотрудника открыли ссылки, 5 ввели учетные данные.',
        createdAt: '2023-11-12T12:30:00Z'
      }
    ],
    actions: [
      {
        id: '1',
        type: 'status_change',
        description: 'Статус изменён на "Решено"',
        performedBy: 'Мария Козлова',
        performedAt: '2023-11-13T16:30:00Z'
      }
    ]
  },
  {
    id: '5',
    title: 'DDoS-атака на корпоративный веб-сайт',
    description: 'Зафиксирована распределенная атака типа "отказ в обслуживании" на корпоративный веб-сайт',
    status: IncidentStatus.CLOSED,
    severity: IncidentSeverity.LOW,
    type: IncidentType.DDOS,
    affectedSystems: ['Веб-сайт', 'Балансировщики нагрузки'],
    detectionSource: 'Network Monitoring',
    detectedAt: '2023-11-10T11:20:00Z',
    reportedBy: 'system',
    assignedTo: 'Дмитрий Волков',
    resolvedAt: '2023-11-10T14:45:00Z',
    resolvedBy: 'Дмитрий Волков',
    closedAt: '2023-11-11T09:00:00Z',
    rootCause: 'Целенаправленная DDoS-атака с ботнета',
    resolution: 'Активация защиты от DDoS у провайдера, фильтрация трафика, масштабирование ресурсов',
    tags: ['ddos', 'website', 'availability'],
    comments: [],
    actions: [
      {
        id: '1',
        type: 'status_change',
        description: 'Статус изменён на "Закрыт"',
        performedBy: 'Дмитрий Волков',
        performedAt: '2023-11-11T09:00:00Z'
      }
    ]
  },
];

const IncidentsPage: React.FC = () => {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState<Incident[]>(mockIncidents);
  const [filteredIncidents, setFilteredIncidents] = useState<Incident[]>(mockIncidents);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  useEffect(() => {
    // Применяем фильтры
    let result = incidents;
    
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(incident => 
        incident.title.toLowerCase().includes(query) || 
        incident.description.toLowerCase().includes(query) ||
        incident.tags.some(tag => tag.toLowerCase().includes(query))
      );
    }
    
    if (statusFilter) {
      result = result.filter(incident => incident.status === statusFilter);
    }
    
    if (severityFilter) {
      result = result.filter(incident => incident.severity === severityFilter);
    }
    
    if (typeFilter) {
      result = result.filter(incident => incident.type === typeFilter);
    }
    
    setFilteredIncidents(result);
    setCurrentPage(1);
  }, [incidents, searchQuery, statusFilter, severityFilter, typeFilter]);

  const handleIncidentClick = (incidentId: string) => {
    navigate(`/incidents/${incidentId}`);
  };

  const handleCreateIncident = () => {
    navigate('/incidents/new');
  };

  // Пагинация
  const totalPages = Math.ceil(filteredIncidents.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedIncidents = filteredIncidents.slice(startIndex, startIndex + itemsPerPage);

  // Статистика
  const totalIncidents = incidents.length;
  const newIncidents = incidents.filter(inc => inc.status === IncidentStatus.NEW).length;
  const inProgressIncidents = incidents.filter(inc => 
    inc.status === IncidentStatus.INVESTIGATING || 
    inc.status === IncidentStatus.MITIGATING
  ).length;
  const criticalIncidents = incidents.filter(inc => inc.severity === IncidentSeverity.CRITICAL).length;

  return (
    <Container>
      <Header>
        <Title>Управление инцидентами</Title>
        <Button onClick={handleCreateIncident}>Создать инцидент</Button>
      </Header>

      <StatsContainer>
        <StatCard>
          <StatValue>{totalIncidents}</StatValue>
          <StatLabel>Всего инцидентов</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{newIncidents}</StatValue>
          <StatLabel>Новые</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{inProgressIncidents}</StatValue>
          <StatLabel>В обработке</StatLabel>
        </StatCard>
        <StatCard>
          <StatValue>{criticalIncidents}</StatValue>
          <StatLabel>Критические</StatLabel>
        </StatCard>
      </StatsContainer>

      <FiltersContainer>
        <SearchInput 
          placeholder="Поиск инцидентов..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <Select 
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">Все статусы</option>
          {Object.values(IncidentStatus).map(status => (
            <option key={status} value={status}>{status}</option>
          ))}
        </Select>
        <Select 
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
        >
          <option value="">Все уровни</option>
          {Object.values(IncidentSeverity).map(severity => (
            <option key={severity} value={severity}>{severity}</option>
          ))}
        </Select>
        <Select 
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">Все типы</option>
          {Object.values(IncidentType).map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </Select>
      </FiltersContainer>

      {filteredIncidents.length > 0 ? (
        <>
          <Table>
            <TableHead>
              <tr>
                <TableHeaderCell>ID</TableHeaderCell>
                <TableHeaderCell>Название</TableHeaderCell>
                <TableHeaderCell>Критичность</TableHeaderCell>
                <TableHeaderCell>Статус</TableHeaderCell>
                <TableHeaderCell>Тип</TableHeaderCell>
                <TableHeaderCell>Обнаружен</TableHeaderCell>
                <TableHeaderCell>Назначен</TableHeaderCell>
              </tr>
            </TableHead>
            <tbody>
              {paginatedIncidents.map(incident => (
                <TableRow key={incident.id} onClick={() => handleIncidentClick(incident.id)}>
                  <TableCell>{incident.id}</TableCell>
                  <TableCell>{incident.title}</TableCell>
                  <TableCell>
                    <SeverityBadge severity={incident.severity}>
                      {incident.severity}
                    </SeverityBadge>
                  </TableCell>
                  <TableCell>
                    <StatusBadge status={incident.status}>
                      {incident.status}
                    </StatusBadge>
                  </TableCell>
                  <TableCell>{incident.type}</TableCell>
                  <TableCell>{new Date(incident.detectedAt).toLocaleString()}</TableCell>
                  <TableCell>{incident.assignedTo || "—"}</TableCell>
                </TableRow>
              ))}
            </tbody>
          </Table>

          {totalPages > 1 && (
            <Pagination>
              <PageButton
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
              >
                &lt;
              </PageButton>
              {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                <PageButton
                  key={page}
                  active={page === currentPage}
                  onClick={() => setCurrentPage(page)}
                >
                  {page}
                </PageButton>
              ))}
              <PageButton
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
              >
                &gt;
              </PageButton>
            </Pagination>
          )}
        </>
      ) : (
        <EmptyState>
          <EmptyStateIcon>🔍</EmptyStateIcon>
          <div>
            <h3>Инцидентов не найдено</h3>
            <p>Попробуйте изменить параметры фильтрации или создайте новый инцидент</p>
          </div>
          <Button onClick={handleCreateIncident} style={{ marginTop: '16px' }}>
            Создать инцидент
          </Button>
        </EmptyState>
      )}
    </Container>
  );
};

export default IncidentsPage; 