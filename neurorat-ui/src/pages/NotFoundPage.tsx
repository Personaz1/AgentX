import React from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  text-align: center;
  padding: 0 20px;
  background-color: #121212;
`;

const ErrorCode = styled.h1`
  font-size: 120px;
  font-weight: 700;
  color: #BD93F9;
  margin: 0;
  line-height: 1;
`;

const Title = styled.h2`
  font-size: 28px;
  font-weight: 600;
  color: #F8F8F2;
  margin: 20px 0;
`;

const Message = styled.p`
  font-size: 16px;
  color: #6C7293;
  margin-bottom: 30px;
  max-width: 500px;
`;

const Button = styled.button`
  padding: 12px 24px;
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
`;

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();
  
  const handleGoBack = () => {
    navigate('/');
  };
  
  return (
    <Container>
      <ErrorCode>404</ErrorCode>
      <Title>Страница не найдена</Title>
      <Message>
        Запрошенная страница не существует или была перемещена.
        Возможно, вы перешли по устаревшей ссылке или ввели неверный адрес.
      </Message>
      <Button onClick={handleGoBack}>Вернуться на главную</Button>
    </Container>
  );
};

export default NotFoundPage; 