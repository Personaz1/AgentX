import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { FiRefreshCw, FiPlay, FiPause, FiTrash2, FiPlus, FiFilter } from 'react-icons/fi';
import { ATSOperation } from '../types';

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

const Filters = styled.div`
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  align-items: center;
`;

const Filter = styled.div`
  display: flex;
  align-items: center;
  padding: 8px 16px;
  background: #1a1c23;
  border-radius: 4px;
  font-size: 14px;
  
  svg {
    margin-right: 8px;
    color: #8a94a6;
  }
`;

const Select = styled.select`
  background: #1a1c23;
  border: none;
  color: white;
  font-size: 14px;
  outline: none;
  padding: 4px;
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
  
  &::placeholder {
    color: #8a94a6;
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  background: #1a1c23;
  border-radius: 8px;
  overflow: hidden;
`;

const TableHead = styled.thead`
  background: #1e2739;
  
  th {
    padding: 12px 16px;
    text-align: left;
    font-weight: 600;
    font-size: 14px;
    border-bottom: 1px solid #2c3a57;
  }
`;

const TableBody = styled.tbody`
  tr {
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    
    &:last-child {
      border-bottom: none;
    }
    
    &:hover {
      background: rgba(255, 255, 255, 0.05);
    }
  }
  
  td {
    padding: 12px 16px;
    font-size: 14px;
  }
`;

const StatusBadge = styled.span<{ status: string }>`
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
  background: ${props => {
    switch (props.status) {
      case 'active':
        return 'rgba(16, 185, 129, 0.2)';
      case 'paused':
        return 'rgba(245, 158, 11, 0.2)';
      case 'completed':
        return 'rgba(59, 130, 246, 0.2)';
      case 'failed':
        return 'rgba(239, 68, 68, 0.2)';
      default:
        return 'rgba(107, 114, 128, 0.2)';
    }
  }};
  color: ${props => {
    switch (props.status) {
      case 'active':
        return '#10B981';
      case 'paused':
        return '#F59E0B';
      case 'completed':
        return '#3B82F6';
      case 'failed':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  }};
`;

const ActionIconButton = styled.button`
  background: none;
  border: none;
  color: #8a94a6;
  cursor: pointer;
  padding: 4px;
  margin-right: 8px;
  transition: all 0.2s;
  
  &:hover {
    color: white;
  }
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

// Mock data structure for ATS operations 
interface MockATSOperation {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'completed' | 'failed';
  type: 'buy' | 'sell' | 'scan' | 'analyze';
  bank: string;
  createdAt: string;
  progress: number;
  profit: number;
}

const ATSOperationsPage: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [operations, setOperations] = useState<MockATSOperation[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  
  useEffect(() => {
    // Имитация загрузки данных
    const fetchData = async () => {
      setLoading(true);
      try {
        // В реальном приложении здесь будет запрос к API
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Моковые данные
        setOperations([
          {
            id: 'ats-001',
            name: 'Анализ вакансий Sber',
            status: 'active',
            type: 'scan',
            bank: 'Sber',
            createdAt: '2023-09-15 08:30:22',
            progress: 67,
            profit: 0
          },
          {
            id: 'ats-002',
            name: 'Поиск уязвимостей VTB Online',
            status: 'paused',
            type: 'analyze',
            bank: 'VTB',
            createdAt: '2023-09-14 15:22:10',
            progress: 43,
            profit: 0
          },
          {
            id: 'ats-003',
            name: 'Тестовые транзакции Tinkoff',
            status: 'completed',
            type: 'buy',
            bank: 'Tinkoff',
            createdAt: '2023-09-12 11:05:33',
            progress: 100,
            profit: 1250
          },
          {
            id: 'ats-004',
            name: 'Arb. Операция Alpha-X',
            status: 'active',
            type: 'buy',
            bank: 'Alfabank',
            createdAt: '2023-09-15 10:15:00',
            progress: 25,
            profit: 320
          },
          {
            id: 'ats-005',
            name: 'Закрытие позиций Test-B',
            status: 'failed',
            type: 'sell',
            bank: 'Raiffeisen',
            createdAt: '2023-09-13 09:45:12',
            progress: 52,
            profit: -180
          },
          {
            id: 'ats-006',
            name: 'Сканирование систем MOEX',
            status: 'completed',
            type: 'scan',
            bank: 'MOEX',
            createdAt: '2023-09-11 14:20:45',
            progress: 100,
            profit: 0
          }
        ]);
      } catch (error) {
        console.error('Ошибка при загрузке операций ATS:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  const filteredOperations = operations.filter(op => {
    const matchesStatus = statusFilter === 'all' || op.status === statusFilter;
    const matchesType = typeFilter === 'all' || op.type === typeFilter;
    const matchesSearch = op.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          op.bank.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          op.id.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesStatus && matchesType && matchesSearch;
  });
  
  const handleCreateOperation = () => {
    alert('Создание новой операции ATS');
    // В реальном приложении здесь будет открытие модального окна или переход на страницу создания
  };
  
  const handleToggleStatus = (id: string, currentStatus: string) => {
    const newStatus = currentStatus === 'active' ? 'paused' : 'active';
    setOperations(operations.map(op => 
      op.id === id ? { ...op, status: newStatus as 'active' | 'paused' | 'completed' | 'failed' } : op
    ));
  };
  
  const handleDeleteOperation = (id: string) => {
    if (confirm('Вы уверены, что хотите удалить эту операцию?')) {
      setOperations(operations.filter(op => op.id !== id));
    }
  };
  
  if (loading) {
    return (
      <LoadingIndicator>
        <FiRefreshCw size={20} />
        Загрузка операций ATS...
      </LoadingIndicator>
    );
  }
  
  return (
    <PageContainer>
      <Header>
        <Title>Операции ATS</Title>
        <ActionButtons>
          <CreateButton onClick={handleCreateOperation}>
            <FiPlus size={16} />
            Новая операция
          </CreateButton>
        </ActionButtons>
      </Header>
      
      <Filters>
        <Filter>
          <FiFilter size={16} />
          Статус:
          <Select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">Все</option>
            <option value="active">Активные</option>
            <option value="paused">Приостановленные</option>
            <option value="completed">Завершенные</option>
            <option value="failed">Неудачные</option>
          </Select>
        </Filter>
        
        <Filter>
          <FiFilter size={16} />
          Тип:
          <Select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="all">Все</option>
            <option value="buy">Покупка</option>
            <option value="sell">Продажа</option>
            <option value="scan">Сканирование</option>
            <option value="analyze">Анализ</option>
          </Select>
        </Filter>
        
        <SearchInput
          placeholder="Поиск по имени, банку или ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </Filters>
      
      {filteredOperations.length > 0 ? (
        <Table>
          <TableHead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th>Статус</th>
              <th>Тип</th>
              <th>Банк</th>
              <th>Создано</th>
              <th>Прогресс</th>
              <th>Профит</th>
              <th>Действия</th>
            </tr>
          </TableHead>
          <TableBody>
            {filteredOperations.map(operation => (
              <tr key={operation.id}>
                <td>{operation.id}</td>
                <td>{operation.name}</td>
                <td>
                  <StatusBadge status={operation.status}>
                    {operation.status === 'active' && 'Активна'}
                    {operation.status === 'paused' && 'Приостановлена'}
                    {operation.status === 'completed' && 'Завершена'}
                    {operation.status === 'failed' && 'Неудачна'}
                  </StatusBadge>
                </td>
                <td>
                  {operation.type === 'buy' && 'Покупка'}
                  {operation.type === 'sell' && 'Продажа'}
                  {operation.type === 'scan' && 'Сканирование'}
                  {operation.type === 'analyze' && 'Анализ'}
                </td>
                <td>{operation.bank}</td>
                <td>{operation.createdAt}</td>
                <td>{operation.progress}%</td>
                <td style={{ color: operation.profit > 0 ? '#10B981' : operation.profit < 0 ? '#EF4444' : 'inherit' }}>
                  {operation.profit > 0 ? `+${operation.profit}` : operation.profit}
                </td>
                <td>
                  {(operation.status === 'active' || operation.status === 'paused') && (
                    <ActionIconButton 
                      title={operation.status === 'active' ? 'Приостановить' : 'Возобновить'}
                      onClick={() => handleToggleStatus(operation.id, operation.status)}
                    >
                      {operation.status === 'active' ? <FiPause size={16} /> : <FiPlay size={16} />}
                    </ActionIconButton>
                  )}
                  <ActionIconButton 
                    title="Удалить"
                    onClick={() => handleDeleteOperation(operation.id)}
                  >
                    <FiTrash2 size={16} />
                  </ActionIconButton>
                </td>
              </tr>
            ))}
          </TableBody>
        </Table>
      ) : (
        <NoDataMessage>
          Операции не найдены. Попробуйте изменить параметры фильтрации или создайте новую операцию.
        </NoDataMessage>
      )}
    </PageContainer>
  );
};

export default ATSOperationsPage; 