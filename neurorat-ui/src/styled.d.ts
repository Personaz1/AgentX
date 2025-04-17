import 'styled-components';

// Расширяем тему styled-components, чтобы типизировать наши кастомные свойства
declare module 'styled-components' {
  export interface DefaultTheme {
    colors?: {
      primary?: string;
      secondary?: string;
      success?: string;
      warning?: string;
      danger?: string;
      info?: string;
      neutral?: string;
    };
    bg?: {
      primary?: string;
      secondary?: string;
      tertiary?: string;
      input?: string;
      hover?: string;
    };
    text?: {
      primary?: string;
      secondary?: string;
      tertiary?: string;
      inverted?: string;
    };
    border?: {
      primary?: string;
      secondary?: string;
    };
    accent?: {
      primary?: string;
      secondary?: string;
    };
  }
} 