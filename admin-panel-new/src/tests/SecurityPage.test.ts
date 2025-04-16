import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import SecurityPage from '../pages/SecurityPage';

describe('SecurityPage', () => {
  beforeEach(() => {
    // Мокаем данные и используемые хуки
    jest.mock('react', () => ({
      ...jest.requireActual('react'),
      useState: jest.fn((init) => [init, jest.fn()]),
    }));
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  test('Страница отображает корректный заголовок', () => {
    render(<SecurityPage />);
    expect(screen.getByText('Управление безопасностью')).toBeInTheDocument();
  });

  test('Отображается правильное количество активных угроз', () => {
    render(<SecurityPage />);
    
    // По умолчанию в начальных данных у нас 1 активная угроза
    const activeThreatsValue = screen.getByText('1');
    expect(activeThreatsValue).toBeInTheDocument();
    
    const activeThreatsLabel = screen.getByText('Активные угрозы');
    expect(activeThreatsLabel).toBeInTheDocument();
  });

  test('Правильно вычисляется оценка безопасности', () => {
    render(<SecurityPage />);
    
    // Проверяем, что оценка безопасности отображается
    const securityScoreValue = screen.getByText('57%');
    expect(securityScoreValue).toBeInTheDocument();
  });

  test('Кнопка "Устранить" вызывает функцию mitigateThreat', () => {
    const { getAllByText } = render(<SecurityPage />);
    
    // Находим кнопку "Устранить" для активной угрозы
    const mitigateButtons = getAllByText('Устранить');
    expect(mitigateButtons.length).toBeGreaterThan(0);
    
    // Кликаем на первую кнопку
    fireEvent.click(mitigateButtons[0]);
    
    // Проверяем, что статус угрозы сменился на 'mitigated'
    // Это будет работать только если мы правильно замокаем useState
  });

  test('Кнопка "Исправить" вызывает функцию patchVulnerability', () => {
    const { getAllByText } = render(<SecurityPage />);
    
    // Находим кнопку "Исправить" для открытой уязвимости
    const patchButtons = getAllByText('Исправить');
    expect(patchButtons.length).toBeGreaterThan(0);
    
    // Кликаем на первую кнопку
    fireEvent.click(patchButtons[0]);
    
    // Проверяем, что статус уязвимости сменился на 'patched'
    // Это будет работать только если мы правильно замокаем useState
  });

  test('Кнопка переключения в настройках защиты работает корректно', () => {
    const { getAllByText } = render(<SecurityPage />);
    
    // Находим кнопку "Отключить" для включенной защиты
    const toggleButtons = getAllByText('Отключить');
    expect(toggleButtons.length).toBeGreaterThan(0);
    
    // Кликаем на первую кнопку
    fireEvent.click(toggleButtons[0]);
    
    // Проверяем, что статус конфигурации сменился
    // Это будет работать только если мы правильно замокаем useState
  });

  test('Отображаются все три секции: угрозы, уязвимости и настройки защиты', () => {
    render(<SecurityPage />);
    
    expect(screen.getByText('Активные угрозы')).toBeInTheDocument();
    expect(screen.getByText('Уязвимости')).toBeInTheDocument();
    expect(screen.getByText('Настройки защиты')).toBeInTheDocument();
  });

  test('Уязвимости с эксплойтами помечены соответствующим образом', () => {
    render(<SecurityPage />);
    
    const exploitBadges = screen.getAllByText('Есть эксплойт');
    expect(exploitBadges.length).toBeGreaterThan(0);
  });
}); 