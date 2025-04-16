import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import styled from 'styled-components';
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

// Styled components
const Container = styled.div`
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  flex-wrap: wrap;
  gap: 16px;
`;

const BackButton = styled.button`
  padding: 8px 16px;
  background-color: #44475A;
  color: #F8F8F2;
  border: none;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  
  &:hover {
    background-color: #6272A4;
  }
`;

const TitleArea = styled.div`
  flex: 1;
`;

const Title = styled.h1`
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #F8F8F2;
`;

const AnomalyId = styled.div`
  font-size: 14px;
  color: #6C7293;
  margin-bottom: 8px;
`;

const BadgesContainer = styled.div`
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
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

const TypeBadge = styled.span`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background-color: #6272A4;
  color: #F8F8F2;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
`;

const Button = styled.button<{ variant?: 'primary' | 'secondary' | 'danger' }>`
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  
  ${props => {
    switch(props.variant) {
      case 'primary':
        return `
          background-color: #BD93F9;
          color: #282A36;
        `;
      case 'danger':
        return `
          background-color: #FF5555;
          color: #F8F8F2;
        `;
      case 'secondary':
      default:
        return `
          background-color: #44475A;
          color: #F8F8F2;
        `;
    }
  }}
  
  &:hover {
    opacity: 0.9;
  }
`;

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`;

const Section = styled.div`
  background-color: #282A36;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 24px;
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #F8F8F2;
  border-bottom: 1px solid #44475A;
  padding-bottom: 8px;
`;

const Description = styled.p`
  margin-bottom: 16px;
  line-height: 1.6;
  color: #F8F8F2;
  white-space: pre-line;
`;

const DetailsList = styled.dl`
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px 16px;
`;

const DetailTerm = styled.dt`
  font-weight: 500;
  color: #6C7293;
`;

const DetailValue = styled.dd`
  margin: 0;
  color: #F8F8F2;
`;

// Mock data
const mockAnomalies: Record<string, Anomaly> = {
  'ANM-2024-001': {
    id: 'ANM-2024-001',
    title: 'Необычная сетевая активность',
    description: 'Обнаружено значительное увеличение исходящего трафика из внутренней сети. Пакеты отправляются на внешний IP, связанный с известными C2-серверами.\n\nАвтоматический анализ пакетов показывает признаки обфускации данных и необычный паттерн передачи.',
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
  'ANM-2024-002': {
    id: 'ANM-2024-002',
    title: 'Подозрительный вход с неизвестного местоположения',
    description: 'Успешный вход в систему с IP-адреса, который никогда ранее не использовался пользователем admin. Геолокация IP указывает на восточноевропейский регион, что не соответствует обычному месту работы сотрудника.\n\nВремя входа - 3:45 утра по местному времени, что также является аномальным.',
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
  }
};

const AnomalyDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [anomaly, setAnomaly] = useState<Anomaly | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // В реальном приложении здесь будет запрос к API
    setLoading(true);
    
    // Имитация API запроса
    setTimeout(() => {
      if (id && mockAnomalies[id]) {
        setAnomaly(mockAnomalies[id]);
        setLoading(false);
      } else {
        setError('Аномалия не найдена');
        setLoading(false);
      }
    }, 500);
  }, [id]);

  const handleBack = () => {
    navigate('/anomalies');
  };

  const handleCreateIncident = () => {
    if (!anomaly) return;
    
    // В реальном приложении здесь будет API запрос для создания инцидента
    console.log('Создание инцидента из аномалии:', anomaly.id);
    navigate('/incidents/new');
  };

  const handleStatusChange = (newStatus: AnomalyStatus) => {
    if (!anomaly) return;
    
    // В реальном приложении здесь будет API запрос для изменения статуса
    console.log(`Изменение статуса аномалии ${anomaly.id} на ${newStatus}`);
    setAnomaly({ ...anomaly, status: newStatus });
  };

  if (loading) {
    return (
      <Container>
        <p>Загрузка данных...</p>
      </Container>
    );
  }

  if (error || !anomaly) {
    return (
      <Container>
        <p>{error || 'Произошла ошибка при загрузке данных'}</p>
        <BackButton onClick={handleBack}>Вернуться к списку аномалий</BackButton>
      </Container>
    );
  }

  return (
    <Container>
      <Header>
        <BackButton onClick={handleBack}>← Назад к списку</BackButton>
        
        <ActionButtons>
          {!anomaly.createdIncident && (
            <Button variant="primary" onClick={handleCreateIncident}>
              Создать инцидент
            </Button>
          )}
          
          {anomaly.status === AnomalyStatus.NEW && (
            <Button 
              onClick={() => handleStatusChange(AnomalyStatus.INVESTIGATING)}
              style={{ backgroundColor: '#FFB86C', color: '#282A36' }}
            >
              Начать расследование
            </Button>
          )}
          
          {anomaly.status !== AnomalyStatus.RESOLVED && anomaly.status !== AnomalyStatus.FALSE_POSITIVE && (
            <Button 
              onClick={() => handleStatusChange(AnomalyStatus.RESOLVED)}
              style={{ backgroundColor: '#50FA7B', color: '#282A36' }}
            >
              Отметить как решенную
            </Button>
          )}
          
          {anomaly.status !== AnomalyStatus.FALSE_POSITIVE && (
            <Button 
              onClick={() => handleStatusChange(AnomalyStatus.FALSE_POSITIVE)}
              style={{ backgroundColor: '#6272A4' }}
            >
              Ложная тревога
            </Button>
          )}
        </ActionButtons>
      </Header>

      <TitleArea>
        <AnomalyId>{anomaly.id}</AnomalyId>
        <Title>{anomaly.title}</Title>
        
        <BadgesContainer>
          <StatusBadge status={anomaly.status}>
            {ANOMALY_STATUS_NAMES[anomaly.status]}
          </StatusBadge>
          <SeverityBadge severity={anomaly.severity}>
            {ANOMALY_SEVERITY_NAMES[anomaly.severity]}
          </SeverityBadge>
          <TypeBadge>{ANOMALY_TYPE_NAMES[anomaly.type]}</TypeBadge>
        </BadgesContainer>
      </TitleArea>

      <ContentGrid>
        <div>
          <Section>
            <SectionTitle>Описание</SectionTitle>
            <Description>{anomaly.description}</Description>
          </Section>

          {anomaly.metricName && anomaly.metricValue && (
            <Section>
              <SectionTitle>Метрики</SectionTitle>
              <DetailsList>
                <DetailTerm>Метрика</DetailTerm>
                <DetailValue>{anomaly.metricName}</DetailValue>
                
                <DetailTerm>Значение</DetailTerm>
                <DetailValue>{anomaly.metricValue}</DetailValue>
                
                <DetailTerm>Порог</DetailTerm>
                <DetailValue>{anomaly.metricThreshold}</DetailValue>
                
                <DetailTerm>Превышение</DetailTerm>
                <DetailValue>
                  {anomaly.metricThreshold
                    ? `${((anomaly.metricValue / anomaly.metricThreshold) * 100 - 100).toFixed(1)}%`
                    : 'N/A'}
                </DetailValue>
              </DetailsList>
            </Section>
          )}
        </div>

        <div>
          <Section>
            <SectionTitle>Информация</SectionTitle>
            <DetailsList>
              {anomaly.zondName && (
                <>
                  <DetailTerm>Зонд</DetailTerm>
                  <DetailValue>{anomaly.zondName} ({anomaly.zondId})</DetailValue>
                </>
              )}
              
              <DetailTerm>Обнаружено</DetailTerm>
              <DetailValue>{formatDate(anomaly.detectedAt)}</DetailValue>
              
              {anomaly.sourceIp && (
                <>
                  <DetailTerm>IP источника</DetailTerm>
                  <DetailValue>{anomaly.sourceIp}</DetailValue>
                </>
              )}
              
              {anomaly.destinationIp && (
                <>
                  <DetailTerm>IP назначения</DetailTerm>
                  <DetailValue>{anomaly.destinationIp}</DetailValue>
                </>
              )}
              
              {anomaly.protocol && (
                <>
                  <DetailTerm>Протокол</DetailTerm>
                  <DetailValue>{anomaly.protocol}</DetailValue>
                </>
              )}
              
              {anomaly.port && (
                <>
                  <DetailTerm>Порт</DetailTerm>
                  <DetailValue>{anomaly.port}</DetailValue>
                </>
              )}
              
              {anomaly.createdIncident && (
                <>
                  <DetailTerm>Связанный инцидент</DetailTerm>
                  <DetailValue>{anomaly.createdIncident}</DetailValue>
                </>
              )}
            </DetailsList>
          </Section>
        </div>
      </ContentGrid>
    </Container>
  );
};

export default AnomalyDetailsPage; 