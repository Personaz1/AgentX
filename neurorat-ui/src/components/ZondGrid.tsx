import React from 'react';
import { 
  SimpleGrid, 
  Box, 
  Skeleton, 
  Flex, 
  Button, 
  Text, 
  Input, 
  InputGroup, 
  InputLeftElement, 
  Select,
  useDisclosure,
  Modal,
  ModalOverlay,
  ModalContent,
  ModalHeader,
  ModalCloseButton,
  ModalBody,
  ModalFooter,
  Icon,
  useColorModeValue
} from '@chakra-ui/react';
import { FiSearch, FiRefreshCw, FiFilter } from 'react-icons/fi';
import ZondCard, { ZondProps } from './ZondCard';

interface ZondGridProps {
  zonds: ZondProps[];
  isLoading?: boolean;
  onZondSelect?: (zond: ZondProps) => void;
  onRefresh?: () => void;
  selectedZond?: ZondProps | null;
}

const ZondGrid: React.FC<ZondGridProps> = ({ 
  zonds, 
  isLoading = false, 
  onZondSelect, 
  onRefresh,
  selectedZond
}) => {
  const [searchTerm, setSearchTerm] = React.useState('');
  const [statusFilter, setStatusFilter] = React.useState('all');
  const [connectionFilter, setConnectionFilter] = React.useState('all');
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  // Фильтрация зондов
  const filteredZonds = React.useMemo(() => {
    return zonds.filter(zond => {
      // Поисковый фильтр
      const searchMatch = 
        searchTerm === '' || 
        zond.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        zond.ip.toLowerCase().includes(searchTerm.toLowerCase()) ||
        zond.os.toLowerCase().includes(searchTerm.toLowerCase());
      
      // Фильтр по статусу
      const statusMatch = statusFilter === 'all' || zond.status === statusFilter;
      
      // Фильтр по типу соединения
      const connectionMatch = connectionFilter === 'all' || zond.connectionType === connectionFilter;
      
      return searchMatch && statusMatch && connectionMatch;
    });
  }, [zonds, searchTerm, statusFilter, connectionFilter]);
  
  // Обработчики
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };
  
  const handleStatusFilter = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setStatusFilter(e.target.value);
  };
  
  const handleConnectionFilter = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setConnectionFilter(e.target.value);
  };
  
  const handleRefresh = () => {
    if (onRefresh) onRefresh();
  };
  
  const handleZondSelect = (zond: ZondProps) => {
    if (onZondSelect) onZondSelect(zond);
  };
  
  const resetFilters = () => {
    setSearchTerm('');
    setStatusFilter('all');
    setConnectionFilter('all');
    onClose();
  };
  
  // Скелетон для состояния загрузки
  const renderSkeletons = () => {
    return Array(6).fill(0).map((_, i) => (
      <Skeleton 
        key={i} 
        height="250px" 
        borderRadius="lg" 
        startColor="gray.100" 
        endColor="gray.300"
      />
    ));
  };
  
  return (
    <Box width="100%">
      {/* Панель управления */}
      <Flex 
        mb={4} 
        justifyContent="space-between" 
        alignItems={{base: 'flex-start', md: 'center'}}
        flexDirection={{base: 'column', md: 'row'}}
        gap={{base: 2, md: 0}}
      >
        <InputGroup maxW={{base: '100%', md: '300px'}}>
          <InputLeftElement pointerEvents="none">
            <Icon as={FiSearch} color="gray.400" />
          </InputLeftElement>
          <Input 
            placeholder="Поиск зонда..." 
            value={searchTerm}
            onChange={handleSearch}
            borderColor={borderColor}
          />
        </InputGroup>
        
        <Flex gap={2}>
          <Button 
            leftIcon={<FiFilter />} 
            onClick={onOpen} 
            variant="outline"
            size="md"
          >
            Фильтры
          </Button>
          
          <Button 
            leftIcon={<FiRefreshCw />} 
            onClick={handleRefresh} 
            isLoading={isLoading}
            loadingText="Обновление"
            colorScheme="blue"
            size="md"
          >
            Обновить
          </Button>
        </Flex>
      </Flex>
      
      {/* Результаты фильтрации */}
      {searchTerm || statusFilter !== 'all' || connectionFilter !== 'all' ? (
        <Flex mb={3} alignItems="center">
          <Text fontSize="sm" color="gray.500">
            Найдено: {filteredZonds.length} {filteredZonds.length === 1 ? 'зонд' : 
              filteredZonds.length > 1 && filteredZonds.length < 5 ? 'зонда' : 'зондов'}
          </Text>
          {(searchTerm || statusFilter !== 'all' || connectionFilter !== 'all') && (
            <Button 
              ml={2} 
              size="xs" 
              onClick={resetFilters}
              variant="link"
              colorScheme="blue"
            >
              Сбросить фильтры
            </Button>
          )}
        </Flex>
      ) : null}
      
      {/* Сетка зондов */}
      {isLoading ? (
        <SimpleGrid columns={{base: 1, md: 2, lg: 3}} spacing={4}>
          {renderSkeletons()}
        </SimpleGrid>
      ) : filteredZonds.length > 0 ? (
        <SimpleGrid columns={{base: 1, md: 2, lg: 3}} spacing={4}>
          {filteredZonds.map(zond => (
            <Box 
              key={zond.id} 
              borderWidth={selectedZond?.id === zond.id ? '2px' : '0px'} 
              borderColor="blue.500"
              borderRadius="lg"
              transform={selectedZond?.id === zond.id ? 'scale(1.02)' : 'none'}
              transition="all 0.2s"
            >
              <ZondCard zond={zond} onClick={handleZondSelect} />
            </Box>
          ))}
        </SimpleGrid>
      ) : (
        <Flex 
          justifyContent="center" 
          alignItems="center" 
          height="200px" 
          bg={bgColor} 
          borderRadius="lg"
          borderWidth="1px"
          borderColor={borderColor}
        >
          <Text color="gray.500">
            {zonds.length > 0 
              ? 'Зонды не найдены по указанным критериям'
              : 'Нет доступных зондов'}
          </Text>
        </Flex>
      )}
      
      {/* Модальное окно фильтров */}
      <Modal isOpen={isOpen} onClose={onClose} isCentered size="sm">
        <ModalOverlay />
        <ModalContent>
          <ModalHeader>Фильтры</ModalHeader>
          <ModalCloseButton />
          
          <ModalBody>
            <Box mb={4}>
              <Text mb={2} fontWeight="medium">Статус зонда</Text>
              <Select 
                value={statusFilter} 
                onChange={handleStatusFilter}
              >
                <option value="all">Все статусы</option>
                <option value="online">Онлайн</option>
                <option value="offline">Офлайн</option>
                <option value="standby">Ожидание</option>
              </Select>
            </Box>
            
            <Box mb={4}>
              <Text mb={2} fontWeight="medium">Тип соединения</Text>
              <Select 
                value={connectionFilter} 
                onChange={handleConnectionFilter}
              >
                <option value="all">Все типы</option>
                <option value="dns">DNS</option>
                <option value="https">HTTPS</option>
                <option value="icmp">ICMP</option>
              </Select>
            </Box>
          </ModalBody>
          
          <ModalFooter>
            <Button variant="outline" mr={3} onClick={resetFilters}>
              Сбросить
            </Button>
            <Button colorScheme="blue" onClick={onClose}>
              Применить
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </Box>
  );
};

export default ZondGrid; 