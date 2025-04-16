import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FiRefreshCw, FiEdit, FiTrash2, FiPlus, FiCheck, FiX } from 'react-icons/fi';

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

const CreateButton = styled(Button)`
  background: #3683dc;
  
  &:hover {
    background: #4394ee;
  }
`;

const SearchInput = styled.input`
  background: #1a1c23;
  border: none;
  color: white;
  font-size: 14px;
  outline: none;
  padding: 8px 16px;
  border-radius: 4px;
  width: 240px;
  margin-bottom: 24px;
  
  &::placeholder {
    color: #8a94a6;
  }
`;

const CardGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
`;

const Card = styled.div`
  background: #1a1c23;
  border-radius: 8px;
  overflow: hidden;
  transition: all 0.2s;
  
  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 24px -8px rgba(0, 0, 0, 0.3);
  }
`;

const CardHeader = styled.div`
  padding: 16px;
  background: #1e2739;
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const CardTitle = styled.h3`
  font-size: 16px;
  font-weight: 600;
  margin: 0;
`;

const CardActions = styled.div`
  display: flex;
  gap: 8px;
`;

const ActionIconButton = styled.button`
  background: none;
  border: none;
  color: #8a94a6;
  cursor: pointer;
  padding: 4px;
  transition: all 0.2s;
  
  &:hover {
    color: white;
  }
`;

const CardContent = styled.div`
  padding: 16px;
`;

const CardInfo = styled.div`
  margin-bottom: 16px;
`;

const InfoRow = styled.div`
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const InfoLabel = styled.span`
  color: #8a94a6;
  font-size: 14px;
`;

const InfoValue = styled.span`
  font-size: 14px;
  font-weight: 500;
`;

const StatusBadge = styled.span<{ active: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: ${props => props.active ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.2)'};
  color: ${props => props.active ? '#10B981' : '#EF4444'};
`;

const CardFooter = styled.div`
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.1);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #8a94a6;
`;

const LoadingIndicator = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;
  font-size: 16px;
  color: #8a94a6;
  
  svg {
    margin-right: 8px;
    animation: spin 1s linear infinite;
  }
  
  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }
`;

const NoDataMessage = styled.div`
  text-align: center;
  padding: 48px;
  color: #8a94a6;
  font-size: 16px;
`;

// Мок интерфейс для конфигурации банка
interface BankConfig {
  id: string;
  name: string;
  url: string;
  apiKey: string;
  active: boolean;
  type: 'commercial' | 'central' | 'investment' | 'crypto';
  lastUpdated: string;
  createdBy: string;
  supportsATS: boolean;
  country: string;
}

const BankConfigsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [configs, setConfigs] = useState<BankConfig[]>([]);
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  useEffect(() => {
    // Имитация загрузки данных
    const fetchData = async () => {
      setLoading(true);
      try {
        // В реальном приложении здесь будет запрос к API
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Моковые данные
        setConfigs([
          {
            id: 'bank-001',
            name: 'Сбербанк',
            url: 'https://api.sberbank.ru/v1',
            apiKey: '******************',
            active: true,
            type: 'commercial',
            lastUpdated: '2023-09-10 14:30:22',
            createdBy: 'admin',
            supportsATS: true,
            country: 'Россия'
          },
          {
            id: 'bank-002',
            name: 'ВТБ',
            url: 'https://api.vtb.ru/v2',
            apiKey: '******************',
            active: true,
            type: 'commercial',
            lastUpdated: '2023-09-12 10:15:33',
            createdBy: 'admin',
            supportsATS: true,
            country: 'Россия'
          },
          {
            id: 'bank-003',
            name: 'Тинькофф',
            url: 'https://api.tinkoff.ru/v1',
            apiKey: '******************',
            active: true,
            type: 'commercial',
            lastUpdated: '2023-09-15 09:45:10',
            createdBy: 'system',
            supportsATS: true,
            country: 'Россия'
          },
          {
            id: 'bank-004',
            name: 'Альфа-Банк',
            url: 'https://api.alfabank.ru/v1',
            apiKey: '******************',
            active: true,
            type: 'commercial',
            lastUpdated: '2023-09-14 16:20:45',
            createdBy: 'admin',
            supportsATS: true,
            country: 'Россия'
          },
          {
            id: 'bank-005',
            name: 'Райффайзенбанк',
            url: 'https://api.raiffeisen.ru/v1',
            apiKey: '******************',
            active: false,
            type: 'commercial',
            lastUpdated: '2023-09-08 11:35:50',
            createdBy: 'admin',
            supportsATS: false,
            country: 'Россия'
          },
          {
            id: 'bank-006',
            name: 'ЦБ РФ',
            url: 'https://api.cbr.ru/v1',
            apiKey: '******************',
            active: true,
            type: 'central',
            lastUpdated: '2023-09-05 08:25:30',
            createdBy: 'system',
            supportsATS: false,
            country: 'Россия'
          },
          {
            id: 'bank-007',
            name: 'Binance',
            url: 'https://api.binance.com/api/v3',
            apiKey: '******************',
            active: true,
            type: 'crypto',
            lastUpdated: '2023-09-16 12:10:15',
            createdBy: 'admin',
            supportsATS: true,
            country: 'Global'
          },
          {
            id: 'bank-008',
            name: 'Московская Биржа',
            url: 'https://api.moex.com/v1',
            apiKey: '******************',
            active: true,
            type: 'investment',
            lastUpdated: '2023-09-13 15:40:05',
            createdBy: 'system',
            supportsATS: true,
            country: 'Россия'
          }
        ]);
      } catch (error) {
        console.error('Ошибка при загрузке конфигураций банков:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  const filteredConfigs = configs.filter(config => 
    config.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    config.type.toLowerCase().includes(searchQuery.toLowerCase()) ||
    config.country.toLowerCase().includes(searchQuery.toLowerCase()) ||
    config.id.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  const handleCreateConfig = () => {
    alert('Создание новой конфигурации банка');
    // В реальном приложении здесь будет открытие модального окна или переход на страницу создания
  };
  
  const handleEditConfig = (id: string) => {
    alert(`Редактирование конфигурации банка с ID: ${id}`);
    // В реальном приложении здесь будет открытие модального окна или переход на страницу редактирования
  };
  
  const handleDeleteConfig = (id: string) => {
    if (confirm('Вы уверены, что хотите удалить эту конфигурацию банка?')) {
      setConfigs(configs.filter(config => config.id !== id));
    }
  };
  
  const handleToggleStatus = (id: string, currentStatus: boolean) => {
    setConfigs(configs.map(config => 
      config.id === id ? { ...config, active: !currentStatus } : config
    ));
  };
  
  if (loading) {
    return (
      <LoadingIndicator>
        <FiRefreshCw size={20} />
        Загрузка конфигураций банков...
      </LoadingIndicator>
    );
  }
  
  return (
    <PageContainer>
      <Header>
        <Title>Конфигурации банков</Title>
        <ActionButtons>
          <CreateButton onClick={handleCreateConfig}>
            <FiPlus size={16} />
            Новая конфигурация
          </CreateButton>
        </ActionButtons>
      </Header>
      
      <SearchInput
        placeholder="Поиск по имени, типу, стране или ID..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />
      
      {filteredConfigs.length > 0 ? (
        <CardGrid>
          {filteredConfigs.map(config => (
            <Card key={config.id}>
              <CardHeader>
                <CardTitle>{config.name}</CardTitle>
                <CardActions>
                  <ActionIconButton 
                    title={config.active ? 'Деактивировать' : 'Активировать'}
                    onClick={() => handleToggleStatus(config.id, config.active)}
                  >
                    {config.active ? <FiX size={16} /> : <FiCheck size={16} />}
                  </ActionIconButton>
                  <ActionIconButton 
                    title="Редактировать"
                    onClick={() => handleEditConfig(config.id)}
                  >
                    <FiEdit size={16} />
                  </ActionIconButton>
                  <ActionIconButton 
                    title="Удалить"
                    onClick={() => handleDeleteConfig(config.id)}
                  >
                    <FiTrash2 size={16} />
                  </ActionIconButton>
                </CardActions>
              </CardHeader>
              <CardContent>
                <CardInfo>
                  <InfoRow>
                    <InfoLabel>ID:</InfoLabel>
                    <InfoValue>{config.id}</InfoValue>
                  </InfoRow>
                  <InfoRow>
                    <InfoLabel>URL API:</InfoLabel>
                    <InfoValue>{config.url}</InfoValue>
                  </InfoRow>
                  <InfoRow>
                    <InfoLabel>Тип:</InfoLabel>
                    <InfoValue>
                      {config.type === 'commercial' && 'Коммерческий'}
                      {config.type === 'central' && 'Центральный'}
                      {config.type === 'investment' && 'Инвестиционный'}
                      {config.type === 'crypto' && 'Криптовалютный'}
                    </InfoValue>
                  </InfoRow>
                  <InfoRow>
                    <InfoLabel>Статус:</InfoLabel>
                    <StatusBadge active={config.active}>
                      {config.active ? 'Активный' : 'Неактивный'}
                    </StatusBadge>
                  </InfoRow>
                  <InfoRow>
                    <InfoLabel>Поддержка ATS:</InfoLabel>
                    <InfoValue>{config.supportsATS ? 'Да' : 'Нет'}</InfoValue>
                  </InfoRow>
                  <InfoRow>
                    <InfoLabel>Страна:</InfoLabel>
                    <InfoValue>{config.country}</InfoValue>
                  </InfoRow>
                </CardInfo>
              </CardContent>
              <CardFooter>
                <span>Создано: {config.createdBy}</span>
                <span>Обновлено: {config.lastUpdated}</span>
              </CardFooter>
            </Card>
          ))}
        </CardGrid>
      ) : (
        <NoDataMessage>
          Конфигурации не найдены. Попробуйте изменить параметры поиска или создайте новую конфигурацию.
        </NoDataMessage>
      )}
    </PageContainer>
  );
};

export default BankConfigsPage; 