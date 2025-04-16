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