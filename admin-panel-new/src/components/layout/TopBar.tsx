import React from 'react';
import { 
  HStack, 
  Menu, 
  MenuButton, 
  MenuList, 
  MenuItem, 
  Avatar, 
  Text, 
  Box, 
  Badge, 
  Flex,
  useColorMode
} from '@chakra-ui/react';
import { ChevronDownIcon } from '@chakra-ui/icons';
import { useAppDispatch } from '../../app/hooks';
import { logout } from '../../features/auth/authSlice';

const TopBar: React.FC = () => {
  const dispatch = useAppDispatch();
  const { colorMode, toggleColorMode } = useColorMode();
  
  const handleLogout = () => {
    dispatch(logout());
  };

  // В реальном приложении эти данные будут из Redux
  const username = 'Администратор';
  const systemStatus = 'online';
  
  return (
    <HStack width="100%" justify="space-between" p={4}>
      <Box>
        <Badge colorScheme={systemStatus === 'online' ? 'green' : 'red'} px={2} py={1} borderRadius="md">
          Система {systemStatus === 'online' ? 'онлайн' : 'офлайн'}
        </Badge>
      </Box>
      
      <Menu>
        <MenuButton as={Flex} alignItems="center" cursor="pointer">
          <Avatar 
            size="sm" 
            name={username} 
            bg="blue.500" 
            color="white"
            mr={2}
          />
          <Text mr={2}>{username}</Text>
          <ChevronDownIcon />
        </MenuButton>
        <MenuList>
          <MenuItem onClick={toggleColorMode}>
            {colorMode === 'light' ? 'Тёмный режим' : 'Светлый режим'}
          </MenuItem>
          <MenuItem>Настройки профиля</MenuItem>
          <MenuItem onClick={handleLogout}>Выйти</MenuItem>
        </MenuList>
      </Menu>
    </HStack>
  );
};

export default TopBar; 