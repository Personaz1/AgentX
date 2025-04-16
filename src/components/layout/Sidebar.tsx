import { Box, VStack, HStack, Text, Icon, Flex, Divider, Heading, useColorModeValue } from '@chakra-ui/react';
import { NavLink, useLocation } from 'react-router-dom';
import { 
  FiHome, 
  FiServer, 
  FiClipboard, 
  FiBriefcase, 
  FiCpu, 
  FiSettings, 
  FiBarChart2, 
  FiInfo,
  FiDatabase
} from 'react-icons/fi';

// Интерфейс для элемента навигации
interface NavItemProps {
  icon: any;
  children: React.ReactNode;
  to: string;
}

// Компонент элемента навигации
const NavItem = ({ icon, children, to }: NavItemProps) => {
  const location = useLocation();
  const isActive = location.pathname === to || location.pathname.startsWith(`${to}/`);
  
  // Цвета для активного и неактивного состояния
  const activeBg = useColorModeValue('brand.50', 'brand.900');
  const activeColor = useColorModeValue('brand.700', 'brand.200');
  const inactiveColor = useColorModeValue('gray.600', 'gray.400');
  const hoverBg = useColorModeValue('gray.100', 'gray.700');
  
  return (
    <NavLink to={to} style={{ width: '100%' }}>
      <Flex
        align="center"
        px="4"
        py="3"
        cursor="pointer"
        role="group"
        fontWeight={isActive ? "semibold" : "normal"}
        color={isActive ? activeColor : inactiveColor}
        bg={isActive ? activeBg : 'transparent'}
        borderRadius="md"
        _hover={{
          bg: isActive ? activeBg : hoverBg,
        }}
        transition="all 0.2s"
      >
        <Icon
          mr="3"
          fontSize="16"
          as={icon}
          color={isActive ? activeColor : inactiveColor}
          _groupHover={{
            color: isActive ? activeColor : 'brand.400',
          }}
        />
        <Text>{children}</Text>
      </Flex>
    </NavLink>
  );
};

// Основной компонент боковой панели
const Sidebar = () => {
  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  return (
    <Box
      as="aside"
      h="full"
      w="full"
      bg={bgColor}
      borderRight="1px"
      borderRightColor={borderColor}
      overflowY="auto"
    >
      {/* Лого и название */}
      <Flex
        h="20"
        alignItems="center"
        justifyContent="center"
        borderBottomWidth="1px"
        borderBottomColor={borderColor}
      >
        <Heading size="md" fontWeight="bold">NeuroRAT</Heading>
      </Flex>
      
      {/* Навигация */}
      <VStack spacing={0} align="stretch" p={3}>
        {/* Общее */}
        <Box mb={1}>
          <Text fontSize="xs" fontWeight="bold" textTransform="uppercase" mb={2} pl={4} color="gray.500">
            Общее
          </Text>
          <NavItem to="/" icon={FiHome}>Панель управления</NavItem>
          <NavItem to="/zonds" icon={FiServer}>Зонды</NavItem>
          <NavItem to="/tasks" icon={FiClipboard}>Задачи</NavItem>
        </Box>
        
        <Divider my={2} />
        
        {/* Управление */}
        <Box mb={1}>
          <Text fontSize="xs" fontWeight="bold" textTransform="uppercase" mb={2} pl={4} color="gray.500">
            Управление
          </Text>
          <NavItem to="/c1brain" icon={FiCpu}>C1Brain</NavItem>
          <NavItem to="/ats" icon={FiBriefcase}>ATS Модуль</NavItem>
          <NavItem to="/analytics" icon={FiBarChart2}>Аналитика</NavItem>
        </Box>
        
        <Divider my={2} />
        
        {/* Системное */}
        <Box>
          <Text fontSize="xs" fontWeight="bold" textTransform="uppercase" mb={2} pl={4} color="gray.500">
            Системное
          </Text>
          <NavItem to="/database" icon={FiDatabase}>База данных</NavItem>
          <NavItem to="/settings" icon={FiSettings}>Настройки</NavItem>
          <NavItem to="/logs" icon={FiInfo}>Журнал событий</NavItem>
        </Box>
      </VStack>
      
      {/* Версия */}
      <Box p={4} mt="auto">
        <Text fontSize="xs" color="gray.500" textAlign="center">
          Версия 1.2.3
        </Text>
      </Box>
    </Box>
  );
};

export default Sidebar; 