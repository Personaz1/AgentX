import React from 'react';
import styled from 'styled-components';
import { Anomaly, AnomalyStatus, AnomalySeverity, AnomalyType, ANOMALY_STATUS_NAMES, ANOMALY_SEVERITY_NAMES, ANOMALY_TYPE_NAMES, formatDate } from '../../types/anomaly';

export interface AnomalyCardProps {
  anomaly: Anomaly;
  onClick?: (anomaly: Anomaly) => void;
}

// Компоненты стилей
const Card = styled.div`
  display: flex;
  flex-direction: column;
  padding: 16px;
  border-radius: 8px;
  background-color: #1A1A2E;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border-left: 4px solid ${(props: { severity: AnomalySeverity }) => {
    switch (props.severity) {
      case AnomalySeverity.CRITICAL: return '#E53E3E';
      case AnomalySeverity.HIGH: return '#DD6B20';
      case AnomalySeverity.MEDIUM: return '#D69E2E';
      case AnomalySeverity.LOW: return '#38A169';
      default: return '#718096';
    }
  }};

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
  }
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
`;

const Title = styled.h3`
  font-size: 18px;
  font-weight: 600;
  color: #E2E8F0;
  margin: 0;
  flex: 1;
`;

const StatusBadge = styled.span`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background-color: ${(props: { status: AnomalyStatus }) => {
    switch (props.status) {
      case AnomalyStatus.NEW: return '#4A5568';
      case AnomalyStatus.INVESTIGATING: return '#3182CE';
      case AnomalyStatus.RESOLVED: return '#38A169';
      case AnomalyStatus.FALSE_POSITIVE: return '#718096';
      default: return '#718096';
    }
  }};
  color: white;
  margin-left: 8px;
`;

const TypeBadge = styled.span`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background-color: #2D3748;
  color: white;
  margin-right: 8px;
`;

const Description = styled.p`
  font-size: 14px;
  color: #A0AEC0;
  margin: 8px 0 12px;
  line-height: 1.4;
`;

const MetaInfo = styled.div`
  display: flex;
  flex-wrap: wrap;
  margin-top: 8px;
`;

const MetaItem = styled.div`
  display: flex;
  align-items: center;
  font-size: 12px;
  color: #CBD5E0;
  margin-right: 16px;
  margin-bottom: 4px;
`;

const MetaLabel = styled.span`
  color: #718096;
  margin-right: 4px;
`;

const AnomalyCard: React.FC<AnomalyCardProps> = ({ anomaly, onClick }) => {
  const handleClick = () => {
    if (onClick) {
      onClick(anomaly);
    }
  };

  return (
    <Card severity={anomaly.severity} onClick={handleClick}>
      <Header>
        <Title>{anomaly.title}</Title>
        <StatusBadge status={anomaly.status}>
          {ANOMALY_STATUS_NAMES[anomaly.status]}
        </StatusBadge>
      </Header>
      
      <div>
        <TypeBadge>{ANOMALY_TYPE_NAMES[anomaly.type]}</TypeBadge>
        <StatusBadge status={anomaly.status} style={{ backgroundColor: 'transparent' }}>
          {ANOMALY_SEVERITY_NAMES[anomaly.severity]}
        </StatusBadge>
      </div>
      
      {anomaly.description && (
        <Description>{anomaly.description}</Description>
      )}
      
      <MetaInfo>
        <MetaItem>
          <MetaLabel>Обнаружено:</MetaLabel>
          {formatDate(anomaly.detectedAt)}
        </MetaItem>
        
        {anomaly.zondName && (
          <MetaItem>
            <MetaLabel>Зонд:</MetaLabel>
            {anomaly.zondName}
          </MetaItem>
        )}
        
        {anomaly.sourceIp && (
          <MetaItem>
            <MetaLabel>Источник:</MetaLabel>
            {anomaly.sourceIp}
          </MetaItem>
        )}
        
        {anomaly.destinationIp && (
          <MetaItem>
            <MetaLabel>Назначение:</MetaLabel>
            {anomaly.destinationIp}
          </MetaItem>
        )}
        
        {anomaly.metricName && (
          <MetaItem>
            <MetaLabel>Метрика:</MetaLabel>
            {anomaly.metricName} 
            {anomaly.metricValue !== undefined && `(${anomaly.metricValue})`}
          </MetaItem>
        )}
        
        {anomaly.createdIncident && (
          <MetaItem>
            <MetaLabel>Инцидент:</MetaLabel>
            {anomaly.createdIncident}
          </MetaItem>
        )}
      </MetaInfo>
    </Card>
  );
};

export default AnomalyCard; 