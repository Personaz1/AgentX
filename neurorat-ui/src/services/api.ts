import axios from 'axios';
import { AnomalyStatus, AnomalySeverity, AnomalyType, Anomaly, AnomalyStats, GetAnomaliesParams, UpdateAnomalyStatusRequest, CreateIncidentFromAnomalyRequest } from '../types/anomaly';
import { 
  SecurityThreat, 
  SecurityVulnerability, 
  SecuritySetting, 
  SecurityStats, 
  SecurityScanRequest, 
  SecurityScanResult, 
  SecurityEvent 
} from '../types/security';
import { IncidentListParams, IncidentListResponse, Incident, IncidentStatus, IncidentIoc, IncidentAffectedAsset, IncidentMitigation } from '../types/incident';
import { SystemSettings, ZondInfo, ZondConnectionStatus } from '../types';
import { ZondsCommand, ZondConnectionStatus as ZondConnectionStatusType, ZondCommandStatus, ZondRatCommandResult } from '../types';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8080/api';

// Типы для Codex операций
export type CodexOperationType = 'ANALYZE' | 'MODIFY' | 'EXECUTE' | 'ASK' | 'EXPLOIT';
export type CodexTargetType = 'FILE' | 'DIRECTORY' | 'URL' | 'CODE_SNIPPET';
export type CodexStatus = 'success' | 'error' | 'pending';

// Тип статуса компонента зонда
export type ZondStatus = 'healthy' | 'warning' | 'critical' | 'inactive';

// Интерфейс компонента системы
export interface ZondComponent {
  id: string;
  name: string;
  icon: string;
  status: ZondStatus;
  lastUpdated: string;
  details: string;
  path: string;
}

// Интерфейс результата операции Codex
export interface CodexResult {
  id: string;
  timestamp: string;
  target: string;
  operation: CodexOperationType;
  status: CodexStatus;
  content: string;
  summary: string;
}

// Интерфейс состояния C1Brain
export interface C1BrainState {
  isActive: boolean;
  currentMode: string;
  lastOperation: string;
  lastOperationTime: string;
}

// Интерфейс доступности LLM
export interface LlmAvailability {
  available: boolean;
  provider: string | null;
  model: string | null;
}

// Функция для получения заголовков авторизации
const getAuthHeader = (): HeadersInit => {
  const token = localStorage.getItem('authToken');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};

// Сервис для работы с Codex API
export const codexService = {
  // Получение истории операций
  getOperationHistory: async (): Promise<CodexResult[]> => {
    try {
      const response = await axios.get(`${API_URL}/codex/history`);
      return response.data;
    } catch (error) {
      console.error('Error fetching Codex operation history:', error);
      return [];
    }
  },

  // Выполнение операции
  runOperation: async (
    target: string,
    operation: CodexOperationType,
    targetType: CodexTargetType = 'FILE',
    options: Record<string, any> = {}
  ): Promise<CodexResult> => {
    try {
      const response = await axios.post(`${API_URL}/codex/operation`, {
        target,
        operation,
        targetType,
        options
      });
      return response.data;
    } catch (error) {
      console.error(`Error running Codex operation ${operation}:`, error);
      throw error;
    }
  }
};

// Сервис для работы с C1 Brain API
export const c1Service = {
  // Получение текущего состояния C1 Brain
  getBrainState: async (): Promise<C1BrainState> => {
    try {
      const response = await axios.get(`${API_URL}/c1/brain/state`);
      return response.data;
    } catch (error) {
      console.error('Error fetching C1 Brain state:', error);
      return {
        isActive: false,
        currentMode: 'ERROR',
        lastOperation: 'Ошибка получения состояния',
        lastOperationTime: new Date().toISOString()
      };
    }
  },

  // Получение доступности LLM
  getLlmAvailability: async (): Promise<LlmAvailability> => {
    try {
      const response = await axios.get(`${API_URL}/c1/llm/availability`);
      return response.data;
    } catch (error) {
      console.error('Error fetching LLM availability:', error);
      return {
        available: false,
        provider: null,
        model: null
      };
    }
  },

  // Переключение состояния C1 Brain (активен/неактивен)
  toggleBrainState: async (): Promise<C1BrainState> => {
    try {
      const response = await axios.post(`${API_URL}/c1/brain/toggle`);
      return response.data;
    } catch (error) {
      console.error('Error toggling C1 Brain state:', error);
      throw error;
    }
  },

  // Отправка промпта в C1 Brain
  sendPrompt: async (prompt: string, mode: string = 'STANDARD'): Promise<any> => {
    try {
      const response = await axios.post(`${API_URL}/c1/brain/prompt`, {
        prompt,
        mode
      });
      return response.data;
    } catch (error) {
      console.error('Error sending prompt to C1 Brain:', error);
      throw error;
    }
  }
};

// Сервис для работы с компонентами системы
export const zondsService = {
  // Получение компонентов системы
  getSystemComponents: async (): Promise<ZondComponent[]> => {
    try {
      const response = await axios.get(`${API_URL}/system/components`);
      return response.data;
    } catch (error) {
      console.error('Error fetching system components:', error);
      // Возвращаем пример данных для демонстрации
      return [
        {
          id: '1',
          name: 'C1 Brain',
          icon: 'brain',
          status: 'healthy',
          lastUpdated: new Date().toISOString(),
          details: 'Центральный компонент управления системой',
          path: '/c1brain'
        },
        {
          id: '2',
          name: 'Codex',
          icon: 'code',
          status: 'healthy',
          lastUpdated: new Date().toISOString(),
          details: 'Модуль анализа и эксплуатации кода',
          path: '/codex'
        },
        {
          id: '3',
          name: 'Система безопасности',
          icon: 'shield',
          status: 'warning',
          lastUpdated: new Date().toISOString(),
          details: 'Обнаружены потенциальные угрозы',
          path: '/security'
        },
        {
          id: '4',
          name: 'Карта инцидентов',
          icon: 'map',
          status: 'healthy',
          lastUpdated: new Date().toISOString(),
          details: 'Географическое расположение событий',
          path: '/incidents/map'
        },
        {
          id: '5',
          name: 'Мониторинг зондов',
          icon: 'monitor',
          status: 'healthy',
          lastUpdated: new Date().toISOString(),
          details: 'Статус и управление зондами',
          path: '/zonds'
        },
        {
          id: '6',
          name: 'Обнаружение вторжений',
          icon: 'alert',
          status: 'critical',
          lastUpdated: new Date().toISOString(),
          details: 'Обнаружены активные попытки вторжения',
          path: '/intrusion'
        }
      ];
    }
  },
  
  // Другие методы для работы с зондами...
};

// Сервис для работы с аномалиями
export const anomalyService = {
  async getAnomalies(params?: GetAnomaliesParams): Promise<Anomaly[]> {
    try {
      const queryParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined) {
            queryParams.append(key, String(value));
          }
        });
      }
      
      const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
      const response = await fetch(`${API_URL}/anomalies${query}`);
      
      if (!response.ok) {
        throw new Error(`Ошибка HTTP: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Ошибка при получении списка аномалий:', error);
      return []; // Возвращаем пустой массив в случае ошибки
    }
  },

  async getAnomalyStats(): Promise<AnomalyStats> {
    try {
      const response = await fetch(`${API_URL}/anomalies/stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error(`Ошибка при получении статистики аномалий: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Ошибка при получении статистики аномалий:', error);
      // Возвращаем структуру данных по умолчанию в случае ошибки
      return {
        total: 0,
        new: 0,
        investigating: 0,
        resolved: 0,
        falsePositive: 0,
        byStatus: {
          [AnomalyStatus.NEW]: 0,
          [AnomalyStatus.INVESTIGATING]: 0,
          [AnomalyStatus.RESOLVED]: 0,
          [AnomalyStatus.FALSE_POSITIVE]: 0
        },
        bySeverity: {
          [AnomalySeverity.LOW]: 0,
          [AnomalySeverity.MEDIUM]: 0,
          [AnomalySeverity.HIGH]: 0,
          [AnomalySeverity.CRITICAL]: 0
        },
        byType: {
          [AnomalyType.TRAFFIC_SPIKE]: 0,
          [AnomalyType.BEHAVIOR_CHANGE]: 0,
          [AnomalyType.NEW_CONNECTION]: 0,
          [AnomalyType.UNUSUAL_LOGIN]: 0,
          [AnomalyType.DATA_EXFILTRATION]: 0,
          [AnomalyType.PRIVILEGE_ESCALATION]: 0,
          [AnomalyType.OTHER]: 0
        }
      };
    }
  },

  async getAnomalyById(id: string): Promise<Anomaly | null> {
    try {
      const response = await fetch(`${API_URL}/anomalies/${id}`);
      
      if (!response.ok) {
        throw new Error(`Ошибка HTTP: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Ошибка при получении аномалии с ID ${id}:`, error);
      return null; // Возвращаем null в случае ошибки
    }
  },

  async updateAnomalyStatus(id: string, status: AnomalyStatus, comment?: string): Promise<boolean> {
    try {
      const data: UpdateAnomalyStatusRequest = { status };
      if (comment) {
        data.comment = comment;
      }
      
      const response = await fetch(`${API_URL}/anomalies/${id}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка HTTP: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при обновлении статуса аномалии с ID ${id}:`, error);
      return false; // Возвращаем false в случае ошибки
    }
  },

  async createIncidentFromAnomaly(id: string, data?: Omit<CreateIncidentFromAnomalyRequest, 'anomalyId'>): Promise<{ success: boolean; incidentId?: string }> {
    try {
      const requestData: CreateIncidentFromAnomalyRequest = {
        anomalyId: id,
        ...data
      };
      
      const response = await fetch(`${API_URL}/anomalies/${id}/create-incident`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка HTTP: ${response.status}`);
      }
      
      const result = await response.json();
      return { 
        success: true, 
        incidentId: result.incidentId 
      };
    } catch (error) {
      console.error(`Ошибка при создании инцидента из аномалии с ID ${id}:`, error);
      return { 
        success: false 
      };
    }
  }
};

// Сервис для работы с модулем безопасности
export const securityService = {
  async getSecurityThreats(): Promise<SecurityThreat[]> {
    try {
      const response = await fetch(`${API_URL}/security/threats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error(`Ошибка при получении угроз безопасности: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Ошибка при получении угроз безопасности:', error);
      return [];
    }
  },

  async getSecurityVulnerabilities(): Promise<SecurityVulnerability[]> {
    try {
      const response = await fetch(`${API_URL}/security/vulnerabilities`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error(`Ошибка при получении уязвимостей: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Ошибка при получении уязвимостей:', error);
      return [];
    }
  },

  async getSecuritySettings(): Promise<SecuritySetting[]> {
    try {
      const response = await fetch(`${API_URL}/security/settings`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error(`Ошибка при получении настроек безопасности: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Ошибка при получении настроек безопасности:', error);
      return [];
    }
  },
  
  async updateSecuritySetting(id: string, enabled: boolean, configValues?: Record<string, any>): Promise<boolean> {
    try {
      const data: any = { enabled };
      if (configValues) {
        data.configValues = configValues;
      }
      
      const response = await fetch(`${API_URL}/security/settings/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при обновлении настройки безопасности: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при обновлении настройки безопасности с ID ${id}:`, error);
      return false;
    }
  },
  
  async getSecurityStats(): Promise<SecurityStats> {
    try {
      const response = await fetch(`${API_URL}/security/stats`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error(`Ошибка при получении статистики безопасности: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Ошибка при получении статистики безопасности:', error);
      // Возвращаем структуру данных по умолчанию в случае ошибки
      return {
        activeThreatCount: 0,
        criticalThreatCount: 0,
        highThreatCount: 0,
        resolvedThreatsLast30Days: 0,
        
        activeVulnerabilityCount: 0,
        criticalVulnerabilityCount: 0,
        highVulnerabilityCount: 0,
        patchedVulnerabilitiesLast30Days: 0,
        
        securityScore: 70, // Значение по умолчанию
        lastScanTime: null
      };
    }
  },
  
  async mitigateThreat(id: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/security/threats/${id}/mitigate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при устранении угрозы: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при устранении угрозы с ID ${id}:`, error);
      return false;
    }
  },
  
  async patchVulnerability(id: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/security/vulnerabilities/${id}/patch`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при установке патча для уязвимости: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при установке патча для уязвимости с ID ${id}:`, error);
      return false;
    }
  },
  
  async ignoreVulnerability(id: string, reason: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/security/vulnerabilities/${id}/ignore`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({ reason })
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при игнорировании уязвимости: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при игнорировании уязвимости с ID ${id}:`, error);
      return false;
    }
  },
  
  async startSecurityScan(scanRequest: SecurityScanRequest): Promise<SecurityScanResult | null> {
    try {
      const response = await fetch(`${API_URL}/security/scan`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(scanRequest)
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при запуске сканирования: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Ошибка при запуске сканирования безопасности:', error);
      return null;
    }
  },
  
  async getSecurityScanStatus(scanId: string): Promise<SecurityScanResult | null> {
    try {
      const response = await fetch(`${API_URL}/security/scan/${scanId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при получении статуса сканирования: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Ошибка при получении статуса сканирования с ID ${scanId}:`, error);
      return null;
    }
  },
  
  async getSecurityEvents(limit = 10, offset = 0): Promise<SecurityEvent[]> {
    try {
      const response = await fetch(`${API_URL}/security/events?limit=${limit}&offset=${offset}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при получении событий безопасности: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Ошибка при получении событий безопасности:', error);
      return [];
    }
  }
};

// Сервис для работы с инцидентами
export const incidentService = {
  // Получение списка инцидентов с пагинацией и фильтрацией
  async getIncidents(params: IncidentListParams): Promise<IncidentListResponse> {
    try {
      const queryParams = new URLSearchParams();
      queryParams.append('page', params.page.toString());
      queryParams.append('pageSize', params.pageSize.toString());
      
      if (params.sortBy) {
        queryParams.append('sortBy', params.sortBy);
        queryParams.append('sortDirection', params.sortDirection || 'desc');
      }
      
      // Обработка фильтров
      if (params.filters) {
        const { status, severity, type, assignedToMe, dateRange, searchTerm } = params.filters;
        
        if (status && status.length > 0) {
          status.forEach(s => queryParams.append('status', s));
        }
        
        if (severity && severity.length > 0) {
          severity.forEach(s => queryParams.append('severity', s));
        }
        
        if (type && type.length > 0) {
          type.forEach(t => queryParams.append('type', t));
        }
        
        if (assignedToMe !== undefined) {
          queryParams.append('assignedToMe', assignedToMe.toString());
        }
        
        if (dateRange) {
          queryParams.append('dateFrom', dateRange.from);
          queryParams.append('dateTo', dateRange.to);
        }
        
        if (searchTerm) {
          queryParams.append('searchTerm', searchTerm);
        }
      }
      
      const response = await fetch(`${API_URL}/incidents?${queryParams.toString()}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при получении списка инцидентов: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Ошибка при получении списка инцидентов:', error);
      // Возвращаем пустой результат в случае ошибки
      return {
        incidents: [],
        totalCount: 0,
        page: params.page,
        pageSize: params.pageSize,
        totalPages: 0
      };
    }
  },
  
  // Получение детальной информации об инциденте по ID
  async getIncidentById(id: string): Promise<Incident | null> {
    try {
      const response = await fetch(`${API_URL}/incidents/${id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при получении инцидента с ID ${id}: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Ошибка при получении инцидента с ID ${id}:`, error);
      return null;
    }
  },
  
  // Обновление статуса инцидента
  async updateIncidentStatus(id: string, status: IncidentStatus, comment?: string): Promise<boolean> {
    try {
      const data: any = { status };
      if (comment) {
        data.comment = comment;
      }
      
      const response = await fetch(`${API_URL}/incidents/${id}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(data)
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при обновлении статуса инцидента с ID ${id}: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при обновлении статуса инцидента с ID ${id}:`, error);
      return false;
    }
  },
  
  // Создание нового инцидента
  async createIncident(incidentData: Omit<Incident, 'id' | 'createdAt' | 'updatedAt'>): Promise<{ success: boolean; incidentId?: string }> {
    try {
      const response = await fetch(`${API_URL}/incidents`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(incidentData)
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при создании инцидента: ${response.status}`);
      }
      
      const result = await response.json();
      return {
        success: true,
        incidentId: result.id
      };
    } catch (error) {
      console.error('Ошибка при создании инцидента:', error);
      return {
        success: false
      };
    }
  },
  
  // Добавление комментария к инциденту
  async addIncidentNote(id: string, content: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/incidents/${id}/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({ content })
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при добавлении комментария к инциденту с ID ${id}: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при добавлении комментария к инциденту с ID ${id}:`, error);
      return false;
    }
  },
  
  // Добавление IOC к инциденту
  async addIncidentIoc(id: string, iocData: Omit<IncidentIoc, 'id' | 'addedAt'>): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/incidents/${id}/iocs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(iocData)
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при добавлении IOC к инциденту с ID ${id}: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при добавлении IOC к инциденту с ID ${id}:`, error);
      return false;
    }
  },
  
  // Добавление затронутого актива к инциденту
  async addIncidentAffectedAsset(id: string, assetData: Omit<IncidentAffectedAsset, 'id'>): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/incidents/${id}/affected-assets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(assetData)
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при добавлении затронутого актива к инциденту с ID ${id}: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при добавлении затронутого актива к инциденту с ID ${id}:`, error);
      return false;
    }
  },
  
  // Добавление мероприятия по устранению инцидента
  async addIncidentMitigation(id: string, mitigationData: Omit<IncidentMitigation, 'id'>): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/incidents/${id}/mitigations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(mitigationData)
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при добавлении мероприятия по устранению инцидента с ID ${id}: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при добавлении мероприятия по устранению инцидента с ID ${id}:`, error);
      return false;
    }
  },
  
  // Загрузка файла, относящегося к инциденту
  async uploadIncidentFile(id: string, file: File): Promise<{ success: boolean; fileId?: string }> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_URL}/incidents/${id}/files`, {
        method: 'POST',
        headers: {
          ...getAuthHeader()
        },
        body: formData
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при загрузке файла для инцидента с ID ${id}: ${response.status}`);
      }
      
      const result = await response.json();
      return {
        success: true,
        fileId: result.id
      };
    } catch (error) {
      console.error(`Ошибка при загрузке файла для инцидента с ID ${id}:`, error);
      return {
        success: false
      };
    }
  },
  
  // Назначение инцидента пользователю
  async assignIncident(id: string, userId: string): Promise<boolean> {
    try {
      const response = await fetch(`${API_URL}/incidents/${id}/assign`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({ userId })
      });
      
      if (!response.ok) {
        throw new Error(`Ошибка при назначении инцидента с ID ${id}: ${response.status}`);
      }
      
      return true;
    } catch (error) {
      console.error(`Ошибка при назначении инцидента с ID ${id}:`, error);
      return false;
    }
  }
};

// Сервис для работы с настройками системы
export const settingsService = {
  // Получение настроек системы
  getSystemSettings: async (): Promise<SystemSettings> => {
    try {
      const response = await fetch(`${API_URL}/settings/system`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error(`Ошибка при получении настроек системы: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Ошибка при получении настроек системы:', error);
      // Возвращаем дефолтные настройки в случае ошибки
      return {
        id: 'default',
        apiEndpoint: API_URL,
        logLevel: 'INFO',
        autoUpdate: true,
        connectionTimeout: 30000,
        darkMode: true,
        notificationsEnabled: true,
        maxConnectedZonds: 100,
        operationsPerSecondLimit: 10,
        dataRetentionDays: 90,
        adminEmail: 'admin@example.com',
        logsVerbosity: 'NORMAL',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
    }
  },

  // Обновление настроек системы
  updateSystemSettings: async (settings: Partial<SystemSettings>): Promise<SystemSettings> => {
    try {
      const response = await fetch(`${API_URL}/settings/system`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify(settings)
      });

      if (!response.ok) {
        throw new Error(`Ошибка при обновлении настроек системы: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Ошибка при обновлении настроек системы:', error);
      throw error;
    }
  },

  // Получение промптов для ИИ
  getPrompts: async (): Promise<{system: {id: string, prompt: string}, user: {id: string, prompt: string}}> => {
    try {
      const response = await fetch(`${API_URL}/settings/prompts`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        }
      });

      if (!response.ok) {
        throw new Error(`Ошибка при получении промптов: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Ошибка при получении промптов:', error);
      return {
        system: {
          id: 'system',
          prompt: 'Ты - ИИ-ассистент для кибербезопасности, помогающий пользователям в анализе угроз и защите информации.'
        },
        user: {
          id: 'user',
          prompt: 'Отвечай кратко и по делу. Фокусируйся на безопасности и защите информации.'
        }
      };
    }
  },

  // Обновление промптов для ИИ
  updatePrompts: async (
    systemPrompt: {id: string, prompt: string}, 
    userPrompt: {id: string, prompt: string}
  ): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/settings/prompts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAuthHeader()
        },
        body: JSON.stringify({
          system: systemPrompt,
          user: userPrompt
        })
      });

      if (!response.ok) {
        throw new Error(`Ошибка при обновлении промптов: ${response.status}`);
      }

      return true;
    } catch (error) {
      console.error('Ошибка при обновлении промптов:', error);
      return false;
    }
  }
}; 