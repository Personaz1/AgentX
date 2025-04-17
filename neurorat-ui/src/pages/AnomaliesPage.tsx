import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { useNavigate } from 'react-router-dom';
import AnomalyList from '../components/anomalies/AnomalyList';
import { 
  Anomaly, 
  AnomalyStats, 
  AnomalyStatus, 
  AnomalySeverity, 
  ANOMALY_STATUS_NAMES, 
  ANOMALY_SEVERITY_NAMES 
} from '../types/anomaly';
import { anomalyService } from '../services/api';
import { darkTheme } from '../theme';

const Container = styled.div`
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 24px;
  color: ${darkTheme.text.primary};
  margin: 0;
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
`;

const StatCard = styled.div`
  background-color: ${darkTheme.bg.secondary};
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const StatTitle = styled.div`
  font-size: 14px;
  color: ${darkTheme.text.secondary};
  margin-bottom: 8px;
`;

const StatValue = styled.div`
  font-size: 24px;
  font-weight: 600;
  color: ${darkTheme.text.primary};
`;

const SeverityStatsContainer = styled.div`
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
`;

const SeverityStatItem = styled.div<{ severity: AnomalySeverity }>`
  display: flex;
  flex-direction: column;
  align-items: center;
`;

const SeverityCircle = styled.div<{ severity: AnomalySeverity, count: number }>`
  width: ${props => Math.max(20, Math.min(40, 20 + props.count * 3))}px;
  height: ${props => Math.max(20, Math.min(40, 20 + props.count * 3))}px;
  border-radius: 50%;
  background-color: ${props => {
    switch (props.severity) {
      case AnomalySeverity.CRITICAL: return '#E53E3E';
      case AnomalySeverity.HIGH: return '#DD6B20';
      case AnomalySeverity.MEDIUM: return '#D69E2E';
      case AnomalySeverity.LOW: return '#38A169';
      default: return '#718096';
    }
  }};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 12px;
`;

const SeverityLabel = styled.div`
  font-size: 10px;
  color: ${darkTheme.text.secondary};
  margin-top: 4px;
`;

const LoadingContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
  width: 100%;
`;

const ErrorContainer = styled.div`
  padding: 16px;
  background-color: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  color: #E53E3E;
  margin-bottom: 24px;
`;

const AnomaliesPage: React.FC = () => {
  const navigate = useNavigate();
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [stats, setStats] = useState<AnomalyStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const [anomaliesData, statsData] = await Promise.all([
          anomalyService.getAnomalies(),
          anomalyService.getAnomalyStats()
        ]);
        
        setAnomalies(anomaliesData);
        setStats(statsData);
      } catch (err) {
        console.error('Ошибка при загрузке данных об аномалиях:', err);
        setError('Не удалось загрузить данные. Пожалуйста, попробуйте позже.');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleStatusChange = async (anomalyId: string, newStatus: AnomalyStatus) => {
    try {
      await anomalyService.updateAnomalyStatus(anomalyId, newStatus);
      
      // Обновляем локальное состояние
      setAnomalies(prev => 
        prev.map(anomaly => 
          anomaly.id === anomalyId 
            ? { ...anomaly, status: newStatus } 
            : anomaly
        )
      );
      
      // Обновляем статистику
      const statsData = await anomalyService.getAnomalyStats();
      setStats(statsData);
    } catch (err) {
      console.error('Ошибка при обновлении статуса аномалии:', err);
      setError('Не удалось обновить статус. Пожалуйста, попробуйте позже.');
    }
  };

  const handleCreateIncident = async (anomalyId: string) => {
    try {
      const result = await anomalyService.createIncidentFromAnomaly(anomalyId);
      if (result.success) {
        navigate(`/incidents/${result.incidentId}`);
      }
    } catch (err) {
      console.error('Ошибка при создании инцидента:', err);
      setError('Не удалось создать инцидент. Пожалуйста, попробуйте позже.');
    }
  };

  if (loading) {
    return (
      <Container>
        <Header>
          <Title>Аномалии</Title>
        </Header>
        <LoadingContainer>
          <div>Загрузка данных...</div>
        </LoadingContainer>
      </Container>
    );
  }

  return (
    <Container>
      <Header>
        <Title>Аномалии</Title>
      </Header>
      
      {error && <ErrorContainer>{error}</ErrorContainer>}
      
      {stats && (
        <StatsContainer>
          <StatCard>
            <StatTitle>Всего аномалий</StatTitle>
            <StatValue>{stats.total}</StatValue>
          </StatCard>
          
          <StatCard>
            <StatTitle>Новые</StatTitle>
            <StatValue>{stats.byStatus[AnomalyStatus.NEW]}</StatValue>
          </StatCard>
          
          <StatCard>
            <StatTitle>В расследовании</StatTitle>
            <StatValue>{stats.byStatus[AnomalyStatus.INVESTIGATING]}</StatValue>
          </StatCard>
          
          <StatCard>
            <StatTitle>Решенные</StatTitle>
            <StatValue>{stats.byStatus[AnomalyStatus.RESOLVED]}</StatValue>
          </StatCard>
          
          <StatCard>
            <StatTitle>Ложные срабатывания</StatTitle>
            <StatValue>{stats.byStatus[AnomalyStatus.FALSE_POSITIVE]}</StatValue>
          </StatCard>
          
          <StatCard>
            <StatTitle>По степени серьезности</StatTitle>
            <SeverityStatsContainer>
              {Object.values(AnomalySeverity).map(severity => (
                <SeverityStatItem key={severity} severity={severity}>
                  <SeverityCircle severity={severity} count={stats.bySeverity[severity]}>
                    {stats.bySeverity[severity]}
                  </SeverityCircle>
                  <SeverityLabel>{ANOMALY_SEVERITY_NAMES[severity]}</SeverityLabel>
                </SeverityStatItem>
              ))}
            </SeverityStatsContainer>
          </StatCard>
        </StatsContainer>
      )}
      
      <AnomalyList 
        anomalies={anomalies} 
        onStatusChange={handleStatusChange}
        onCreateIncident={handleCreateIncident}
      />
    </Container>
  );
};

export default AnomaliesPage; 