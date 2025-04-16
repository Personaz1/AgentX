import { Box, Button, Heading, Text, VStack, useColorModeValue } from '@chakra-ui/react';
import { Link } from 'react-router-dom';

const NotFoundPage = () => {
  const bgColor = useColorModeValue('gray.50', 'gray.900');
  const textColor = useColorModeValue('gray.600', 'gray.400');
  
  return (
    <Box 
      display="flex" 
      alignItems="center" 
      justifyContent="center" 
      minH="100vh"
      bg={bgColor}
    >
      <VStack spacing={8} textAlign="center" px={4}>
        <Heading size="4xl">404</Heading>
        <Heading size="xl">Страница не найдена</Heading>
        <Text fontSize="lg" color={textColor} maxW="xl">
          Запрашиваемая страница не существует или была перемещена. 
          Проверьте URL-адрес или вернитесь на главную страницу.
        </Text>
        <Button
          as={Link}
          to="/"
          colorScheme="brand"
          size="lg"
        >
          Вернуться на главную
        </Button>
      </VStack>
    </Box>
  );
};

export default NotFoundPage; 