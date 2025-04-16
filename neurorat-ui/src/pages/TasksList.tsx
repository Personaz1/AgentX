import React, { useState } from 'react';
import styled from 'styled-components';

// Типы
interface Task {
  id: string;
  name: string;
  type: 'collect' | 'execute' | 'analyze' | 'control';
  status: 'pending' | 'running' | 'completed' | 'failed';
  zondId: string;
  zondName: string;
  createdAt: string;
  completedAt?: string;
  progress: number;
}

// Стилизованные компоненты
const Container = styled.div`
  padding: 20px 0;
`;

const Title = styled.h1`
  font-size: 1.8rem;
  margin-bottom: 20px;
  color: ${props => props.theme.text.primary};
`;

const ControlPanel = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
`;

const Filters = styled.div`
  display: flex;
  gap: 10px;
  
  @media (max-width: 768px) {
    width: 100%;
    overflow-x: auto;
  }
`;

const FilterButton = styled.button<{ active?: boolean }>`
  padding: 8px 15px;
  border-radius: 4px;
  background-color: ${props => props.active ? props.theme.accent.primary : props.theme.bg.tertiary};
  color: ${props => props.active ? 'white' : props.theme.text.primary};
  border: none;
  cursor: pointer;
  
  &:hover {
    background-color: ${props => props.active ? props.theme.accent.secondary : '#444'};
  }
`;

const SearchInput = styled.input`
  padding: 10px;
  border-radius: 4px;
  background-color: ${props => props.theme.bg.tertiary};
  border: 1px solid #444;
  color: ${props => props.theme.text.primary};
  width: 300px;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent.primary};
  }
  
  @media (max-width: 768px) {
    width: 100%;
  }
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 10px;
`;

const Button = styled.button`
  padding: 10px 15px;
  border-radius: 4px;
  background-color: ${props => props.theme.accent.primary};
  color: white;
  border: none;
  cursor: pointer;
  
  &:hover {
    background-color: ${props => props.theme.accent.secondary};
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background-color: ${props => props.theme.bg.secondary};
  border-radius: 8px;
  overflow: hidden;
`;

const Th = styled.th`
  text-align: left;
  padding: 15px;
  border-bottom: 1px solid #444;
  color: ${props => props.theme.text.secondary};
  font-weight: 500;
`;

const Td = styled.td`
  padding: 15px;
  border-bottom: 1px solid #444;
  color: ${props => props.theme.text.primary};
`;

const StatusBadge = styled.span<{ status: 'pending' | 'running' | 'completed' | 'failed' }>`
  display: inline-block;
  padding: 5px 10px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 500;
  background-color: ${props => 
    props.status === 'pending' ? 'rgba(255, 193, 7, 0.2)' :
    props.status === 'running' ? 'rgba(0, 123, 255, 0.2)' :
    props.status === 'completed' ? 'rgba(40, 167, 69, 0.2)' :
    'rgba(220, 53, 69, 0.2)'
  };
  color: ${props => 
    props.status === 'pending' ? props.theme.warning :
    props.status === 'running' ? props.theme.info :
    props.status === 'completed' ? props.theme.success :
    props.theme.danger
  };
`;

const ProgressBar = styled.div`
  width: 100%;
  height: 8px;
  background-color: ${props => props.theme.bg.tertiary};
  border-radius: 4px;
  overflow: hidden;
`;

const ProgressIndicator = styled.div<{ progress: number }>`
  height: 100%;
  width: ${props => `${props.progress}%`};
  background-color: ${props => 
    props.progress < 30 ? props.theme.danger :
    props.progress < 70 ? props.theme.warning :
    props.theme.success
  };
`;

const ActionLink = styled.a`
  color: ${props => props.theme.accent.primary};
  text-decoration: none;
  margin-right: 10px;
  cursor: pointer;
  
  &:hover {
    text-decoration: underline;
  }
`;

const TasksList: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  
  // Моковые данные задач
  const tasks: Task[] = [
    { id: 'task-001', name: 'Сбор данных браузера', type: 'collect', status: 'completed', zondId: 'zond-001', zondName: 'Desktop-RU-Moscow-01', createdAt: '2023-10-15 10:30', completedAt: '2023-10-15 10:35', progress: 100 },
    { id: 'task-002', name: 'Удаленное выполнение кода', type: 'execute', status: 'running', zondId: 'zond-001', zondName: 'Desktop-RU-Moscow-01', createdAt: '2023-10-15 10:40', progress: 65 },
    { id: 'task-003', name: 'Кейлоггер', type: 'collect', status: 'pending', zondId: 'zond-004', zondName: 'Desktop-UK-London-01', createdAt: '2023-10-15 11:00', progress: 0 },
    { id: 'task-004', name: 'Анализ файловой системы', type: 'analyze', status: 'failed', zondId: 'zond-003', zondName: 'Server-DE-Berlin-01', createdAt: '2023-10-14 15:20', completedAt: '2023-10-14 15:22', progress: 30 },
    { id: 'task-005', name: 'Обновление C1 модуля', type: 'control', status: 'completed', zondId: 'zond-002', zondName: 'Mobile-RU-SPB-01', createdAt: '2023-10-14 12:00', completedAt: '2023-10-14 12:05', progress: 100 },
  ];
  
  // Фильтрация задач
  const filteredTasks = tasks.filter(task => {
    // Фильтр по статусу
    if (statusFilter !== 'all' && task.status !== statusFilter) return false;
    
    // Фильтр по типу
    if (typeFilter !== 'all' && task.type !== typeFilter) return false;
    
    // Поиск
    if (search && !(
      task.name.toLowerCase().includes(search.toLowerCase()) ||
      task.id.toLowerCase().includes(search.toLowerCase()) ||
      task.zondName.toLowerCase().includes(search.toLowerCase())
    )) return false;
    
    return true;
  });
  
  // Переводы статусов
  const getStatusLabel = (status: string) => {
    switch(status) {
      case 'pending': return 'Ожидание';
      case 'running': return 'Выполняется';
      case 'completed': return 'Завершено';
      case 'failed': return 'Ошибка';
      default: return status;
    }
  };
  
  // Переводы типов задач
  const getTypeLabel = (type: string) => {
    switch(type) {
      case 'collect': return 'Сбор данных';
      case 'execute': return 'Выполнение';
      case 'analyze': return 'Анализ';
      case 'control': return 'Управление';
      default: return type;
    }
  };
  
  return (
    <Container>
      <Title>Управление задачами</Title>
      
      <ControlPanel>
        <Filters>
          <FilterButton 
            active={statusFilter === 'all'} 
            onClick={() => setStatusFilter('all')}
          >
            Все статусы
          </FilterButton>
          <FilterButton 
            active={statusFilter === 'pending'} 
            onClick={() => setStatusFilter('pending')}
          >
            Ожидание
          </FilterButton>
          <FilterButton 
            active={statusFilter === 'running'} 
            onClick={() => setStatusFilter('running')}
          >
            Выполняется
          </FilterButton>
          <FilterButton 
            active={statusFilter === 'completed'} 
            onClick={() => setStatusFilter('completed')}
          >
            Завершено
          </FilterButton>
          <FilterButton 
            active={statusFilter === 'failed'} 
            onClick={() => setStatusFilter('failed')}
          >
            Ошибка
          </FilterButton>
        </Filters>
        
        <SearchInput 
          type="text" 
          placeholder="Поиск по имени, ID или зонду..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </ControlPanel>
      
      <ControlPanel>
        <Filters>
          <FilterButton 
            active={typeFilter === 'all'} 
            onClick={() => setTypeFilter('all')}
          >
            Все типы
          </FilterButton>
          <FilterButton 
            active={typeFilter === 'collect'} 
            onClick={() => setTypeFilter('collect')}
          >
            Сбор данных
          </FilterButton>
          <FilterButton 
            active={typeFilter === 'execute'} 
            onClick={() => setTypeFilter('execute')}
          >
            Выполнение
          </FilterButton>
          <FilterButton 
            active={typeFilter === 'analyze'} 
            onClick={() => setTypeFilter('analyze')}
          >
            Анализ
          </FilterButton>
          <FilterButton 
            active={typeFilter === 'control'} 
            onClick={() => setTypeFilter('control')}
          >
            Управление
          </FilterButton>
        </Filters>
        
        <ActionButtons>
          <Button>Новая задача</Button>
          <Button>Массовые действия</Button>
        </ActionButtons>
      </ControlPanel>
      
      <Table>
        <thead>
          <tr>
            <Th>ID</Th>
            <Th>Название</Th>
            <Th>Тип</Th>
            <Th>Статус</Th>
            <Th>Прогресс</Th>
            <Th>Зонд</Th>
            <Th>Создано</Th>
            <Th>Завершено</Th>
            <Th>Действия</Th>
          </tr>
        </thead>
        <tbody>
          {filteredTasks.map(task => (
            <tr key={task.id}>
              <Td>{task.id}</Td>
              <Td>{task.name}</Td>
              <Td>{getTypeLabel(task.type)}</Td>
              <Td>
                <StatusBadge status={task.status}>
                  {getStatusLabel(task.status)}
                </StatusBadge>
              </Td>
              <Td>
                <ProgressBar>
                  <ProgressIndicator progress={task.progress} />
                </ProgressBar>
              </Td>
              <Td>{task.zondName}</Td>
              <Td>{task.createdAt}</Td>
              <Td>{task.completedAt || '-'}</Td>
              <Td>
                <ActionLink href={`/tasks/${task.id}`}>Детали</ActionLink>
                {task.status === 'pending' && <ActionLink>Запустить</ActionLink>}
                {task.status === 'running' && <ActionLink>Остановить</ActionLink>}
                <ActionLink>Удалить</ActionLink>
              </Td>
            </tr>
          ))}
        </tbody>
      </Table>
    </Container>
  );
};

export default TasksList; 