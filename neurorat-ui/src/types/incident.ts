export enum IncidentStatus {
  NEW = 'NEW',
  INVESTIGATING = 'INVESTIGATING',
  MITIGATED = 'MITIGATED',
  RESOLVED = 'RESOLVED',
  CLOSED = 'CLOSED',
  FALSE_POSITIVE = 'FALSE_POSITIVE'
}

export enum IncidentSeverity {
  CRITICAL = 'CRITICAL',
  HIGH = 'HIGH',
  MEDIUM = 'MEDIUM',
  LOW = 'LOW',
  INFO = 'INFO'
}

export enum IncidentType {
  INTRUSION = 'INTRUSION',
  MALWARE = 'MALWARE',
  DATA_BREACH = 'DATA_BREACH',
  PRIVILEGE_ESCALATION = 'PRIVILEGE_ESCALATION',
  LATERAL_MOVEMENT = 'LATERAL_MOVEMENT',
  UNUSUAL_BEHAVIOR = 'UNUSUAL_BEHAVIOR',
  NETWORK_ANOMALY = 'NETWORK_ANOMALY',
  SUSPICIOUS_CONNECTION = 'SUSPICIOUS_CONNECTION',
  SYSTEM_COMPROMISE = 'SYSTEM_COMPROMISE',
  SERVICE_DISRUPTION = 'SERVICE_DISRUPTION'
}

export interface IncidentAttachedFile {
  id: string;
  filename: string;
  size: number;
  uploadedAt: string;
  contentType: string;
  url: string;
}

export interface IncidentNote {
  id: string;
  content: string;
  createdAt: string;
  createdBy: {
    id: string;
    username: string;
  };
  updatedAt?: string;
}

export interface IncidentTimelineEvent {
  id: string;
  timestamp: string;
  eventType: string;
  description: string;
  performedBy?: {
    id: string;
    username: string;
  };
  metadata?: Record<string, any>;
}

export interface IncidentAffectedAsset {
  id: string;
  name: string;
  type: string; // 'SERVER' | 'ENDPOINT' | 'NETWORK_DEVICE' | 'CLOUD_RESOURCE' etc.
  ipAddress?: string;
  hostname?: string;
  impact: string; // 'DIRECT' | 'INDIRECT' | 'POTENTIAL'
}

export interface IncidentIoc {
  id: string;
  type: string; // 'IP' | 'DOMAIN' | 'URL' | 'HASH' | 'EMAIL' | 'FILE' etc.
  value: string;
  description?: string;
  addedAt: string;
  confidence: string; // 'HIGH' | 'MEDIUM' | 'LOW'
  source?: string;
}

export interface IncidentMitigation {
  id: string;
  action: string;
  status: string; // 'PLANNED' | 'IN_PROGRESS' | 'COMPLETED' | 'FAILED'
  assignedTo?: {
    id: string;
    username: string;
  };
  description: string;
  startedAt?: string;
  completedAt?: string;
  outcome?: string;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  type: IncidentType;
  detectedAt: string;
  createdAt: string;
  updatedAt: string;
  closedAt?: string;
  assignedTo?: {
    id: string;
    username: string;
  };
  reportedBy?: {
    id: string;
    username: string;
  };
  sourceSystem?: string;
  sourceAlert?: string;
  ttd?: number; // Time to detect (minutes)
  ttr?: number; // Time to respond (minutes)
  ttm?: number; // Time to mitigate (minutes)
  ttc?: number; // Time to close (minutes)
  notes?: IncidentNote[];
  timeline?: IncidentTimelineEvent[];
  affectedAssets?: IncidentAffectedAsset[];
  iocs?: IncidentIoc[];
  mitigations?: IncidentMitigation[];
  attachedFiles?: IncidentAttachedFile[];
  tags?: string[];
  relatedIncidents?: string[]; // IDs of related incidents
}

export interface IncidentFilter {
  status?: IncidentStatus[];
  severity?: IncidentSeverity[];
  type?: IncidentType[];
  assignedToMe?: boolean;
  dateRange?: {
    from: string;
    to: string;
  };
  searchTerm?: string;
}

export interface IncidentListParams {
  page: number;
  pageSize: number;
  sortBy?: string;
  sortDirection?: 'asc' | 'desc';
  filters?: IncidentFilter;
}

export interface IncidentListResponse {
  incidents: Incident[];
  totalCount: number;
  page: number;
  pageSize: number;
  totalPages: number;
} 