import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { 
  Incident, 
  IncidentStatus, 
  IncidentSeverity, 
  IncidentType,
  IncidentListParams,
  IncidentFilter
} from '../types/incident';
import { incidentService } from '../services/api';

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
  color: ${props => props.theme.text?.primary || '#F8F8F2'};
`;

const StatsContainer = styled.div`
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
`;

const StatCard = styled.div`
  background: ${props => props.theme.bg?.secondary || '#1E1E2E'};
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
  color: ${props => props.theme.text?.primary || '#F8F8F2'};
`;

const StatLabel = styled.div`
  font-size: 14px;
  color: ${props => props.theme.text?.secondary || '#6C7293'};
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
  border: 1px solid ${props => props.theme.border?.primary || '#44475A'};
  background: ${props => props.theme.bg?.input || '#1E1E2E'};
  color: ${props => props.theme.text?.primary || '#F8F8F2'};
  flex: 1;
  min-width: 250px;

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors?.primary || '#0F94FF'};
  }
`;

const Select = styled.select`
  padding: 8px 16px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.border?.primary || '#44475A'};
  background: ${props => props.theme.bg?.input || '#1E1E2E'};
  color: ${props => props.theme.text?.primary || '#F8F8F2'};

  &:focus {
    outline: none;
    border-color: ${props => props.theme.colors?.primary || '#0F94FF'};
  }
`;

const Button = styled.button`
  padding: 8px 16px;
  border-radius: 4px;
  background: ${props => props.theme.colors?.primary || '#0F94FF'};
  color: white;
  border: none;
  cursor: pointer;
  font-weight: bold;

  &:hover {
    background: ${props => props.theme.accent?.primary || '#BD93F9'};
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background: ${props => props.theme.bg?.secondary || '#1E1E2E'};
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const TableHead = styled.thead`
  background: ${props => props.theme.bg?.tertiary || '#282A36'};
  border-bottom: 1px solid ${props => props.theme.border?.primary || '#44475A'};
`;

const TableRow = styled.tr`
  cursor: pointer;
  
  &:hover {
    background: ${props => props.theme.bg?.hover || '#333333'};
  }

  &:not(:last-child) {
    border-bottom: 1px solid ${props => props.theme.border?.secondary || '#6C7293'};
  }
`;

const TableHeaderCell = styled.th`
  text-align: left;
  padding: 16px;
  font-weight: bold;
  color: ${props => props.theme.text?.primary || '#F8F8F2'};
`;

const TableCell = styled.td`
  padding: 16px;
  color: ${props => props.theme.text?.primary || '#F8F8F2'};
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
      case IncidentStatus.MITIGATED:
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
      case IncidentStatus.MITIGATED:
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
  color: ${props => props.theme.text?.secondary || '#6C7293'};
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
    ? props.theme.colors?.primary || '#0F94FF'
    : props.theme.border?.primary || '#44475A'};
  background: ${props => props.active 
    ? props.theme.colors?.primary || '#0F94FF'
    : props.theme.bg?.input || '#1E1E2E'};
  color: ${props => props.active 
    ? 'white' 
    : props.theme.text?.primary || '#F8F8F2'};
  cursor: pointer;
  
  &:hover {
    background: ${props => props.active 
      ? props.theme.accent?.primary || '#BD93F9'
      : props.theme.bg?.hover || '#383A59'};
  }
`;

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  width: 100%;
`;

const ErrorContainer = styled.div`
  background-color: #ffebee;
  color: #b71c1c;
  padding: 16px;
  border-radius: 4px;
  margin-bottom: 16px;
`;

const IncidentsPage: React.FC = () => {
  const navigate = useNavigate();
  
  // Состояние для API данных
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [filteredIncidents, setFilteredIncidents] = useState<Incident[]>([]);
  
  // Состояние для пагинации и фильтрации
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const itemsPerPage = 10;
  
  // Состояние для фильтров
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  // Загрузка данных с сервера
  useEffect(() => {
    fetchIncidents();
  }, [currentPage, statusFilter, severityFilter, typeFilter, searchQuery]);

  const fetchIncidents = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Формируем параметры запроса
      const filters: IncidentFilter = {};
      
      if (statusFilter) {
        filters.status = [statusFilter as IncidentStatus];
      }
      
      if (severityFilter) {
        filters.severity = [severityFilter as IncidentSeverity];
      }
      
      if (typeFilter) {
        filters.type = [typeFilter as IncidentType];
      }
      
      if (searchQuery) {
        filters.searchTerm = searchQuery;
      }
      
      const params: IncidentListParams = {
        page: currentPage,
        pageSize: itemsPerPage,
        sortBy: 'detectedAt',
        sortDirection: 'desc',
        filters
      };
      
      const result = await incidentService.getIncidents(params);
      
      setTotalCount(result.totalCount);
      setTotalPages(result.totalPages);
      setIncidents(result.incidents);
      setFilteredIncidents(result.incidents);
      
    } catch (err) {
      console.error('Ошибка при загрузке инцидентов:', err);
      setError('Не удалось загрузить список инцидентов. Пожалуйста, попробуйте позже.');
    } finally {
      setLoading(false);
    }
  };

  const handleIncidentClick = (incidentId: string) => {
    navigate(`/incidents/${incidentId}`);
  };

  const handleCreateIncident = () => {
    navigate('/incidents/new');
  };

  // Статистика
  const newIncidents = incidents.filter(inc => inc.status === IncidentStatus.NEW).length;
  const inProgressIncidents = incidents.filter(inc => 
    inc.status === IncidentStatus.INVESTIGATING || 
    inc.status === IncidentStatus.MITIGATED
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
          <StatValue>{totalCount}</StatValue>
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

      {error && <ErrorContainer>{error}</ErrorContainer>}
      
      {loading ? (
        <LoadingContainer>
          <div>Загрузка инцидентов...</div>
        </LoadingContainer>
      ) : filteredIncidents.length > 0 ? (
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
              {filteredIncidents.map(incident => (
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
                  <TableCell>{incident.assignedTo ? incident.assignedTo.username : "—"}</TableCell>
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