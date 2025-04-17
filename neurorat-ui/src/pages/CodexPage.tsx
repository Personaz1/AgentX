import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Paper, 
  TextField, 
  Button, 
  Select, 
  MenuItem, 
  FormControl, 
  InputLabel, 
  Divider, 
  Alert, 
  CircularProgress,
  Snackbar,
  FormHelperText,
  Card,
  CardContent,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  SelectChangeEvent,
  Stack,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Checkbox
} from '@mui/material';
import { CodeOutlined, BugReportOutlined, MemoryOutlined, SendOutlined, AnalyticsOutlined, ExpandMore, AddOutlined, DeleteOutlined } from '@mui/icons-material';
import { codexService, c1Service, CodexOperationType, CodexTargetType, CodexResult, LlmAvailability, C1BrainState } from '../services/api';

// Интерфейс расширяет CodexResult
interface OperationHistoryItem extends CodexResult {
  targetType?: CodexTargetType;
}

// Интерфейс для задач Codex
interface CodexTask {
  id: string;
  description: string;
  completed: boolean;
  priority: 'low' | 'medium' | 'high';
  createdAt: string;
}

const CodexPage: React.FC = () => {
  // Состояния для формы операции
  const [target, setTarget] = useState<string>('');
  const [operation, setOperation] = useState<CodexOperationType>('ANALYZE');
  const [targetType, setTargetType] = useState<CodexTargetType>('FILE');
  const [options, setOptions] = useState<string[]>([]);
  
  // Состояния для результатов и истории
  const [operationHistory, setOperationHistory] = useState<OperationHistoryItem[]>([]);
  const [currentResult, setCurrentResult] = useState<CodexResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  
  // Состояния для C1Brain и LLM
  const [brainState, setBrainState] = useState<C1BrainState>({
    isActive: false,
    currentMode: '',
    lastOperation: '',
    lastOperationTime: ''
  });
  const [llmAvailable, setLlmAvailable] = useState<LlmAvailability>({
    available: false,
    provider: null,
    model: null
  });
  
  // Состояния для уведомлений
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({
    open: false,
    message: '',
    severity: 'info'
  });

  // Состояние для задач Codex
  const [codexTasks, setCodexTasks] = useState<CodexTask[]>([]);
  const [newTaskDescription, setNewTaskDescription] = useState<string>('');
  const [taskPriority, setTaskPriority] = useState<'low' | 'medium' | 'high'>('medium');

  // Функция для получения иконки операции
  const getOperationIcon = (op: CodexOperationType) => {
    switch (op) {
      case 'ANALYZE': return <AnalyticsOutlined />;
      case 'EXPLOIT': return <BugReportOutlined />;
      default: return <SendOutlined />;
    }
  };

  // Обработчик изменения поля "цель"
  const handleTargetChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTarget(e.target.value);
  };

  // Загрузка начальных данных
  useEffect(() => {
    fetchInitialData();
    
    // Загружаем задачи из локального хранилища
    const savedTasks = localStorage.getItem('codexTasks');
    if (savedTasks) {
      setCodexTasks(JSON.parse(savedTasks));
    }
  }, []);

  // Сохраняем задачи при изменении
  useEffect(() => {
    localStorage.setItem('codexTasks', JSON.stringify(codexTasks));
  }, [codexTasks]);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      
      // Параллельная загрузка истории операций, состояния C1 и статуса LLM
      const [historyData, brainStateData, llmData] = await Promise.all([
        codexService.getOperationHistory(),
        c1Service.getBrainState(),
        c1Service.getLlmAvailability()
      ]);

      setOperationHistory(historyData);
      setBrainState(brainStateData);
      setLlmAvailable(llmData);
      
      // Если есть хотя бы одна операция, выбираем последнюю
      if (historyData.length > 0) {
        setCurrentResult(historyData[0]);
      }
    } catch (error) {
      console.error('Ошибка при загрузке данных:', error);
      setSnackbar({
        open: true,
        message: 'Не удалось загрузить данные. Проверьте соединение.',
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };

  // Функция для рендеринга результатов операции
  const renderResult = (result: CodexResult) => {
    // Если операция была неуспешной, отображаем ошибку
    if (result.status !== 'success') {
      return <Typography color="error">{result.summary}</Typography>;
    }

    // В зависимости от типа операции отображаем результат по-разному
    switch (result.operation) {
      case 'ANALYZE':
        return <Typography variant="body1">{result.content}</Typography>;
      case 'EXECUTE':
        return <pre>{result.content}</pre>;
      default:
        return <Typography variant="body1">{result.content}</Typography>;
    }
  };

  // Выполнение операции Codex
  const handleRunOperation = async () => {
    // Проверка доступности LLM для операций, которые этого требуют
    if ((operation === 'ASK' || operation === 'ANALYZE') && llmAvailable.available === false) {
      setSnackbar({
        open: true,
        message: 'LLM недоступен! Эта операция требует работающий LLM.',
        severity: 'error'
      });
      return;
    }

    setLoading(true);
    setCurrentResult(null);

    try {
      // Парсинг JSON-опций
      let parsedOptions = {};
      try {
        parsedOptions = JSON.parse(options.join(','));
      } catch (e) {
        throw new Error('Неверный формат JSON в опциях');
      }

      const result = await codexService.runOperation(target, operation, targetType, parsedOptions);
      
      const historyItem: OperationHistoryItem = {
        ...result,
        targetType
      };

      setCurrentResult(result);
      
      // Обновление истории операций
      setOperationHistory(prev => [historyItem, ...prev]);
      
      setSnackbar({
        open: true,
        message: result.status === 'success' ? 'Операция успешно выполнена' : `Ошибка выполнения операции: ${result.summary}`,
        severity: result.status === 'success' ? 'success' : 'error'
      });
      
      // Обновление состояния C1Brain после операции
      const newBrainState = await c1Service.getBrainState();
      setBrainState(newBrainState);
    } catch (error) {
      console.error('Error running Codex operation:', error);
      setSnackbar({
        open: true,
        message: `Ошибка выполнения операции: ${error instanceof Error ? error.message : 'Неизвестная ошибка'}`,
        severity: 'error'
      });
    } finally {
      setLoading(false);
    }
  };
  
  // Обработчики изменения формы
  const handleOperationChange = (event: SelectChangeEvent<string>) => {
    setOperation(event.target.value as CodexOperationType);
  };
  
  const handleTargetTypeChange = (event: SelectChangeEvent<string>) => {
    setTargetType(event.target.value as CodexTargetType);
  };
  
  // Переключение состояния C1Brain
  const toggleC1Brain = async () => {
    try {
      setSnackbar({
        open: true,
        message: 'Переключение состояния C1Brain...',
        severity: 'info'
      });
      
      const newState = await c1Service.toggleBrainState();
      
      setBrainState(newState);
      
      setSnackbar({
        open: true,
        message: `C1Brain сейчас ${newState.isActive ? 'активен' : 'неактивен'}`,
        severity: 'success'
      });
    } catch (error) {
      console.error('Error toggling C1Brain state:', error);
      setSnackbar({
        open: true,
        message: 'Ошибка переключения состояния C1Brain',
        severity: 'error'
      });
    }
  };

  // Функции для управления задачами
  const addTask = () => {
    if (!newTaskDescription.trim()) return;
    
    const newTask: CodexTask = {
      id: Date.now().toString(),
      description: newTaskDescription,
      completed: false,
      priority: taskPriority,
      createdAt: new Date().toISOString()
    };
    
    setCodexTasks(prev => [...prev, newTask]);
    setNewTaskDescription('');
    setTaskPriority('medium');
  };
  
  const toggleTaskCompletion = (id: string) => {
    setCodexTasks(prev => 
      prev.map(task => 
        task.id === id ? { ...task, completed: !task.completed } : task
      )
    );
  };
  
  const deleteTask = (id: string) => {
    setCodexTasks(prev => prev.filter(task => task.id !== id));
  };
  
  const getPriorityColor = (priority: 'low' | 'medium' | 'high'): string => {
    switch (priority) {
      case 'low': return '#4CAF50';
      case 'medium': return '#FF9800';
      case 'high': return '#F44336';
      default: return '#FF9800';
    }
  };

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Typography variant="h4" gutterBottom>
        NeuroZond Codex Control
      </Typography>
      
      <Stack spacing={3}>
        {/* Статус системы */}
        <Box>
          <Typography variant="h5" sx={{ mb: 2 }}>
            Системный статус
          </Typography>
          
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <Card sx={{ flex: 1 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <MemoryOutlined color="primary" />
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    C1 Brain
                  </Typography>
                  <Chip 
                    label={brainState.isActive ? 'Активен' : 'Неактивен'} 
                    color={brainState.isActive ? 'success' : 'error'}
                    size="small"
                    sx={{ ml: 2 }}
                  />
                </Box>
                
                <Typography variant="body2">
                  Последняя синхронизация: {brainState.lastOperationTime}
                </Typography>
                
                <Button 
                  variant="outlined" 
                  color={brainState.isActive ? 'error' : 'success'} 
                  size="small"
                  onClick={toggleC1Brain}
                  sx={{ mt: 2 }}
                >
                  {brainState.isActive ? 'Остановить' : 'Запустить'}
                </Button>
              </CardContent>
            </Card>
            <Card sx={{ flex: 1 }}>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                  <CodeOutlined color="primary" />
                  <Typography variant="h6" sx={{ ml: 1 }}>
                    LLM Статус
                  </Typography>
                  <Chip 
                    label={llmAvailable.available ? 'Доступен' : 'Недоступен'} 
                    color={llmAvailable.available ? 'success' : 'error'}
                    size="small"
                    sx={{ ml: 2 }}
                  />
                </Box>
                
                <Typography variant="body2">
                  Модель: {llmAvailable.model}
                </Typography>
              </CardContent>
            </Card>
          </Stack>
        </Box>
        
        {/* Задачи Codex */}
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Задачи Codex
          </Typography>
          
          <Box sx={{ mb: 3, display: 'flex', gap: 2, alignItems: 'flex-start' }}>
            <TextField
              label="Новая задача"
              value={newTaskDescription}
              onChange={(e) => setNewTaskDescription(e.target.value)}
              fullWidth
              sx={{ flexGrow: 1 }}
            />
            
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel>Приоритет</InputLabel>
              <Select
                value={taskPriority}
                label="Приоритет"
                onChange={(e) => setTaskPriority(e.target.value as 'low' | 'medium' | 'high')}
                size="small"
              >
                <MenuItem value="low">Низкий</MenuItem>
                <MenuItem value="medium">Средний</MenuItem>
                <MenuItem value="high">Высокий</MenuItem>
              </Select>
            </FormControl>
            
            <Button 
              variant="contained" 
              color="primary" 
              onClick={addTask}
              startIcon={<AddOutlined />}
            >
              Добавить
            </Button>
          </Box>
          
          <List>
            {codexTasks.length === 0 ? (
              <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                Нет активных задач. Добавьте новую задачу выше.
              </Typography>
            ) : (
              codexTasks.map(task => (
                <ListItem
                  key={task.id}
                  secondaryAction={
                    <IconButton edge="end" onClick={() => deleteTask(task.id)}>
                      <DeleteOutlined />
                    </IconButton>
                  }
                  sx={{
                    bgcolor: 'background.paper',
                    borderLeft: `4px solid ${getPriorityColor(task.priority)}`,
                    mb: 1,
                    borderRadius: 1,
                  }}
                >
                  <ListItemIcon>
                    <Checkbox
                      edge="start"
                      checked={task.completed}
                      onChange={() => toggleTaskCompletion(task.id)}
                    />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography
                        variant="body1"
                        style={{
                          textDecoration: task.completed ? 'line-through' : 'none',
                          color: task.completed ? 'text.secondary' : 'text.primary'
                        }}
                      >
                        {task.description}
                      </Typography>
                    }
                    secondary={`Создано: ${new Date(task.createdAt).toLocaleString()}`}
                  />
                </ListItem>
              ))
            )}
          </List>
        </Paper>
        
        {/* Форма операции */}
        <Paper elevation={3} sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom>
            Выполнить операцию Codex
          </Typography>
          
          <Stack spacing={3}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
              <FormControl fullWidth>
                <InputLabel>Тип операции</InputLabel>
                <Select
                  value={operation}
                  label="Тип операции"
                  onChange={handleOperationChange}
                >
                  <MenuItem value="ANALYZE">Анализ</MenuItem>
                  <MenuItem value="MODIFY">Модификация</MenuItem>
                  <MenuItem value="EXECUTE">Выполнение</MenuItem>
                  <MenuItem value="ASK">Запрос</MenuItem>
                  <MenuItem value="EXPLOIT">Эксплуатация</MenuItem>
                </Select>
                <FormHelperText>
                  {operation === 'ANALYZE' && 'Анализ кода или системы с использованием LLM'}
                  {operation === 'MODIFY' && 'Модификация кода с помощью Codex'}
                  {operation === 'EXECUTE' && 'Выполнение команд или сценариев'}
                  {operation === 'ASK' && 'Запрос информации у LLM'}
                  {operation === 'EXPLOIT' && 'Поиск и эксплуатация уязвимостей'}
                </FormHelperText>
              </FormControl>
              
              <FormControl fullWidth>
                <InputLabel>Тип цели</InputLabel>
                <Select
                  value={targetType}
                  label="Тип цели"
                  onChange={handleTargetTypeChange}
                >
                  <MenuItem value="FILE">Файл</MenuItem>
                  <MenuItem value="DIRECTORY">Директория</MenuItem>
                  <MenuItem value="URL">URL</MenuItem>
                  <MenuItem value="CODE_SNIPPET">Фрагмент кода</MenuItem>
                </Select>
              </FormControl>
            </Stack>
            
            <TextField
              label="Цель"
              fullWidth
              value={target}
              onChange={handleTargetChange}
              multiline={targetType === 'CODE_SNIPPET'}
              rows={targetType === 'CODE_SNIPPET' ? 4 : 1}
              placeholder={
                targetType === 'FILE' ? '/path/to/file.c' : 
                targetType === 'DIRECTORY' ? '/path/to/directory/' :
                targetType === 'URL' ? 'https://example.com/api' :
                'Введите фрагмент кода для анализа'
              }
            />
            
            <TextField
              label="Дополнительные опции (JSON)"
              fullWidth
              value={options.join(',')}
              onChange={(e) => setOptions(e.target.value.split(','))}
              multiline
              rows={3}
              placeholder='{"recursive": true, "depth": 2}'
            />
            
            <Button 
              variant="contained" 
              color="primary" 
              onClick={handleRunOperation}
              disabled={loading || !target || !operation}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : getOperationIcon(operation as CodexOperationType)}
              fullWidth
            >
              {loading ? 'Выполнение...' : 'Выполнить'}
            </Button>
          </Stack>
        </Paper>
        
        {/* Результаты операции */}
        {currentResult && (
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Результат операции
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Chip 
                label={currentResult.status === 'success' ? 'Успешно' : 'Ошибка'} 
                color={currentResult.status === 'success' ? 'success' : 'error'}
                sx={{ mr: 1 }}
              />
              <Typography variant="body2" display="inline">
                ID: {currentResult.id} | 
                {new Date(currentResult.timestamp).toLocaleString()}
              </Typography>
            </Box>
            
            <Typography variant="h6" gutterBottom>
              Краткий результат:
            </Typography>
            <Typography variant="body1" sx={{ mb: 2 }}>
              {currentResult.summary}
            </Typography>
            
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Typography>Подробный результат</Typography>
              </AccordionSummary>
              <AccordionDetails>
                {renderResult(currentResult)}
              </AccordionDetails>
            </Accordion>
          </Paper>
        )}
        
        {/* История операций */}
        <Box>
          <Typography variant="h5" gutterBottom>
            История операций
          </Typography>
          
          {operationHistory.length === 0 ? (
            <Paper elevation={1} sx={{ p: 2 }}>
              <Typography variant="body1">
                Нет записей об операциях. Выполните операцию Codex, чтобы увидеть результаты здесь.
              </Typography>
            </Paper>
          ) : (
            <Stack spacing={2}>
              {operationHistory.map((op) => (
                <Paper key={op.id} elevation={1} sx={{ p: 2 }}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="h6">
                      {op.operation} - {op.target}
                    </Typography>
                    <Chip 
                      label={op.status === 'success' ? 'Успешно' : 'Ошибка'} 
                      color={op.status === 'success' ? 'success' : 'error'} 
                      size="small" 
                    />
                  </Box>
                  
                  <Typography variant="caption" display="block" gutterBottom>
                    {new Date(op.timestamp).toLocaleString()} | ID: {op.id}
                  </Typography>
                  
                  <Typography variant="body2" sx={{ mt: 1 }}>
                    {renderResult(op)}
                  </Typography>
                  
                  <Button 
                    size="small" 
                    sx={{ mt: 1 }} 
                    onClick={() => setCurrentResult(op)}
                  >
                    Просмотреть
                  </Button>
                </Paper>
              ))}
            </Stack>
          )}
        </Box>
      </Stack>
      
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
      >
        <Alert severity={snackbar.severity} onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default CodexPage; 