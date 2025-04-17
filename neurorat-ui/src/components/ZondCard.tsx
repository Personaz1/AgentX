import React from 'react';
import {
  Card,
  CardContent,
  CardActionArea,
  Typography,
  Box,
  Chip,
  Stack,
  LinearProgress,
  useTheme
} from '@mui/material';
import { 
  CheckCircle as HealthyIcon,
  Warning as WarningIcon,
  Error as CriticalIcon,
  Cancel as InactiveIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

export type ZondStatus = 'healthy' | 'warning' | 'critical' | 'inactive';

export interface ZondCardProps {
  title: string;
  status: ZondStatus;
  description: string;
  icon: string;
  lastUpdated: string;
  path: string;
}

const ZondCard: React.FC<ZondCardProps> = ({ 
  title, 
  status, 
  description, 
  icon, 
  lastUpdated,
  path 
}) => {
  const theme = useTheme();
  const navigate = useNavigate();

  const getStatusIcon = () => {
    switch (status) {
      case 'healthy': return <HealthyIcon sx={{ color: theme.palette.success.main }} />;
      case 'warning': return <WarningIcon sx={{ color: theme.palette.warning.main }} />;
      case 'critical': return <CriticalIcon sx={{ color: theme.palette.error.main }} />;
      case 'inactive': return <InactiveIcon sx={{ color: theme.palette.text.disabled }} />;
      default: return <WarningIcon sx={{ color: theme.palette.warning.main }} />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'healthy': return theme.palette.success.main;
      case 'warning': return theme.palette.warning.main;
      case 'critical': return theme.palette.error.main;
      case 'inactive': return theme.palette.text.disabled;
      default: return theme.palette.warning.main;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'healthy': return 'Норма';
      case 'warning': return 'Внимание';
      case 'critical': return 'Критично';
      case 'inactive': return 'Не активен';
      default: return 'Неизвестно';
    }
  };

  const handleClick = () => {
    navigate(path);
  };

  return (
    <Card 
      sx={{ 
        height: '100%',
        display: 'flex', 
        flexDirection: 'column',
        borderLeft: `4px solid ${getStatusColor()}`,
        transition: 'transform 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 4
        }
      }}
    >
      <CardActionArea 
        onClick={handleClick}
        sx={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'flex-start',
          height: '100%'
        }}
      >
        <CardContent sx={{ width: '100%', p: 2 }}>
          <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
            <Box sx={{ 
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 1,
              p: 1,
              bgcolor: `${getStatusColor()}10`
            }}>
              {getStatusIcon()}
            </Box>
            <Box sx={{ flexGrow: 1 }}>
              <Typography variant="h6" component="div" noWrap>
                {title}
              </Typography>
            </Box>
            <Chip 
              size="small" 
              label={getStatusText()}
              sx={{ 
                bgcolor: `${getStatusColor()}20`,
                color: getStatusColor(),
                fontWeight: 'medium'
              }} 
            />
          </Stack>
          
          <Typography 
            variant="body2" 
            color="text.secondary" 
            sx={{ 
              mb: 2,
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
              height: '40px'
            }}
          >
            {description}
          </Typography>
          
          <Box sx={{ width: '100%', mt: 'auto' }}>
            <Typography variant="caption" color="text.secondary" display="block">
              Обновлено: {new Date(lastUpdated).toLocaleString('ru-RU')}
            </Typography>
          </Box>
        </CardContent>
      </CardActionArea>
    </Card>
  );
};

export default ZondCard; 