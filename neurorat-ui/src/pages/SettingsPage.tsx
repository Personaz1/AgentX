import React, { useState } from 'react';
import styled from 'styled-components';

// Стили
const Container = styled.div`
  padding: 20px 0;
`;

const Title = styled.h1`
  font-size: 1.8rem;
  margin-bottom: 20px;
  color: ${props => props.theme.text.primary};
`;

const TabsContainer = styled.div`
  display: flex;
  margin-bottom: 20px;
  border-bottom: 1px solid ${props => props.theme.border.primary};
`;

const Tab = styled.div<{active: boolean}>`
  padding: 12px 20px;
  cursor: pointer;
  font-weight: ${props => props.active ? 600 : 400};
  color: ${props => props.active ? props.theme.accent.primary : props.theme.text.primary};
  position: relative;
  
  &:after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 2px;
    background-color: ${props => props.active ? props.theme.accent.primary : 'transparent'};
  }
  
  &:hover {
    color: ${props => props.active ? props.theme.accent.primary : props.theme.accent.secondary};
  }
`;

const SettingsSection = styled.div`
  background-color: ${props => props.theme.bg.secondary};
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
`;

const SectionTitle = styled.h2`
  font-size: 1.2rem;
  margin-bottom: 20px;
  color: ${props => props.theme.text.primary};
`;

const SettingGroup = styled.div`
  margin-bottom: 24px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const SettingRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const SettingLabel = styled.div`
  font-size: 1rem;
  color: ${props => props.theme.text.primary};
`;

const SettingDescription = styled.div`
  font-size: 0.85rem;
  color: ${props => props.theme.text.secondary};
  margin-top: 4px;
`;

const Input = styled.input`
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.border.primary};
  background-color: ${props => props.theme.bg.input};
  color: ${props => props.theme.text.primary};
  width: 300px;
  
  &:focus {
    border-color: ${props => props.theme.accent.primary};
    outline: none;
  }
`;

const Select = styled.select`
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.border.primary};
  background-color: ${props => props.theme.bg.input};
  color: ${props => props.theme.text.primary};
  width: 300px;
  
  &:focus {
    border-color: ${props => props.theme.accent.primary};
    outline: none;
  }
`;

const Button = styled.button<{variant?: 'primary' | 'secondary' | 'danger'}>`
  padding: 10px 15px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  
  background-color: ${props => 
    props.variant === 'danger' ? props.theme.danger :
    props.variant === 'secondary' ? props.theme.bg.tertiary :
    props.theme.accent.primary
  };
  
  color: ${props => 
    props.variant === 'secondary' ? props.theme.text.primary :
    'white'
  };
  
  &:hover {
    opacity: 0.9;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  margin-top: 30px;
`;

const ToggleSwitch = styled.label`
  position: relative;
  display: inline-block;
  width: 52px;
  height: 26px;
  
  input {
    opacity: 0;
    width: 0;
    height: 0;
  }
`;

const Slider = styled.span`
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: ${props => props.theme.bg.tertiary};
  transition: .4s;
  border-radius: 34px;
  
  &:before {
    position: absolute;
    content: "";
    height: 18px;
    width: 18px;
    left: 4px;
    bottom: 4px;
    background-color: white;
    transition: .4s;
    border-radius: 50%;
  }
  
  input:checked + & {
    background-color: ${props => props.theme.accent.primary};
  }
  
  input:checked + &:before {
    transform: translateX(26px);
  }
`;

// Компонент страницы настроек
const SettingsPage: React.FC = () => {
  // Состояния для разных настроек
  const [activeTab, setActiveTab] = useState('general');
  const [apiEndpoint, setApiEndpoint] = useState('https://api.neuronet.local/v1');
  const [logLevel, setLogLevel] = useState('info');
  const [autoUpdate, setAutoUpdate] = useState(true);
  const [connectionTimeout, setConnectionTimeout] = useState(30);
  const [darkMode, setDarkMode] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [maxConnectedZonds, setMaxConnectedZonds] = useState(100);
  const [operationsPerSecondLimit, setOperationsPerSecondLimit] = useState(50);
  const [dataRetentionDays, setDataRetentionDays] = useState(90);
  const [logsVerbosity, setLogsVerbosity] = useState('normal');
  const [encryptionKey, setEncryptionKey] = useState('**********************');
  const [adminEmail, setAdminEmail] = useState('admin@neuronet.org');
  
  // Обработчик сохранения настроек
  const handleSaveSettings = () => {
    // Имитация сохранения настроек
    console.log('Настройки сохранены');
    alert('Настройки успешно сохранены');
  };
  
  // Обработчик сброса настроек
  const handleResetSettings = () => {
    if (window.confirm('Вы уверены, что хотите сбросить все настройки до значений по умолчанию?')) {
      // Сброс всех настроек
      setApiEndpoint('https://api.neuronet.local/v1');
      setLogLevel('info');
      setAutoUpdate(true);
      setConnectionTimeout(30);
      setDarkMode(true);
      setNotificationsEnabled(true);
      setMaxConnectedZonds(100);
      setOperationsPerSecondLimit(50);
      setDataRetentionDays(90);
      setLogsVerbosity('normal');
      console.log('Настройки сброшены');
    }
  };
  
  return (
    <Container>
      <Title>Настройки системы</Title>
      
      <TabsContainer>
        <Tab active={activeTab === 'general'} onClick={() => setActiveTab('general')}>
          Общие
        </Tab>
        <Tab active={activeTab === 'security'} onClick={() => setActiveTab('security')}>
          Безопасность
        </Tab>
        <Tab active={activeTab === 'performance'} onClick={() => setActiveTab('performance')}>
          Производительность
        </Tab>
        <Tab active={activeTab === 'notifications'} onClick={() => setActiveTab('notifications')}>
          Уведомления
        </Tab>
        <Tab active={activeTab === 'advanced'} onClick={() => setActiveTab('advanced')}>
          Расширенные
        </Tab>
      </TabsContainer>
      
      {/* Общие настройки */}
      {activeTab === 'general' && (
        <>
          <SettingsSection>
            <SectionTitle>Базовые настройки</SectionTitle>
            
            <SettingGroup>
              <SettingRow>
                <div>
                  <SettingLabel>API эндпоинт</SettingLabel>
                  <SettingDescription>URL для подключения к API</SettingDescription>
                </div>
                <Input 
                  type="text" 
                  value={apiEndpoint} 
                  onChange={e => setApiEndpoint(e.target.value)} 
                />
              </SettingRow>
              
              <SettingRow>
                <div>
                  <SettingLabel>Email администратора</SettingLabel>
                  <SettingDescription>Адрес для уведомлений системы</SettingDescription>
                </div>
                <Input 
                  type="email" 
                  value={adminEmail} 
                  onChange={e => setAdminEmail(e.target.value)} 
                />
              </SettingRow>
              
              <SettingRow>
                <div>
                  <SettingLabel>Уровень логирования</SettingLabel>
                  <SettingDescription>Детализация системных логов</SettingDescription>
                </div>
                <Select 
                  value={logLevel} 
                  onChange={e => setLogLevel(e.target.value)}
                >
                  <option value="error">Только ошибки</option>
                  <option value="warn">Предупреждения</option>
                  <option value="info">Информационный</option>
                  <option value="debug">Отладка</option>
                  <option value="verbose">Детальный</option>
                </Select>
              </SettingRow>
              
              <SettingRow>
                <div>
                  <SettingLabel>Автоматические обновления</SettingLabel>
                  <SettingDescription>Автоматически проверять и устанавливать обновления</SettingDescription>
                </div>
                <ToggleSwitch>
                  <input 
                    type="checkbox" 
                    checked={autoUpdate} 
                    onChange={() => setAutoUpdate(!autoUpdate)} 
                  />
                  <Slider />
                </ToggleSwitch>
              </SettingRow>
              
              <SettingRow>
                <div>
                  <SettingLabel>Таймаут соединения (сек)</SettingLabel>
                  <SettingDescription>Время ожидания ответа от зондов</SettingDescription>
                </div>
                <Input 
                  type="number" 
                  value={connectionTimeout} 
                  onChange={e => setConnectionTimeout(Number(e.target.value))} 
                />
              </SettingRow>
            </SettingGroup>
          </SettingsSection>
          
          <SettingsSection>
            <SectionTitle>Настройки интерфейса</SectionTitle>
            
            <SettingGroup>
              <SettingRow>
                <div>
                  <SettingLabel>Темная тема</SettingLabel>
                  <SettingDescription>Использовать темный режим интерфейса</SettingDescription>
                </div>
                <ToggleSwitch>
                  <input 
                    type="checkbox" 
                    checked={darkMode} 
                    onChange={() => setDarkMode(!darkMode)} 
                  />
                  <Slider />
                </ToggleSwitch>
              </SettingRow>
              
              <SettingRow>
                <div>
                  <SettingLabel>Уведомления</SettingLabel>
                  <SettingDescription>Показывать системные уведомления</SettingDescription>
                </div>
                <ToggleSwitch>
                  <input 
                    type="checkbox" 
                    checked={notificationsEnabled} 
                    onChange={() => setNotificationsEnabled(!notificationsEnabled)} 
                  />
                  <Slider />
                </ToggleSwitch>
              </SettingRow>
            </SettingGroup>
          </SettingsSection>
        </>
      )}
      
      {/* Настройки безопасности */}
      {activeTab === 'security' && (
        <SettingsSection>
          <SectionTitle>Параметры безопасности</SectionTitle>
          
          <SettingGroup>
            <SettingRow>
              <div>
                <SettingLabel>Ключ шифрования</SettingLabel>
                <SettingDescription>Используется для шифрования данных</SettingDescription>
              </div>
              <Input 
                type="password" 
                value={encryptionKey} 
                onChange={e => setEncryptionKey(e.target.value)} 
              />
            </SettingRow>
            
            <SettingRow>
              <div>
                <SettingLabel>Срок хранения данных (дни)</SettingLabel>
                <SettingDescription>Период хранения собранной информации</SettingDescription>
              </div>
              <Input 
                type="number" 
                value={dataRetentionDays} 
                onChange={e => setDataRetentionDays(Number(e.target.value))} 
              />
            </SettingRow>
            
            <SettingRow>
              <div>
                <SettingLabel>Двухфакторная аутентификация</SettingLabel>
                <SettingDescription>Усиленная защита доступа к системе</SettingDescription>
              </div>
              <ToggleSwitch>
                <input 
                  type="checkbox" 
                  checked={true} 
                  readOnly 
                />
                <Slider />
              </ToggleSwitch>
            </SettingRow>
          </SettingGroup>
        </SettingsSection>
      )}
      
      {/* Настройки производительности */}
      {activeTab === 'performance' && (
        <SettingsSection>
          <SectionTitle>Параметры производительности</SectionTitle>
          
          <SettingGroup>
            <SettingRow>
              <div>
                <SettingLabel>Макс. кол-во подключенных зондов</SettingLabel>
                <SettingDescription>Лимит одновременно подключенных устройств</SettingDescription>
              </div>
              <Input 
                type="number" 
                value={maxConnectedZonds} 
                onChange={e => setMaxConnectedZonds(Number(e.target.value))} 
              />
            </SettingRow>
            
            <SettingRow>
              <div>
                <SettingLabel>Лимит операций в секунду</SettingLabel>
                <SettingDescription>Ограничение для предотвращения перегрузки</SettingDescription>
              </div>
              <Input 
                type="number" 
                value={operationsPerSecondLimit} 
                onChange={e => setOperationsPerSecondLimit(Number(e.target.value))} 
              />
            </SettingRow>
          </SettingGroup>
        </SettingsSection>
      )}
      
      {/* Настройки уведомлений */}
      {activeTab === 'notifications' && (
        <SettingsSection>
          <SectionTitle>Настройки уведомлений</SectionTitle>
          
          <SettingGroup>
            <SettingRow>
              <div>
                <SettingLabel>Уведомления о новых зондах</SettingLabel>
                <SettingDescription>Оповещения при подключении новых устройств</SettingDescription>
              </div>
              <ToggleSwitch>
                <input 
                  type="checkbox" 
                  checked={true} 
                  onChange={() => {}} 
                />
                <Slider />
              </ToggleSwitch>
            </SettingRow>
            
            <SettingRow>
              <div>
                <SettingLabel>Уведомления об ошибках</SettingLabel>
                <SettingDescription>Оповещения о критических сбоях системы</SettingDescription>
              </div>
              <ToggleSwitch>
                <input 
                  type="checkbox" 
                  checked={true} 
                  onChange={() => {}} 
                />
                <Slider />
              </ToggleSwitch>
            </SettingRow>
            
            <SettingRow>
              <div>
                <SettingLabel>Уведомления о выполненных задачах</SettingLabel>
                <SettingDescription>Оповещения о завершении операций</SettingDescription>
              </div>
              <ToggleSwitch>
                <input 
                  type="checkbox" 
                  checked={false} 
                  onChange={() => {}} 
                />
                <Slider />
              </ToggleSwitch>
            </SettingRow>
          </SettingGroup>
        </SettingsSection>
      )}
      
      {/* Расширенные настройки */}
      {activeTab === 'advanced' && (
        <SettingsSection>
          <SectionTitle>Расширенные настройки</SectionTitle>
          
          <SettingGroup>
            <SettingRow>
              <div>
                <SettingLabel>Детализация логов</SettingLabel>
                <SettingDescription>Уровень подробности журналов</SettingDescription>
              </div>
              <Select 
                value={logsVerbosity} 
                onChange={e => setLogsVerbosity(e.target.value)}
              >
                <option value="minimal">Минимальная</option>
                <option value="normal">Стандартная</option>
                <option value="detailed">Детальная</option>
                <option value="debug">Отладочная</option>
              </Select>
            </SettingRow>
            
            <SettingRow>
              <div>
                <SettingLabel>Экспериментальные функции</SettingLabel>
                <SettingDescription>Активировать тестовые возможности</SettingDescription>
              </div>
              <ToggleSwitch>
                <input 
                  type="checkbox" 
                  checked={false} 
                  onChange={() => {}} 
                />
                <Slider />
              </ToggleSwitch>
            </SettingRow>
          </SettingGroup>
        </SettingsSection>
      )}
      
      {/* Кнопки действий */}
      <ButtonGroup>
        <Button variant="secondary" onClick={handleResetSettings}>
          Сбросить настройки
        </Button>
        <Button onClick={handleSaveSettings}>
          Сохранить изменения
        </Button>
      </ButtonGroup>
    </Container>
  );
};

export default SettingsPage; 