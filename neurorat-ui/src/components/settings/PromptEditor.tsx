import React from 'react';
import { Card, Box, Typography } from '@mui/material';
import CodeEditor from '@uiw/react-textarea-code-editor';
import { darkTheme } from '../../theme';

// Интерфейс для промпта
export interface Prompt {
  name: string;
  description: string;
  version: string;
  prompt: string;
}

interface PromptEditorProps {
  prompt: Prompt | null;
  onChange: (newPrompt: Prompt) => void;
  title: string;
  description: string;
  minHeight?: string;
}

export const PromptEditor: React.FC<PromptEditorProps> = ({
  prompt,
  onChange,
  title,
  description,
  minHeight = '300px'
}) => {
  
  const handleChange = (value: string) => {
    if (prompt) {
      onChange({
        ...prompt,
        prompt: value
      });
    }
  };
  
  return (
    <Card
      sx={{
        p: 2,
        mb: 3,
        backgroundColor: darkTheme.bg.secondary,
        border: `1px solid ${darkTheme.border.primary}`,
        borderRadius: '8px',
      }}
    >
      <Typography variant="h6" sx={{ mb: 2 }}>
        {title}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        {description}
      </Typography>
      <Box sx={{ borderRadius: '4px', overflow: 'hidden' }}>
        <CodeEditor
          value={prompt?.prompt || ''}
          language="json"
          placeholder={`${title}...`}
          onChange={(evn) => handleChange(evn.target.value)}
          padding={15}
          style={{
            fontSize: 14,
            backgroundColor: darkTheme.bg.primary,
            fontFamily: 'ui-monospace,SFMono-Regular,SF Mono,Consolas,Liberation Mono,Menlo,monospace',
            minHeight: minHeight,
          }}
        />
      </Box>
    </Card>
  );
};

export default PromptEditor; 