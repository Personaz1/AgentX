import React from 'react';
import styled from 'styled-components';
import { Incident, IncidentStatus, IncidentSeverity, IncidentType } from '../../types/incident';
import { format } from 'date-fns';
import { ru } from 'date-fns/locale';

interface IncidentCardProps {
  incident: Incident;
  onClick?: (id: string) => void;
}

const Card = styled.div`
  background-color: #1E1E2D;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
  border-left: 4px solid transparent;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
  }
  
  &[data-severity="CRITICAL"] {
    border-left-color: #FF3D71;
  }
  
  &[data-severity="HIGH"] {
    border-left-color: #FF6B4A;
  }
  
  &[data-severity="MEDIUM"] {
    border-left-color: #FFAA00;
  }
  
  &[data-severity="LOW"] {
    border-left-color: #0095FF;
  }
  
  &[data-severity="INFO"] {
    border-left-color: #2CE69B;
  }
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
`;

const Title = styled.h3`
  font-size: 16px;
  font-weight: 600;
  color: #fff;
  margin: 0;
  flex: 1;
`;

const StatusBadge = styled.span`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  margin-left: 8px;
  
  &[data-status="NEW"] {
    background-color: #0095FF;
    color: white;
  }
  
  &[data-status="INVESTIGATING"] {
    background-color: #FFAA00;
    color: black;
  }
  
  &[data-status="MITIGATED"] {
    background-color: #0095FF;
    color: white;
  }
  
  &[data-status="RESOLVED"] {
    background-color: #2CE69B;
    color: black;
  }
  
  &[data-status="CLOSED"] {
    background-color: #6C757D;
    color: white;
  }
  
  &[data-status="FALSE_POSITIVE"] {
    background-color: #8F9BB3;
    color: white;
  }
`;

const SeverityBadge = styled.span`
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  margin-left: 8px;
  
  &[data-severity="CRITICAL"] {
    background-color: #FF3D71;
    color: white;
  }
  
  &[data-severity="HIGH"] {
    background-color: #FF6B4A;
    color: white;
  }
  
  &[data-severity="MEDIUM"] {
    background-color: #FFAA00;
    color: black;
  }
  
  &[data-severity="LOW"] {
    background-color: #0095FF;
    color: white;
  }
  
  &[data-severity="INFO"] {
    background-color: #2CE69B;
    color: black;
  }
`;

const TypeLabel = styled.span`
  font-size: 13px;
  color: #8F9BB3;
  display: block;
  margin-bottom: 8px;
`;

const MetaInfo = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-top: 8px;
`;

const MetaItem = styled.div`
  display: flex;
  flex-direction: column;
  
  span:first-child {
    font-size: 12px;
    color: #8F9BB3;
  }
  
  span:last-child {
    font-size: 14px;
    color: #EDF1F7;
  }
`;

const typeToRussian = (type: IncidentType): string => {
  const mapping: Record<IncidentType, string> = {
    [IncidentType.INTRUSION]: 'Вторжение',
    [IncidentType.MALWARE]: 'Вредоносное ПО',
    [IncidentType.DATA_BREACH]: 'Утечка данных',
    [IncidentType.PRIVILEGE_ESCALATION]: 'Повышение привилегий',
    [IncidentType.LATERAL_MOVEMENT]: 'Горизонтальное перемещение',
    [IncidentType.UNUSUAL_BEHAVIOR]: 'Необычное поведение',
    [IncidentType.NETWORK_ANOMALY]: 'Сетевая аномалия',
    [IncidentType.SUSPICIOUS_CONNECTION]: 'Подозрительное подключение',
    [IncidentType.SYSTEM_COMPROMISE]: 'Компрометация системы',
    [IncidentType.SERVICE_DISRUPTION]: 'Нарушение работы сервиса'
  };
  return mapping[type];
};

const statusToRussian = (status: IncidentStatus): string => {
  const mapping: Record<IncidentStatus, string> = {
    [IncidentStatus.NEW]: 'Новый',
    [IncidentStatus.INVESTIGATING]: 'Расследуется',
    [IncidentStatus.MITIGATED]: 'Смягчен',
    [IncidentStatus.RESOLVED]: 'Устранен',
    [IncidentStatus.CLOSED]: 'Закрыт',
    [IncidentStatus.FALSE_POSITIVE]: 'Ложное срабатывание'
  };
  return mapping[status];
};

const severityToRussian = (severity: IncidentSeverity): string => {
  const mapping: Record<IncidentSeverity, string> = {
    [IncidentSeverity.CRITICAL]: 'Критический',
    [IncidentSeverity.HIGH]: 'Высокий',
    [IncidentSeverity.MEDIUM]: 'Средний',
    [IncidentSeverity.LOW]: 'Низкий',
    [IncidentSeverity.INFO]: 'Информационный'
  };
  return mapping[severity];
};

const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return format(date, 'dd MMM yyyy HH:mm', { locale: ru });
};

const IncidentCard: React.FC<IncidentCardProps> = ({ incident, onClick }) => {
  const handleClick = () => {
    if (onClick) {
      onClick(incident.id);
    }
  };

  return (
    <Card 
      data-severity={incident.severity} 
      onClick={handleClick}
    >
      <Header>
        <Title>{incident.title}</Title>
        <div>
          <StatusBadge data-status={incident.status}>
            {statusToRussian(incident.status)}
          </StatusBadge>
          <SeverityBadge data-severity={incident.severity}>
            {severityToRussian(incident.severity)}
          </SeverityBadge>
        </div>
      </Header>
      
      <TypeLabel>{typeToRussian(incident.type)}</TypeLabel>
      
      <MetaInfo>
        <MetaItem>
          <span>Обнаружен</span>
          <span>{formatDate(incident.detectedAt)}</span>
        </MetaItem>
        
        {incident.assignedTo && (
          <MetaItem>
            <span>Назначен</span>
            <span>{incident.assignedTo.username}</span>
          </MetaItem>
        )}
        
        {incident.affectedAssets && (
          <MetaItem>
            <span>Затронуто систем</span>
            <span>{incident.affectedAssets.length}</span>
          </MetaItem>
        )}
      </MetaInfo>
    </Card>
  );
};

export default IncidentCard; 