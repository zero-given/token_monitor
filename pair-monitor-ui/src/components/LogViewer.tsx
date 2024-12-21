import React from 'react';
import { Paper, Typography, Box, Chip } from '@mui/material';
import InfoIcon from '@mui/icons-material/Info';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';

interface LogEntry {
  level: string;
  message: string;
  timestamp: string;
}

interface LogViewerProps {
  logs: LogEntry[];
}

const LogViewer: React.FC<LogViewerProps> = ({ logs }) => {
  const getLogIcon = (level: string) => {
    switch (level.toLowerCase()) {
      case 'success':
        return <CheckCircleIcon fontSize="small" color="success" />;
      case 'warning':
        return <WarningIcon fontSize="small" color="warning" />;
      case 'error':
        return <ErrorIcon fontSize="small" color="error" />;
      default:
        return <InfoIcon fontSize="small" color="info" />;
    }
  };

  const getLogColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'success':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'info';
    }
  };

  return (
    <Paper 
      variant="outlined" 
      sx={{ 
        p: 2, 
        mb: 2, 
        backgroundColor: 'background.paper',
        maxHeight: '200px',
        overflowY: 'auto',
        '&::-webkit-scrollbar': {
          width: '8px',
        },
        '&::-webkit-scrollbar-track': {
          background: 'rgba(0,0,0,0.1)',
          borderRadius: '4px',
        },
        '&::-webkit-scrollbar-thumb': {
          background: 'rgba(255,255,255,0.1)',
          borderRadius: '4px',
          '&:hover': {
            background: 'rgba(255,255,255,0.2)',
          },
        },
      }}
    >
      <Typography variant="h6" gutterBottom>
        Server Activity
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column-reverse' }}>
        {logs.map((log, index) => (
          <Box 
            key={index} 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              mb: 1,
              opacity: 1 - (index * 0.1), // Fade out older logs
              minHeight: '28px',
            }}
          >
            <Chip
              icon={getLogIcon(log.level)}
              label={log.level.toUpperCase()}
              size="small"
              color={getLogColor(log.level) as any}
              sx={{ mr: 1, minWidth: '90px' }}
            />
            <Typography 
              variant="body2" 
              sx={{ 
                mr: 2,
                color: 'text.secondary',
                fontSize: '0.75rem',
                minWidth: '75px'
              }}
            >
              {new Date(log.timestamp).toLocaleTimeString()}
            </Typography>
            <Typography variant="body2">
              {log.message}
            </Typography>
          </Box>
        ))}
      </Box>
    </Paper>
  );
};

export default LogViewer; 