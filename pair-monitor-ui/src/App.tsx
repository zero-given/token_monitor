import React, { useEffect, useState } from 'react';
import { Container, CssBaseline, ThemeProvider, createTheme, AppBar, Toolbar, Typography, Box } from '@mui/material';
import { Pair } from './types';
import PairCard from './components/PairCard';
import LogViewer from './components/LogViewer';
import io from 'socket.io-client';

const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#0a1929',
      paper: '#132f4c',
    },
  },
  typography: {
    h5: {
      fontWeight: 600,
    },
    h6: {
      fontWeight: 600,
    },
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
  },
});

interface LogEntry {
  level: string;
  message: string;
  timestamp: string;
}

function App() {
  const [pairs, setPairs] = useState<Pair[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);

  const addLog = (level: string, message: string, timestamp: string) => {
    setLogs(prevLogs => {
      const newLogs = [{ level, message, timestamp }, ...prevLogs];
      // Keep only the last 50 logs
      return newLogs.slice(0, 50);
    });
  };

  useEffect(() => {
    // Initial fetch of pairs
    fetch('http://localhost:5001/pairs')
      .then(response => response.json())
      .then(data => {
        setPairs(data);
        setLastUpdate(new Date());
        addLog('success', 'Successfully fetched existing pairs', new Date().toISOString());
      })
      .catch(error => {
        console.error('Error fetching pairs:', error);
        addLog('error', `Failed to fetch pairs: ${error.message}`, new Date().toISOString());
      });

    // Set up WebSocket connection
    const socket = io('http://localhost:5001');

    socket.on('connect', () => {
      addLog('success', 'Connected to server', new Date().toISOString());
    });

    socket.on('disconnect', () => {
      addLog('error', 'Disconnected from server', new Date().toISOString());
    });

    socket.on('new_pair', (pair: Pair) => {
      setPairs(prevPairs => [pair, ...prevPairs]);
      setLastUpdate(new Date());
      addLog('info', `New pair detected: ${pair.token0_symbol}/${pair.token1_symbol}`, new Date().toISOString());
    });

    socket.on('pair_updated', (updatedPair: Pair) => {
      setPairs(prevPairs => 
        prevPairs.map(pair => 
          pair.pair_address === updatedPair.pair_address ? updatedPair : pair
        )
      );
      setLastUpdate(new Date());
      addLog('info', `Updated pair: ${updatedPair.token0_symbol}/${updatedPair.token1_symbol}`, new Date().toISOString());
    });

    socket.on('server_log', (log: { level: string; message: string; timestamp: string }) => {
      addLog(log.level, log.message, log.timestamp);
    });

    return () => {
      socket.disconnect();
    };
  }, []);

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Box sx={{ flexGrow: 1 }}>
        <AppBar position="fixed" elevation={0} sx={{ backgroundColor: 'background.paper', borderBottom: 1, borderColor: 'divider' }}>
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Uniswap V2 Pair Monitor
            </Typography>
            {lastUpdate && (
              <Typography variant="body2" color="text.secondary">
                Last update: {lastUpdate.toLocaleTimeString()}
              </Typography>
            )}
          </Toolbar>
        </AppBar>
        <Toolbar /> {/* Spacer for fixed AppBar */}
        <Container maxWidth="lg" sx={{ py: 4 }}>
          <LogViewer logs={logs} />
          {pairs.map(pair => (
            <PairCard key={pair.pair_address} pair={pair} />
          ))}
          {pairs.length === 0 && (
            <Typography variant="body1" color="text.secondary" align="center" sx={{ mt: 4 }}>
              No pairs detected yet. Waiting for new pairs...
            </Typography>
          )}
        </Container>
      </Box>
    </ThemeProvider>
  );
}

export default App;
