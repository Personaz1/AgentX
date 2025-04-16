// Общие перечисления
export enum ZondStatus {
  ACTIVE = 'ACTIVE',
  INACTIVE = 'INACTIVE',
  CONNECTING = 'CONNECTING',
  ERROR = 'ERROR',
  COMPROMISED = 'COMPROMISED'
}

export enum TaskPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export enum TaskStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELED = 'CANCELED'
}

export enum Role {
  ADMIN = 'ADMIN',
  OPERATOR = 'OPERATOR',
  VIEWER = 'VIEWER'
}

export enum ReportType {
  SECURITY = 'SECURITY',
  ACTIVITY = 'ACTIVITY',
  PERFORMANCE = 'PERFORMANCE',
  FINANCIAL = 'FINANCIAL',
  SUMMARY = 'SUMMARY'
}

export enum AlertSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

// Интерфейсы пользователей
export interface User {
  id: string;
  username: string;
  email: string;
  role: Role;
  lastLogin?: string;
  avatar?: string;
  createdAt: string;
  updatedAt: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

// Интерфейсы для зондов
export interface Zond {
  id: string;
  name: string;
  status: ZondStatus;
  ipAddress: string;
  location: string;
  os: string;
  version: string;
  lastSeen: string;
  cpuUsage: number;
  ramUsage: number;
  diskUsage: number;
  activeProcesses: number;
  connectedSince: string;
  ping: number;
  activeOperations: number;
  tags?: string[];
}

export interface ZondStats {
  total: number;
  active: number;
  inactive: number;
  error: number;
  compromised: number;
}

// Интерфейсы для задач
export interface Task {
  id: string;
  title: string;
  description: string;
  zondId: string;
  status: TaskStatus;
  priority: TaskPriority;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  progress: number;
  assignedTo?: string;
  type: string;
  tags: string[];
  result?: TaskResult;
}

export interface TaskResult {
  id: string;
  taskId: string;
  success: boolean;
  data?: any;
  error?: string;
  timestamp: string;
}

// Интерфейсы для отчетов
export interface Report {
  id: string;
  title: string;
  date: string;
  type: ReportType;
  status: 'готов' | 'в обработке' | 'ошибка';
  size: string;
  author: string;
  content?: any;
}

// Интерфейсы для активности системы
export interface SystemActivity {
  id: string;
  type: 'connection' | 'task' | 'data' | 'alert';
  description: string;
  timestamp: string;
  severity?: AlertSeverity;
  details?: any;
}

export interface Alert {
  id: string;
  message: string;
  severity: AlertSeverity;
  timestamp: string;
  resolved: boolean;
  details?: any;
}

// Интерфейсы для настроек
export interface SystemSettings {
  id: string;
  apiEndpoint: string;
  logLevel: string;
  autoUpdate: boolean;
  connectionTimeout: number;
  darkMode: boolean;
  notificationsEnabled: boolean;
  maxConnectedZonds: number;
  operationsPerSecondLimit: number;
  dataRetentionDays: number;
  adminEmail: string;
  logsVerbosity: string;
  createdAt: string;
  updatedAt: string;
}

// Статистика системы
export interface SystemStats {
  activeZonds: number;
  totalOperations: number;
  successRate: number;
  activeTasks: number;
  dataCollected: string;
  systemUptime: string;
}

// Интерфейсы для инцидентов
export enum IncidentStatus {
  NEW = 'NEW',
  INVESTIGATING = 'INVESTIGATING',
  MITIGATING = 'MITIGATING', 
  RESOLVED = 'RESOLVED',
  CLOSED = 'CLOSED'
}

export enum IncidentSeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

export enum IncidentType {
  UNAUTHORIZED_ACCESS = 'UNAUTHORIZED_ACCESS',
  DATA_BREACH = 'DATA_BREACH',
  MALWARE = 'MALWARE',
  DOS = 'DOS',
  CREDENTIAL_COMPROMISE = 'CREDENTIAL_COMPROMISE',
  CONFIGURATION_ERROR = 'CONFIGURATION_ERROR',
  SOCIAL_ENGINEERING = 'SOCIAL_ENGINEERING',
  INSIDER_THREAT = 'INSIDER_THREAT',
  OTHER = 'OTHER'
}

export interface IncidentComment {
  id: string;
  incidentId: string;
  userId: string;
  username: string;
  content: string;
  timestamp: string;
}

export interface IncidentAttachment {
  id: string;
  incidentId: string;
  filename: string;
  fileType: string;
  fileSize: number;
  uploadedBy: string;
  uploadTimestamp: string;
  url: string;
}

export interface IncidentAction {
  id: string;
  incidentId: string;
  description: string;
  actionType: string;
  assignedTo?: string;
  status: 'pending' | 'completed' | 'failed';
  timestamp: string;
  completedAt?: string;
  result?: string;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  type: IncidentType;
  affectedSystems: string[];
  affectedZonds: string[];
  detectionSource: string;
  detectedAt: string;
  reportedBy: string;
  assignedTo?: string; 
  resolvedAt?: string;
  closedAt?: string;
  resolvedBy?: string;
  rootCause?: string;
  resolution?: string;
  comments?: IncidentComment[];
  attachments?: IncidentAttachment[];
  actions?: IncidentAction[];
  tags: string[];
  impactDescription?: string;
  mitigationSteps?: string;
  relatedIncidents?: string[];
}

export interface IncidentStats {
  total: number;
  new: number;
  investigating: number;
  mitigating: number;
  resolved: number;
  closed: number;
  bySeverity: {
    low: number;
    medium: number;
    high: number;
    critical: number;
  };
  byType: Record<IncidentType, number>;
}

// Статусы подключения зондов
export enum ZondConnectionStatus {
  ONLINE = 'ONLINE',
  OFFLINE = 'OFFLINE',
  CONNECTING = 'CONNECTING',
  ERROR = 'ERROR',
  COMPROMISED = 'COMPROMISED'
}

// Информация о системе
export interface SystemInfo {
  cpuUsage: number;
  ramTotal: number;
  ramUsed: number;
  diskTotal: number;
  diskUsed: number;
  hostname: string;
  osVersion: string;
  ipAddress: string;
}

// Информация о зонде
export interface ZondInfo {
  id: string;
  name: string;
  status: ZondConnectionStatus;
  ipAddress: string;
  location?: string;
  os: string;
  version: string;
  lastSeen: string;
  cpuUsage: number;
  ramUsage: number;
  diskUsage: number;
  activeProcesses: number;
  connectedSince?: string;
  ping?: number;
  activeOperations?: number;
  systemInfo?: SystemInfo;
}

// Задача для зонда
export interface ZondTask {
  id: string;
  title: string;
  description?: string;
  priority: TaskPriority;
  status: TaskStatus;
  createdAt: string;
  updatedAt: string;
  deadline?: string;
  assignedTo?: string;
  assignedZonds: string[];
  progress?: number;
  result?: string;
}

// Режимы мышления ИИ
export enum ThinkingMode {
  DEFENSIVE = 'DEFENSIVE',
  NEUTRAL = 'NEUTRAL',
  AGGRESSIVE = 'AGGRESSIVE',
  LEARNING = 'LEARNING'
}

// Состояние "мозга" C1
export interface C1BrainState {
  thinkingMode: ThinkingMode;
  threatLevel: number;
  activeAnalysis: boolean;
  learningRate: number;
  confidenceScore: number;
  lastDecision: string;
  lastDecisionTime: string;
}

// Конфигурация банка данных
export interface BankConfig {
  storagePath: string;
  maxSize: number;
  encryptionEnabled: boolean;
  compressionLevel: number;
  autoBakup: boolean;
  backupInterval: number;
  backupPath: string;
}

// Операция АТС
export interface ATSOperation {
  id: string;
  type: string;
  status: string;
  target: string;
  startTime: string;
  endTime?: string;
  result?: string;
  initiatedBy: string;
}

// Состояние АТС
export interface ATSState {
  status: string;
  activeOperations: number;
  totalOperations: number;
  successRate: number;
  lastOperation?: ATSOperation;
}

// Типы инцидентов
export enum IncidentType {
  UNAUTHORIZED_ACCESS = 'UNAUTHORIZED_ACCESS',
  DATA_BREACH = 'DATA_BREACH',
  MALWARE = 'MALWARE',
  DDOS = 'DDOS',
  PHISHING = 'PHISHING',
  INSIDER_THREAT = 'INSIDER_THREAT',
  RANSOMWARE = 'RANSOMWARE',
  SYSTEM_COMPROMISE = 'SYSTEM_COMPROMISE',
  NETWORK_INTRUSION = 'NETWORK_INTRUSION',
  SOCIAL_ENGINEERING = 'SOCIAL_ENGINEERING',
  UNKNOWN = 'UNKNOWN'
}

// Комментарий к инциденту
export interface IncidentComment {
  id: string;
  author: string;
  text: string;
  createdAt: string;
}

// Действие в хронологии инцидента
export interface IncidentAction {
  id: string;
  type: 'status_change' | 'assignment' | 'comment' | 'remediation' | 'other';
  description: string;
  performedBy: string;
  performedAt: string;
}

// Инцидент
export interface Incident {
  id: string;
  title: string;
  description: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  type: IncidentType;
  affectedSystems?: string[];
  affectedZonds?: string[];
  detectionSource: string;
  detectedAt: string;
  reportedBy: string;
  assignedTo?: string;
  resolvedAt?: string;
  resolvedBy?: string;
  closedAt?: string;
  rootCause?: string;
  resolution?: string;
  tags: string[];
  impactDescription?: string;
  comments?: IncidentComment[];
  actions?: IncidentAction[];
} 