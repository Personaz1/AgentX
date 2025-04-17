import React, { useState, useEffect } from 'react';
import { Box, Heading, Flex, Button, Text, useDisclosure, Spinner, useToast } from '@chakra-ui/react';
import { FiPlus, FiRefreshCw, FiDownload } from 'react-icons/fi';
import ZondGrid from '../components/ZondGrid';
import { ZondProps } from '../components/ZondCard';

// Временные моковые данные для иллюстрации
const mockZonds: ZondProps[] = [
  {
    id: 'znd-001',
    name: 'Server-Alpha',
    ip: '192.168.1.101',
    status: 'online',
    lastSeen: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 минут назад
    os: 'Linux Ubuntu 20.04',
    version: '1.2.3',
    cpu: 22,
    memory: 45,
    activeTasks: 2,
    location: {
      country: 'Россия',
      city: 'Москва',
      coordinates: [55.755826, 37.6173]
    },
    connectionType: 'dns'
  },
  {
    id: 'znd-002',
    name: 'Desktop-Charlie',
    ip: '192.168.1.102',
    status: 'standby',
    lastSeen: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 минут назад
    os: 'Windows 10 Pro',
    version: '1.2.1',
    cpu: 5,
    memory: 32,
    activeTasks: 0,
    location: {
      country: 'Россия',
      city: 'Санкт-Петербург',
      coordinates: [59.9343, 30.3351]
    },
    connectionType: 'https'
  },
  {
    id: 'znd-003',
    name: 'NAS-Bravo',
    ip: '192.168.1.103',
    status: 'offline',
    lastSeen: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(), // 3 часа назад
    os: 'FreeBSD 13.0',
    version: '1.2.0',
    cpu: 0,
    memory: 0,
    activeTasks: 0,
    location: {
      country: 'Россия',
      city: 'Казань',
      coordinates: [55.8304, 49.0661]
    },
    connectionType: 'icmp'
  },
  {
    id: 'znd-004',
    name: 'Workstation-Delta',
    ip: '192.168.1.104',
    status: 'online',
    lastSeen: new Date(Date.now() - 1000 * 60 * 2).toISOString(), // 2 минуты назад
    os: 'macOS 12.3',
    version: '1.2.3',
    cpu: 67,
    memory: 78,
    activeTasks: 5,
    location: {
      country: 'Россия',
      city: 'Новосибирск',
      coordinates: [55.0084, 82.9357]
    },
    connectionType: 'https'
  }
];

const ZondsPage: React.FC = () => {
  const [zonds, setZonds] = useState<ZondProps[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedZond, setSelectedZond] = useState<ZondProps | null>(null);
  const { isOpen, onOpen, onClose } = useDisclosure();
  const toast = useToast();

  // Имитация загрузки данных с сервера
  useEffect(() => {
    const fetchZonds = async () => {
      setIsLoading(true);
      try {
        // Здесь должен быть реальный API-запрос
        // const response = await api.getZonds();
        // setZonds(response.data);
        
        // Имитация задержки сети
        setTimeout(() => {
          setZonds(mockZonds);
          setIsLoading(false);
        }, 1500);
      } catch (error) {
        console.error('Ошибка при загрузке зондов:', error);
        toast({
          title: 'Ошибка загрузки',
          description: 'Не удалось загрузить список зондов',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
        setIsLoading(false);
      }
    };

    fetchZonds();
  }, [toast]);

  const handleRefresh = () => {
    // Имитация обновления данных
    setIsLoading(true);
    setTimeout(() => {
      // Обновляем случайные данные для демонстрации
      const updatedZonds = zonds.map(zond => ({
        ...zond,
        cpu: Math.floor(Math.random() * 100),
        memory: Math.floor(Math.random() * 100),
        lastSeen: new Date().toISOString()
      }));
      setZonds(updatedZonds);
      setIsLoading(false);

      toast({
        title: 'Обновлено',
        description: 'Список зондов успешно обновлен',
        status: 'success',
        duration: 3000,
        isClosable: true,
      });
    }, 1000);
  };

  const handleSelectZond = (zond: ZondProps) => {
    setSelectedZond(zond);
    onOpen();
    // Здесь можно открыть модальное окно с детальной информацией о зонде
    // или перенаправить на страницу с детальной информацией
    console.log('Выбран зонд:', zond);
    
    toast({
      title: 'Зонд выбран',
      description: `Выбран зонд ${zond.name} (${zond.id})`,
      status: 'info',
      duration: 2000,
      isClosable: true,
    });
  };

  return (
    <Box p={5}>
      <Flex justifyContent="space-between" alignItems="center" mb={6}>
        <Heading size="lg">Управление зондами</Heading>
        <Flex>
          <Button 
            leftIcon={<FiRefreshCw />} 
            mr={3}
            onClick={handleRefresh}
            isLoading={isLoading}
            loadingText="Обновление"
            colorScheme="blue"
            variant="outline"
          >
            Обновить
          </Button>
          <Button 
            leftIcon={<FiDownload />} 
            mr={3}
            colorScheme="teal"
            variant="outline"
          >
            Скачать агент
          </Button>
          <Button 
            leftIcon={<FiPlus />} 
            colorScheme="purple"
          >
            Новое задание
          </Button>
        </Flex>
      </Flex>

      {isLoading && zonds.length === 0 ? (
        <Flex justifyContent="center" alignItems="center" height="300px">
          <Spinner size="xl" color="purple.500" mr={4} />
          <Text>Загрузка зондов...</Text>
        </Flex>
      ) : (
        <ZondGrid 
          zonds={zonds} 
          isLoading={isLoading}
          onSelectZond={handleSelectZond}
        />
      )}

      {/* TODO: Добавить модальное окно для отображения детальной информации о зонде */}
      {/* <ZondDetailModal isOpen={isOpen} onClose={onClose} zond={selectedZond} /> */}
    </Box>
  );
};

export default ZondsPage; 