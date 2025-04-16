// Определение типов темы для styled-components
import 'styled-components';

// Расширение DefaultTheme
declare module 'styled-components' {
  export interface DefaultTheme {
    bg: {
      primary: string;
      secondary: string;
      tertiary: string;
      input: string;
      hover: string;
    };
    text: {
      primary: string;
      secondary: string;
      tertiary: string;
      placeholder: string;
    };
    accent: {
      primary: string;
      secondary: string;
    };
    border: {
      primary: string;
      secondary: string;
    };
    success: string;
    warning: string;
    danger: string;
    info: string;
  }
}

// Темная тема по умолчанию
export const darkTheme = {
  bg: {
    primary: '#1A202C',
    secondary: '#2D3748',
    tertiary: '#4A5568',
    input: '#2D3748',
    hover: '#3A4A5F',
  },
  text: {
    primary: '#F7FAFC',
    secondary: '#A0AEC0',
    tertiary: '#718096',
    placeholder: '#718096',
  },
  accent: {
    primary: '#3683DC',
    secondary: '#4299E1',
  },
  border: {
    primary: '#4A5568',
    secondary: '#2D3748',
  },
  success: '#38A169',
  warning: '#DD6B20',
  danger: '#E53E3E',
  info: '#3182CE',
};

// Светлая тема (для будущего использования)
export const lightTheme = {
  bg: {
    primary: '#F7FAFC',
    secondary: '#EDF2F7',
    tertiary: '#E2E8F0',
    input: '#FFFFFF',
    hover: '#EDF2F7',
  },
  text: {
    primary: '#1A202C',
    secondary: '#4A5568',
    tertiary: '#718096',
    placeholder: '#A0AEC0',
  },
  accent: {
    primary: '#3683DC',
    secondary: '#4299E1',
  },
  border: {
    primary: '#E2E8F0',
    secondary: '#EDF2F7',
  },
  success: '#38A169',
  warning: '#DD6B20',
  danger: '#E53E3E',
  info: '#3182CE',
}; 