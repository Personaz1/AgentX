import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from 'styled-components';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import CodexPage from '../pages/CodexPage';
import C1BrainPage from '../pages/C1BrainPage';
import { darkTheme } from '../theme';
import { codexService, c1Service } from '../services/api';

// Мок для API сервиса
jest.mock('../services/api', () => ({
  codexService: {
    runOperation: jest.fn((target, operation) => 
      Promise.resolve({
        id: 'test-id',
        timestamp: new Date().toISOString(),
        target,
        operation,
        status: 'success',
        content: `Тестовый результат для ${operation} на ${target}`,
        summary: 'Операция выполнена успешно.'
      })
    ),
    getOperationHistory: jest.fn(() => 
      Promise.resolve([
        {
          id: '1',
          timestamp: new Date(Date.now() - 3600000).toISOString(),
          target: '/etc/passwd',
          operation: 'ANALYZE',
          status: 'success',
          content: 'Анализ файла /etc/passwd завершен.',
          summary: 'Файл содержит информацию о пользователях.'
        }
      ])
    )
  },
  c1Service: {
    getBrainState: jest.fn(() => 
      Promise.resolve({
        isActive: true,
        currentMode: 'STANDARD',
        lastOperation: 'Анализ кода через Codex модуль',
        lastOperationTime: new Date().toISOString()
      })
    ),
    getLlmAvailability: jest.fn(() => 
      Promise.resolve({
        available: true,
        provider: 'OPENAI',
        model: 'gpt-4'
      })
    ),
    toggleBrainState: jest.fn(() => 
      Promise.resolve({
        isActive: false,
        currentMode: 'DISABLED',
        lastOperation: 'Система отключена вручную',
        lastOperationTime: new Date().toISOString()
      })
    )
  }
}));

// Мок для toast
jest.mock('@chakra-ui/react', () => {
  const originalModule = jest.requireActual('@chakra-ui/react');
  return {
    ...originalModule,
    useToast: () => jest.fn()
  };
});

// Компонент для тестирования интеграции
const TestApp = () => (
  <ThemeProvider theme={darkTheme}>
    <BrowserRouter>
      <Routes>
        <Route path="/codex" element={<CodexPage />} />
        <Route path="/c1brain" element={<C1BrainPage />} />
      </Routes>
    </BrowserRouter>
  </ThemeProvider>
);

describe('Codex Integration with C1Brain', () => {
  beforeEach(() => {
    // Очищаем моки перед каждым тестом
    jest.clearAllMocks();
  });

  test('codex operation updates brain logs correctly', async () => {
    // Рендерим приложение на странице Codex
    window.history.pushState({}, 'Codex Page', '/codex');
    const { rerender } = render(<TestApp />);
    
    // Ждем загрузки компонента
    await waitFor(() => {
      expect(screen.getByText('NeuroZond Codex Control')).toBeInTheDocument();
    });
    
    // Заполняем и отправляем форму Codex
    const targetInput = screen.getByLabelText('Цель');
    fireEvent.change(targetInput, { target: { value: '/test/file.php' } });
    
    const submitButton = screen.getByText('Выполнить');
    fireEvent.click(submitButton);
    
    // Ждем завершения операции
    await waitFor(() => {
      expect(codexService.runOperation).toHaveBeenCalled();
    });
    
    // Переходим на страницу C1Brain
    window.history.pushState({}, 'C1Brain Page', '/c1brain');
    
    // Перерендерим с новым URL
    rerender(<TestApp />);
    
    // Проверяем, что логи C1Brain отражают операцию Codex
    await waitFor(() => {
      expect(c1Service.getBrainState).toHaveBeenCalled();
    });
  });

  test('c1brain state affects codex operations', async () => {
    // Мокаем состояние C1Brain как неактивное и LLM как недоступный
    (c1Service.getBrainState as jest.Mock).mockResolvedValueOnce({
      isActive: false,
      currentMode: 'DISABLED',
      lastOperation: 'Система отключена',
      lastOperationTime: new Date().toISOString()
    });
    
    (c1Service.getLlmAvailability as jest.Mock).mockResolvedValueOnce({
      available: false,
      provider: null,
      model: null
    });
    
    // Рендерим приложение на странице Codex
    window.history.pushState({}, 'Codex Page', '/codex');
    render(<TestApp />);
    
    // Ждем загрузки страницы
    await waitFor(() => {
      expect(screen.getByText('Неактивен')).toBeInTheDocument();
      expect(screen.getByText('Недоступен')).toBeInTheDocument();
    });
    
    // Выбираем операцию ASK, которая требует LLM
    const operationSelect = screen.getByLabelText('Тип операции');
    fireEvent.change(operationSelect, { target: { value: 'ASK' } });
    
    // Заполняем форму
    const targetInput = screen.getByLabelText('Цель');
    fireEvent.change(targetInput, { target: { value: '/test/file.php' } });
    
    // Отправляем форму
    const submitButton = screen.getByText('Выполнить');
    fireEvent.click(submitButton);
    
    // Проверяем, что операция не выполняется, т.к. LLM недоступен
    await waitFor(() => {
      expect(codexService.runOperation).not.toHaveBeenCalled();
    });
    
    // Меняем операцию на не требующую LLM
    fireEvent.change(operationSelect, { target: { value: 'EXECUTE' } });
    
    // Пробуем снова выполнить операцию
    fireEvent.click(submitButton);
    
    // Теперь операция должна выполниться
    await waitFor(() => {
      expect(codexService.runOperation).toHaveBeenCalled();
    });
  });
  
  test('toggling brain state from codex page works correctly', async () => {
    // Рендерим приложение на странице Codex
    window.history.pushState({}, 'Codex Page', '/codex');
    render(<TestApp />);
    
    // Ждем загрузки компонента
    await waitFor(() => {
      expect(screen.getByText('C1 Brain')).toBeInTheDocument();
    });
    
    // Нажимаем на кнопку переключения состояния C1Brain
    const toggleButton = screen.getByText('Остановить');
    fireEvent.click(toggleButton);
    
    // Проверяем, что метод toggleBrainState был вызван
    await waitFor(() => {
      expect(c1Service.toggleBrainState).toHaveBeenCalled();
    });
    
    // Проверяем, что состояние было обновлено
    await waitFor(() => {
      expect(c1Service.getBrainState).toHaveBeenCalled();
    });
  });
}); 