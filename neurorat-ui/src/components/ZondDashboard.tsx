import React, { useState, useEffect } from 'react';
import { Grid, Box, Typography, Alert, CircularProgress } from '@mui/material';
import ZondCard, { ZondStatus } from './ZondCard';
import { zondsService } from '../services/api';

export interface SystemComponent {
  id: string;
  title: string;
  status: ZondStatus;
  description: string;
  icon: string;
  lastUpdated: string;
  path: string;
}

const ZondDashboard: React.FC = () => {
  const [components, setComponents] = useState<SystemComponent[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSystemComponents = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await zondsService.getSystemComponents();
      setComponents(data);
    } catch (err) {
      console.error('Ошибка при загрузке компонентов:', err);
      setError('Не удалось загрузить компоненты системы. Попробуйте позже.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSystemComponents();

    // Обновляем статус компонентов каждые 30 секунд
    const interval = setInterval(() => {
      fetchSystemComponents();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  if (loading && components.length === 0) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%', p: 3 }}>
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}
      
      <Typography variant="h4" component="h1" gutterBottom>
        Статус системы
      </Typography>
      
      <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
        Мониторинг состояния всех компонентов системы NeuroZond
      </Typography>
      
      <Grid container spacing={3}>
        {components.map((component) => (
          <Grid item xs={12} sm={6} md={4} lg={3} key={component.id}>
            <ZondCard
              title={component.title}
              status={component.status}
              description={component.description}
              icon={component.icon}
              lastUpdated={component.lastUpdated}
              path={component.path}
            />
          </Grid>
        ))}
        
        {components.length === 0 && !loading && (
          <Grid item xs={12}>
            <Alert severity="info">
              Компоненты системы не найдены
            </Alert>
          </Grid>
        )}
      </Grid>
    </Box>
  );
};

export default ZondDashboard; 