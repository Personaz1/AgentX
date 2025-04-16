import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { MapContainer, TileLayer, Marker, Popup, Circle } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import { IncidentType, IncidentSeverity, IncidentStatus } from '../types';

// Фикс для иконок Leaflet
// @ts-ignore
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

// Интерфейсы
interface IncidentLocation {
  id: string;
  title: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  type: IncidentType;
  lat: number;
  lng: number;
  address?: string;
  detectedDate: string;
  affectedSystems?: string[];
  impactRadius?: number; // радиус влияния в метрах, для визуализации на карте
}

// Стилизованные компоненты
const Container = styled.div`
  padding: 24px;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const Title = styled.h1`
  font-size: 28px;
  font-weight: 700;
  margin: 0;
  color: #F8F8F2;
`;

const FiltersContainer = styled.div`
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
`;

const Select = styled.select`
  background-color: #282A36;
  border: 1px solid #44475A;
  color: #F8F8F2;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  
  &:focus {
    outline: none;
    border-color: #BD93F9;
  }
`;

const MapWrapper = styled.div`
  flex: 1;
  .leaflet-container {
    height: 100%;
    border-radius: 8px;
  }
`;

const Legend = styled.div`
  position: absolute;
  bottom: 30px;
  right: 30px;
  z-index: 1000;
  background-color: rgba(40, 42, 54, 0.9);
  padding: 12px;
  border-radius: 6px;
  color: #F8F8F2;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
`;

const LegendItem = styled.div`
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const LegendColor = styled.div<{ color: string }>`
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background-color: ${props => props.color};
  margin-right: 8px;
`;

const InfoPane = styled.div`
  position: absolute;
  top: 100px;
  right: 30px;
  z-index: 1000;
  background-color: rgba(40, 42, 54, 0.9);
  padding: 16px;
  border-radius: 6px;
  color: #F8F8F2;
  min-width: 250px;
  max-width: 300px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
`;

const InfoTitle = styled.h3`
  margin-top: 0;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
`;

const InfoStats = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
`;

const StatItem = styled.div`
  display: flex;
  flex-direction: column;
`;

const StatValue = styled.span`
  font-size: 18px;
  font-weight: 700;
`;

const StatLabel = styled.span`
  font-size: 12px;
  color: #6C7293;
`;

// Функции-помощники
const getSeverityColor = (severity: IncidentSeverity): string => {
  switch (severity) {
    case IncidentSeverity.CRITICAL:
      return '#FF5555';
    case IncidentSeverity.HIGH:
      return '#FFB86C';
    case IncidentSeverity.MEDIUM:
      return '#F1FA8C';
    case IncidentSeverity.LOW:
      return '#50FA7B';
    default:
      return '#BD93F9';
  }
};

const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleString('ru-RU', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// Мокап данных
const mockIncidentLocations: IncidentLocation[] = [
  {
    id: 'inc-001',
    title: 'DDoS атака на основной сервер',
    status: IncidentStatus.INVESTIGATING,
    severity: IncidentSeverity.HIGH,
    type: IncidentType.DDOS,
    lat: 55.755826,
    lng: 37.617300,
    address: 'Москва, ЦОД Кремлин',
    detectedDate: '2023-06-15T08:23:15',
    affectedSystems: ['Веб-сервер', 'Балансировщик'],
    impactRadius: 2000
  },
  {
    id: 'inc-002',
    title: 'Несанкционированный доступ',
    status: IncidentStatus.MITIGATING,
    severity: IncidentSeverity.CRITICAL,
    type: IncidentType.UNAUTHORIZED_ACCESS,
    lat: 59.939099,
    lng: 30.315877,
    address: 'Санкт-Петербург, Офис Восток',
    detectedDate: '2023-06-14T22:15:30',
    affectedSystems: ['БД пользователей', 'Платежная система'],
    impactRadius: 1500
  },
  {
    id: 'inc-003',
    title: 'Заражение вредоносным ПО',
    status: IncidentStatus.NEW,
    severity: IncidentSeverity.MEDIUM,
    type: IncidentType.MALWARE,
    lat: 56.838011,
    lng: 60.597474,
    address: 'Екатеринбург, Офис Регион',
    detectedDate: '2023-06-16T10:05:12',
    affectedSystems: ['Рабочие станции'],
    impactRadius: 1000
  },
  {
    id: 'inc-004',
    title: 'Фишинговая атака',
    status: IncidentStatus.RESOLVED,
    severity: IncidentSeverity.LOW,
    type: IncidentType.PHISHING,
    lat: 54.989342,
    lng: 73.368212,
    address: 'Омск, Филиал Сибирь',
    detectedDate: '2023-06-13T14:33:20',
    affectedSystems: ['Почтовые сервисы'],
    impactRadius: 800
  },
  {
    id: 'inc-005',
    title: 'Взлом корпоративной сети',
    status: IncidentStatus.INVESTIGATING,
    severity: IncidentSeverity.HIGH,
    type: IncidentType.NETWORK_INTRUSION,
    lat: 43.585472,
    lng: 39.723098,
    address: 'Сочи, Датацентр Юг',
    detectedDate: '2023-06-15T19:41:05',
    affectedSystems: ['Маршрутизаторы', 'Внутренняя сеть'],
    impactRadius: 1800
  }
];

const IncidentMapPage: React.FC = () => {
  const [incidents, setIncidents] = useState<IncidentLocation[]>(mockIncidentLocations);
  const [filteredIncidents, setFilteredIncidents] = useState<IncidentLocation[]>(incidents);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [selectedIncident, setSelectedIncident] = useState<IncidentLocation | null>(null);
  
  // Центр карты России
  const mapCenter: [number, number] = [55.755826, 37.617300];
  
  // Применение фильтров при изменении данных
  useEffect(() => {
    let result = incidents;
    
    // Фильтрация по статусу
    if (statusFilter) {
      result = result.filter(incident => incident.status === statusFilter);
    }
    
    // Фильтрация по уровню критичности
    if (severityFilter) {
      result = result.filter(incident => incident.severity === severityFilter);
    }
    
    // Фильтрация по типу
    if (typeFilter) {
      result = result.filter(incident => incident.type === typeFilter);
    }
    
    setFilteredIncidents(result);
  }, [incidents, statusFilter, severityFilter, typeFilter]);
  
  // Функция для подсчета статистики
  const getStats = () => {
    return {
      total: incidents.length,
      critical: incidents.filter(inc => inc.severity === IncidentSeverity.CRITICAL).length,
      high: incidents.filter(inc => inc.severity === IncidentSeverity.HIGH).length,
      medium: incidents.filter(inc => inc.severity === IncidentSeverity.MEDIUM).length,
      low: incidents.filter(inc => inc.severity === IncidentSeverity.LOW).length,
      active: incidents.filter(inc => inc.status !== IncidentStatus.RESOLVED && inc.status !== IncidentStatus.CLOSED).length
    };
  };
  
  const stats = getStats();
  
  return (
    <Container>
      <Header>
        <Title>Карта инцидентов</Title>
      </Header>
      
      <FiltersContainer>
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
          <option value="">Все уровни важности</option>
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
      
      <MapWrapper>
        <MapContainer 
          center={mapCenter} 
          zoom={4} 
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          {filteredIncidents.map(incident => (
            <React.Fragment key={incident.id}>
              <Marker 
                position={[incident.lat, incident.lng]}
                eventHandlers={{
                  click: () => setSelectedIncident(incident)
                }}
              >
                <Popup>
                  <strong>{incident.title}</strong><br />
                  Статус: {incident.status}<br />
                  Важность: {incident.severity}<br />
                  Тип: {incident.type}<br />
                  {incident.address && <>Адрес: {incident.address}<br /></>}
                  Обнаружен: {formatDate(incident.detectedDate)}
                </Popup>
              </Marker>
              
              {incident.impactRadius && (
                <Circle 
                  center={[incident.lat, incident.lng]} 
                  radius={incident.impactRadius}
                  pathOptions={{
                    color: getSeverityColor(incident.severity),
                    fillColor: getSeverityColor(incident.severity),
                    fillOpacity: 0.2
                  }}
                />
              )}
            </React.Fragment>
          ))}
        </MapContainer>
        
        <Legend>
          <div style={{ marginBottom: '8px', fontWeight: 'bold' }}>Важность инцидентов:</div>
          <LegendItem>
            <LegendColor color={getSeverityColor(IncidentSeverity.CRITICAL)} />
            <span>Критическая</span>
          </LegendItem>
          <LegendItem>
            <LegendColor color={getSeverityColor(IncidentSeverity.HIGH)} />
            <span>Высокая</span>
          </LegendItem>
          <LegendItem>
            <LegendColor color={getSeverityColor(IncidentSeverity.MEDIUM)} />
            <span>Средняя</span>
          </LegendItem>
          <LegendItem>
            <LegendColor color={getSeverityColor(IncidentSeverity.LOW)} />
            <span>Низкая</span>
          </LegendItem>
        </Legend>
        
        <InfoPane>
          <InfoTitle>Статистика инцидентов</InfoTitle>
          <InfoStats>
            <StatItem>
              <StatValue>{stats.total}</StatValue>
              <StatLabel>Всего</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>{stats.active}</StatValue>
              <StatLabel>Активных</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>{stats.critical}</StatValue>
              <StatLabel>Критических</StatLabel>
            </StatItem>
            <StatItem>
              <StatValue>{stats.high}</StatValue>
              <StatLabel>Высоких</StatLabel>
            </StatItem>
          </InfoStats>
        </InfoPane>
        
        {selectedIncident && (
          <div style={{ 
            position: 'absolute', 
            top: '100px', 
            left: '30px', 
            zIndex: 1000,
            backgroundColor: 'rgba(40, 42, 54, 0.9)',
            padding: '16px',
            borderRadius: '8px',
            color: '#F8F8F2',
            maxWidth: '350px',
            boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)'
          }}>
            <h3 style={{ marginTop: 0 }}>{selectedIncident.title}</h3>
            <div style={{ 
              display: 'flex', 
              gap: '8px', 
              marginBottom: '12px' 
            }}>
              <span style={{ 
                padding: '4px 8px', 
                borderRadius: '4px',
                backgroundColor: getSeverityColor(selectedIncident.severity),
                fontSize: '12px',
                fontWeight: 'bold'
              }}>
                {selectedIncident.severity}
              </span>
              <span style={{ 
                padding: '4px 8px', 
                borderRadius: '4px',
                backgroundColor: '#6272A4',
                fontSize: '12px'
              }}>
                {selectedIncident.status}
              </span>
              <span style={{ 
                padding: '4px 8px', 
                borderRadius: '4px',
                backgroundColor: '#44475A',
                fontSize: '12px'
              }}>
                {selectedIncident.type}
              </span>
            </div>
            
            {selectedIncident.address && (
              <div style={{ marginBottom: '8px' }}>
                <strong>Адрес:</strong> {selectedIncident.address}
              </div>
            )}
            
            <div style={{ marginBottom: '8px' }}>
              <strong>Обнаружен:</strong> {formatDate(selectedIncident.detectedDate)}
            </div>
            
            {selectedIncident.affectedSystems && selectedIncident.affectedSystems.length > 0 && (
              <div>
                <strong>Затронутые системы:</strong>
                <div style={{ 
                  display: 'flex', 
                  flexWrap: 'wrap', 
                  gap: '6px',
                  marginTop: '6px'
                }}>
                  {selectedIncident.affectedSystems.map((system, index) => (
                    <span key={index} style={{ 
                      padding: '4px 8px', 
                      borderRadius: '4px',
                      backgroundColor: '#44475A',
                      fontSize: '12px'
                    }}>
                      {system}
                    </span>
                  ))}
                </div>
              </div>
            )}
            
            <button 
              onClick={() => setSelectedIncident(null)}
              style={{
                marginTop: '16px',
                padding: '8px 16px',
                backgroundColor: '#6272A4',
                color: '#F8F8F2',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Закрыть
            </button>
          </div>
        )}
      </MapWrapper>
    </Container>
  );
};

export default IncidentMapPage; 