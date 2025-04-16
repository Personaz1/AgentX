import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

const PageContainer = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #121212;
`;

const LoginCard = styled.div`
  background-color: #1E1E2E;
  border-radius: 8px;
  padding: 40px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.2);
`;

const Logo = styled.div`
  text-align: center;
  margin-bottom: 32px;
`;

const LogoText = styled.h1`
  font-size: 2rem;
  font-weight: bold;
  color: #BD93F9;
  margin: 0;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
`;

const FormGroup = styled.div`
  margin-bottom: 20px;
`;

const Label = styled.label`
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
  color: #F8F8F2;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px;
  background-color: #282A36;
  border: 1px solid #44475A;
  border-radius: 4px;
  color: #F8F8F2;
  font-size: 16px;
  
  &:focus {
    outline: none;
    border-color: #BD93F9;
  }
`;

const SubmitButton = styled.button`
  padding: 12px;
  background-color: #BD93F9;
  color: #282A36;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #A580FF;
  }
  
  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
`;

const ErrorMessage = styled.div`
  color: #FF5555;
  font-size: 14px;
  margin-top: 16px;
  text-align: center;
`;

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    // В реальном приложении здесь был бы запрос к API
    setTimeout(() => {
      if (username === 'admin' && password === 'password') {
        // Для демонстрации просто сохраняем токен в localStorage
        localStorage.setItem('token', 'demo-token');
        navigate('/');
      } else {
        setError('Неверное имя пользователя или пароль');
        setLoading(false);
      }
    }, 1000);
  };

  return (
    <PageContainer>
      <LoginCard>
        <Logo>
          <LogoText>NeuroRAT</LogoText>
        </Logo>
        
        <Form onSubmit={handleSubmit}>
          <FormGroup>
            <Label htmlFor="username">Имя пользователя</Label>
            <Input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </FormGroup>
          
          <FormGroup>
            <Label htmlFor="password">Пароль</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </FormGroup>
          
          <SubmitButton type="submit" disabled={loading}>
            {loading ? 'Вход...' : 'Войти'}
          </SubmitButton>
          
          {error && <ErrorMessage>{error}</ErrorMessage>}
        </Form>
      </LoginCard>
    </PageContainer>
  );
};

export default LoginPage; 