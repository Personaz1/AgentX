export interface ThemeColors {
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
    placeholder: string;
    inverted: string;
  };
  border: {
    primary: string;
    secondary: string;
  };
  accent: {
    primary: string;
    secondary: string;
  };
  success: string;
  warning: string;
  danger: string;
  info: string;
}

export const darkTheme: ThemeColors = {
  bg: {
    primary: '#121212',
    secondary: '#1E1E1E',
    tertiary: '#2D2D2D',
    input: '#252525',
    hover: '#333333',
  },
  text: {
    primary: '#FFFFFF',
    secondary: '#A0A0A0',
    placeholder: '#6C6C6C',
    inverted: '#000000',
  },
  border: {
    primary: '#3A3A3A',
    secondary: '#4D4D4D',
  },
  accent: {
    primary: '#0F94FF',
    secondary: '#107EFF',
  },
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#3B82F6',
};

export const lightTheme: ThemeColors = {
  bg: {
    primary: '#F5F5F5',
    secondary: '#FFFFFF',
    tertiary: '#EEEEEE',
    input: '#FFFFFF',
    hover: '#E0E0E0',
  },
  text: {
    primary: '#121212',
    secondary: '#666666',
    placeholder: '#AAAAAA',
    inverted: '#FFFFFF',
  },
  border: {
    primary: '#E0E0E0',
    secondary: '#CCCCCC',
  },
  accent: {
    primary: '#0F84FF',
    secondary: '#0070E0',
  },
  success: '#10B981',
  warning: '#F59E0B',
  danger: '#EF4444',
  info: '#3B82F6',
}; 