import { createGlobalStyle } from 'styled-components';

const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }
  
  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
      'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    background-color: ${props => props.theme.bg.primary};
    color: ${props => props.theme.text.primary};
    min-height: 100vh;
  }
  
  /* Скроллбар */
  ::-webkit-scrollbar {
    width: 8px;
    height: 8px;
  }
  
  ::-webkit-scrollbar-track {
    background: ${props => props.theme.bg.primary};
  }
  
  ::-webkit-scrollbar-thumb {
    background: ${props => props.theme.border.primary};
    border-radius: 4px;
  }
  
  ::-webkit-scrollbar-thumb:hover {
    background: ${props => props.theme.text.secondary};
  }
  
  /* Типографика */
  h1, h2, h3, h4, h5, h6 {
    margin: 0;
    font-weight: 600;
  }
  
  p {
    margin: 0;
  }
  
  a {
    text-decoration: none;
    color: ${props => props.theme.accent.primary};
    
    &:hover {
      text-decoration: underline;
    }
  }
  
  /* Формы */
  button, input, select, textarea {
    font-family: inherit;
  }
  
  button {
    cursor: pointer;
  }
  
  /* Анимации и переходы */
  button, a, input, select {
    transition: all 0.2s ease;
  }
  
  /* Контейнер */
  .container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
  }
  
  /* Утилиты */
  .visually-hidden {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border-width: 0;
  }
`;

export default GlobalStyle; 