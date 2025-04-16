import { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import {
  Box,
  Flex,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  useDisclosure,
  useColorMode,
  IconButton,
  HStack,
  Heading,
  Text,
  useBreakpointValue,
  useColorModeValue,
  Container,
} from '@chakra-ui/react';
import { 
  HamburgerIcon, 
  MoonIcon, 
  SunIcon, 
  BellIcon 
} from '@chakra-ui/icons';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

const MainLayout = () => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { colorMode, toggleColorMode } = useColorMode();
  const location = useLocation();
  
  // Определение, является ли устройство мобильным
  const isMobile = useBreakpointValue({ base: true, lg: false }) || false;
  
  // Закрывать drawer при изменении маршрута на мобильных устройствах
  useEffect(() => {
    if (isMobile && isOpen) {
      onClose();
    }
  }, [location, isMobile, isOpen, onClose]);
  
  // Получение заголовка страницы на основе пути
  const getPageTitle = () => {
    const path = location.pathname;
    
    if (path === '/') return 'Панель управления';
    if (path.startsWith('/zonds')) return 'Управление зондами';
    if (path.startsWith('/tasks')) return 'Задачи';
    if (path.startsWith('/c1brain')) return 'C1Brain';
    if (path.startsWith('/ats')) return 'ATS Модуль';
    
    return 'NeuroRAT Control Panel';
  };
  
  // Цвета фона в зависимости от темы
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const boxBgColor = useColorModeValue('white', 'gray.800');

  return (
    <Flex h="100vh" bgColor={bgColor}>
      {/* Сайдбар на десктопе */}
      <Box
        display={{ base: 'none', lg: 'block' }}
        w="250px"
        bg={boxBgColor}
        boxShadow="sm"
        position="fixed"
        h="100%"
      >
        <Sidebar />
      </Box>
      
      {/* Drawer на мобильных устройствах */}
      <Drawer
        isOpen={isOpen}
        placement="left"
        onClose={onClose}
        returnFocusOnClose={false}
        onOverlayClick={onClose}
      >
        <DrawerOverlay />
        <DrawerContent maxW="250px">
          <Sidebar />
        </DrawerContent>
      </Drawer>
      
      {/* Основной контент */}
      <Box
        ml={{ base: 0, lg: '250px' }}
        width={{ base: '100%', lg: 'calc(100% - 250px)' }}
        transition="margin-left 0.3s"
      >
        {/* Верхний бар */}
        <TopBar 
          onMenuClick={onOpen}
          title={getPageTitle()}
        />
        
        {/* Контент страницы */}
        <Box
          as="main"
          p={4}
          overflowY="auto"
          h="calc(100vh - 80px)" // Высота экрана минус высота верхнего бара
        >
          <Container maxW="full" p={0}>
            <Outlet />
          </Container>
        </Box>
      </Box>
    </Flex>
  );
};

export default MainLayout; 