import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import {
  AnomalyStatus,
  AnomalySeverity,
  AnomalyType,
  Anomaly,
  ANOMALY_STATUS_NAMES,
  ANOMALY_SEVERITY_NAMES,
  ANOMALY_TYPE_NAMES,
  formatDate
} from '../types/anomaly';

// Компоненты стилей
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

const AnomaliesTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  background-color: #282A36;
  border-radius: 8px;
  overflow: hidden;
`;

const TableHead = styled.thead`
  background-color: #44475A;
  
  th {
    padding: 16px;
    text-align: left;
    color: #F8F8F2;
    font-weight: 600;
    font-size: 14px;
  }
`;

const TableBody = styled.tbody`
  tr {
    border-bottom: 1px solid #44475A;
    cursor: pointer;
    transition: background-color 0.2s;
    
    &:hover {
      background-color: #383A59;
    }
    
    &:last-child {
      border-bottom: none;
    }
  }
  
  td {
    padding: 16px;
    color: #F8F8F2;
    font-size: 14px;
  }
`;

const StatusBadge = styled.span<{ status: AnomalyStatus }>`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  
  ${props => {
    switch(props.status) {
      case AnomalyStatus.NEW:
        return `
          background-color: #FF5555;
          color: #F8F8F2;
        `;
      case AnomalyStatus.INVESTIGATING:
        return `
          background-color: #FFB86C;
          color: #282A36;
        `;
      case AnomalyStatus.RESOLVED:
        return `
          background-color: #50FA7B;
          color: #282A36;
        `;
      case AnomalyStatus.FALSE_POSITIVE:
        return `
          background-color: #6272A4;
          color: #F8F8F2;
        `;
      default:
        return `
          background-color: #44475A;
          color: #F8F8F2;
        `;
    }
  }}
`;

const SeverityBadge = styled.span<{ severity: AnomalySeverity }>`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  
  ${props => {
    switch(props.severity) {
      case AnomalySeverity.CRITICAL:
        return `
          background-color: #FF5555;
          color: #F8F8F2;
        `;
      case AnomalySeverity.HIGH:
        return `
          background-color: #FFB86C;
          color: #282A36;
        `;
      case AnomalySeverity.MEDIUM:
        return `
          background-color: #F1FA8C;
          color: #282A36;
        `;
      case AnomalySeverity.LOW:
        return `
          background-color: #8BE9FD;
          color: #282A36;
        `;
      default:
        return `
          background-color: #44475A;
          color: #F8F8F2;
        `;
    }
  }}
`;

const ActionButton = styled.button`
  padding: 8px 12px;
  background-color: #BD93F9;
  color: #282A36;
  border: none;
  border-radius: 4px;
  font-weight: 600;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #A580FF;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
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

// Данные для примера
const mockAnomalies: Anomaly[] = [
  {
    id: 'ANM-2024-001',
    title: 'Необычная сетевая активность',
    description: 'Обнаружено значительное увеличение исходящего трафика из внутренней сети',
    type: AnomalyType.TRAFFIC_SPIKE,
    severity: AnomalySeverity.HIGH,
    status: AnomalyStatus.NEW,
    detectedAt: '2024-05-15T14:23:00',
    zondId: 'ZND-045',
    zondName: 'Корпоративный кластер #3',
    sourceIp: '192.168.1.45',
    destinationIp: '45.67.89.123',
    protocol: 'TCP',
    port: 8080,
    metricName: 'outbound_traffic_rate',
    metricValue: 45.7,
    metricThreshold: 10
  },
  {
    id: 'ANM-2024-002',
    title: 'Подозрительный вход с неизвестного местоположения',
    description: 'Успешный вход в систему с IP-адреса, который никогда ранее не использовался',
    type: AnomalyType.UNUSUAL_LOGIN,
    severity: AnomalySeverity.MEDIUM,
    status: AnomalyStatus.INVESTIGATING,
    detectedAt: '2024-05-15T10:45:00',
    zondId: 'ZND-012',
    zondName: 'Сервер аутентификации',
    sourceIp: '78.90.123.45',
    destinationIp: '192.168.5.10',
    protocol: 'HTTPS',
    port: 443
  },
  {
    id: 'ANM-2024-003',
    title: 'Аномальное поведение процесса',
    description: 'Системный процесс выполняет нетипичные операции доступа к файлам',
    type: AnomalyType.BEHAVIOR_CHANGE,
    severity: AnomalySeverity.CRITICAL,
    status: AnomalyStatus.NEW,
    detectedAt: '2024-05-14T23:10:00',
    zondId: 'ZND-031',
    zondName: 'Файловый сервер',
    metricName: 'process_behavior_score',
    metricValue: 0.92,
    metricThreshold: 0.75,
    createdIncident: 'INC-2024-005'
  },
  {
    id: 'ANM-2024-004',
    title: 'Установление соединения с подозрительным доменом',
    description: 'Обнаружено соединение с доменом, связанным с известной вредоносной активностью',
    type: AnomalyType.NEW_CONNECTION,
    severity: AnomalySeverity.HIGH,
    status: AnomalyStatus.RESOLVED,
    detectedAt: '2024-05-14T16:30:00',
    zondId: 'ZND-027',
    zondName: 'Рабочая станция техподдержки',
    destinationIp: '203.0.113.100',
    protocol: 'DNS'
  },
  {
    id: 'ANM-2024-005',
    title: 'Необычная модель доступа к базе данных',
    description: 'Нетипичный объем запросов SELECT на таблицы с конфиденциальными данными',
    type: AnomalyType.DATA_EXFILTRATION,
    severity: AnomalySeverity.MEDIUM,
    status: AnomalyStatus.FALSE_POSITIVE,
    detectedAt: '2024-05-13T09:15:00',
    zondId: 'ZND-008',
    zondName: 'База данных клиентов',
    sourceIp: '192.168.2.34',
    metricName: 'sensitive_data_access_count',
    metricValue: 427,
    metricThreshold: 250
  },
  {
    id: 'ANM-2024-006',
    title: 'Повышение привилегий пользователя',
    description: 'Пользователь получил права администратора без запроса через стандартный процесс',
    type: AnomalyType.PRIVILEGE_ESCALATION,
    severity: AnomalySeverity.CRITICAL,
    status: AnomalyStatus.INVESTIGATING,
    detectedAt: '2024-05-12T15:40:00',
    zondId: 'ZND-003',
    zondName: 'Контроллер домена',
    sourceIp: '192.168.1.78',
    createdIncident: 'INC-2024-004'
  }
];

const AnomalyDetectionPage: React.FC = () => {
  const navigate = useNavigate();
  const [anomalies, setAnomalies] = useState<Anomaly[]>(mockAnomalies);
  const [filteredAnomalies, setFilteredAnomalies] = useState<Anomaly[]>(anomalies);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [severityFilter, setSeverityFilter] = useState('all');
  const [typeFilter, setTypeFilter] = useState('all');

  // Применение фильтров при изменении данных
  useEffect(() => {
    let result = anomalies;
    
    // Поиск по названию и ID
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(anomaly => 
        anomaly.title.toLowerCase().includes(query) || 
        anomaly.id.toLowerCase().includes(query) ||
        (anomaly.zondName && anomaly.zondName.toLowerCase().includes(query))
      );
    }
    
    // Фильтрация по статусу
    if (statusFilter !== 'all') {
      result = result.filter(anomaly => anomaly.status === statusFilter);
    }
    
    // Фильтрация по важности
    if (severityFilter !== 'all') {
      result = result.filter(anomaly => anomaly.severity === severityFilter);
    }
    
    // Фильтрация по типу
    if (typeFilter !== 'all') {
      result = result.filter(anomaly => anomaly.type === typeFilter);
    }
    
    setFilteredAnomalies(result);
  }, [anomalies, searchQuery, statusFilter, severityFilter, typeFilter]);

  // Подсчет статистики
  const totalAnomalies = anomalies.length;
  const newAnomalies = anomalies.filter(a => a.status === AnomalyStatus.NEW).length;
  const criticalAnomalies = anomalies.filter(a => a.severity === AnomalySeverity.CRITICAL).length;
  const investigatingAnomalies = anomalies.filter(a => a.status === AnomalyStatus.INVESTIGATING).length;

  // Обработчик перехода к деталям аномалии
  const handleAnomalyClick = (id: string) => {
    navigate(`/anomalies/${id}`);
  };

  // Обработчик создания инцидента
  const handleCreateIncident = (anomalyId: string, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation(); // Предотвращаем переход на страницу деталей при клике на кнопку
    }
    
    console.log(`Создание инцидента для аномалии: ${anomalyId}`);
    // Здесь будет логика создания инцидента из аномалии
    const updatedAnomalies = anomalies.map(anomaly => {
      if (anomaly.id === anomalyId) {
        return {
          ...anomaly,
          status: AnomalyStatus.INVESTIGATING,
          createdIncident: `INC-2024-${Math.floor(Math.random() * 1000).toString().padStart(3, '0')}`
        };
      }
      return anomaly;
    });
    
    setAnomalies(updatedAnomalies);
  };

  // Обработчик изменения статуса
  const handleStatusChange = (anomalyId: string, newStatus: AnomalyStatus, event?: React.MouseEvent) => {
    if (event) {
      event.stopPropagation(); // Предотвращаем переход на страницу деталей при клике на кнопку
    }
    
    console.log(`Изменение статуса для аномалии ${anomalyId} на ${newStatus}`);
    // Здесь будет логика изменения статуса аномалии
    const updatedAnomalies = anomalies.map(anomaly => {
      if (anomaly.id === anomalyId) {
        return { ...anomaly, status: newStatus };
      }
      return anomaly;
    });
    
    setAnomalies(updatedAnomalies);
  };

  return (
    <PageContainer>
      <Header>
        <Title>Обнаружение аномалий</Title>
      </Header>

      {/* Статистика */}
      <StatsContainer>
        <StatCard color="#BD93F9">
          <h3>Всего аномалий</h3>
          <p>{totalAnomalies}</p>
        </StatCard>
        <StatCard color="#FF5555">
          <h3>Новые</h3>
          <p>{newAnomalies}</p>
        </StatCard>
        <StatCard color="#FFB86C">
          <h3>В расследовании</h3>
          <p>{investigatingAnomalies}</p>
        </StatCard>
        <StatCard color="#FF5555">
          <h3>Критические</h3>
          <p>{criticalAnomalies}</p>
        </StatCard>
      </StatsContainer>

      {/* Фильтры */}
      <FiltersContainer>
        <SearchInput 
          placeholder="Поиск по названию, ID или зонду..." 
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        
        <FilterGroup>
          <FilterLabel>Статус</FilterLabel>
          <Select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
            <option value="all">Все статусы</option>
            <option value={AnomalyStatus.NEW}>Новые</option>
            <option value={AnomalyStatus.INVESTIGATING}>Расследование</option>
            <option value={AnomalyStatus.RESOLVED}>Решенные</option>
            <option value={AnomalyStatus.FALSE_POSITIVE}>Ложные срабатывания</option>
          </Select>
        </FilterGroup>
        
        <FilterGroup>
          <FilterLabel>Важность</FilterLabel>
          <Select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)}>
            <option value="all">Все уровни</option>
            <option value={AnomalySeverity.CRITICAL}>Критическая</option>
            <option value={AnomalySeverity.HIGH}>Высокая</option>
            <option value={AnomalySeverity.MEDIUM}>Средняя</option>
            <option value={AnomalySeverity.LOW}>Низкая</option>
          </Select>
        </FilterGroup>
        
        <FilterGroup>
          <FilterLabel>Тип</FilterLabel>
          <Select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
            <option value="all">Все типы</option>
            <option value={AnomalyType.TRAFFIC_SPIKE}>Скачок трафика</option>
            <option value={AnomalyType.BEHAVIOR_CHANGE}>Изменение поведения</option>
            <option value={AnomalyType.NEW_CONNECTION}>Новое соединение</option>
            <option value={AnomalyType.UNUSUAL_LOGIN}>Необычный вход</option>
            <option value={AnomalyType.DATA_EXFILTRATION}>Утечка данных</option>
            <option value={AnomalyType.PRIVILEGE_ESCALATION}>Повышение привилегий</option>
            <option value={AnomalyType.OTHER}>Другое</option>
          </Select>
        </FilterGroup>
      </FiltersContainer>

      {/* Таблица аномалий */}
      {filteredAnomalies.length > 0 ? (
        <AnomaliesTable>
          <TableHead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th>Тип</th>
              <th>Важность</th>
              <th>Статус</th>
              <th>Зонд</th>
              <th>Обнаружено</th>
              <th>Действия</th>
            </tr>
          </TableHead>
          <TableBody>
            {filteredAnomalies.map((anomaly) => (
              <tr key={anomaly.id} onClick={() => handleAnomalyClick(anomaly.id)}>
                <td>{anomaly.id}</td>
                <td>{anomaly.title}</td>
                <td>{ANOMALY_TYPE_NAMES[anomaly.type]}</td>
                <td>
                  <SeverityBadge severity={anomaly.severity}>
                    {ANOMALY_SEVERITY_NAMES[anomaly.severity]}
                  </SeverityBadge>
                </td>
                <td>
                  <StatusBadge status={anomaly.status}>
                    {ANOMALY_STATUS_NAMES[anomaly.status]}
                  </StatusBadge>
                </td>
                <td>{anomaly.zondName || '-'}</td>
                <td>{formatDate(anomaly.detectedAt)}</td>
                <td onClick={(e) => e.stopPropagation()}>
                  {!anomaly.createdIncident && anomaly.status !== AnomalyStatus.FALSE_POSITIVE && (
                    <ActionButton onClick={(e) => handleCreateIncident(anomaly.id, e)}>
                      Создать инцидент
                    </ActionButton>
                  )}
                  {anomaly.status === AnomalyStatus.NEW && (
                    <ActionButton 
                      onClick={(e) => handleStatusChange(anomaly.id, AnomalyStatus.INVESTIGATING, e)}
                      style={{ marginLeft: '8px', backgroundColor: '#FFB86C' }}
                    >
                      Расследовать
                    </ActionButton>
                  )}
                  {(anomaly.status === AnomalyStatus.NEW || anomaly.status === AnomalyStatus.INVESTIGATING) && (
                    <ActionButton 
                      onClick={(e) => handleStatusChange(anomaly.id, AnomalyStatus.FALSE_POSITIVE, e)}
                      style={{ marginLeft: '8px', backgroundColor: '#6272A4' }}
                    >
                      Ложная тревога
                    </ActionButton>
                  )}
                </td>
              </tr>
            ))}
          </TableBody>
        </AnomaliesTable>
      ) : (
        <EmptyState>
          <h3>Аномалии не найдены</h3>
          <p>По указанным критериям не найдено ни одной аномалии</p>
        </EmptyState>
      )}
    </PageContainer>
  );
};

export default AnomalyDetectionPage; 