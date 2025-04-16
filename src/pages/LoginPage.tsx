import { useState, FormEvent } from 'react';
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  Input,
  VStack,
  Heading,
  Text,
  Link,
  InputGroup,
  InputRightElement,
  IconButton,
  Alert,
  AlertIcon,
  useColorMode,
  Container,
  Center,
} from '@chakra-ui/react';
import { ViewIcon, ViewOffIcon } from '@chakra-ui/icons';
import { useAppDispatch, useAppSelector } from '../app/hooks';
import { loginUser, selectAuthStatus, selectAuthError } from '../features/auth/authSlice';

const LoginPage = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const dispatch = useAppDispatch();
  const status = useAppSelector(selectAuthStatus);
  const error = useAppSelector(selectAuthError);
  const { colorMode } = useColorMode();
  
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (username && password) {
      dispatch(loginUser({ username, password }));
    }
  };
  
  return (
    <Center minH="100vh" bg={colorMode === 'dark' ? 'gray.900' : 'gray.50'}>
      <Container maxW="md">
        <Box 
          p={8} 
          mx="auto" 
          bg={colorMode === 'dark' ? 'gray.800' : 'white'}
          borderRadius="lg"
          boxShadow="lg"
        >
          <VStack spacing={6} align="flex-start" w="full">
            <VStack spacing={2} align="center" w="full">
              <Heading size="xl">NeuroRAT</Heading>
              <Heading size="md" color="brand.500">Панель Управления</Heading>
              <Text color={colorMode === 'dark' ? 'gray.400' : 'gray.600'}>
                Войдите в систему для продолжения
              </Text>
            </VStack>
            
            {error && (
              <Alert status="error" borderRadius="md">
                <AlertIcon />
                {error}
              </Alert>
            )}
            
            <form onSubmit={handleSubmit} style={{ width: '100%' }}>
              <VStack spacing={4} w="full">
                <FormControl isRequired>
                  <FormLabel htmlFor="username">Имя пользователя</FormLabel>
                  <Input
                    id="username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="Введите имя пользователя"
                  />
                </FormControl>
                
                <FormControl isRequired>
                  <FormLabel htmlFor="password">Пароль</FormLabel>
                  <InputGroup>
                    <Input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Введите пароль"
                    />
                    <InputRightElement>
                      <IconButton
                        aria-label={showPassword ? 'Скрыть пароль' : 'Показать пароль'}
                        icon={showPassword ? <ViewOffIcon /> : <ViewIcon />}
                        variant="ghost"
                        onClick={() => setShowPassword(!showPassword)}
                        size="sm"
                      />
                    </InputRightElement>
                  </InputGroup>
                </FormControl>
                
                <Button
                  w="full"
                  colorScheme="brand"
                  type="submit"
                  isLoading={status === 'loading'}
                  loadingText="Вход..."
                  size="lg"
                  mt={4}
                >
                  Войти
                </Button>
              </VStack>
            </form>
            
            <Text fontSize="sm" alignSelf="center">
              Забыли пароль? <Link color="brand.500">Восстановить доступ</Link>
            </Text>
          </VStack>
        </Box>
        <Text mt={4} textAlign="center" fontSize="sm" color={colorMode === 'dark' ? 'gray.400' : 'gray.600'}>
          NeuroRAT Control Panel © {new Date().getFullYear()}
        </Text>
      </Container>
    </Center>
  );
};

export default LoginPage; 