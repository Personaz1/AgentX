import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider } from 'styled-components';
import CodexPage from '../pages/CodexPage';
import { BrowserRouter } from 'react-router-dom';
import { darkTheme } from '../theme';

// Мок API сервиса
jest.mock('../services/api', () => ({
  codexService: {
    runOperation: jest.fn().mockResolvedValue({
      id: 'test-id',
      timestamp: new Date().toISOString(),
      target: '/test/file.php',
      operation: 'ANALYZE',
      status: 'success',
      content: 'Результат анализа файла',
      summary: 'Операция выполнена успешно'
    }),
    getOperationHistory: jest.fn().mockResolvedValue([
      {
        id: 'history-1',
        timestamp: new Date().toISOString(),
        target: '/etc/passwd',
        operation: 'ANALYZE',
        status: 'success',
        content: 'Содержимое файла: ...', 
        summary: 'Файл содержит информацию о пользователях'
      },
      {
        id: 'history-2',
        timestamp: new Date().toISOString(),
        target: '/var/www/html/index.php',
        operation: 'MODIFY',
        status: 'success',
        content: 'Код модифицирован', 
        summary: 'Файл успешно изменен'
      }
    ])
  },
  c1Service: {
    getBrainState: jest.fn().mockResolvedValue({
      isActive: true,
      currentMode: 'STANDARD',
      lastOperation: 'Анализ кода',
      lastOperationTime: new Date().toISOString()
    }),
    getLlmAvailability: jest.fn().mockResolvedValue({
      available: true,
      provider: 'OPENAI',
      model: 'gpt-4'
    }),
    toggleBrainState: jest.fn().mockResolvedValue({
      isActive: false,
      currentMode: 'DISABLED',
      lastOperation: 'Система отключена',
      lastOperationTime: new Date().toISOString()
    })
  }
}));

// Обертка для компонента с необходимыми провайдерами
const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={darkTheme}>
        {component}
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('CodexPage Component', () => {
  beforeEach(() => {
    // Очищаем моки перед каждым тестом
    jest.clearAllMocks();
  });

  test('renders the CodexPage component correctly', async () => {
    renderWithProviders(<CodexPage />);
    
    // Проверяем наличие заголовка
    expect(screen.getByText('NeuroZond Codex Control')).toBeInTheDocument();
    
    // Проверяем наличие основных элементов формы
    await waitFor(() => {
      expect(screen.getByText('Тип операции')).toBeInTheDocument();
      expect(screen.getByText('Тип цели')).toBeInTheDocument();
      expect(screen.getByText('Выполнить')).toBeInTheDocument();
      expect(screen.getByText('История операций')).toBeInTheDocument();
    });
  });

  test('loads and displays brain and LLM status', async () => {
    renderWithProviders(<CodexPage />);
    
    await waitFor(() => {
      expect(screen.getByText('C1 Brain')).toBeInTheDocument();
      expect(screen.getByText('LLM Статус')).toBeInTheDocument();
    });
  });

  test('submits form with correct values', async () => {
    renderWithProviders(<CodexPage />);
    
    // Ждем загрузки компонента
    await waitFor(() => {
      expect(screen.getByText('Выполнить операцию Codex')).toBeInTheDocument();
    });
    
    // Заполняем форму
    const targetInput = screen.getByLabelText('Цель');
    fireEvent.change(targetInput, { target: { value: '/test/file.php' } });
    
    // Отправляем форму
    const submitButton = screen.getByText('Выполнить');
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      // Проверяем, что API был вызван с правильными параметрами
      expect(require('../services/api').codexService.runOperation).toHaveBeenCalledWith(
        '/test/file.php',
        'ANALYZE',
        'FILE',
        expect.any(Object)
      );
    });
  });

  test('displays operation history', async () => {
    renderWithProviders(<CodexPage />);
    
    await waitFor(() => {
      expect(screen.getByText('/etc/passwd')).toBeInTheDocument();
      expect(screen.getByText('/var/www/html/index.php')).toBeInTheDocument();
    });
  });

  test('toggles C1Brain state', async () => {
    renderWithProviders(<CodexPage />);
    
    await waitFor(() => {
      const toggleButton = screen.getByText('Остановить');
      fireEvent.click(toggleButton);
    });
    
    await waitFor(() => {
      expect(require('../services/api').c1Service.toggleBrainState).toHaveBeenCalled();
    });
  });

  test('shows warning when attempting LLM operation with LLM unavailable', async () => {
    // Переопределяем мок для недоступного LLM
    require('../services/api').c1Service.getLlmAvailability.mockResolvedValueOnce({
      available: false,
      provider: null,
      model: null
    });
    
    renderWithProviders(<CodexPage />);
    
    // Ждем загрузки компонента и отображения статуса LLM
    await waitFor(() => {
      expect(screen.getByText('Недоступен')).toBeInTheDocument();
    });
    
    // Выбираем операцию, которая требует LLM
    const operationSelect = screen.getByLabelText('Тип операции');
    fireEvent.change(operationSelect, { target: { value: 'ASK' } });
    
    // Заполняем форму
    const targetInput = screen.getByLabelText('Цель');
    fireEvent.change(targetInput, { target: { value: '/test/file.php' } });
    
    // Отправляем форму
    const submitButton = screen.getByText('Выполнить');
    fireEvent.click(submitButton);
    
    // Должно появиться сообщение об ошибке
    await waitFor(() => {
      expect(require('../services/api').codexService.runOperation).not.toHaveBeenCalled();
    });
  });
}); 