import React, { useState } from 'react';
import styled from 'styled-components';

// Типы
interface ReportData {
  id: string;
  title: string;
  date: string;
  type: 'security' | 'activity' | 'performance' | 'financial' | 'summary';
  status: 'готов' | 'в обработке' | 'ошибка';
  size: string;
  author: string;
}

interface StatData {
  label: string;
  value: number;
  change: number;
  unit?: string;
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

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const StatCard = styled.div`
  background-color: ${props => props.theme.bg.secondary};
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
`;

const StatLabel = styled.div`
  font-size: 0.9rem;
  color: ${props => props.theme.text.secondary};
  margin-bottom: 10px;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: 600;
  color: ${props => props.theme.text.primary};
  margin-bottom: 5px;
  display: flex;
  align-items: baseline;
`;

const Unit = styled.span`
  font-size: 1rem;
  font-weight: 400;
  color: ${props => props.theme.text.secondary};
  margin-left: 4px;
`;

const StatChange = styled.div<{positive: boolean}>`
  font-size: 0.9rem;
  font-weight: 500;
  color: ${props => props.positive ? props.theme.success : props.theme.danger};
  display: flex;
  align-items: center;
  gap: 4px;
`;

const Arrow = styled.span<{positive: boolean}>`
  font-size: 1rem;
  transform: ${props => props.positive ? 'rotate(-45deg)' : 'rotate(45deg)'};
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

const ControlPanel = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
`;

const SearchAndFilter = styled.div`
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

const Button = styled.button<{variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning'}>`
  padding: 10px 15px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  
  background-color: ${props => 
    props.variant === 'danger' ? props.theme.danger :
    props.variant === 'success' ? props.theme.success :
    props.variant === 'warning' ? props.theme.warning :
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

const DataTable = styled.table`
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 30px;
`;

const TableHead = styled.thead`
  background-color: ${props => props.theme.bg.secondary};
  border-bottom: 1px solid ${props => props.theme.border.primary};
`;

const TableRow = styled.tr`
  border-bottom: 1px solid ${props => props.theme.border.primary};
  
  &:hover {
    background-color: ${props => props.theme.bg.hover};
  }
`;

const TableHeaderCell = styled.th`
  text-align: left;
  padding: 12px 16px;
  font-weight: 500;
  color: ${props => props.theme.text.secondary};
  font-size: 0.9rem;
`;

const TableCell = styled.td`
  padding: 12px 16px;
  color: ${props => props.theme.text.primary};
  font-size: 0.9rem;
`;

const StatusBadge = styled.span<{status: string}>`
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 500;
  
  background-color: ${props => 
    props.status === 'готов' ? 'rgba(16, 185, 129, 0.1)' :
    props.status === 'в обработке' ? 'rgba(245, 158, 11, 0.1)' :
    'rgba(239, 68, 68, 0.1)'
  };
  
  color: ${props => 
    props.status === 'готов' ? props.theme.success :
    props.status === 'в обработке' ? props.theme.warning :
    props.theme.danger
  };
`;

const ActionsCell = styled.div`
  display: flex;
  gap: 10px;
`;

const IconButton = styled.button<{variant?: 'primary' | 'secondary' | 'danger' | 'success' | 'warning'}>`
  padding: 6px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  background-color: ${props => 
    props.variant === 'danger' ? props.theme.danger :
    props.variant === 'success' ? props.theme.success :
    props.variant === 'warning' ? props.theme.warning :
    props.variant === 'secondary' ? props.theme.bg.tertiary :
    props.theme.accent.primary
  };
  color: white;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    opacity: 0.9;
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const Pagination = styled.div`
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
`;

const PageButton = styled.button<{active?: boolean}>`
  width: 36px;
  height: 36px;
  border-radius: 4px;
  border: 1px solid ${props => props.active ? props.theme.accent.primary : props.theme.border.primary};
  background-color: ${props => props.active ? props.theme.accent.primary : props.theme.bg.secondary};
  color: ${props => props.active ? 'white' : props.theme.text.primary};
  cursor: pointer;
  
  &:hover {
    border-color: ${props => props.theme.accent.primary};
    color: ${props => props.active ? 'white' : props.theme.accent.primary};
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
`;

const PageInfo = styled.div`
  font-size: 0.9rem;
  color: ${props => props.theme.text.secondary};
`;

const ReportsPage: React.FC = () => {
  // Состояния
  const [activeTab, setActiveTab] = useState('reports');
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  
  // Моковые данные для статистики
  const statsData: StatData[] = [
    { label: 'Активные зонды', value: 24, change: 2, unit: 'зонда' },
    { label: 'Успешные операции', value: 156, change: 8, unit: 'за месяц' },
    { label: 'Обнаруженные уязвимости', value: 17, change: -3, unit: 'за месяц' },
    { label: 'Средний пинг', value: 87, change: 12, unit: 'мс' },
    { label: 'Выполнено задач', value: 342, change: 45, unit: 'за месяц' },
    { label: 'Собрано данных', value: 1.8, change: 0.3, unit: 'ТБ' }
  ];
  
  // Моковые данные для отчетов
  const reportsData: ReportData[] = [
    {
      id: 'rep-001',
      title: 'Ежемесячный отчет по безопасности',
      date: '2023-10-01',
      type: 'security',
      status: 'готов',
      size: '4.2 МБ',
      author: 'C1Brain'
    },
    {
      id: 'rep-002',
      title: 'Анализ активности зондов',
      date: '2023-10-05',
      type: 'activity',
      status: 'готов',
      size: '2.7 МБ',
      author: 'Admin'
    },
    {
      id: 'rep-003',
      title: 'Производительность системы - Q3 2023',
      date: '2023-10-10',
      type: 'performance',
      status: 'готов',
      size: '8.1 МБ',
      author: 'C1Brain'
    },
    {
      id: 'rep-004',
      title: 'Финансовый анализ операций',
      date: '2023-10-12',
      type: 'financial',
      status: 'в обработке',
      size: '1.5 МБ',
      author: 'Admin'
    },
    {
      id: 'rep-005',
      title: 'Итоговый отчет за неделю',
      date: '2023-10-14',
      type: 'summary',
      status: 'готов',
      size: '3.0 МБ',
      author: 'C1Brain'
    },
    {
      id: 'rep-006',
      title: 'Аудит безопасности внешних подключений',
      date: '2023-10-15',
      type: 'security',
      status: 'ошибка',
      size: '0.8 МБ',
      author: 'Admin'
    },
    {
      id: 'rep-007',
      title: 'Анализ сетевой активности',
      date: '2023-10-15',
      type: 'activity',
      status: 'в обработке',
      size: '5.3 МБ',
      author: 'C1Brain'
    }
  ];
  
  // Форматирование даты для отображения
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('ru-RU').format(date);
  };
  
  // Фильтрация отчетов
  const filteredReports = reportsData.filter(report => {
    const matchesSearch = report.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
                          report.author.toLowerCase().includes(searchQuery.toLowerCase());
    
    if (typeFilter === 'all') return matchesSearch;
    return matchesSearch && report.type === typeFilter;
  });
  
  // Обработчики событий
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };
  
  const handleTypeFilterChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setTypeFilter(e.target.value);
  };
  
  const handleDownloadReport = (id: string) => {
    console.log(`Скачивание отчета с ID: ${id}`);
    // Здесь будет логика скачивания отчета
  };
  
  const handleDeleteReport = (id: string) => {
    if (window.confirm('Вы уверены, что хотите удалить этот отчет?')) {
      // Здесь будет логика удаления отчета
      console.log(`Удаление отчета с ID: ${id}`);
    }
  };
  
  const handleGenerateReport = () => {
    // Здесь будет логика создания нового отчета
    console.log('Создание нового отчета');
  };
  
  // Перевод типа отчета на русский
  const getReportTypeText = (type: string): string => {
    switch(type) {
      case 'security': return 'Безопасность';
      case 'activity': return 'Активность';
      case 'performance': return 'Производительность';
      case 'financial': return 'Финансы';
      case 'summary': return 'Сводный';
      default: return 'Другое';
    }
  };
  
  return (
    <Container>
      <Title>Отчеты и аналитика</Title>
      
      {/* Панель статистики */}
      <StatsGrid>
        {statsData.map((stat, index) => (
          <StatCard key={index}>
            <StatLabel>{stat.label}</StatLabel>
            <StatValue>
              {stat.value}{stat.unit && <Unit>{stat.unit}</Unit>}
            </StatValue>
            <StatChange positive={stat.change > 0}>
              <Arrow positive={stat.change > 0}>{stat.change > 0 ? '↗' : '↘'}</Arrow>
              {Math.abs(stat.change)}
            </StatChange>
          </StatCard>
        ))}
      </StatsGrid>
      
      {/* Вкладки */}
      <TabsContainer>
        <Tab active={activeTab === 'reports'} onClick={() => setActiveTab('reports')}>
          Отчеты
        </Tab>
        <Tab active={activeTab === 'analytics'} onClick={() => setActiveTab('analytics')}>
          Аналитика
        </Tab>
        <Tab active={activeTab === 'insights'} onClick={() => setActiveTab('insights')}>
          Инсайты C1Brain
        </Tab>
      </TabsContainer>
      
      {/* Панель управления */}
      <ControlPanel>
        <SearchAndFilter>
          <SearchInput 
            type="text" 
            placeholder="Поиск по названию или автору" 
            value={searchQuery}
            onChange={handleSearchChange}
          />
          <FilterSelect value={typeFilter} onChange={handleTypeFilterChange}>
            <option value="all">Все типы</option>
            <option value="security">Безопасность</option>
            <option value="activity">Активность</option>
            <option value="performance">Производительность</option>
            <option value="financial">Финансы</option>
            <option value="summary">Сводные</option>
          </FilterSelect>
        </SearchAndFilter>
        
        <Button onClick={handleGenerateReport}>Создать отчет</Button>
      </ControlPanel>
      
      {/* Таблица отчетов */}
      <DataTable>
        <TableHead>
          <TableRow>
            <TableHeaderCell>Название</TableHeaderCell>
            <TableHeaderCell>Дата</TableHeaderCell>
            <TableHeaderCell>Тип</TableHeaderCell>
            <TableHeaderCell>Статус</TableHeaderCell>
            <TableHeaderCell>Размер</TableHeaderCell>
            <TableHeaderCell>Автор</TableHeaderCell>
            <TableHeaderCell>Действия</TableHeaderCell>
          </TableRow>
        </TableHead>
        <tbody>
          {filteredReports.map(report => (
            <TableRow key={report.id}>
              <TableCell>{report.title}</TableCell>
              <TableCell>{formatDate(report.date)}</TableCell>
              <TableCell>{getReportTypeText(report.type)}</TableCell>
              <TableCell>
                <StatusBadge status={report.status}>{report.status}</StatusBadge>
              </TableCell>
              <TableCell>{report.size}</TableCell>
              <TableCell>{report.author}</TableCell>
              <TableCell>
                <ActionsCell>
                  <IconButton 
                    variant="primary" 
                    onClick={() => handleDownloadReport(report.id)}
                    disabled={report.status !== 'готов'}
                  >
                    ⬇️
                  </IconButton>
                  <IconButton 
                    variant="danger" 
                    onClick={() => handleDeleteReport(report.id)}
                  >
                    🗑️
                  </IconButton>
                </ActionsCell>
              </TableCell>
            </TableRow>
          ))}
        </tbody>
      </DataTable>
      
      {/* Пагинация */}
      <Pagination>
        <PageButton disabled={currentPage === 1} onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}>
          &lt;
        </PageButton>
        <PageButton active={currentPage === 1} onClick={() => setCurrentPage(1)}>1</PageButton>
        <PageButton active={currentPage === 2} onClick={() => setCurrentPage(2)}>2</PageButton>
        <PageButton active={currentPage === 3} onClick={() => setCurrentPage(3)}>3</PageButton>
        <PageInfo>Страница {currentPage} из 3</PageInfo>
        <PageButton disabled={currentPage === 3} onClick={() => setCurrentPage(prev => Math.min(prev + 1, 3))}>
          &gt;
        </PageButton>
      </Pagination>
    </Container>
  );
};

export default ReportsPage; 