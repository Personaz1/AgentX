import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FiShield, FiAlertTriangle, FiLock, FiBell, FiRefreshCw, FiSettings, FiPlusCircle } from 'react-icons/fi';

// Интерфейсы
interface Threat {
  id: string;
  timestamp: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  source: string;
  description: string;
  status: 'active' | 'mitigated' | 'investigating';
  affectedSystem: string;
}

interface Vulnerability {
  id: string;
  name: string;
  description: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  discoveredAt: string;
  status: 'open' | 'patched' | 'ignored';
  affectedZonds: number;
  cveId?: string;
  exploitAvailable: boolean;
}

interface SecurityConfig {
  id: string;
  name: string;
  description: string;
  type: 'firewall' | 'ids' | 'encryption' | 'authentication';
  status: 'enabled' | 'disabled';
}

// Styled Components
const PageContainer = styled.div`
  padding: 20px;
  height: 100%;
  overflow-y: auto;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const Title = styled.h1`
  font-size: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 10px;
`;

const Button = styled.button<{ primary?: boolean }>`
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 8px 15px;
  border-radius: 5px;
  border: none;
  background: ${props => props.primary ? '#3182ce' : '#2D3748'};
  color: white;
  cursor: pointer;
  font-weight: 500;
  
  &:hover {
    opacity: 0.9;
  }
`;

const Grid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto;
  gap: 20px;
  margin-bottom: 20px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const Panel = styled.div`
  background: #1A202C;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
`;

const PanelHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #2D3748;
`;

const PanelTitle = styled.h2`
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
`;

const ListItem = styled.div<{ severity?: string }>`
  padding: 12px;
  margin-bottom: 10px;
  border-radius: 6px;
  background: #2D3748;
  display: flex;
  justify-content: space-between;
  position: relative;
  border-left: 4px solid ${props => {
    if (props.severity === 'critical') return '#E53E3E';
    if (props.severity === 'high') return '#DD6B20';
    if (props.severity === 'medium') return '#D69E2E';
    if (props.severity === 'low') return '#38A169';
    return '#3182CE';
  }};
`;

const ItemDetails = styled.div`
  flex: 1;
`;

const ItemTitle = styled.div`
  font-weight: 600;
  margin-bottom: 5px;
`;

const ItemDescription = styled.div`
  font-size: 13px;
  color: #A0AEC0;
`;

const ItemMetadata = styled.div`
  display: flex;
  gap: 10px;
  margin-top: 5px;
  font-size: 12px;
`;

const Badge = styled.span<{ type?: string }>`
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  background: ${props => {
    switch(props.type) {
      case 'active': return '#2C7A7B';
      case 'mitigated': return '#38A169';
      case 'investigating': return '#D69E2E';
      case 'open': return '#E53E3E';
      case 'patched': return '#38A169';
      case 'ignored': return '#718096';
      case 'enabled': return '#38A169';
      case 'disabled': return '#718096';
      case 'critical': return '#E53E3E';
      case 'high': return '#DD6B20';
      case 'medium': return '#D69E2E';
      case 'low': return '#38A169';
      default: return '#4A5568';
    }
  }};
  color: white;
`;

const StatsContainer = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 20px;
  
  @media (max-width: 1100px) {
    grid-template-columns: repeat(2, 1fr);
  }
  
  @media (max-width: 600px) {
    grid-template-columns: 1fr;
  }
`;

const StatCard = styled.div<{ severity?: string }>`
  background: #2D3748;
  border-radius: 8px;
  padding: 15px;
  display: flex;
  align-items: center;
  border-left: 4px solid ${props => {
    if (props.severity === 'critical') return '#E53E3E';
    if (props.severity === 'high') return '#DD6B20';
    if (props.severity === 'medium') return '#D69E2E';
    if (props.severity === 'low') return '#38A169';
    return '#3182CE';
  }};
`;

const StatIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #1A202C;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  
  svg {
    color: #A0AEC0;
    font-size: 20px;
  }
`;

const StatInfo = styled.div`
  flex: 1;
`;

const StatValue = styled.div`
  font-size: 20px;
  font-weight: 600;
`;

const StatLabel = styled.div`
  font-size: 13px;
  color: #A0AEC0;
`;

const SecurityPage: React.FC = () => {
  // Состояние
  const [threats, setThreats] = useState<Threat[]>([
    {
      id: "t1",
      timestamp: "2023-05-15T14:32:00",
      severity: "high",
      source: "IDS",
      description: "Обнаружена попытка брутфорс-атаки на систему аутентификации",
      status: "active",
      affectedSystem: "Компонент аутентификации"
    },
    {
      id: "t2",
      timestamp: "2023-05-15T10:17:00",
      severity: "critical",
      source: "Firewall",
      description: "Зафиксирована подозрительная активность из IP-диапазона, известного фишинговыми атаками",
      status: "investigating",
      affectedSystem: "Сетевая подсистема"
    },
    {
      id: "t3",
      timestamp: "2023-05-14T08:45:00",
      severity: "medium",
      source: "ATS",
      description: "Выявлена аномалия в шаблонах транзакций",
      status: "mitigated",
      affectedSystem: "Финансовый модуль"
    }
  ]);
  
  const [vulnerabilities, setVulnerabilities] = useState<Vulnerability[]>([
    {
      id: "v1",
      name: "SQL-инъекция в модуле поиска",
      description: "Уязвимость позволяет выполнять произвольные SQL-запросы через недостаточно фильтруемые поля ввода",
      severity: "high",
      discoveredAt: "2023-05-10",
      status: "open",
      affectedZonds: 12,
      cveId: "CVE-2023-4567",
      exploitAvailable: true
    },
    {
      id: "v2",
      name: "Устаревшие библиотеки OpenSSL",
      description: "Используется уязвимая версия OpenSSL с известными проблемами безопасности",
      severity: "medium",
      discoveredAt: "2023-05-05",
      status: "patched",
      affectedZonds: 8,
      cveId: "CVE-2023-1234",
      exploitAvailable: true
    },
    {
      id: "v3",
      name: "Отсутствие защиты от XSS в веб-интерфейсе",
      description: "Веб-интерфейс не обеспечивает достаточную защиту от межсайтового скриптинга",
      severity: "medium",
      discoveredAt: "2023-05-02",
      status: "open",
      affectedZonds: 15,
      exploitAvailable: false
    }
  ]);
  
  const [securityConfig, setSecurityConfig] = useState<SecurityConfig[]>([
    {
      id: "cf1",
      name: "Адаптивный файрвол",
      description: "Интеллектуальный файрвол с динамическими правилами и обнаружением аномалий",
      type: "firewall",
      status: "enabled"
    },
    {
      id: "cf2",
      name: "Система предотвращения вторжений",
      description: "Нейросетевая IDS с поведенческим анализом",
      type: "ids",
      status: "enabled"
    },
    {
      id: "cf3",
      name: "Шифрование диска",
      description: "Полное шифрование данных всех зондов",
      type: "encryption",
      status: "disabled"
    },
    {
      id: "cf4",
      name: "Двухфакторная аутентификация",
      description: "2FA для всех критических операций и доступа к панели управления",
      type: "authentication",
      status: "enabled"
    }
  ]);
  
  // Статистика
  const activeThreats = threats.filter(t => t.status === 'active').length;
  const criticalVulnerabilities = vulnerabilities.filter(v => v.severity === 'critical' && v.status === 'open').length;
  const highVulnerabilities = vulnerabilities.filter(v => v.severity === 'high' && v.status === 'open').length;
  const securityScore = Math.round(70 - (activeThreats * 5) - (criticalVulnerabilities * 10) - (highVulnerabilities * 3));
  
  // Обработчики
  const toggleSecurityConfig = (id: string) => {
    setSecurityConfig(prev => 
      prev.map(config => 
        config.id === id 
          ? {...config, status: config.status === 'enabled' ? 'disabled' : 'enabled'} 
          : config
      )
    );
  };
  
  const mitigateThreat = (id: string) => {
    setThreats(prev => 
      prev.map(threat => 
        threat.id === id 
          ? {...threat, status: 'mitigated'} 
          : threat
      )
    );
  };
  
  const patchVulnerability = (id: string) => {
    setVulnerabilities(prev => 
      prev.map(vuln => 
        vuln.id === id 
          ? {...vuln, status: 'patched'} 
          : vuln
      )
    );
  };
  
  // Рендер
  return (
    <PageContainer>
      <Header>
        <Title><FiShield size={22} /> Управление безопасностью</Title>
        <ActionButtons>
          <Button><FiBell /> Оповещения</Button>
          <Button><FiRefreshCw /> Сканировать</Button>
          <Button primary><FiSettings /> Настройки</Button>
        </ActionButtons>
      </Header>
      
      <StatsContainer>
        <StatCard>
          <StatIcon><FiAlertTriangle /></StatIcon>
          <StatInfo>
            <StatValue>{activeThreats}</StatValue>
            <StatLabel>Активные угрозы</StatLabel>
          </StatInfo>
        </StatCard>
        
        <StatCard severity="high">
          <StatIcon><FiLock /></StatIcon>
          <StatInfo>
            <StatValue>{criticalVulnerabilities + highVulnerabilities}</StatValue>
            <StatLabel>Критические уязвимости</StatLabel>
          </StatInfo>
        </StatCard>
        
        <StatCard severity={securityScore > 80 ? 'low' : securityScore > 60 ? 'medium' : 'high'}>
          <StatIcon><FiShield /></StatIcon>
          <StatInfo>
            <StatValue>{securityScore}%</StatValue>
            <StatLabel>Оценка безопасности</StatLabel>
          </StatInfo>
        </StatCard>
        
        <StatCard>
          <StatIcon><FiSettings /></StatIcon>
          <StatInfo>
            <StatValue>{securityConfig.filter(c => c.status === 'enabled').length}/{securityConfig.length}</StatValue>
            <StatLabel>Активные защиты</StatLabel>
          </StatInfo>
        </StatCard>
      </StatsContainer>
      
      <Grid>
        <Panel>
          <PanelHeader>
            <PanelTitle><FiAlertTriangle size={18} /> Активные угрозы</PanelTitle>
            <Button><FiPlusCircle size={14} /> Добавить</Button>
          </PanelHeader>
          
          {threats.map(threat => (
            <ListItem key={threat.id} severity={threat.severity}>
              <ItemDetails>
                <ItemTitle>{threat.description}</ItemTitle>
                <ItemDescription>Система: {threat.affectedSystem} | Источник: {threat.source}</ItemDescription>
                <ItemMetadata>
                  <Badge type={threat.severity}>{threat.severity}</Badge>
                  <Badge type={threat.status}>{threat.status}</Badge>
                </ItemMetadata>
              </ItemDetails>
              {threat.status !== 'mitigated' && (
                <Button onClick={() => mitigateThreat(threat.id)}>Устранить</Button>
              )}
            </ListItem>
          ))}
        </Panel>
        
        <Panel>
          <PanelHeader>
            <PanelTitle><FiLock size={18} /> Уязвимости</PanelTitle>
            <Button><FiRefreshCw size={14} /> Сканировать</Button>
          </PanelHeader>
          
          {vulnerabilities.map(vuln => (
            <ListItem key={vuln.id} severity={vuln.severity}>
              <ItemDetails>
                <ItemTitle>{vuln.name}</ItemTitle>
                <ItemDescription>{vuln.description}</ItemDescription>
                <ItemMetadata>
                  <Badge type={vuln.severity}>{vuln.severity}</Badge>
                  <Badge type={vuln.status}>{vuln.status}</Badge>
                  {vuln.cveId && <Badge>{vuln.cveId}</Badge>}
                  {vuln.exploitAvailable && <Badge type="high">Есть эксплойт</Badge>}
                </ItemMetadata>
              </ItemDetails>
              {vuln.status === 'open' && (
                <Button onClick={() => patchVulnerability(vuln.id)}>Исправить</Button>
              )}
            </ListItem>
          ))}
        </Panel>
      </Grid>
      
      <Panel>
        <PanelHeader>
          <PanelTitle><FiSettings size={18} /> Настройки защиты</PanelTitle>
          <Button><FiPlusCircle size={14} /> Добавить</Button>
        </PanelHeader>
        
        <Grid>
          {securityConfig.map(config => (
            <ListItem key={config.id}>
              <ItemDetails>
                <ItemTitle>{config.name}</ItemTitle>
                <ItemDescription>{config.description}</ItemDescription>
                <ItemMetadata>
                  <Badge type={config.type}>{config.type}</Badge>
                  <Badge type={config.status}>{config.status}</Badge>
                </ItemMetadata>
              </ItemDetails>
              <Button onClick={() => toggleSecurityConfig(config.id)}>
                {config.status === 'enabled' ? 'Отключить' : 'Включить'}
              </Button>
            </ListItem>
          ))}
        </Grid>
      </Panel>
    </PageContainer>
  );
};

export default SecurityPage; 