import { extendTheme, type ThemeConfig } from '@chakra-ui/react';

// Конфигурация темы, включая настройки для темного режима
const config: ThemeConfig = {
  initialColorMode: 'dark',
  useSystemColorMode: false,
};

// Расширенная тема
export const theme = extendTheme({
  config,
  colors: {
    // Основной цвет бренда
    brand: {
      50: '#e6f1fe',
      100: '#cce3fd',
      200: '#99c7fb',
      300: '#66aaf9',
      400: '#338ef7',
      500: '#0072f5', // Основной цвет
      600: '#005bc2',
      700: '#00448f',
      800: '#002e5c',
      900: '#001729',
    },
    // Дополнительные семантические цвета
    success: {
      50: '#e6f7ed',
      100: '#ccf0db',
      200: '#99e0b7',
      300: '#66d193',
      400: '#33c16f',
      500: '#00b24b',
      600: '#008e3c',
      700: '#006b2d',
      800: '#00471e',
      900: '#00240f',
    },
    warning: {
      50: '#fff8e6',
      100: '#fff1cc',
      200: '#ffe399',
      300: '#ffd666',
      400: '#ffc833',
      500: '#ffbb00',
      600: '#cc9500',
      700: '#997000',
      800: '#664b00',
      900: '#332500',
    },
    error: {
      50: '#fce8e8',
      100: '#f9d1d1',
      200: '#f4a3a3',
      300: '#ee7575',
      400: '#e94747',
      500: '#e31919',
      600: '#b61414',
      700: '#880f0f',
      800: '#5b0a0a',
      900: '#2d0505',
    },
  },
  fonts: {
    heading: 'Inter, system-ui, sans-serif',
    body: 'Inter, system-ui, sans-serif',
  },
  components: {
    // Стили для компонентов
    Button: {
      defaultProps: {
        colorScheme: 'brand',
      },
      variants: {
        solid: (props: any) => ({
          bg: `${props.colorScheme}.500`,
          color: 'white',
          _hover: {
            bg: `${props.colorScheme}.600`,
          },
        }),
      },
    },
    Card: {
      baseStyle: {
        container: {
          borderRadius: 'lg',
          boxShadow: 'sm',
        },
        header: {
          padding: 4,
        },
        body: {
          padding: 4,
        },
        footer: {
          padding: 4,
        },
      },
    },
    Badge: {
      defaultProps: {
        variant: 'subtle',
      },
    },
  },
  styles: {
    global: (props: any) => ({
      body: {
        bg: props.colorMode === 'dark' ? 'gray.900' : 'gray.50',
        color: props.colorMode === 'dark' ? 'white' : 'gray.800',
      },
    }),
  },
}); 