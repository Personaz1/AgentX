// Статусы подключения зондов
export enum ZondConnectionStatus {
  ONLINE = 'online',
  OFFLINE = 'offline',
  CONNECTING = 'connecting',
  ERROR = 'error'
}

// Информация о системе
export interface SystemInfo {
  totalZonds: number;
  activeZonds: number;
  activeTasks: number;
  completedTasks: number;
  pendingTasks: number;
  systemLoad: number;
  uptime: number;
  version: string;
  lastUpdate: string;
}

// Информация о зонде
export interface ZondInfo {
  id: string;
  name: string;
  ip: string;
  country: string;
  status: ZondConnectionStatus;
  os: string;
  lastSeen: string;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  activeTasks: number;
  completedTasks: number;
  installedDate: string;
  version: string;
  location?: {
    lat: number;
    long: number;
    city: string;
    country: string;
  };
  capabilities: string[];
}

// Приоритет задачи
export enum TaskPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

// Статус задачи
export enum TaskStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

// Задача для зонда
export interface ZondTask {
  id: string;
  title: string;
  description: string;
  type: string;
  zondId: string;
  priority: TaskPriority;
  status: TaskStatus;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  progress: number;
  result?: any;
  error?: string;
  parameters: Record<string, any>;
}

// Режим мышления C1Brain
export enum ThinkingMode {
  STANDARD = 'standard',
  AGGRESSIVE = 'aggressive',
  CAUTIOUS = 'cautious',
  CREATIVE = 'creative',
  AUTONOMOUS = 'autonomous'
}

// Состояние C1Brain
export interface C1BrainState {
  active: boolean;
  mode: ThinkingMode;
  lastThinking: string;
  processingTasks: number;
  learningEnabled: boolean;
  autonomyLevel: number;
  decisionLog: {
    timestamp: string;
    decision: string;
    reasoning: string;
  }[];
  commandQueue: {
    id: string;
    command: string;
    priority: number;
    status: string;
  }[];
  insights: {
    id: string;
    content: string;
    timestamp: string;
    confidence: number;
  }[];
}

// Конфигурация банка для ATS
export interface BankConfig {
  id: string;
  name: string;
  code: string;
  loginUrl: string;
  loginSelector: string;
  passwordSelector: string;
  submitSelector: string;
  balanceSelector: string;
  isActive: boolean;
  lastUpdated: string;
  successRate: number;
}

// Операция ATS
export interface ATSOperation {
  id: string;
  zondId: string;
  bankId: string;
  type: string;
  amount: number;
  status: string;
  createdAt: string;
  completedAt?: string;
  targetAccount?: string;
  sourceAccount?: string;
  metadata: Record<string, any>;
  errorMessage?: string;
}

// Состояние модуля ATS
export interface ATSState {
  operations: ATSOperation[];
  banks: BankConfig[];
  status: 'idle' | 'loading' | 'succeeded' | 'failed';
  error: string | null;
  activeOperations: number;
  successfulOperations: number;
  failedOperations: number;
  totalAmount: number;
  lastOperationDate: string | null;
} 