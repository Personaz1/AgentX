import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { Anomaly, AnomalyStatus, AnomalySeverity, AnomalyType, ANOMALY_STATUS_NAMES, ANOMALY_SEVERITY_NAMES, ANOMALY_TYPE_NAMES } from '../../types/anomaly';
import AnomalyCard from './AnomalyCard';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  width: 100%;
  padding: 20px;
`;

const Header = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;

  @media (max-width: 768px) {
    flex-direction: column;
    align-items: flex-start;
  }
`;

const Title = styled.h1`
  font-size: 24px;
  color: #E2E8F0;
  margin: 0;
`;

const FiltersContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
  
  @media (max-width: 768px) {
    flex-direction: column;
    width: 100%;
  }
`;

const FilterGroup = styled.div`
  display: flex;
  flex-direction: column;
`;

const FilterLabel = styled.label`
  font-size: 14px;
  color: #A0AEC0;
  margin-bottom: 4px;
`;

const FilterSelect = styled.select`
  background-color: #2D3748;
  border: 1px solid #4A5568;
  border-radius: 4px;
  color: #E2E8F0;
  padding: 8px 12px;
  font-size: 14px;
  min-width: 150px;
  
  &:focus {
    outline: none;
    border-color: #3182CE;
  }
`;

const SearchInput = styled.input`
  background-color: #2D3748;
  border: 1px solid #4A5568;
  border-radius: 4px;
  color: #E2E8F0;
  padding: 8px 12px;
  font-size: 14px;
  min-width: 250px;
  
  &:focus {
    outline: none;
    border-color: #3182CE;
  }
  
  &::placeholder {
    color: #718096;
  }
`;

const ListContainer = styled.div`
  display: flex;
  flex-direction: column;
`;

const EmptyState = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  background-color: #1A1A2E;
  border-radius: 8px;
  text-align: center;
`;

const EmptyStateText = styled.p`
  font-size: 16px;
  color: #A0AEC0;
  margin: 0;
`;

const PaginationContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-top: 20px;
`;

const PaginationButton = styled.button<{ isActive?: boolean }>`
  background-color: ${props => props.isActive ? '#3182CE' : '#2D3748'};
  color: ${props => props.isActive ? 'white' : '#A0AEC0'};
  border: none;
  border-radius: 4px;
  padding: 8px 12px;
  margin: 0 4px;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: ${props => props.isActive ? '#3182CE' : '#4A5568'};
  }
  
  &:disabled {
    background-color: #1A202C;
    color: #4A5568;
    cursor: not-allowed;
  }
`;

interface AnomalyListProps {
  anomalies: Anomaly[];
  loading?: boolean;
  onAnomalyClick?: (anomaly: Anomaly) => void;
}

const AnomalyList: React.FC<AnomalyListProps> = ({ 
  anomalies, 
  loading = false,
  onAnomalyClick 
}) => {
  const [filteredAnomalies, setFilteredAnomalies] = useState<Anomaly[]>(anomalies);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [currentPage, setCurrentPage] = useState<number>(1);
  const itemsPerPage = 10;

  useEffect(() => {
    applyFilters();
  }, [anomalies, statusFilter, severityFilter, typeFilter, searchQuery]);

  const applyFilters = () => {
    let filtered = [...anomalies];
    
    // Применение фильтров
    if (statusFilter !== 'all') {
      filtered = filtered.filter(a => a.status === statusFilter as AnomalyStatus);
    }
    
    if (severityFilter !== 'all') {
      filtered = filtered.filter(a => a.severity === severityFilter as AnomalySeverity);
    }
    
    if (typeFilter !== 'all') {
      filtered = filtered.filter(a => a.type === typeFilter as AnomalyType);
    }
    
    // Поиск по тексту
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(a => 
        a.title.toLowerCase().includes(query) || 
        (a.description && a.description.toLowerCase().includes(query)) ||
        (a.zondName && a.zondName.toLowerCase().includes(query)) ||
        (a.sourceIp && a.sourceIp.toLowerCase().includes(query)) ||
        (a.destinationIp && a.destinationIp.toLowerCase().includes(query))
      );
    }
    
    setFilteredAnomalies(filtered);
    setCurrentPage(1); // Сбрасываем страницу при изменении фильтров
  };

  // Пагинация
  const pageCount = Math.ceil(filteredAnomalies.length / itemsPerPage);
  const paginatedAnomalies = filteredAnomalies.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  // Генерация номеров страниц для пагинации
  const getPaginationNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;
    
    if (pageCount <= maxPagesToShow) {
      for (let i = 1; i <= pageCount; i++) {
        pages.push(i);
      }
    } else {
      // Всегда показываем первую и последнюю страницу
      let startPage = Math.max(1, currentPage - Math.floor(maxPagesToShow / 2));
      let endPage = Math.min(pageCount, startPage + maxPagesToShow - 1);
      
      // Корректировка, если мы близко к концу
      if (endPage - startPage + 1 < maxPagesToShow) {
        startPage = Math.max(1, endPage - maxPagesToShow + 1);
      }
      
      if (startPage > 1) {
        pages.push(1);
        if (startPage > 2) pages.push('...');
      }
      
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
      
      if (endPage < pageCount) {
        if (endPage < pageCount - 1) pages.push('...');
        pages.push(pageCount);
      }
    }
    
    return pages;
  };

  return (
    <Container>
      <Header>
        <Title>Аномалии</Title>
      </Header>
      
      <FiltersContainer>
        <FilterGroup>
          <FilterLabel>Статус</FilterLabel>
          <FilterSelect 
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="all">Все статусы</option>
            {Object.entries(ANOMALY_STATUS_NAMES).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </FilterSelect>
        </FilterGroup>
        
        <FilterGroup>
          <FilterLabel>Критичность</FilterLabel>
          <FilterSelect 
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
          >
            <option value="all">Все уровни</option>
            {Object.entries(ANOMALY_SEVERITY_NAMES).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </FilterSelect>
        </FilterGroup>
        
        <FilterGroup>
          <FilterLabel>Тип</FilterLabel>
          <FilterSelect 
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
          >
            <option value="all">Все типы</option>
            {Object.entries(ANOMALY_TYPE_NAMES).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </FilterSelect>
        </FilterGroup>
        
        <FilterGroup>
          <FilterLabel>Поиск</FilterLabel>
          <SearchInput 
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Поиск по названию, IP, зонду..."
          />
        </FilterGroup>
      </FiltersContainer>
      
      <ListContainer>
        {loading ? (
          <EmptyState>
            <EmptyStateText>Загрузка аномалий...</EmptyStateText>
          </EmptyState>
        ) : paginatedAnomalies.length === 0 ? (
          <EmptyState>
            <EmptyStateText>Аномалии не найдены</EmptyStateText>
          </EmptyState>
        ) : (
          paginatedAnomalies.map(anomaly => (
            <AnomalyCard 
              key={anomaly.id} 
              anomaly={anomaly} 
              onClick={onAnomalyClick}
            />
          ))
        )}
      </ListContainer>
      
      {pageCount > 1 && (
        <PaginationContainer>
          <PaginationButton 
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
          >
            &lt;
          </PaginationButton>
          
          {getPaginationNumbers().map((page, index) => (
            typeof page === 'number' ? (
              <PaginationButton 
                key={index}
                isActive={currentPage === page}
                onClick={() => setCurrentPage(page)}
              >
                {page}
              </PaginationButton>
            ) : (
              <span key={index} style={{ margin: '0 4px', color: '#A0AEC0' }}>{page}</span>
            )
          ))}
          
          <PaginationButton 
            onClick={() => setCurrentPage(prev => Math.min(pageCount, prev + 1))}
            disabled={currentPage === pageCount}
          >
            &gt;
          </PaginationButton>
        </PaginationContainer>
      )}
    </Container>
  );
};

export default AnomalyList; 