// Типы для модуля безопасности

// Статусы угроз
export enum ThreatStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  RESOLVED = 'RESOLVED'
}

// Уровни серьезности угроз
export enum ThreatSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

// Статусы уязвимостей
export enum VulnerabilityStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  PATCHED = 'PATCHED',
  IGNORED = 'IGNORED'
}

// Уровни серьезности уязвимостей
export enum VulnerabilitySeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

// Интерфейс для угрозы безопасности
export interface SecurityThreat {
  id: string;
  title: string;
  description: string;
  severity: ThreatSeverity;
  status: ThreatStatus;
  detectedAt: string;
  source: string;
  affectedSystem: string;
  remediation?: string;
  context?: Record<string, any>;
}

// Интерфейс для уязвимости
export interface SecurityVulnerability {
  id: string;
  title: string;
  description: string;
  severity: VulnerabilitySeverity;
  status: VulnerabilityStatus;
  detectedAt: string;
  affectedSystem: string;
  cve: string | null;
  patchUrl?: string;
  remediation?: string;
  context?: Record<string, any>;
}

// Интерфейс для настройки безопасности
export interface SecuritySetting {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  category: string;
  configurable?: boolean;
  configValues?: Record<string, any>;
}

// Интерфейс для статистики безопасности
export interface SecurityStats {
  activeThreatCount: number;
  criticalThreatCount: number;
  highThreatCount: number;
  resolvedThreatsLast30Days: number;
  
  activeVulnerabilityCount: number;
  criticalVulnerabilityCount: number;
  highVulnerabilityCount: number;
  patchedVulnerabilitiesLast30Days: number;
  
  securityScore: number; // 0-100
  lastScanTime: string | null;
}

// Интерфейс для события безопасности
export interface SecurityEvent {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  eventType: string;
  severity: ThreatSeverity;
  source: string;
  relatedEntityId?: string;
  relatedEntityType?: string;
  metadata?: Record<string, any>;
}

// Интерфейс для запроса сканирования безопасности
export interface SecurityScanRequest {
  scanType: 'QUICK' | 'FULL' | 'VULNERABILITY' | 'THREAT' | 'CUSTOM';
  targetSystems?: string[];
  scanOptions?: Record<string, any>;
  priority?: 'LOW' | 'MEDIUM' | 'HIGH';
  scheduleTime?: string;
}

// Интерфейс для результата сканирования безопасности
export interface SecurityScanResult {
  id: string;
  scanType: string;
  startTime: string;
  endTime: string | null;
  status: 'QUEUED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED' | 'CANCELLED';
  threatsFound: number;
  vulnerabilitiesFound: number;
  newIssuesFound: number;
  resolvedIssues: number;
  scanReport?: string;
  error?: string;
} 