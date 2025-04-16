import React from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

const PageContainer = styled.div`
  padding: 24px;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
`;

const Title = styled.h1`
  font-size: 28px;
  font-weight: 700;
  color: #F8F8F2;
  margin: 0;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
  margin-bottom: 36px;
`;

const StatCard = styled.div<{ color: string }>`
  background-color: #282A36;
  border-radius: 8px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background-color: ${props => props.color};
  }
`;

const StatTitle = styled.h3`
  font-size: 14px;
  font-weight: 500;
  color: #6C7293;
  margin: 0 0 12px 0;
`;

const StatValue = styled.p`
  font-size: 32px;
  font-weight: 700;
  color: #F8F8F2;
  margin: 0 0 8px 0;
`;

const StatTrend = styled.div<{ positive?: boolean }>`
  font-size: 14px;
  color: ${props => props.positive ? '#50FA7B' : '#FF5555'};
  display: flex;
  align-items: center;
  gap: 4px;
`;

const SectionsGrid = styled.div`
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  
  @media (max-width: 1024px) {
    grid-template-columns: 1fr;
  }
`;

const Section = styled.div`
  background-color: #282A36;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
`;

const SectionTitle = styled.h2`
  font-size: 18px;
  font-weight: 600;
  color: #F8F8F2;
  margin: 0 0 16px 0;
  border-bottom: 1px solid #44475A;
  padding-bottom: 10px;
`;

const AlertList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

const Alert = styled.div<{ severity: 'critical' | 'high' | 'medium' | 'low' }>`
  padding: 16px;
  border-radius: 6px;
  background-color: ${props => {
    switch(props.severity) {
      case 'critical': return 'rgba(255, 85, 85, 0.15)';
      case 'high': return 'rgba(255, 184, 108, 0.15)';
      case 'medium': return 'rgba(241, 250, 140, 0.15)';
      case 'low': return 'rgba(139, 233, 253, 0.15)';
      default: return 'transparent';
    }
  }};
  border-left: 4px solid ${props => {
    switch(props.severity) {
      case 'critical': return '#FF5555';
      case 'high': return '#FFB86C';
      case 'medium': return '#F1FA8C';
      case 'low': return '#8BE9FD';
      default: return 'transparent';
    }
  }};
`;

const AlertTitle = styled.h4`
  font-size: 16px;
  font-weight: 600;
  color: #F8F8F2;
  margin: 0 0 8px 0;
`;

const AlertInfo = styled.p`
  font-size: 14px;
  color: #6C7293;
  margin: 0;
`;

const EventList = styled.div`
  display: flex;
  flex-direction: column;
`;

const Event = styled.div`
  padding: 12px 0;
  border-bottom: 1px solid #44475A;
  
  &:last-child {
    border-bottom: none;
  }
`;

const EventTime = styled.span`
  font-size: 12px;
  color: #6C7293;
  display: block;
  margin-bottom: 4px;
`;

const EventDescription = styled.p`
  font-size: 14px;
  color: #F8F8F2;
  margin: 0;
`;

const ZondCard = styled.div`
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-radius: 6px;
  background-color: #1E1E2E;
  margin-bottom: 16px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const ZondStatus = styled.div<{ status: string }>`
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background-color: ${props => {
    switch(props.status) {
      case 'active': return '#50FA7B';
      case 'inactive': return '#6C7293';
      case 'error': return '#FF5555';
      default: return '#6C7293';
    }
  }};
`;

const ZondInfo = styled.div`
  flex: 1;
`;

const ZondName = styled.h4`
  font-size: 16px;
  font-weight: 600;
  color: #F8F8F2;
  margin: 0 0 4px 0;
`;

const ZondDetails = styled.p`
  font-size: 12px;
  color: #6C7293;
  margin: 0;
`;

const ActionButton = styled.button`
  padding: 8px 16px;
  background-color: #44475A;
  color: #F8F8F2;
  border: none;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  
  &:hover {
    background-color: #6272A4;
  }
`;

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  
  const handleViewZonds = () => {
    navigate('/zonds');
  };
  
  const handleViewAnomalies = () => {
    navigate('/anomalies');
  };
  
  const handleViewIncidents = () => {
    navigate('/incidents');
  };
  
  return (
    <PageContainer>
      <Header>
        <Title>Панель управления</Title>
      </Header>
      
      <StatsGrid>
        <StatCard color="#BD93F9">
          <StatTitle>Активные зонды</StatTitle>
          <StatValue>24</StatValue>
          <StatTrend positive>
            +2 за последние 24 часа
          </StatTrend>
        </StatCard>
        
        <StatCard color="#FF5555">
          <StatTitle>Обнаруженные аномалии</StatTitle>
          <StatValue>8</StatValue>
          <StatTrend>
            +3 за последние 24 часа
          </StatTrend>
        </StatCard>
        
        <StatCard color="#FFB86C">
          <StatTitle>Открытые инциденты</StatTitle>
          <StatValue>4</StatValue>
          <StatTrend>
            +1 за последние 24 часа
          </StatTrend>
        </StatCard>
        
        <StatCard color="#50FA7B">
          <StatTitle>Общий статус системы</StatTitle>
          <StatValue>97%</StatValue>
          <StatTrend positive>
            +2% за последние 24 часа
          </StatTrend>
        </StatCard>
      </StatsGrid>
      
      <SectionsGrid>
        <div>
          <Section>
            <SectionTitle>Недавние предупреждения</SectionTitle>
            <AlertList>
              <Alert severity="critical">
                <AlertTitle>Обнаружена подозрительная активность в сети</AlertTitle>
                <AlertInfo>Зонд #12 зафиксировал необычный сетевой трафик в течение последних 30 минут</AlertInfo>
              </Alert>
              
              <Alert severity="high">
                <AlertTitle>Попытка несанкционированного доступа</AlertTitle>
                <AlertInfo>Многократные попытки входа в систему с IP 185.173.x.x</AlertInfo>
              </Alert>
              
              <Alert severity="medium">
                <AlertTitle>Необычная активность пользователя</AlertTitle>
                <AlertInfo>Массовое скачивание файлов пользователем admin в нерабочее время</AlertInfo>
              </Alert>
            </AlertList>
            
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <ActionButton onClick={handleViewAnomalies}>Показать все аномалии</ActionButton>
            </div>
          </Section>
          
          <Section>
            <SectionTitle>События системы</SectionTitle>
            <EventList>
              <Event>
                <EventTime>Сегодня, 14:32</EventTime>
                <EventDescription>Зонд #45 подключился к сети</EventDescription>
              </Event>
              
              <Event>
                <EventTime>Сегодня, 13:17</EventTime>
                <EventDescription>Обновлены правила обнаружения аномалий</EventDescription>
              </Event>
              
              <Event>
                <EventTime>Сегодня, 11:05</EventTime>
                <EventDescription>Пользователь admin вошел в систему</EventDescription>
              </Event>
              
              <Event>
                <EventTime>Сегодня, 09:23</EventTime>
                <EventDescription>Инцидент #1234 закрыт</EventDescription>
              </Event>
              
              <Event>
                <EventTime>Сегодня, 08:15</EventTime>
                <EventDescription>Выполнена ежедневная синхронизация данных</EventDescription>
              </Event>
            </EventList>
          </Section>
        </div>
        
        <div>
          <Section>
            <SectionTitle>Последние инциденты</SectionTitle>
            <AlertList>
              <Alert severity="high">
                <AlertTitle>INC-2024-007: Утечка данных</AlertTitle>
                <AlertInfo>Статус: В расследовании • Создан: 12.06.2024</AlertInfo>
              </Alert>
              
              <Alert severity="critical">
                <AlertTitle>INC-2024-006: Вирусная активность</AlertTitle>
                <AlertInfo>Статус: Открыт • Создан: 11.06.2024</AlertInfo>
              </Alert>
              
              <Alert severity="medium">
                <AlertTitle>INC-2024-005: Нарушение политик безопасности</AlertTitle>
                <AlertInfo>Статус: Закрыт • Создан: 10.06.2024</AlertInfo>
              </Alert>
            </AlertList>
            
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <ActionButton onClick={handleViewIncidents}>Показать все инциденты</ActionButton>
            </div>
          </Section>
          
          <Section>
            <SectionTitle>Зонды с ошибками</SectionTitle>
            <ZondCard>
              <ZondStatus status="error" />
              <ZondInfo>
                <ZondName>Зонд #37 - Финансовый кластер</ZondName>
                <ZondDetails>Ошибка с 08:45 • Последняя активность: 13 минут назад</ZondDetails>
              </ZondInfo>
            </ZondCard>
            
            <ZondCard>
              <ZondStatus status="error" />
              <ZondInfo>
                <ZondName>Зонд #22 - Серверная зона DMZ</ZondName>
                <ZondDetails>Ошибка с 10:12 • Последняя активность: 25 минут назад</ZondDetails>
              </ZondInfo>
            </ZondCard>
            
            <div style={{ textAlign: 'center', marginTop: '16px' }}>
              <ActionButton onClick={handleViewZonds}>Управление зондами</ActionButton>
            </div>
          </Section>
        </div>
      </SectionsGrid>
    </PageContainer>
  );
};

export default Dashboard; 