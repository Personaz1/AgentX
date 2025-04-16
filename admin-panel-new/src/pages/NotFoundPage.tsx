import React from 'react';
import styled from 'styled-components';
import { Link } from 'react-router-dom';

const Container = styled.div`
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
  padding: 20px;
  text-align: center;
`;

const ErrorCode = styled.div`
  font-size: 8rem;
  font-weight: 800;
  color: ${props => props.theme.accent.primary};
  margin-bottom: 10px;
  line-height: 1;
  
  background: linear-gradient(
    135deg, 
    ${props => props.theme.accent.primary}, 
    ${props => props.theme.accent.secondary}
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
`;

const Title = styled.h1`
  font-size: 2.5rem;
  font-weight: 700;
  color: ${props => props.theme.text.primary};
  margin-bottom: 20px;
`;

const Description = styled.p`
  font-size: 1.1rem;
  color: ${props => props.theme.text.secondary};
  max-width: 500px;
  margin-bottom: 30px;
  line-height: 1.5;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 15px;
  
  @media (max-width: 480px) {
    flex-direction: column;
  }
`;

const Button = styled(Link)<{variant?: 'primary' | 'secondary'}>`
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  text-align: center;
  
  background-color: ${props => 
    props.variant === 'secondary' ? 'transparent' : props.theme.accent.primary
  };
  
  color: ${props => 
    props.variant === 'secondary' ? props.theme.text.primary : 'white'
  };
  
  border: ${props => 
    props.variant === 'secondary' ? `2px solid ${props.theme.border.primary}` : 'none'
  };
  
  &:hover {
    text-decoration: none;
    opacity: 0.9;
    transform: translateY(-2px);
  }
  
  transition: all 0.2s ease;
`;

const CodeBox = styled.div`
  background-color: ${props => props.theme.bg.secondary};
  padding: 10px 20px;
  border-radius: 4px;
  margin-top: 40px;
  display: inline-block;
  
  pre {
    font-family: monospace;
    font-size: 0.9rem;
    color: ${props => props.theme.text.secondary};
  }
`;

const NotFoundPage: React.FC = () => {
  return (
    <Container>
      <ErrorCode>404</ErrorCode>
      <Title>Страница не найдена</Title>
      <Description>
        Запрошенная страница не существует или была перемещена.
        Возможно, вы перешли по неверной ссылке.
      </Description>
      
      <ButtonGroup>
        <Button to="/dashboard">На главную</Button>
        <Button to="/" variant="secondary">Обновить страницу</Button>
      </ButtonGroup>
      
      <CodeBox>
        <pre>
          Error: Route not found in routing table<br/>
          at NeuroRouter.resolve (router.ts:213)<br/>
          at NetworkAgent.handleRequest (network.ts:109)
        </pre>
      </CodeBox>
    </Container>
  );
};

export default NotFoundPage; 