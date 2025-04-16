import { extendTheme, ThemeConfig } from '@chakra-ui/react';
import { mode } from '@chakra-ui/theme-tools';

const config: ThemeConfig = {
  initialColorMode: 'dark',
  useSystemColorMode: false,
};

const theme = extendTheme({
  config,
  fonts: {
    heading: 'Inter, system-ui, sans-serif',
    body: 'Inter, system-ui, sans-serif',
  },
  colors: {
    brand: {
      50: '#e3f2fd',
      100: '#bbdefb',
      200: '#90caf9',
      300: '#64b5f6',
      400: '#42a5f5',
      500: '#2196f3',
      600: '#1e88e5',
      700: '#1976d2',
      800: '#1565c0',
      900: '#0d47a1',
    },
    neutralDark: {
      50: '#f8f9fa',
      100: '#edf2f7',
      200: '#e2e8f0',
      300: '#cbd5e0',
      400: '#a0aec0',
      500: '#718096',
      600: '#4a5568',
      700: '#2d3748',
      800: '#1a202c',
      900: '#171923',
    },
    status: {
      success: '#38A169',
      warning: '#DD6B20',
      danger: '#E53E3E',
      info: '#3182CE',
    }
  },
  styles: {
    global: (props: any) => ({
      body: {
        bg: mode('white', '#121212')(props),
        color: mode('gray.800', 'white')(props),
      },
    }),
  },
  components: {
    Button: {
      baseStyle: {
        fontWeight: 'medium',
        borderRadius: 'md',
      },
      variants: {
        primary: {
          bg: 'brand.600',
          color: 'white',
          _hover: {
            bg: 'brand.700',
          },
        },
        secondary: {
          bg: 'gray.200',
          color: 'gray.800',
          _hover: {
            bg: 'gray.300',
          },
          _dark: {
            bg: 'gray.700',
            color: 'white',
            _hover: {
              bg: 'gray.600',
            },
          },
        },
        danger: {
          bg: 'red.500',
          color: 'white',
          _hover: {
            bg: 'red.600',
          },
        },
      },
    },
  },
});

// Типы для styled-components
export const darkTheme = {
  colors: {
    primary: '#0F94FF',
    secondary: '#6272A4',
    success: '#50FA7B',
    warning: '#FFB86C',
    danger: '#FF5555',
    info: '#8BE9FD',
    neutral: '#F8F8F2'
  },
  bg: {
    primary: '#121212',
    secondary: '#1E1E2E',
    tertiary: '#282A36',
    input: '#1E1E2E',
    hover: '#383A59'
  },
  text: {
    primary: '#F8F8F2',
    secondary: '#6C7293',
    tertiary: '#A0A0A0',
    inverted: '#282A36'
  },
  border: {
    primary: '#44475A',
    secondary: '#6C7293'
  },
  accent: {
    primary: '#BD93F9',
    secondary: '#A580FF'
  }
};

export default theme; 