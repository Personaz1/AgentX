import React, { useState } from 'react';
import styled from 'styled-components';

// Стили
const Container = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: ${props => props.theme.bg.primary};
  position: relative;
  overflow: hidden;
`;

const BackgroundAnimation = styled.div`
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(
    135deg,
    rgba(0, 0, 0, 0.1) 0%,
    rgba(30, 30, 30, 0.1) 100%
  );
  z-index: 1;
  
  &:before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(
      circle,
      ${props => props.theme.accent.primary + '20'} 0%,
      transparent 80%
    );
    animation: rotate 30s linear infinite;
  }
  
  @keyframes rotate {
    0% {
      transform: rotate(0deg);
    }
    100% {
      transform: rotate(360deg);
    }
  }
`;

const LoginCard = styled.div`
  position: relative;
  z-index: 10;
  background-color: ${props => props.theme.bg.secondary};
  border-radius: 12px;
  padding: 40px;
  width: 400px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
`;

const Logo = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 30px;
`;

const LogoImage = styled.div`
  font-size: 2.5rem;
  font-weight: 700;
  color: ${props => props.theme.accent.primary};
  background: linear-gradient(135deg, ${props => props.theme.accent.primary}, ${props => props.theme.accent.secondary});
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin: 0;
`;

const Title = styled.h1`
  font-size: 1.8rem;
  font-weight: 700;
  text-align: center;
  margin-bottom: 30px;
  color: ${props => props.theme.text.primary};
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  font-size: 0.9rem;
  font-weight: 500;
  color: ${props => props.theme.text.secondary};
`;

const Input = styled.input`
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid ${props => props.theme.border.primary};
  background-color: ${props => props.theme.bg.input};
  color: ${props => props.theme.text.primary};
  font-size: 1rem;
  transition: all 0.2s ease;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.accent.primary + '40'};
  }
  
  &::placeholder {
    color: ${props => props.theme.text.placeholder};
  }
`;

const Button = styled.button`
  padding: 14px;
  border-radius: 8px;
  border: none;
  background-color: ${props => props.theme.accent.primary};
  color: white;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  margin-top: 10px;
  
  &:hover {
    background-color: ${props => props.theme.accent.secondary};
  }
  
  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
`;

const TwoFactorContainer = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const TwoFactorTitle = styled.h2`
  font-size: 1.2rem;
  font-weight: 600;
  color: ${props => props.theme.text.primary};
  text-align: center;
  margin-bottom: 10px;
`;

const TwoFactorDescription = styled.p`
  font-size: 0.9rem;
  color: ${props => props.theme.text.secondary};
  text-align: center;
  margin-bottom: 20px;
`;

const OTPInputContainer = styled.div`
  display: flex;
  justify-content: center;
  gap: 10px;
`;

const OTPInput = styled.input`
  width: 50px;
  height: 60px;
  border-radius: 8px;
  border: 1px solid ${props => props.theme.border.primary};
  background-color: ${props => props.theme.bg.input};
  color: ${props => props.theme.text.primary};
  font-size: 1.5rem;
  font-weight: 600;
  text-align: center;
  
  &:focus {
    outline: none;
    border-color: ${props => props.theme.accent.primary};
    box-shadow: 0 0 0 2px ${props => props.theme.accent.primary + '40'};
  }
`;

const ErrorMessage = styled.div`
  padding: 10px;
  background-color: rgba(239, 68, 68, 0.1);
  border-radius: 8px;
  color: ${props => props.theme.danger};
  font-size: 0.9rem;
  margin-bottom: 10px;
`;

const Separator = styled.div`
  display: flex;
  align-items: center;
  margin: 15px 0;
  
  &:before, &:after {
    content: "";
    flex: 1;
    border-bottom: 1px solid ${props => props.theme.border.primary};
  }
  
  span {
    padding: 0 10px;
    font-size: 0.85rem;
    color: ${props => props.theme.text.secondary};
  }
`;

const FingerprintButton = styled.button`
  padding: 14px;
  border-radius: 8px;
  border: 1px solid ${props => props.theme.border.primary};
  background-color: transparent;
  color: ${props => props.theme.text.primary};
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;
  
  &:hover {
    background-color: ${props => props.theme.bg.hover};
  }
`;

const FingerprintIcon = styled.span`
  font-size: 1.5rem;
`;

const Footer = styled.div`
  margin-top: 30px;
  text-align: center;
  font-size: 0.85rem;
  color: ${props => props.theme.text.secondary};
  
  a {
    color: ${props => props.theme.accent.primary};
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
`;

const LoginPage: React.FC = () => {
  // Состояния
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showTwoFactor, setShowTwoFactor] = useState(false);
  const [otpValues, setOtpValues] = useState(['', '', '', '']);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // Обработчики событий
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!username || !password) {
      setError('Пожалуйста, введите логин и пароль');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    // Имитация запроса к API
    setTimeout(() => {
      setIsLoading(false);
      
      // Успешный вход - переход к двухфакторной аутентификации
      if (username === 'admin' && password === 'admin123') {
        setShowTwoFactor(true);
      } else {
        setError('Неверные учетные данные. Попробуйте снова.');
      }
    }, 1500);
  };
  
  const handleOtpChange = (index: number, value: string) => {
    // Обновляем значение в массиве OTP
    const newValues = [...otpValues];
    newValues[index] = value;
    setOtpValues(newValues);
    
    // Автоматически переходим к следующему полю ввода
    if (value && index < otpValues.length - 1) {
      const nextInput = document.getElementById(`otp-${index + 1}`) as HTMLInputElement;
      if (nextInput) {
        nextInput.focus();
      }
    }
  };
  
  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    // При нажатии Backspace, если поле пустое, переходим к предыдущему полю
    if (e.key === 'Backspace' && !otpValues[index] && index > 0) {
      const prevInput = document.getElementById(`otp-${index - 1}`) as HTMLInputElement;
      if (prevInput) {
        prevInput.focus();
      }
    }
  };
  
  const handleVerifyOtp = () => {
    const otp = otpValues.join('');
    
    if (otp.length !== 4) {
      setError('Пожалуйста, введите полный код подтверждения');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    // Имитация проверки OTP
    setTimeout(() => {
      setIsLoading(false);
      
      // Для демо всегда считаем, что OTP 1234 - правильный
      if (otp === '1234') {
        // Перенаправление на главную страницу
        window.location.href = '/dashboard';
      } else {
        setError('Неверный код подтверждения');
      }
    }, 1000);
  };
  
  const handleFingerprintAuth = () => {
    setIsLoading(true);
    setError('');
    
    // Имитация биометрической аутентификации
    setTimeout(() => {
      setIsLoading(false);
      // В реальном приложении здесь была бы интеграция с биометрией
      // Для демо - просто перенаправляем на главную страницу
      window.location.href = '/dashboard';
    }, 2000);
  };
  
  // Визуализация компонента в зависимости от состояния аутентификации
  const renderLoginForm = () => (
    <>
      {error && <ErrorMessage>{error}</ErrorMessage>}
      <Form onSubmit={handleSubmit}>
        <InputGroup>
          <Label htmlFor="username">Имя пользователя</Label>
          <Input 
            id="username"
            type="text" 
            placeholder="Введите имя пользователя"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </InputGroup>
        
        <InputGroup>
          <Label htmlFor="password">Пароль</Label>
          <Input 
            id="password"
            type="password" 
            placeholder="Введите пароль"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </InputGroup>
        
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Вход...' : 'Войти в систему'}
        </Button>
      </Form>
      
      <Separator>
        <span>ИЛИ</span>
      </Separator>
      
      <FingerprintButton onClick={handleFingerprintAuth} disabled={isLoading}>
        <FingerprintIcon>👆</FingerprintIcon>
        Войти с биометрией
      </FingerprintButton>
      
      <Footer>
        Система управления NeuroNet v2.0<br />
        <a href="#">Политика безопасности</a> • <a href="#">Поддержка</a>
      </Footer>
    </>
  );
  
  const renderTwoFactorForm = () => (
    <TwoFactorContainer>
      <TwoFactorTitle>Двухфакторная аутентификация</TwoFactorTitle>
      <TwoFactorDescription>
        Введите 4-значный код, отправленный на ваше устройство безопасности
      </TwoFactorDescription>
      
      {error && <ErrorMessage>{error}</ErrorMessage>}
      
      <OTPInputContainer>
        {otpValues.map((value, index) => (
          <OTPInput
            key={index}
            id={`otp-${index}`}
            type="text"
            maxLength={1}
            value={value}
            onChange={(e) => handleOtpChange(index, e.target.value)}
            onKeyDown={(e) => handleOtpKeyDown(index, e)}
            autoFocus={index === 0}
          />
        ))}
      </OTPInputContainer>
      
      <Button onClick={handleVerifyOtp} disabled={isLoading}>
        {isLoading ? 'Проверка...' : 'Подтвердить'}
      </Button>
      
      <Footer>
        <a href="#" onClick={() => setShowTwoFactor(false)}>Назад к входу</a>
      </Footer>
    </TwoFactorContainer>
  );
  
  return (
    <Container>
      <BackgroundAnimation />
      <LoginCard>
        <Logo>
          <LogoImage>NeuroNet</LogoImage>
        </Logo>
        <Title>Панель управления</Title>
        
        {showTwoFactor ? renderTwoFactorForm() : renderLoginForm()}
      </LoginCard>
    </Container>
  );
};

export default LoginPage; 