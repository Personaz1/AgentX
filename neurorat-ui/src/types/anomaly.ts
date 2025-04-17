// Перечисления для аномалий
export enum AnomalyStatus {
  NEW = 'NEW',
  INVESTIGATING = 'INVESTIGATING',
  RESOLVED = 'RESOLVED',
  FALSE_POSITIVE = 'FALSE_POSITIVE'
}

export enum AnomalySeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export enum AnomalyType {
  TRAFFIC_SPIKE = 'TRAFFIC_SPIKE',
  BEHAVIOR_CHANGE = 'BEHAVIOR_CHANGE',
  NEW_CONNECTION = 'NEW_CONNECTION',
  UNUSUAL_LOGIN = 'UNUSUAL_LOGIN',
  DATA_EXFILTRATION = 'DATA_EXFILTRATION',
  PRIVILEGE_ESCALATION = 'PRIVILEGE_ESCALATION',
  OTHER = 'OTHER'
}

// Интерфейсы для аномалий
export interface Anomaly {
  id: string;
  title: string;
  description: string;
  type: AnomalyType;
  severity: AnomalySeverity;
  status: AnomalyStatus;
  detectedAt: string;
  zondId?: string;
  zondName?: string;
  sourceIp?: string;
  destinationIp?: string;
  protocol?: string;
  port?: number;
  metricName?: string;
  metricValue?: number;
  metricThreshold?: number;
  createdIncident?: string;
}

export interface AnomalyStats {
  total: number;
  new: number;
  investigating: number;
  resolved: number;
  falsePositive: number;
  byStatus: {
    [key in AnomalyStatus]: number;
  };
  bySeverity: {
    [key in AnomalySeverity]: number;
  };
  byType: {
    [key in AnomalyType]: number;
  };
}

// Типы для запросов API
export interface GetAnomaliesParams {
  status?: AnomalyStatus;
  severity?: AnomalySeverity;
  type?: AnomalyType;
  zondId?: string;
  startDate?: string;
  endDate?: string;
  search?: string;
  page?: number;
  limit?: number;
}

export interface UpdateAnomalyStatusRequest {
  status: AnomalyStatus;
  comment?: string;
}

export interface CreateIncidentFromAnomalyRequest {
  anomalyId: string;
  title?: string;
  description?: string;
  assignTo?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
}

// Вспомогательные константы
export const ANOMALY_STATUS_NAMES: Record<AnomalyStatus, string> = {
  [AnomalyStatus.NEW]: 'Новая',
  [AnomalyStatus.INVESTIGATING]: 'Расследование',
  [AnomalyStatus.RESOLVED]: 'Решена',
  [AnomalyStatus.FALSE_POSITIVE]: 'Ложное срабатывание'
};

export const ANOMALY_SEVERITY_NAMES: Record<AnomalySeverity, string> = {
  [AnomalySeverity.LOW]: 'Низкая',
  [AnomalySeverity.MEDIUM]: 'Средняя',
  [AnomalySeverity.HIGH]: 'Высокая',
  [AnomalySeverity.CRITICAL]: 'Критическая'
};

export const ANOMALY_TYPE_NAMES: Record<AnomalyType, string> = {
  [AnomalyType.TRAFFIC_SPIKE]: 'Скачок трафика',
  [AnomalyType.BEHAVIOR_CHANGE]: 'Изменение поведения',
  [AnomalyType.NEW_CONNECTION]: 'Новое соединение',
  [AnomalyType.UNUSUAL_LOGIN]: 'Необычный вход',
  [AnomalyType.DATA_EXFILTRATION]: 'Утечка данных',
  [AnomalyType.PRIVILEGE_ESCALATION]: 'Повышение привилегий',
  [AnomalyType.OTHER]: 'Другое'
};

// Вспомогательные функции
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleDateString('ru-RU', { 
    day: '2-digit', 
    month: '2-digit', 
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}; 