import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import IncidentCard, { IncidentCardProps } from '../components/incidents/IncidentCard';

// Стилизованные компоненты
const PageContainer = styled.div`
  padding: 24px;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 28px;
  font-weight: 700;
  color: #F8F8F2;
  margin: 0;
`;

const FiltersContainer = styled.div`
  display: flex;
  background-color: #282A36;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
`;

const SearchInput = styled.input`
  padding: 10px 16px;
  border-radius: 6px;
  border: 1px solid #44475A;
  background-color: #1E1E2E;
  color: #F8F8F2;
  flex: 1;
  min-width: 200px;
  
  &:focus {
    outline: none;
    border-color: #BD93F9;
  }

  &::placeholder {
    color: #6C7293;
  }
`;

const FilterGroup = styled.div`
  display: flex;
  flex-direction: column;
  min-width: 150px;
`;

const FilterLabel = styled.label`
  font-size: 12px;
  color: #6C7293;
  margin-bottom: 6px;
`;

const Select = styled.select`
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #44475A;
  background-color: #1E1E2E;
  color: #F8F8F2;
  
  &:focus {
    outline: none;
    border-color: #BD93F9;
  }
`;

const GridContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
`;

const StatsContainer = styled.div`
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
`;

const StatCard = styled.div<{ color: string }>`
  background-color: #282A36;
  border-left: 4px solid ${props => props.color};
  border-radius: 8px;
  padding: 16px;
  min-width: 180px;
  
  h3 {
    font-size: 14px;
    color: #6C7293;
    margin: 0 0 8px 0;
  }
  
  p {
    font-size: 24px;
    font-weight: 700;
    color: #F8F8F2;
    margin: 0;
  }
`;

const NewIncidentButton = styled.button`
  padding: 10px 20px;
  background-color: #BD93F9;
  color: #282A36;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #A580FF;
  }
`;

const EmptyState = styled.div`
  text-align: center;
  padding: 60px 0;
  color: #6C7293;
  
  h3 {
    font-size: 18px;
    margin-bottom: 16px;
  }
  
  p {
    font-size: 14px;
    margin-bottom: 24px;
  }
`;

// Мок данных с инцидентами для примера
const mockIncidents: IncidentCardProps[] = [
  {
    id: 'INC-2024-001',
    title: 'Подозрительная активность в сети Зонда #45',
    status: 'investigating',
    severity: 'high',
    type: 'intrusion',
    detectedDate: new Date('2024-05-15T14:23:00'),
    assignedTo: 'Иванов А.П.'
  },
  {
    id: 'INC-2024-002',
    title: 'Обнаружено вредоносное ПО на рабочей станции',
    status: 'new',
    severity: 'critical',
    type: 'malware',
    detectedDate: new Date('2024-05-15T10:45:00')
  },
  {
    id: 'INC-2024-003',
    title: 'Неавторизованный доступ к серверу баз данных',
    status: 'resolved',
    severity: 'critical',
    type: 'unauthorized_access',
    detectedDate: new Date('2024-05-14T18:30:00'),
    assignedTo: 'Петрова Е.С.'
  },
  {
    id: 'INC-2024-004',
    title: 'Утечка данных из внутренней сети',
    status: 'investigating',
    severity: 'high',
    type: 'data_breach',
    detectedDate: new Date('2024-05-14T09:15:00'),
    assignedTo: 'Сидоров В.А.'
  },
  {
    id: 'INC-2024-005',
    title: 'DDoS атака на внешний периметр',
    status: 'closed',
    severity: 'medium',
    type: 'dos',
    detectedDate: new Date('2024-05-13T16:20:00'),
    assignedTo: 'Иванов А.П.'
  },
  {
    id: 'INC-2024-006',
    title: 'Аномальная активность в сетевом трафике',
    status: 'new',
    severity: 'low',
    type: 'other',
    detectedDate: new Date('2024-05-13T08:50:00')
  }
];

const IncidentsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState<IncidentCardProps[]>(mockIncidents);
  const [filteredIncidents, setFilteredIncidents] = useState<IncidentCardProps[]>(incidents);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  // Применение фильтров при изменении данных
  useEffect(() => {
    let result = incidents;
    
    // Поиск по названию и ID
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(incident => 
        incident.title.toLowerCase().includes(query) || 
        incident.id.toLowerCase().includes(query)
      );
    }
    
    // Фильтрация по статусу
    if (statusFilter !== 'all') {
      result = result.filter(incident => incident.status === statusFilter);
    }
    
    // Фильтрация по важности
    if (severityFilter !== 'all') {
      result = result.filter(incident => incident.severity === severityFilter);
    }
    
    // Фильтрация по типу
    if (typeFilter !== 'all') {
      result = result.filter(incident => incident.type === typeFilter);
    }
    
    setFilteredIncidents(result);
  }, [incidents, searchQuery, statusFilter, severityFilter, typeFilter]);

  // Подсчет статистики
  const totalIncidents = incidents.length;
  const newIncidents = incidents.filter(i => i.status === 'new').length;
  const criticalIncidents = incidents.filter(i => i.severity === 'critical').length;
  const resolvedIncidents = incidents.filter(i => i.status === 'resolved' || i.status === 'closed').length;

  // Обработчик клика по карточке
  const handleIncidentClick = (id: string) => {
    navigate(`/incidents/${id}`);
  };

  // Обработчик создания нового инцидента
  const handleCreateIncident = () => {
    navigate('/incidents/new');
  };

  return (
    <PageContainer>
      <Header>
        <Title>Инциденты безопасности</Title>
        <NewIncidentButton onClick={handleCreateIncident}>
          Создать инцидент
        </NewIncidentButton>
      </Header>
      
      <StatsContainer>
        <StatCard color="#BD93F9">
          <h3>Всего инцидентов</h3>
          <p>{totalIncidents}</p>
        </StatCard>
        <StatCard color="#FF5555">
          <h3>Новых</h3>
          <p>{newIncidents}</p>
        </StatCard>
        <StatCard color="#FF5555">
          <h3>Критических</h3>
          <p>{criticalIncidents}</p>
        </StatCard>
        <StatCard color="#50FA7B">
          <h3>Решенных</h3>
          <p>{resolvedIncidents}</p>
        </StatCard>
      </StatsContainer>
      
      <FiltersContainer>
        <SearchInput 
          placeholder="Поиск по названию или ID" 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        
        <FilterGroup>
          <FilterLabel>Статус</FilterLabel>
          <Select 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">Все статусы</option>
            <option value="new">Новые</option>
            <option value="investigating">Расследование</option>
            <option value="resolved">Решенные</option>
            <option value="closed">Закрытые</option>
          </Select>
        </FilterGroup>
        
        <FilterGroup>
          <FilterLabel>Важность</FilterLabel>
          <Select 
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="all">Любая</option>
            <option value="critical">Критическая</option>
            <option value="high">Высокая</option>
            <option value="medium">Средняя</option>
            <option value="low">Низкая</option>
          </Select>
        </FilterGroup>
        
        <FilterGroup>
          <FilterLabel>Тип</FilterLabel>
          <Select 
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="all">Все типы</option>
            <option value="intrusion">Вторжение</option>
            <option value="malware">Вредоносное ПО</option>
            <option value="dos">DoS-атака</option>
            <option value="unauthorized_access">Несанкционированный доступ</option>
            <option value="data_breach">Утечка данных</option>
            <option value="other">Другое</option>
          </Select>
        </FilterGroup>
      </FiltersContainer>
      
      {filteredIncidents.length > 0 ? (
        <GridContainer>
          {filteredIncidents.map(incident => (
            <IncidentCard
              key={incident.id}
              {...incident}
              onClick={() => handleIncidentClick(incident.id)}
            />
          ))}
        </GridContainer>
      ) : (
        <EmptyState>
          <h3>Нет подходящих инцидентов</h3>
          <p>Попробуйте изменить параметры фильтрации или создайте новый инцидент</p>
          <NewIncidentButton onClick={handleCreateIncident}>
            Создать инцидент
          </NewIncidentButton>
        </EmptyState>
      )}
    </PageContainer>
  );
};

export default IncidentsListPage; 