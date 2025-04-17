import React, { useState, useEffect } from 'react';
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
  max-width: 1400px;
  margin: 0 auto;
`;

const Title = styled.h1`
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 24px;
  color: ${props => props.theme.colors.text.primary};
`;

const StatsPanel = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
`;

const StatCard = styled.div<{ color?: string }>`
  background: ${props => props.theme.colors.background.secondary};
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  
  h3 {
    font-size: 14px;
    color: ${props => props.theme.colors.text.secondary};
    margin-bottom: 8px;
  }
  
  p {
    font-size: 28px;
    font-weight: 700;
    margin: 0;
    color: ${props => props.color || props.theme.colors.text.primary};
  }
`;

const SeverityBadge = styled.span<{ severity: IncidentSeverity }>`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  
  ${props => {
    switch(props.severity) {
      case IncidentSeverity.LOW:
        return `
          background-color: rgba(52, 211, 153, 0.2);
          color: #10B981;
        `;
      case IncidentSeverity.MEDIUM:
        return `
          background-color: rgba(250, 204, 21, 0.2);
          color: #EAB308;
        `;
      case IncidentSeverity.HIGH:
        return `
          background-color: rgba(251, 146, 60, 0.2);
          color: #F97316;
        `;
      case IncidentSeverity.CRITICAL:
        return `
          background-color: rgba(239, 68, 68, 0.2);
          color: #EF4444;
        `;
      default:
        return '';
    }
  }}
`;

const StatusBadge = styled.span<{ status: IncidentStatus }>`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  
  ${props => {
    switch(props.status) {
      case IncidentStatus.NEW:
        return `
          background-color: rgba(99, 102, 241, 0.2);
          color: #6366F1;
        `;
      case IncidentStatus.INVESTIGATING:
        return `
          background-color: rgba(251, 146, 60, 0.2);
          color: #F97316;
        `;
      case IncidentStatus.MITIGATED:
        return `
          background-color: rgba(14, 165, 233, 0.2);
          color: #0EA5E9;
        `;
      case IncidentStatus.RESOLVED:
        return `
          background-color: rgba(52, 211, 153, 0.2);
          color: #10B981;
        `;
      case IncidentStatus.CLOSED:
        return `
          background-color: rgba(107, 114, 128, 0.2);
          color: #6B7280;
        `;
      default:
        return '';
    }
  }}
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
  border: 1px solid ${props => props.theme.colors.border.primary};
  background: ${props => props.theme.colors.background.secondary};
  color: ${props => props.theme.colors.text.primary};
  font-size: 14px;
  flex: 1;
  min-width: 240px;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const SelectFilter = styled.select`
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.colors.border.primary};
  background: ${props => props.theme.colors.background.secondary};
  color: ${props => props.theme.colors.text.primary};
  font-size: 14px;
  min-width: 160px;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors.primary};
  }
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  display: flex;
  align-items: center;
  gap: 8px;
  
  ${props => {
    switch(props.variant) {
      case 'primary':
        return `
          background: ${props.theme.colors.primary};
          color: white;
        `;
      case 'danger':
        return `
          background: #EF4444;
          color: white;
        `;
      case 'secondary':
      default:
        return `
          background: ${props.theme.colors.background.tertiary};
          color: ${props.theme.colors.text.primary};
          border: 1px solid ${props.theme.colors.border.primary};
        `;
    }
  }}
  
  &:hover {
    opacity: 0.9;
  }
`;

const IncidentsTable = styled.table`
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  
  th, td {
    padding: 12px 16px;
    text-align: left;
    border-bottom: 1px solid ${props => props.theme.colors.border.primary};
    font-size: 14px;
  }
  
  th {
    font-weight: 600;
    color: ${props => props.theme.colors.text.secondary};
    background: ${props => props.theme.colors.background.secondary};
    position: sticky;
    top: 0;
    z-index: 10;
  }
  
  tr:last-child td {
    border-bottom: none;
  }
  
  tr:hover td {
    background: ${props => props.theme.colors.background.hover};
  }
`;

const ActionsContainer = styled.div`
  display: flex;
  gap: 8px;
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px;
  text-align: center;
  
  h3 {
    font-size: 18px;
    margin-bottom: 8px;
    color: ${props => props.theme.colors.text.primary};
  }
  
  p {
    color: ${props => props.theme.colors.text.secondary};
    margin-bottom: 24px;
  }
`;

const TableContainer = styled.div`
  background: ${props => props.theme.colors.background.secondary};
  border-radius: 8px;
  overflow: auto;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
  max-height: 600px;
`;

// Sample data
const mockIncidents: Incident[] = [
  {
    id: '1',
    title: 'Несанкционированный доступ к системе SCADA',
    description: 'Обнаружен несанкционированный доступ к системе управления промышленными процессами SCADA через уязвимый контроллер.',
    status: IncidentStatus.INVESTIGATING,
    severity: IncidentSeverity.CRITICAL,
    type: IncidentType.UNAUTHORIZED_ACCESS,
    affectedSystems: ['SCADA-01', 'PLC-Controller-12'],
    affectedZonds: ['ZND-08', 'ZND-15'],
    detectionSource: 'IDS Alert',
    detectedAt: '2023-10-15T14:32:00Z',
    reportedBy: 'system',
    tags: ['scada', 'industrial', 'unauthorized-access'],
    impactDescription: 'Потенциальный контроль над промышленным оборудованием, риск повреждения инфраструктуры'
  },
  {
    id: '2',
    title: 'Подозрительная активность Mimikatz',
    description: 'Обнаружены признаки работы инструмента Mimikatz на рабочей станции финансового департамента.',
    status: IncidentStatus.MITIGATED,
    severity: IncidentSeverity.HIGH,
    type: IncidentType.CREDENTIAL_COMPROMISE,
    affectedSystems: ['WS-FIN-023'],
    affectedZonds: ['ZND-03'],
    detectionSource: 'EDR Alert',
    detectedAt: '2023-10-14T09:45:00Z',
    reportedBy: 'anton.petrov',
    assignedTo: 'irina.voronina',
    tags: ['mimikatz', 'credential-theft', 'financial-department']
  },
  {
    id: '3',
    title: 'Фишинговая кампания на сотрудников HR',
    description: 'Массовая фишинговая атака, нацеленная на сотрудников отдела кадров с вредоносными вложениями.',
    status: IncidentStatus.RESOLVED,
    severity: IncidentSeverity.MEDIUM,
    type: IncidentType.SOCIAL_ENGINEERING,
    affectedSystems: ['Mail-Server'],
    affectedZonds: [],
    detectionSource: 'User Report',
    detectedAt: '2023-10-10T11:20:00Z',
    reportedBy: 'elena.mihailova',
    assignedTo: 'dmitry.sokolov',
    resolvedAt: '2023-10-12T16:30:00Z',
    resolvedBy: 'dmitry.sokolov',
    rootCause: 'Фишинговая кампания с использованием поддельных писем о новых кандидатах',
    resolution: 'Заблокированы все домены отправителей, проведен инструктаж сотрудников HR',
    tags: ['phishing', 'hr', 'email-security']
  },
  {
    id: '4',
    title: 'Обнаружение вредоносного ПО TrickBot',
    description: 'На рабочей станции бухгалтерии обнаружены следы активности вредоносного ПО TrickBot.',
    status: IncidentStatus.NEW,
    severity: IncidentSeverity.HIGH,
    type: IncidentType.MALWARE,
    affectedSystems: ['WS-ACC-007'],
    affectedZonds: ['ZND-10'],
    detectionSource: 'Anti-Virus Alert',
    detectedAt: '2023-10-16T08:15:00Z',
    reportedBy: 'system',
    tags: ['trickbot', 'banking-trojan', 'malware']
  },
  {
    id: '5',
    title: 'Атака на веб-сервер компании',
    description: 'Обнаружена попытка эксплуатации уязвимости SQL-инъекции на корпоративном веб-сервере.',
    status: IncidentStatus.CLOSED,
    severity: IncidentSeverity.LOW,
    type: IncidentType.UNAUTHORIZED_ACCESS,
    affectedSystems: ['WEB-SRV-01'],
    affectedZonds: ['ZND-01'],
    detectionSource: 'WAF Log',
    detectedAt: '2023-10-08T22:40:00Z',
    reportedBy: 'system',
    assignedTo: 'igor.volkov',
    resolvedAt: '2023-10-09T14:10:00Z',
    closedAt: '2023-10-10T09:30:00Z',
    resolvedBy: 'igor.volkov',
    rootCause: 'Неправильно обработанный пользовательский ввод в форме авторизации',
    resolution: 'Исправлен код формы авторизации, добавлена параметризация запросов',
    tags: ['sql-injection', 'web-server', 'waf']
  }
];

const IncidentsManagementPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>(mockIncidents);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  
  // Расчет статистики
  const stats = {
    total: incidents.length,
    new: incidents.filter(inc => inc.status === IncidentStatus.NEW).length,
    investigating: incidents.filter(inc => inc.status === IncidentStatus.INVESTIGATING).length,
    mitigating: incidents.filter(inc => inc.status === IncidentStatus.MITIGATED).length,
    resolved: incidents.filter(inc => inc.status === IncidentStatus.RESOLVED).length,
    closed: incidents.filter(inc => inc.status === IncidentStatus.CLOSED).length,
    critical: incidents.filter(inc => inc.severity === IncidentSeverity.CRITICAL).length,
    high: incidents.filter(inc => inc.severity === IncidentSeverity.HIGH).length,
    medium: incidents.filter(inc => inc.severity === IncidentSeverity.MEDIUM).length,
    low: incidents.filter(inc => inc.severity === IncidentSeverity.LOW).length,
  };

  // Фильтрация инцидентов
  const filteredIncidents = incidents.filter(incident => {
    // Поиск по заголовку и описанию
    const searchMatch = !searchQuery || 
      incident.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
      incident.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      incident.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    
    // Фильтр по статусу
    const statusMatch = !statusFilter || incident.status === statusFilter;
    
    // Фильтр по важности
    const severityMatch = !severityFilter || incident.severity === severityFilter;
    
    // Фильтр по типу
    const typeMatch = !typeFilter || incident.type === typeFilter;
    
    return searchMatch && statusMatch && severityMatch && typeMatch;
  });

  // Обработчики
  const handleViewIncident = (id: string) => {
    console.log(`Просмотр инцидента: ${id}`);
    // Реализация навигации на страницу деталей инцидента
  };
  
  const handleAssignIncident = (id: string) => {
    console.log(`Назначение инцидента: ${id}`);
    // Реализация диалога назначения
  };
  
  const handleUpdateStatus = (id: string, newStatus: IncidentStatus) => {
    console.log(`Обновление статуса инцидента ${id} на ${newStatus}`);
    setIncidents(prev => 
      prev.map(inc => 
        inc.id === id ? { ...inc, status: newStatus } : inc
      )
    );
  };
  
  const handleCreateIncident = () => {
    console.log('Создание нового инцидента');
    // Реализация навигации на страницу создания инцидента
  };

  return (
    <Container>
      <Title>Управление инцидентами</Title>
      
      {/* Панель статистики */}
      <StatsPanel>
        <StatCard>
          <h3>Всего инцидентов</h3>
          <p>{stats.total}</p>
        </StatCard>
        <StatCard color="#6366F1">
          <h3>Новые</h3>
          <p>{stats.new}</p>
        </StatCard>
        <StatCard color="#F97316">
          <h3>Расследуются</h3>
          <p>{stats.investigating}</p>
        </StatCard>
        <StatCard color="#0EA5E9">
          <h3>Устраняются</h3>
          <p>{stats.mitigating}</p>
        </StatCard>
        <StatCard color="#10B981">
          <h3>Решены</h3>
          <p>{stats.resolved}</p>
        </StatCard>
        <StatCard color="#EF4444">
          <h3>Критические</h3>
          <p>{stats.critical}</p>
        </StatCard>
      </StatsPanel>
      
      {/* Фильтры и поиск */}
      <FiltersContainer>
        <SearchInput 
          placeholder="Поиск по заголовку, описанию или тегам..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        
        <SelectFilter 
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
        >
          <option value="">Все статусы</option>
          {Object.values(IncidentStatus).map(status => (
            <option key={status} value={status}>{status}</option>
          ))}
        </SelectFilter>
        
        <SelectFilter 
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
        >
          <option value="">Все уровни важности</option>
          {Object.values(IncidentSeverity).map(severity => (
            <option key={severity} value={severity}>{severity}</option>
          ))}
        </SelectFilter>
        
        <SelectFilter 
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
          <option value="">Все типы</option>
          {Object.values(IncidentType).map(type => (
            <option key={type} value={type}>{type}</option>
          ))}
        </SelectFilter>
        
        <Button variant="primary" onClick={handleCreateIncident}>
          Создать инцидент
        </Button>
      </FiltersContainer>
      
      {/* Таблица инцидентов */}
      <TableContainer>
        {filteredIncidents.length > 0 ? (
          <IncidentsTable>
            <thead>
              <tr>
                <th>ID</th>
                <th>Заголовок</th>
                <th>Важность</th>
                <th>Статус</th>
                <th>Тип</th>
                <th>Обнаружен</th>
                <th>Назначен</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {filteredIncidents.map(incident => (
                <tr key={incident.id}>
                  <td>{incident.id}</td>
                  <td>{incident.title}</td>
                  <td>
                    <SeverityBadge severity={incident.severity}>
                      {incident.severity}
                    </SeverityBadge>
                  </td>
                  <td>
                    <StatusBadge status={incident.status}>
                      {incident.status}
                    </StatusBadge>
                  </td>
                  <td>{incident.type}</td>
                  <td>{new Date(incident.detectedAt).toLocaleString()}</td>
                  <td>{incident.assignedTo || '-'}</td>
                  <td>
                    <ActionsContainer>
                      <Button onClick={() => handleViewIncident(incident.id)}>
                        Просмотр
                      </Button>
                      
                      {!incident.assignedTo && (
                        <Button onClick={() => handleAssignIncident(incident.id)}>
                          Назначить
                        </Button>
                      )}
                      
                      {incident.status === IncidentStatus.NEW && (
                        <Button 
                          variant="primary"
                          onClick={() => handleUpdateStatus(incident.id, IncidentStatus.INVESTIGATING)}
                        >
                          Начать расследование
                        </Button>
                      )}
                      
                      {incident.status === IncidentStatus.INVESTIGATING && (
                        <Button 
                          variant="primary"
                          onClick={() => handleUpdateStatus(incident.id, IncidentStatus.MITIGATED)}
                        >
                          Начать устранение
                        </Button>
                      )}
                      
                      {incident.status === IncidentStatus.MITIGATED && (
                        <Button 
                          variant="primary"
                          onClick={() => handleUpdateStatus(incident.id, IncidentStatus.RESOLVED)}
                        >
                          Отметить как решенный
                        </Button>
                      )}
                      
                      {incident.status === IncidentStatus.RESOLVED && (
                        <Button 
                          onClick={() => handleUpdateStatus(incident.id, IncidentStatus.CLOSED)}
                        >
                          Закрыть инцидент
                        </Button>
                      )}
                    </ActionsContainer>
                  </td>
                </tr>
              ))}
            </tbody>
          </IncidentsTable>
        ) : (
          <EmptyState>
            <h3>Нет инцидентов</h3>
            <p>Не найдено инцидентов, соответствующих критериям поиска</p>
            <Button variant="primary" onClick={handleCreateIncident}>
              Создать инцидент
            </Button>
          </EmptyState>
        )}
      </TableContainer>
    </Container>
  );
};

export default IncidentsManagementPage; 