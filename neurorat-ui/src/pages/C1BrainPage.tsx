import React, { useState } from 'react';
import styled from 'styled-components';
import { FiRefreshCw, FiPlay, FiPause, FiDownload, FiAlertTriangle } from 'react-icons/fi';

const PageContainer = styled.div`
  padding: 24px;
  width: 100%;
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
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 12px;
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px 16px;
  border-radius: 4px;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.2s;
  cursor: pointer;
  background: #1e2739;
  color: white;
  border: none;
  
  &:hover {
    background: #2c3a57;
  }
  
  svg {
    margin-right: 8px;
  }
`;

const ControlButton = styled(Button)<{ active?: boolean }>`
  background: ${props => props.active ? '#10B981' : '#3683dc'};
  
  &:hover {
    background: ${props => props.active ? '#0E9F6E' : '#4394ee'};
  }
`;

const DownloadButton = styled(Button)`
  background: #1e2739;
  
  &:hover {
    background: #2c3a57;
  }
`;

const MainContent = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const Panel = styled.div`
  background: #1a1c23;
  border-radius: 8px;
  overflow: hidden;
`;

const PanelHeader = styled.div`
  padding: 16px;
  background: #1e2739;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const PanelTitle = styled.h3`
  font-size: 16px;
  font-weight: 600;
  margin: 0;
`;

const PanelContent = styled.div`
  padding: 16px;
`;

const StatusPanel = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 24px;
`;

const StatusCard = styled.div`
  background: rgba(30, 39, 57, 0.5);
  border-radius: 6px;
  padding: 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const StatusInfo = styled.div`
  display: flex;
  flex-direction: column;
`;

const StatusLabel = styled.span`
  font-size: 14px;
  color: #8a94a6;
  margin-bottom: 4px;
`;

const StatusValue = styled.span`
  font-size: 16px;
  font-weight: 500;
`;

const StatusIcon = styled.div<{ status: 'active' | 'inactive' | 'warning' | 'error' }>`
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: ${props => {
    switch (props.status) {
      case 'active': return '#10B981';
      case 'inactive': return '#8a94a6';
      case 'warning': return '#F59E0B';
      case 'error': return '#EF4444';
      default: return '#8a94a6';
    }
  }};
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 6px;
  background: rgba(30, 39, 57, 0.5);
  border-radius: 3px;
  overflow: hidden;
  position: relative;
`;

const Progress = styled.div<{ value: number }>`
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: ${props => props.value}%;
  background: #3683dc;
  border-radius: 3px;
  transition: width 0.3s ease;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
`;

const StatCard = styled.div`
  background: rgba(30, 39, 57, 0.5);
  border-radius: 6px;
  padding: 16px;
  display: flex;
  flex-direction: column;
`;

const StatLabel = styled.span`
  font-size: 14px;
  color: #8a94a6;
  margin-bottom: 4px;
`;

const StatValue = styled.span`
  font-size: 24px;
  font-weight: 600;
`;

const ThinkingModesPanel = styled.div`
  margin-top: 24px;
`;

const ThinkingModesList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const ThinkingModeCard = styled.div<{ active: boolean }>`
  background: ${props => props.active ? 'rgba(54, 131, 220, 0.2)' : 'rgba(30, 39, 57, 0.5)'};
  border: 1px solid ${props => props.active ? '#3683dc' : 'transparent'};
  border-radius: 6px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: ${props => props.active ? 'rgba(54, 131, 220, 0.3)' : 'rgba(30, 39, 57, 0.7)'};
  }
`;

const ThinkingModeHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

const ThinkingModeName = styled.span`
  font-size: 16px;
  font-weight: 500;
`;

const ThinkingModeActiveIndicator = styled.span<{ active: boolean }>`
  font-size: 12px;
  color: ${props => props.active ? '#10B981' : '#8a94a6'};
`;

const ThinkingModeDescription = styled.p`
  font-size: 14px;
  color: #8a94a6;
  margin: 0;
`;

const ConsolePanel = styled.div`
  height: 100%;
  display: flex;
  flex-direction: column;
`;

const ConsoleOutput = styled.div`
  background: #111318;
  border-radius: 6px;
  padding: 16px;
  font-family: monospace;
  font-size: 14px;
  color: #e2e8f0;
  height: 500px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  margin-bottom: 16px;
`;

const ConsoleLog = styled.div`
  margin-bottom: 8px;
`;

const LogTime = styled.span`
  color: #8a94a6;
  margin-right: 8px;
`;

const LogMessage = styled.span<{ type: 'info' | 'warn' | 'error' | 'success' }>`
  color: ${props => {
    switch (props.type) {
      case 'info': return '#3683dc';
      case 'warn': return '#F59E0B';
      case 'error': return '#EF4444';
      case 'success': return '#10B981';
      default: return '#e2e8f0';
    }
  }};
`;

const ActionPanel = styled.div`
  margin-top: auto;
  padding-top: 16px;
`;

const PromptsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
`;

const PromptCard = styled.div`
  background: rgba(30, 39, 57, 0.5);
  border-radius: 6px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    background: rgba(30, 39, 57, 0.7);
  }
`;

const PromptTitle = styled.div`
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
`;

const PromptDescription = styled.div`
  font-size: 12px;
  color: #8a94a6;
`;

const WarningBanner = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(245, 158, 11, 0.2);
  border-left: 4px solid #F59E0B;
  padding: 12px 16px;
  margin-bottom: 24px;
  border-radius: 0 6px 6px 0;
`;

const WarningIcon = styled.div`
  color: #F59E0B;
`;

const WarningText = styled.div`
  font-size: 14px;
  flex: 1;
`;

enum ThinkingMode {
  STANDARD = 'STANDARD',
  DEFENSIVE = 'DEFENSIVE',
  AGGRESSIVE = 'AGGRESSIVE',
  STEALTH = 'STEALTH',
  LEARNING = 'LEARNING'
}

interface LogEntry {
  time: string;
  message: string;
  type: 'info' | 'warn' | 'error' | 'success';
}

const C1BrainPage: React.FC = () => {
  const [isActive, setIsActive] = useState<boolean>(false);
  const [currentMode, setCurrentMode] = useState<ThinkingMode>(ThinkingMode.STANDARD);
  const [logs, setLogs] = useState<LogEntry[]>([
    { time: '10:15:22', message: 'C1 Brain инициализирован', type: 'info' },
    { time: '10:15:23', message: 'Загрузка нейронных сетей...', type: 'info' },
    { time: '10:15:25', message: 'Загрузка предварительно обученных моделей...', type: 'info' },
    { time: '10:15:30', message: 'Модели загружены успешно', type: 'success' },
    { time: '10:15:31', message: 'Подключение к базе данных...', type: 'info' },
    { time: '10:15:32', message: 'Подключение установлено', type: 'success' },
    { time: '10:15:35', message: 'Анализ состояния системы...', type: 'info' },
    { time: '10:15:40', message: 'Обнаружено 2 активных зонда', type: 'info' },
    { time: '10:15:42', message: 'Проверка банковских интеграций...', type: 'info' },
    { time: '10:15:45', message: 'Внимание! Одна из банковских конфигураций требует обновления API ключа', type: 'warn' },
    { time: '10:16:01', message: 'C1 Brain готов к работе в режиме STANDARD', type: 'success' }
  ]);
  
  const [memoryUsage, setMemoryUsage] = useState<number>(42);
  const [cpuUsage, setCpuUsage] = useState<number>(28);
  const [learningProgress, setLearningProgress] = useState<number>(67);
  const [anomalyScore, setAnomalyScore] = useState<number>(12);
  
  const handleToggleActive = () => {
    setIsActive(prev => !prev);
    
    const newLog: LogEntry = { 
      time: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      message: !isActive ? 'C1 Brain активирован' : 'C1 Brain деактивирован',
      type: !isActive ? 'success' : 'info'
    };
    
    setLogs(prev => [...prev, newLog]);
  };
  
  const handleSetMode = (mode: ThinkingMode) => {
    if (mode === currentMode) return;
    
    setCurrentMode(mode);
    
    const newLog: LogEntry = { 
      time: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      message: `Режим мышления изменен на ${mode}`,
      type: 'info'
    };
    
    setLogs(prev => [...prev, newLog]);
  };
  
  const handleRunPrompt = (title: string) => {
    const newLog: LogEntry = { 
      time: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      message: `Запущен промпт: ${title}`,
      type: 'info'
    };
    
    setLogs(prev => [...prev, newLog]);
    
    // Имитация получения результатов
    setTimeout(() => {
      const resultLog: LogEntry = { 
        time: new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
        message: `Результат промпта "${title}": Анализ завершен успешно`,
        type: 'success'
      };
      
      setLogs(prev => [...prev, resultLog]);
    }, 2000);
  };
  
  const getThinkingModeDescription = (mode: ThinkingMode): string => {
    switch(mode) {
      case ThinkingMode.STANDARD:
        return 'Сбалансированный режим анализа с оптимальным использованием ресурсов. Подходит для повседневной работы.';
      case ThinkingMode.DEFENSIVE:
        return 'Приоритет на обнаружение и предотвращение внешних угроз. Повышенная безопасность, сниженная скорость работы.';
      case ThinkingMode.AGGRESSIVE:
        return 'Максимальная производительность, активный сбор данных, минимальная маскировка операций. Высокое потребление ресурсов.';
      case ThinkingMode.STEALTH:
        return 'Минимальное использование сетевого трафика, маскировка операций. Пониженная производительность, но максимальная незаметность.';
      case ThinkingMode.LEARNING:
        return 'Режим обучения ИИ. Повышенное использование ресурсов для анализа и обработки новых данных, создания нейронных связей.';
      default:
        return '';
    }
  };
  
  return (
    <PageContainer>
      <Header>
        <Title>C1 Brain - Интеллектуальный анализ</Title>
        <ActionButtons>
          <ControlButton 
            active={isActive}
            onClick={handleToggleActive}
          >
            {isActive ? <FiPause size={16} /> : <FiPlay size={16} />}
            {isActive ? 'Остановить' : 'Запустить'}
          </ControlButton>
          <DownloadButton>
            <FiDownload size={16} />
            Экспорт данных
          </DownloadButton>
        </ActionButtons>
      </Header>
      
      <WarningBanner>
        <WarningIcon>
          <FiAlertTriangle size={20} />
        </WarningIcon>
        <WarningText>
          Внимание! Модуль C1 Brain находится в бета-версии. Некоторые функции могут работать нестабильно.
        </WarningText>
      </WarningBanner>
      
      <MainContent>
        <Panel>
          <PanelHeader>
            <PanelTitle>Статус системы</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <StatusPanel>
              <StatusCard>
                <StatusInfo>
                  <StatusLabel>Статус C1 Brain</StatusLabel>
                  <StatusValue>{isActive ? 'Активен' : 'Неактивен'}</StatusValue>
                </StatusInfo>
                <StatusIcon status={isActive ? 'active' : 'inactive'} />
              </StatusCard>
              
              <StatusCard>
                <StatusInfo>
                  <StatusLabel>Текущий режим мышления</StatusLabel>
                  <StatusValue>{currentMode}</StatusValue>
                </StatusInfo>
                <StatusIcon status="active" />
              </StatusCard>
              
              <StatusCard>
                <StatusInfo>
                  <StatusLabel>Нейронная сеть</StatusLabel>
                  <StatusValue>Подключена (v2.3.4)</StatusValue>
                </StatusInfo>
                <StatusIcon status="active" />
              </StatusCard>
              
              <StatusCard>
                <StatusInfo>
                  <StatusLabel>База знаний</StatusLabel>
                  <StatusValue>Обновлена (3 часа назад)</StatusValue>
                </StatusInfo>
                <StatusIcon status="warning" />
              </StatusCard>
            </StatusPanel>
            
            <StatsGrid>
              <StatCard>
                <StatLabel>Использование памяти</StatLabel>
                <StatValue>{memoryUsage}%</StatValue>
                <ProgressBar>
                  <Progress value={memoryUsage} />
                </ProgressBar>
              </StatCard>
              
              <StatCard>
                <StatLabel>Использование CPU</StatLabel>
                <StatValue>{cpuUsage}%</StatValue>
                <ProgressBar>
                  <Progress value={cpuUsage} />
                </ProgressBar>
              </StatCard>
              
              <StatCard>
                <StatLabel>Прогресс обучения</StatLabel>
                <StatValue>{learningProgress}%</StatValue>
                <ProgressBar>
                  <Progress value={learningProgress} />
                </ProgressBar>
              </StatCard>
              
              <StatCard>
                <StatLabel>Уровень аномалий</StatLabel>
                <StatValue>{anomalyScore}%</StatValue>
                <ProgressBar>
                  <Progress value={anomalyScore} />
                </ProgressBar>
              </StatCard>
            </StatsGrid>
            
            <ThinkingModesPanel>
              <PanelTitle>Режимы мышления</PanelTitle>
              <ThinkingModesList>
                {Object.values(ThinkingMode).map(mode => (
                  <ThinkingModeCard 
                    key={mode} 
                    active={currentMode === mode}
                    onClick={() => handleSetMode(mode)}
                  >
                    <ThinkingModeHeader>
                      <ThinkingModeName>{mode}</ThinkingModeName>
                      <ThinkingModeActiveIndicator active={currentMode === mode}>
                        {currentMode === mode ? 'Активен' : 'Неактивен'}
                      </ThinkingModeActiveIndicator>
                    </ThinkingModeHeader>
                    <ThinkingModeDescription>
                      {getThinkingModeDescription(mode)}
                    </ThinkingModeDescription>
                  </ThinkingModeCard>
                ))}
              </ThinkingModesList>
            </ThinkingModesPanel>
          </PanelContent>
        </Panel>
        
        <Panel>
          <PanelHeader>
            <PanelTitle>Консоль C1 Brain</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <ConsolePanel>
              <ConsoleOutput>
                {logs.map((log, index) => (
                  <ConsoleLog key={index}>
                    <LogTime>[{log.time}]</LogTime>
                    <LogMessage type={log.type}>{log.message}</LogMessage>
                  </ConsoleLog>
                ))}
              </ConsoleOutput>
              
              <ActionPanel>
                <PanelTitle>Быстрые промпты</PanelTitle>
                <PromptsGrid>
                  <PromptCard onClick={() => handleRunPrompt('Системный анализ')}>
                    <PromptTitle>Системный анализ</PromptTitle>
                    <PromptDescription>Комплексная проверка всех подсистем</PromptDescription>
                  </PromptCard>
                  
                  <PromptCard onClick={() => handleRunPrompt('Анализ безопасности')}>
                    <PromptTitle>Анализ безопасности</PromptTitle>
                    <PromptDescription>Проверка на уязвимости и угрозы</PromptDescription>
                  </PromptCard>
                  
                  <PromptCard onClick={() => handleRunPrompt('Финансовый анализ')}>
                    <PromptTitle>Финансовый анализ</PromptTitle>
                    <PromptDescription>Анализ банковских операций и прогнозы</PromptDescription>
                  </PromptCard>
                  
                  <PromptCard onClick={() => handleRunPrompt('Поиск аномалий')}>
                    <PromptTitle>Поиск аномалий</PromptTitle>
                    <PromptDescription>Выявление подозрительной активности</PromptDescription>
                  </PromptCard>
                </PromptsGrid>
              </ActionPanel>
            </ConsolePanel>
          </PanelContent>
        </Panel>
      </MainContent>
    </PageContainer>
  );
};

export default C1BrainPage; 