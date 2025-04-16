import { 
  HStack, 
  Flex, 
  IconButton, 
  Menu, 
  MenuButton, 
  MenuList, 
  MenuItem, 
  Avatar, 
  Text, 
  Box, 
  Badge, 
  useColorMode, 
  useColorModeValue, 
  Heading, 
  Icon
} from '@chakra-ui/react';
import { 
  HamburgerIcon, 
  MoonIcon, 
  SunIcon, 
  BellIcon, 
  ChevronDownIcon,
  SettingsIcon, 
  QuestionIcon
} from '@chakra-ui/icons';
import { FiServer } from 'react-icons/fi';
import { useAppDispatch } from '../../app/hooks';
import { logout } from '../../features/auth/authSlice';

interface TopBarProps {
  onMenuClick: () => void;
  title: string;
}

const TopBar = ({ onMenuClick, title }: TopBarProps) => {
  const { colorMode, toggleColorMode } = useColorMode();
  const dispatch = useAppDispatch();
  
  // Цвета в зависимости от темы
  const bg = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');
  
  // Функция выхода из системы
  const handleLogout = () => {
    dispatch(logout());
  };
  
  return (
    <Flex
      as="header"
      align="center"
      justify="space-between"
      w="full"
      px={4}
      h="80px"
      bg={bg}
      borderBottomWidth="1px"
      borderBottomColor={borderColor}
      position="sticky"
      top="0"
      zIndex="docked"
    >
      <HStack spacing={4}>
        <IconButton
          aria-label="Открыть меню"
          variant="ghost"
          icon={<HamburgerIcon />}
          display={{ base: 'flex', lg: 'none' }}
          onClick={onMenuClick}
          fontSize="20px"
        />
        
        <Heading size="md" display={{ base: 'none', md: 'flex' }}>
          {title}
        </Heading>
      </HStack>
      
      <HStack spacing={4}>
        {/* Статус системы */}
        <Flex align="center" display={{ base: 'none', md: 'flex' }}>
          <Icon as={FiServer} color="green.500" mr={2} />
          <Text fontSize="sm" mr={2}>Статус системы:</Text>
          <Badge colorScheme="green" variant="solid" borderRadius="full" px={2}>
            Онлайн
          </Badge>
        </Flex>
        
        {/* Переключатель темы */}
        <IconButton
          aria-label={colorMode === 'light' ? 'Включить темную тему' : 'Включить светлую тему'}
          icon={colorMode === 'light' ? <MoonIcon /> : <SunIcon />}
          variant="ghost"
          onClick={toggleColorMode}
        />
        
        {/* Уведомления */}
        <Menu>
          <MenuButton
            as={IconButton}
            aria-label="Уведомления"
            icon={<BellIcon />}
            variant="ghost"
            position="relative"
          >
            <Box
              position="absolute"
              top="1"
              right="1"
              w="2"
              h="2"
              bg="red.500"
              borderRadius="full"
            />
          </MenuButton>
          <MenuList zIndex={1000}>
            <MenuItem>Новый зонд подключен (3 мин)</MenuItem>
            <MenuItem>C1Brain: обнаружена активность (12 мин)</MenuItem>
            <MenuItem>Задача выполнена успешно (45 мин)</MenuItem>
            <MenuItem>ATS операция завершена (2 ч)</MenuItem>
          </MenuList>
        </Menu>
        
        {/* Аватар пользователя с меню */}
        <Menu>
          <MenuButton>
            <HStack>
              <Avatar size="sm" name="Админ" bg="brand.500" />
              <ChevronDownIcon />
            </HStack>
          </MenuButton>
          <MenuList zIndex={1000}>
            <MenuItem icon={<SettingsIcon />}>Профиль</MenuItem>
            <MenuItem icon={<QuestionIcon />}>Помощь</MenuItem>
            <MenuItem onClick={handleLogout}>Выйти</MenuItem>
          </MenuList>
        </Menu>
      </HStack>
    </Flex>
  );
};

export default TopBar;