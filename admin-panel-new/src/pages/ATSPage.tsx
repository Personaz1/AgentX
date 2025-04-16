import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FiRefreshCw, FiPlay, FiPause, FiDownload, FiAlertTriangle, FiBarChart2, FiDollarSign, FiCheck, FiX } from 'react-icons/fi';

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
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr;
  }
`;

const Panel = styled.div`
  background: #1a1c23;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 24px;
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

const TransactionsList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 500px;
  overflow-y: auto;
`;

const TransactionCard = styled.div`
  background: rgba(30, 39, 57, 0.5);
  border-radius: 6px;
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 16px;
`;

const TransactionIcon = styled.div<{ type: 'deposit' | 'withdrawal' | 'transfer' }>`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: ${props => {
    switch (props.type) {
      case 'deposit': return 'rgba(16, 185, 129, 0.2)';
      case 'withdrawal': return 'rgba(239, 68, 68, 0.2)';
      case 'transfer': return 'rgba(54, 131, 220, 0.2)';
      default: return 'rgba(30, 39, 57, 0.5)';
    }
  }};
  color: ${props => {
    switch (props.type) {
      case 'deposit': return '#10B981';
      case 'withdrawal': return '#EF4444';
      case 'transfer': return '#3683dc';
      default: return '#8a94a6';
    }
  }};
  display: flex;
  align-items: center;
  justify-content: center;
`;

const TransactionInfo = styled.div`
  flex: 1;
`;

const TransactionHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
`;

const TransactionName = styled.span`
  font-size: 16px;
  font-weight: 500;
`;

const TransactionAmount = styled.span<{ type: 'deposit' | 'withdrawal' | 'transfer' }>`
  font-size: 16px;
  font-weight: 600;
  color: ${props => {
    switch (props.type) {
      case 'deposit': return '#10B981';
      case 'withdrawal': return '#EF4444';
      case 'transfer': return '#3683dc';
      default: return '#8a94a6';
    }
  }};
`;

const TransactionDetails = styled.div`
  display: flex;
  justify-content: space-between;
`;

const TransactionDetail = styled.span`
  font-size: 14px;
  color: #8a94a6;
`;

const TransactionStatus = styled.div<{ status: 'completed' | 'pending' | 'failed' }>`
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  font-weight: 500;
  color: ${props => {
    switch (props.status) {
      case 'completed': return '#10B981';
      case 'pending': return '#F59E0B';
      case 'failed': return '#EF4444';
      default: return '#8a94a6';
    }
  }};
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

const RulesList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const RuleCard = styled.div<{ active: boolean }>`
  background: ${props => props.active ? 'rgba(54, 131, 220, 0.2)' : 'rgba(30, 39, 57, 0.5)'};
  border: 1px solid ${props => props.active ? '#3683dc' : 'transparent'};
  border-radius: 6px;
  padding: 16px;
  display: flex;
  flex-direction: column;
`;

const RuleHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
`;

const RuleName = styled.span`
  font-size: 16px;
  font-weight: 500;
`;

const RuleStatus = styled.div`
  display: flex;
  align-items: center;
`;

const ToggleSwitch = styled.div<{ active: boolean }>`
  width: 36px;
  height: 20px;
  background: ${props => props.active ? '#10B981' : '#4b5563'};
  border-radius: 10px;
  position: relative;
  cursor: pointer;
  transition: all 0.2s;
  
  &:before {
    content: '';
    position: absolute;
    left: ${props => props.active ? '18px' : '2px'};
    top: 2px;
    width: 16px;
    height: 16px;
    background: white;
    border-radius: 50%;
    transition: all 0.2s;
  }
`;

const RuleDescription = styled.p`
  font-size: 14px;
  color: #8a94a6;
  margin: 0 0 8px 0;
`;

const RuleSettings = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 8px;
  background: rgba(30, 39, 57, 0.3);
  border-radius: 4px;
  margin-top: 8px;
`;

const RuleSetting = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const RuleSettingLabel = styled.span`
  font-size: 14px;
  color: #8a94a6;
`;

const RuleSettingValue = styled.span`
  font-size: 14px;
  font-weight: 500;
`;

enum TransactionType {
  DEPOSIT = 'deposit',
  WITHDRAWAL = 'withdrawal',
  TRANSFER = 'transfer'
}

enum TransactionStatus {
  COMPLETED = 'completed',
  PENDING = 'pending',
  FAILED = 'failed'
}

interface Transaction {
  id: string;
  type: TransactionType;
  amount: number;
  currency: string;
  description: string;
  date: string;
  time: string;
  status: TransactionStatus;
  bank: string;
}

interface Rule {
  id: string;
  name: string;
  description: string;
  active: boolean;
  settings: {
    [key: string]: string | number | boolean;
  };
}

const ATSPage: React.FC = () => {
  const [isActive, setIsActive] = useState<boolean>(false);
  const [transactions, setTransactions] = useState<Transaction[]>([
    {
      id: '1',
      type: TransactionType.DEPOSIT,
      amount: 5000,
      currency: 'RUB',
      description: 'Пополнение счета',
      date: '28.09.2023',
      time: '14:32',
      status: TransactionStatus.COMPLETED,
      bank: 'Сбербанк'
    },
    {
      id: '2',
      type: TransactionType.WITHDRAWAL,
      amount: 1500,
      currency: 'RUB',
      description: 'Снятие средств',
      date: '27.09.2023',
      time: '10:15',
      status: TransactionStatus.COMPLETED,
      bank: 'Тинькофф'
    },
    {
      id: '3',
      type: TransactionType.TRANSFER,
      amount: 3000,
      currency: 'RUB',
      description: 'Перевод на карту',
      date: '26.09.2023',
      time: '18:45',
      status: TransactionStatus.COMPLETED,
      bank: 'Альфа-Банк'
    },
    {
      id: '4',
      type: TransactionType.DEPOSIT,
      amount: 10000,
      currency: 'RUB',
      description: 'Пополнение счета',
      date: '25.09.2023',
      time: '09:30',
      status: TransactionStatus.COMPLETED,
      bank: 'ВТБ'
    },
    {
      id: '5',
      type: TransactionType.WITHDRAWAL,
      amount: 2000,
      currency: 'RUB',
      description: 'Снятие средств',
      date: '24.09.2023',
      time: '16:20',
      status: TransactionStatus.FAILED,
      bank: 'Сбербанк'
    },
    {
      id: '6',
      type: TransactionType.TRANSFER,
      amount: 7500,
      currency: 'RUB',
      description: 'Перевод на счет',
      date: '23.09.2023',
      time: '12:10',
      status: TransactionStatus.PENDING,
      bank: 'Райффайзен'
    }
  ]);
  
  const [rules, setRules] = useState<Rule[]>([
    {
      id: '1',
      name: 'Автоматическое снятие',
      description: 'Периодическое снятие средств на основе заданного графика',
      active: true,
      settings: {
        amount: 1500,
        frequency: 'Еженедельно',
        dayOfWeek: 'Пятница',
        time: '10:00',
        bank: 'Тинькофф'
      }
    },
    {
      id: '2',
      name: 'Автоматический перевод',
      description: 'Перевод средств при достижении определенного баланса на счете',
      active: false,
      settings: {
        thresholdAmount: 50000,
        transferAmount: 30000,
        targetAccount: 'Сберегательный счет',
        bank: 'Сбербанк'
      }
    },
    {
      id: '3',
      name: 'Интеллектуальное распределение',
      description: 'Распределение средств между счетами на основе ИИ-анализа',
      active: true,
      settings: {
        minBalance: 10000,
        maxAllocation: 70,
        riskLevel: 'Средний',
        preferredBanks: 'Все'
      }
    },
    {
      id: '4',
      name: 'Защита от мошенничества',
      description: 'Блокировка подозрительных транзакций на основе поведенческого анализа',
      active: true,
      settings: {
        sensitivityLevel: 'Высокий',
        notifyOnBlock: true,
        blockThreshold: 85,
        autoReport: true
      }
    }
  ]);
  
  const [totalBalance, setTotalBalance] = useState<number>(125000);
  const [monthlyVolume, setMonthlyVolume] = useState<number>(45000);
  const [activeRules, setActiveRules] = useState<number>(3);
  const [successRate, setSuccessRate] = useState<number>(92);
  
  const handleToggleActive = () => {
    setIsActive(prev => !prev);
  };
  
  const handleToggleRule = (id: string) => {
    setRules(prev => 
      prev.map(rule => 
        rule.id === id ? {...rule, active: !rule.active} : rule
      )
    );
    
    // Обновляем количество активных правил
    const updatedRules = rules.map(rule => 
      rule.id === id ? {...rule, active: !rule.active} : rule
    );
    
    setActiveRules(updatedRules.filter(rule => rule.active).length);
  };
  
  const getTransactionIcon = (type: TransactionType) => {
    switch(type) {
      case TransactionType.DEPOSIT:
        return <FiDownload size={20} />;
      case TransactionType.WITHDRAWAL:
        return <FiDollarSign size={20} />;
      case TransactionType.TRANSFER:
        return <FiRefreshCw size={20} />;
      default:
        return <FiBarChart2 size={20} />;
    }
  };
  
  const getStatusIcon = (status: TransactionStatus) => {
    switch(status) {
      case TransactionStatus.COMPLETED:
        return <FiCheck size={14} />;
      case TransactionStatus.PENDING:
        return <FiRefreshCw size={14} />;
      case TransactionStatus.FAILED:
        return <FiX size={14} />;
      default:
        return null;
    }
  };
  
  return (
    <PageContainer>
      <Header>
        <Title>ATS - Автоматизированная система транзакций</Title>
        <ActionButtons>
          <ControlButton 
            active={isActive}
            onClick={handleToggleActive}
          >
            {isActive ? <FiPause size={16} /> : <FiPlay size={16} />}
            {isActive ? 'Остановить ATS' : 'Запустить ATS'}
          </ControlButton>
          <DownloadButton>
            <FiDownload size={16} />
            Экспорт отчета
          </DownloadButton>
        </ActionButtons>
      </Header>
      
      <WarningBanner>
        <WarningIcon>
          <FiAlertTriangle size={20} />
        </WarningIcon>
        <WarningText>
          Внимание! Модуль ATS выполняет реальные финансовые операции. Убедитесь в правильности настроек перед активацией.
        </WarningText>
      </WarningBanner>
      
      <MainContent>
        <div>
          <Panel>
            <PanelHeader>
              <PanelTitle>Статистика</PanelTitle>
            </PanelHeader>
            <PanelContent>
              <StatsGrid>
                <StatCard>
                  <StatLabel>Общий баланс</StatLabel>
                  <StatValue>{totalBalance.toLocaleString()} ₽</StatValue>
                </StatCard>
                
                <StatCard>
                  <StatLabel>Месячный объем</StatLabel>
                  <StatValue>{monthlyVolume.toLocaleString()} ₽</StatValue>
                </StatCard>
                
                <StatCard>
                  <StatLabel>Активных правил</StatLabel>
                  <StatValue>{activeRules}</StatValue>
                </StatCard>
                
                <StatCard>
                  <StatLabel>Успешность транзакций</StatLabel>
                  <StatValue>{successRate}%</StatValue>
                </StatCard>
              </StatsGrid>
            </PanelContent>
          </Panel>
          
          <Panel>
            <PanelHeader>
              <PanelTitle>Последние транзакции</PanelTitle>
            </PanelHeader>
            <PanelContent>
              <TransactionsList>
                {transactions.map(transaction => (
                  <TransactionCard key={transaction.id}>
                    <TransactionIcon type={transaction.type}>
                      {getTransactionIcon(transaction.type)}
                    </TransactionIcon>
                    <TransactionInfo>
                      <TransactionHeader>
                        <TransactionName>{transaction.description}</TransactionName>
                        <TransactionAmount type={transaction.type}>
                          {transaction.type === TransactionType.DEPOSIT ? '+' : 
                           transaction.type === TransactionType.WITHDRAWAL ? '-' : ''}
                          {transaction.amount.toLocaleString()} {transaction.currency}
                        </TransactionAmount>
                      </TransactionHeader>
                      <TransactionDetails>
                        <TransactionDetail>{transaction.bank} • {transaction.date} {transaction.time}</TransactionDetail>
                        <TransactionStatus status={transaction.status}>
                          {getStatusIcon(transaction.status)}
                          {transaction.status === TransactionStatus.COMPLETED ? 'Выполнено' : 
                           transaction.status === TransactionStatus.PENDING ? 'В обработке' : 'Ошибка'}
                        </TransactionStatus>
                      </TransactionDetails>
                    </TransactionInfo>
                  </TransactionCard>
                ))}
              </TransactionsList>
            </PanelContent>
          </Panel>
        </div>
        
        <div>
          <Panel>
            <PanelHeader>
              <PanelTitle>Статус системы</PanelTitle>
            </PanelHeader>
            <PanelContent>
              <StatusPanel>
                <StatusCard>
                  <StatusInfo>
                    <StatusLabel>Статус ATS</StatusLabel>
                    <StatusValue>{isActive ? 'Активна' : 'Неактивна'}</StatusValue>
                  </StatusInfo>
                  <StatusIcon status={isActive ? 'active' : 'inactive'} />
                </StatusCard>
                
                <StatusCard>
                  <StatusInfo>
                    <StatusLabel>Банковские интеграции</StatusLabel>
                    <StatusValue>Подключены (4/5)</StatusValue>
                  </StatusInfo>
                  <StatusIcon status="warning" />
                </StatusCard>
                
                <StatusCard>
                  <StatusInfo>
                    <StatusLabel>C1 Brain соединение</StatusLabel>
                    <StatusValue>Стабильное</StatusValue>
                  </StatusInfo>
                  <StatusIcon status="active" />
                </StatusCard>
                
                <StatusCard>
                  <StatusInfo>
                    <StatusLabel>Последняя синхронизация</StatusLabel>
                    <StatusValue>5 минут назад</StatusValue>
                  </StatusInfo>
                  <StatusIcon status="active" />
                </StatusCard>
              </StatusPanel>
            </PanelContent>
          </Panel>
          
          <Panel>
            <PanelHeader>
              <PanelTitle>Правила автоматизации</PanelTitle>
            </PanelHeader>
            <PanelContent>
              <RulesList>
                {rules.map(rule => (
                  <RuleCard key={rule.id} active={rule.active}>
                    <RuleHeader>
                      <RuleName>{rule.name}</RuleName>
                      <RuleStatus>
                        <ToggleSwitch 
                          active={rule.active}
                          onClick={() => handleToggleRule(rule.id)}
                        />
                      </RuleStatus>
                    </RuleHeader>
                    <RuleDescription>{rule.description}</RuleDescription>
                    
                    {rule.active && (
                      <RuleSettings>
                        {Object.entries(rule.settings).map(([key, value]) => (
                          <RuleSetting key={key}>
                            <RuleSettingLabel>{key.charAt(0).toUpperCase() + key.slice(1).replace(/([A-Z])/g, ' $1')}</RuleSettingLabel>
                            <RuleSettingValue>{value.toString()}</RuleSettingValue>
                          </RuleSetting>
                        ))}
                      </RuleSettings>
                    )}
                  </RuleCard>
                ))}
              </RulesList>
            </PanelContent>
          </Panel>
        </div>
      </MainContent>
    </PageContainer>
  );
};

export default ATSPage; 