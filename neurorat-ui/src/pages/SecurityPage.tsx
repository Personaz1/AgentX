import React, { useState } from 'react';
import styled from 'styled-components';
import { 
  SecurityThreat, 
  ThreatStatus, 
  ThreatSeverity, 
  SecurityVulnerability, 
  VulnerabilityStatus, 
  SecuritySetting,
  VulnerabilitySeverity
} from '../types/security';

// Стилизованные компоненты
const Container = styled.div`
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 24px;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
`;

const StatCard = styled.div<{ $accent?: string }>`
  background: ${props => props.$accent ? `linear-gradient(to right, ${props.$accent}15, transparent)` : '#ffffff'};
  border-left: ${props => props.$accent ? `4px solid ${props.$accent}` : '4px solid #e0e0e0'};
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  padding: 16px;
`;

const StatValue = styled.div`
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
`;

const StatLabel = styled.div`
  font-size: 14px;
  color: #666;
`;

const ContentGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 24px;
`;

const Panel = styled.div`
  background: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  overflow: hidden;
`;

const PanelHeader = styled.div`
  background: #f5f5f5;
  padding: 16px;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const PanelTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  margin: 0;
`;

const PanelContent = styled.div`
  padding: 16px;
  max-height: 400px;
  overflow-y: auto;
`;

const ListItem = styled.div`
  padding: 14px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;

  &:last-child {
    border-bottom: none;
  }
`;

const ItemInfo = styled.div`
  flex: 1;
`;

const ItemTitle = styled.div`
  font-weight: 600;
  margin-bottom: 4px;
`;

const ItemDescription = styled.div`
  font-size: 14px;
  color: #666;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
`;

const ItemMeta = styled.div`
  display: flex;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
  color: #999;
`;

const Badge = styled.span<{ $color: string }>`
  background-color: ${props => props.$color};
  color: white;
  font-size: 12px;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
`;

const ActionButton = styled.button<{ $variant?: 'primary' | 'danger' | 'success' }>`
  background-color: ${props => {
    switch (props.$variant) {
      case 'danger': return '#ff4d4f';
      case 'success': return '#52c41a';
      default: return '#1890ff';
    }
  }};
  color: #fff;
  border: none;
  border-radius: 4px;
  padding: 8px 12px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    opacity: 0.85;
  }
`;

const SettingRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid #eee;

  &:last-child {
    border-bottom: none;
  }
`;

const SettingInfo = styled.div`
  flex: 1;
`;

const SettingName = styled.div`
  font-weight: 600;
  margin-bottom: 4px;
`;

const SettingDescription = styled.div`
  font-size: 14px;
  color: #666;
`;

const Toggle = styled.div<{ $enabled: boolean }>`
  width: 50px;
  height: 28px;
  background-color: ${props => props.$enabled ? '#52c41a' : '#d9d9d9'};
  border-radius: 14px;
  position: relative;
  cursor: pointer;
  transition: all 0.3s;
  
  &:after {
    content: '';
    position: absolute;
    width: 24px;
    height: 24px;
    border-radius: 12px;
    background-color: #fff;
    top: 2px;
    left: ${props => props.$enabled ? '24px' : '2px'};
    transition: all 0.3s;
  }
`;

const SecurityPage: React.FC = () => {
  // Состояние для угроз безопасности
  const [threats, setThreats] = useState<SecurityThreat[]>([
    {
      id: '1',
      title: 'Подозрительная активность SSH',
      description: 'Обнаружено несколько неудачных попыток входа по SSH с IP-адреса 192.168.1.150',
      severity: ThreatSeverity.HIGH,
      status: ThreatStatus.PENDING,
      detectedAt: '2023-07-15T10:30:45Z',
      source: 'log-analyzer',
      affectedSystem: 'server-01',
    },
    {
      id: '2',
      title: 'Обнаружена попытка перебора паролей',
      description: 'Зафиксировано большое количество запросов аутентификации с одного IP-адреса',
      severity: ThreatSeverity.CRITICAL,
      status: ThreatStatus.IN_PROGRESS,
      detectedAt: '2023-07-16T08:15:20Z',
      source: 'auth-monitor',
      affectedSystem: 'auth-service',
    },
    {
      id: '3',
      title: 'Потенциальная утечка данных',
      description: 'Обнаружен необычный объем исходящего трафика на нестандартный порт',
      severity: ThreatSeverity.MEDIUM,
      status: ThreatStatus.PENDING,
      detectedAt: '2023-07-14T22:45:10Z',
      source: 'network-monitor',
      affectedSystem: 'data-storage',
    }
  ]);

  // Состояние для уязвимостей
  const [vulnerabilities, setVulnerabilities] = useState<SecurityVulnerability[]>([
    {
      id: '1',
      title: 'Устаревшая версия OpenSSL',
      description: 'Используется версия OpenSSL, подверженная CVE-2023-0286',
      severity: VulnerabilitySeverity.HIGH,
      status: VulnerabilityStatus.PENDING,
      detectedAt: '2023-07-10T14:20:30Z',
      affectedSystem: 'server-01',
      cve: 'CVE-2023-0286',
      patchUrl: 'https://openssl.org/patches/CVE-2023-0286',
    },
    {
      id: '2',
      title: 'Незащищенный конфигурационный файл',
      description: 'Обнаружен конфигурационный файл с небезопасными разрешениями',
      severity: VulnerabilitySeverity.MEDIUM,
      status: VulnerabilityStatus.IN_PROGRESS,
      detectedAt: '2023-07-12T09:15:40Z',
      affectedSystem: 'config-server',
      cve: null,
    },
    {
      id: '3',
      title: 'Уязвимость SQL инъекции',
      description: 'Обнаружена потенциальная уязвимость SQL инъекции в API эндпоинте',
      severity: VulnerabilitySeverity.CRITICAL,
      status: VulnerabilityStatus.PENDING,
      detectedAt: '2023-07-13T11:30:15Z',
      affectedSystem: 'api-service',
      cve: null,
    }
  ]);

  // Состояние для настроек безопасности
  const [securitySettings, setSecuritySettings] = useState<SecuritySetting[]>([
    {
      id: '1',
      name: 'Двухфакторная аутентификация',
      description: 'Требовать 2ФА для всех пользователей при входе в систему',
      enabled: true,
      category: 'authentication',
    },
    {
      id: '2',
      name: 'Автоматическое обновление',
      description: 'Автоматически устанавливать обновления безопасности',
      enabled: true,
      category: 'updates',
    },
    {
      id: '3',
      name: 'Мониторинг сетевого трафика',
      description: 'Анализировать весь сетевой трафик на предмет вредоносной активности',
      enabled: false,
      category: 'monitoring',
    },
    {
      id: '4',
      name: 'Блокировка подозрительных IP',
      description: 'Автоматически блокировать IP-адреса с подозрительной активностью',
      enabled: true,
      category: 'firewall',
    },
    {
      id: '5',
      name: 'Резервное копирование данных',
      description: 'Ежедневное резервное копирование критически важных данных',
      enabled: true,
      category: 'backup',
    }
  ]);

  // Подсчет статистики
  const activeThreatCount = threats.filter(t => t.status !== ThreatStatus.RESOLVED).length;
  const criticalThreatCount = threats.filter(t => t.severity === ThreatSeverity.CRITICAL).length;
  const highThreatCount = threats.filter(t => t.severity === ThreatSeverity.HIGH).length;
  
  const activeVulnCount = vulnerabilities.filter(v => v.status !== VulnerabilityStatus.PATCHED).length;
  const criticalVulnCount = vulnerabilities.filter(v => v.severity === VulnerabilitySeverity.CRITICAL).length;
  const highVulnCount = vulnerabilities.filter(v => v.severity === VulnerabilitySeverity.HIGH).length;
  
  const enabledSettingsCount = securitySettings.filter(s => s.enabled).length;
  const securityScore = Math.round((enabledSettingsCount / securitySettings.length) * 100 - 
                                  (criticalThreatCount * 10) - 
                                  (highThreatCount * 5) - 
                                  (criticalVulnCount * 8) - 
                                  (highVulnCount * 4));

  // Обработчики
  const toggleSetting = (id: string) => {
    setSecuritySettings(prev => 
      prev.map(setting => 
        setting.id === id 
          ? { ...setting, enabled: !setting.enabled } 
          : setting
      )
    );
  };

  const mitigateThreat = (id: string) => {
    setThreats(prev => 
      prev.map(threat => 
        threat.id === id 
          ? { ...threat, status: ThreatStatus.IN_PROGRESS } 
          : threat
      )
    );
  };

  const resolveThreat = (id: string) => {
    setThreats(prev => 
      prev.map(threat => 
        threat.id === id 
          ? { ...threat, status: ThreatStatus.RESOLVED } 
          : threat
      )
    );
  };

  const patchVulnerability = (id: string) => {
    setVulnerabilities(prev => 
      prev.map(vuln => 
        vuln.id === id 
          ? { ...vuln, status: VulnerabilityStatus.PATCHED } 
          : vuln
      )
    );
  };

  // Вспомогательные функции
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const translateThreatStatus = (status: ThreatStatus): string => {
    const translations: Record<ThreatStatus, string> = {
      [ThreatStatus.PENDING]: 'Ожидает',
      [ThreatStatus.IN_PROGRESS]: 'В работе',
      [ThreatStatus.RESOLVED]: 'Решено'
    };
    return translations[status];
  };

  const translateVulnStatus = (status: VulnerabilityStatus): string => {
    const translations: Record<VulnerabilityStatus, string> = {
      [VulnerabilityStatus.PENDING]: 'Ожидает',
      [VulnerabilityStatus.IN_PROGRESS]: 'В работе',
      [VulnerabilityStatus.PATCHED]: 'Исправлено',
      [VulnerabilityStatus.IGNORED]: 'Игнорируется'
    };
    return translations[status];
  };

  const getSeverityColor = (severity: ThreatSeverity | VulnerabilitySeverity): string => {
    const colors: Record<string, string> = {
      [ThreatSeverity.LOW]: '#52c41a',
      [ThreatSeverity.MEDIUM]: '#faad14',
      [ThreatSeverity.HIGH]: '#ff7a45',
      [ThreatSeverity.CRITICAL]: '#f5222d'
    };
    return colors[severity];
  };

  const translateSeverity = (severity: ThreatSeverity | VulnerabilitySeverity): string => {
    const translations: Record<string, string> = {
      [ThreatSeverity.LOW]: 'Низкая',
      [ThreatSeverity.MEDIUM]: 'Средняя',
      [ThreatSeverity.HIGH]: 'Высокая',
      [ThreatSeverity.CRITICAL]: 'Критическая'
    };
    return translations[severity];
  };

  return (
    <Container>
      <Header>
        <Title>Управление безопасностью</Title>
        <ActionButton>Запустить сканирование</ActionButton>
      </Header>

      <StatsGrid>
        <StatCard $accent="#f5222d">
          <StatValue>{activeThreatCount}</StatValue>
          <StatLabel>Активные угрозы</StatLabel>
        </StatCard>
        <StatCard $accent="#ff7a45">
          <StatValue>{activeVulnCount}</StatValue>
          <StatLabel>Активные уязвимости</StatLabel>
        </StatCard>
        <StatCard $accent={securityScore < 60 ? "#f5222d" : securityScore < 80 ? "#faad14" : "#52c41a"}>
          <StatValue>{securityScore}%</StatValue>
          <StatLabel>Рейтинг безопасности</StatLabel>
        </StatCard>
        <StatCard $accent="#1890ff">
          <StatValue>{enabledSettingsCount}/{securitySettings.length}</StatValue>
          <StatLabel>Активные настройки</StatLabel>
        </StatCard>
      </StatsGrid>

      <ContentGrid>
        <Panel>
          <PanelHeader>
            <PanelTitle>Активные угрозы</PanelTitle>
          </PanelHeader>
          <PanelContent>
            {threats
              .filter(threat => threat.status !== ThreatStatus.RESOLVED)
              .map(threat => (
                <ListItem key={threat.id}>
                  <ItemInfo>
                    <ItemTitle>{threat.title}</ItemTitle>
                    <ItemDescription>{threat.description}</ItemDescription>
                    <ItemMeta>
                      <span>Обнаружено: {formatDate(threat.detectedAt)}</span>
                      <span>Система: {threat.affectedSystem}</span>
                    </ItemMeta>
                  </ItemInfo>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-end' }}>
                    <Badge $color={getSeverityColor(threat.severity)}>
                      {translateSeverity(threat.severity)}
                    </Badge>
                    {threat.status === ThreatStatus.PENDING ? (
                      <ActionButton $variant="primary" onClick={() => mitigateThreat(threat.id)}>
                        Устранить
                      </ActionButton>
                    ) : (
                      <ActionButton $variant="success" onClick={() => resolveThreat(threat.id)}>
                        Решено
                      </ActionButton>
                    )}
                  </div>
                </ListItem>
              ))}
          </PanelContent>
        </Panel>

        <Panel>
          <PanelHeader>
            <PanelTitle>Уязвимости</PanelTitle>
          </PanelHeader>
          <PanelContent>
            {vulnerabilities
              .filter(vuln => vuln.status !== VulnerabilityStatus.PATCHED)
              .map(vuln => (
                <ListItem key={vuln.id}>
                  <ItemInfo>
                    <ItemTitle>{vuln.title}</ItemTitle>
                    <ItemDescription>{vuln.description}</ItemDescription>
                    <ItemMeta>
                      <span>Обнаружено: {formatDate(vuln.detectedAt)}</span>
                      <span>Система: {vuln.affectedSystem}</span>
                      {vuln.cve && <span>CVE: {vuln.cve}</span>}
                    </ItemMeta>
                  </ItemInfo>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-end' }}>
                    <Badge $color={getSeverityColor(vuln.severity)}>
                      {translateSeverity(vuln.severity)}
                    </Badge>
                    <ActionButton $variant="primary" onClick={() => patchVulnerability(vuln.id)}>
                      Исправить
                    </ActionButton>
                  </div>
                </ListItem>
              ))}
          </PanelContent>
        </Panel>
      </ContentGrid>

      <Panel>
        <PanelHeader>
          <PanelTitle>Настройки безопасности</PanelTitle>
        </PanelHeader>
        <PanelContent>
          {securitySettings.map(setting => (
            <SettingRow key={setting.id}>
              <SettingInfo>
                <SettingName>{setting.name}</SettingName>
                <SettingDescription>{setting.description}</SettingDescription>
              </SettingInfo>
              <Toggle 
                $enabled={setting.enabled} 
                onClick={() => toggleSetting(setting.id)}
              />
            </SettingRow>
          ))}
        </PanelContent>
      </Panel>
    </Container>
  );
};

export default SecurityPage; 